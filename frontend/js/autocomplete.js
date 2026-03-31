const chatInput = document.getElementById("chatInput");
const autocompleteList = document.getElementById("autocompleteList");

if (chatInput && autocompleteList) {
  const CONFIG = {
    MIN_QUERY_LEN: 2,
    DEBOUNCE_MS: 120,
    MAX_SUGGESTIONS: 8,

    // Fuzzy search via Fuse.js (crypto prioritized)
    FUSE_LIMIT_CRYPTO: 10,
    FUSE_LIMIT_DICT: 14,
    MIN_CONFIDENCE: 0.42,

    // If query matches as a prefix/substr, we bump confidence above Fuse score.
    PREFIX_BONUS: 0.08,
    CONTAINS_BONUS: 0.03
  };

  const DICT_URLS = {
    crypto: "../js/dictionary/crypto_glossary.csv",
    lemmas: "../js/dictionary/lemmas.csv",
    wordforms: "../js/dictionary/wordforms.csv"
  };

  // State
  let activeIndex = -1;
  let currentSuggestions = [];
  let loadPromise = null;

  let cryptoEntries = []; // [{ term, freq }]
  let dictEntries = []; // [{ term, freq }]
  let cryptoFuse = null;
  let dictFuse = null;
  let cryptoMaxFreq = 1;
  let dictMaxFreq = 1;

  /* -------------------------
     Utils
  ------------------------- */
  function escapeHtml(text) {
    return String(text)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function clamp01(x) {
    return Math.max(0, Math.min(1, x));
  }

  function debounce(fn, ms) {
    let t = null;
    return (...args) => {
      if (t) clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  function normalizeFreq(freq, maxFreq) {
    // Use log scaling to avoid overweighting very frequent tokens.
    const f = Number(freq);
    if (!Number.isFinite(f) || f <= 0) return 0;
    const mf = Number(maxFreq) || 1;
    return clamp01(Math.log10(1 + f) / Math.log10(1 + mf));
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = src;
      s.async = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error(`Failed to load script: ${src}`));
      document.head.appendChild(s);
    });
  }

  async function ensureFuseLoaded() {
    if (window.Fuse) return;
    // Fuse.js v6 UMD exposes global `Fuse`
    await loadScript("https://cdn.jsdelivr.net/npm/fuse.js@6.6.2/dist/fuse.min.js");
    if (!window.Fuse) throw new Error("Fuse.js is not available after loading");
  }

  async function fetchText(url) {
    const res = await fetch(url, { method: "GET", headers: { Accept: "text/plain,*/*" } });
    if (!res.ok) throw new Error(`Failed to fetch ${url} (${res.status})`);
    return await res.text();
  }

  // Simple CSV/TSV parser with quotes support.
  function parseDelimited(text, delimiter) {
    const rows = [];
    let row = [];
    let cell = "";
    let inQuotes = false;

    for (let i = 0; i < text.length; i++) {
      const ch = text[i];
      const next = text[i + 1];

      if (ch === '"') {
        if (inQuotes && next === '"') {
          cell += '"';
          i++;
        } else {
          inQuotes = !inQuotes;
        }
        continue;
      }

      if (!inQuotes && ch === delimiter) {
        row.push(cell);
        cell = "";
        continue;
      }

      if (!inQuotes && (ch === "\n" || ch === "\r")) {
        if (ch === "\r" && next === "\n") i++;
        if (cell.length > 0 || row.length > 0) row.push(cell);
        const finishedRow = row.map(c => c.trim());
        // Skip empty lines
        if (finishedRow.some(c => c !== "")) rows.push(finishedRow);
        row = [];
        cell = "";
        continue;
      }

      cell += ch;
    }

    if (cell.length > 0 || row.length > 0) {
      row.push(cell);
      const finishedRow = row.map(c => c.trim());
      if (finishedRow.some(c => c !== "")) rows.push(finishedRow);
    }

    return rows;
  }

  function parseCryptoGlossary(tsvText) {
    // Header: word\tfreq
    const lines = parseDelimited(tsvText, "\t");
    // Remove header if present
    const maybeHeader = (lines[0]?.[0] || "").toLowerCase();
    const start = maybeHeader === "word" ? 1 : 0;

    const out = [];
    for (let i = start; i < lines.length; i++) {
      const [termRaw, freqRaw] = lines[i] || [];
      const term = String(termRaw || "").trim();
      const freq = Number(freqRaw);
      if (!term || !Number.isFinite(freq)) continue;
      out.push({ term, freq });
    }
    return out;
  }

  function parseLemmas(tsvText) {
    // Header includes: Lemma, PoS, Freq(ipm), ...
    const lines = parseDelimited(tsvText, "\t");
    const header0 = (lines[0]?.[0] || "").toLowerCase();
    const start = header0 === "lemma" ? 1 : 0;

    const out = [];
    for (let i = start; i < lines.length; i++) {
      const row = lines[i] || [];
      const term = String(row[0] || "").trim();
      const freq = Number(row[2]);
      if (!term || !Number.isFinite(freq)) continue;
      out.push({ term, freq });
    }
    return out;
  }

  function parseWordforms(csvText) {
    // Header: Словоформа,Частота_ipm,Капитализация
    const rows = parseDelimited(csvText, ",");
    const start = (rows[0]?.[0] || "").toLowerCase().includes("словоформа") ? 1 : 0;

    const out = [];
    for (let i = start; i < rows.length; i++) {
      const row = rows[i] || [];
      const term = String(row[0] || "").trim();
      const freq = Number(row[1]);
      if (!term || !Number.isFinite(freq)) continue;
      out.push({ term, freq });
    }
    return out;
  }

  function buildUniqueMaxFreq(entries) {
    const map = new Map();
    for (const e of entries) {
      const term = e.term;
      const f = Number(e.freq) || 0;
      const prev = map.get(term);
      if (!prev || f > prev.freq) map.set(term, { term, freq: f });
    }
    return [...map.values()];
  }

  function findHighlightHtml(term, query) {
    // Best-effort highlighting: prefix first, then first substring occurrence.
    const t = String(term);
    const q = String(query);
    const qLower = q.toLowerCase();
    const tLower = t.toLowerCase();

    if (!qLower) return escapeHtml(t);

    let start = 0;
    if (tLower.startsWith(qLower)) {
      start = 0;
    } else {
      start = tLower.indexOf(qLower);
      if (start < 0) return escapeHtml(t);
    }

    const end = start + q.length;
    const left = escapeHtml(t.slice(0, start));
    const mid = escapeHtml(t.slice(start, end));
    const right = escapeHtml(t.slice(end));

    return `${left}<mark>${mid}</mark>${right}`;
  }

  function confidenceColor(conf01) {
    const conf = Math.round(conf01 * 100);
    if (conf >= 80) return { bg: "#d1fae5", fg: "#065f46", bd: "#10b981" }; // green-ish
    if (conf >= 55) return { bg: "#fef3c7", fg: "#92400e", bd: "#f59e0b" }; // amber-ish
    return { bg: "#fee2e2", fg: "#991b1b", bd: "#ef4444" }; // red-ish
  }

  function computeConfidence({ query, term, fuseScore, freq, source }) {
    const qLower = String(query).toLowerCase();
    const tLower = String(term).toLowerCase();

    let matchConf = 0;
    if (tLower === qLower) matchConf = 1;
    else if (tLower.startsWith(qLower)) matchConf = 0.92;
    else if (tLower.includes(qLower)) matchConf = 0.72;
    else {
      // Fuse score: lower is better. Convert to confidence.
      const s = Number(fuseScore);
      const fuseConf = Number.isFinite(s) ? clamp01(1 - s) : 0.35;
      matchConf = fuseConf * 0.95;
    }

    if (tLower.startsWith(qLower)) matchConf = clamp01(matchConf + CONFIG.PREFIX_BONUS);
    else if (tLower.includes(qLower)) matchConf = clamp01(matchConf + CONFIG.CONTAINS_BONUS);

    const maxFreq = source === "crypto" ? cryptoMaxFreq : dictMaxFreq;
    const freqNorm = normalizeFreq(freq, maxFreq);

    // Crypto gets a mild bonus only for already relevant matches.
    const cryptoBoost =
      source === "crypto"
        ? matchConf >= 0.82
          ? 0.08
          : matchConf >= 0.68
            ? 0.04
            : 0
        : 0;

    // Relevance dominates; frequency helps tie-break similar terms.
    const conf01 = clamp01(0.78 * matchConf + 0.22 * freqNorm + cryptoBoost);
    return conf01;
  }

  async function ensureDictionariesLoaded() {
    if (loadPromise) return loadPromise;
    loadPromise = (async () => {
      await ensureFuseLoaded();

      // Load and parse dictionaries
      const [cryptoText, lemmasText, wordformsText] = await Promise.all([
        fetchText(DICT_URLS.crypto),
        fetchText(DICT_URLS.lemmas),
        fetchText(DICT_URLS.wordforms)
      ]);

      cryptoEntries = parseCryptoGlossary(cryptoText);
      const lemmas = parseLemmas(lemmasText);
      const wordforms = parseWordforms(wordformsText);

      // Combine dict sources and dedupe by max frequency
      dictEntries = buildUniqueMaxFreq([
        ...lemmas,
        ...wordforms
      ]);

      cryptoMaxFreq = cryptoEntries.reduce((m, e) => Math.max(m, Number(e.freq) || 0), 1);
      dictMaxFreq = dictEntries.reduce((m, e) => Math.max(m, Number(e.freq) || 0), 1);

      // Create Fuse indices (crypto separate to keep priority controllable)
      cryptoFuse = new window.Fuse(
        cryptoEntries,
        {
          keys: ["term"],
          includeScore: true,
          // Strict-ish but still fuzzy for small typos.
          threshold: 0.35,
          ignoreLocation: true,
          minMatchCharLength: 2
        }
      );

      dictFuse = new window.Fuse(
        dictEntries,
        {
          keys: ["term"],
          includeScore: true,
          threshold: 0.4,
          ignoreLocation: true,
          minMatchCharLength: 2
        }
      );
    })();

    return loadPromise;
  }

  /* -------------------------
     Rendering
  ------------------------- */
  function closeSuggestions() {
    autocompleteList.classList.remove("open");
    autocompleteList.innerHTML = "";
    activeIndex = -1;
    currentSuggestions = [];
  }

  function setActiveSuggestionUI(nextIndex) {
    activeIndex = nextIndex;
    const children = autocompleteList.children;
    for (let i = 0; i < children.length; i++) {
      children[i].classList.toggle("active", i === activeIndex);
    }
  }

  function chooseSuggestion(index) {
    const s = currentSuggestions[index];
    if (!s) return;
    const value = String(chatInput.value || "");
    const caret = typeof chatInput.selectionStart === "number" ? chatInput.selectionStart : value.length;
    const { start, end } = getTokenRangeAtCaret(value, caret);

    // Replace only the current token (the word being typed)
    const nextValue = value.slice(0, start) + s.term + value.slice(end);
    chatInput.value = nextValue;
    const nextCaret = start + s.term.length;
    try {
      chatInput.setSelectionRange(nextCaret, nextCaret);
    } catch (_) { }
    closeSuggestions();
    chatInput.focus();
  }

  function getTokenRangeAtCaret(text, caretIndex) {
    const t = String(text || "");
    const caret = Math.max(0, Math.min(Number(caretIndex) || 0, t.length));

    // We autocomplete "words": letters (latin/cyrillic), digits, '_' and '-'.
    const isWordChar = (ch) => /[0-9A-Za-zА-Яа-яЁё_\-]/.test(ch);

    let start = caret;
    while (start > 0 && isWordChar(t[start - 1])) start--;

    let end = caret;
    while (end < t.length && isWordChar(t[end])) end++;

    return { start, end, token: t.slice(start, end) };
  }

  function renderSuggestions(suggestions, query) {
    currentSuggestions = suggestions;
    activeIndex = -1;
    autocompleteList.innerHTML = "";

    for (let i = 0; i < suggestions.length; i++) {
      const s = suggestions[i];
      const confPct = Math.round((s.confidence01 || 0) * 100);
      const colors = confidenceColor(s.confidence01 || 0);
      const sourceBadgeClass = s.source === "crypto" ? "badge-crypto" : "badge-wiki";

      const li = document.createElement("li");
      li.className = "autocomplete-item";
      li.setAttribute("role", "option");
      li.setAttribute("aria-selected", "false");
      li.dataset.index = String(i);

      li.style.justifyContent = "space-between";

      li.innerHTML = `
        <span class="autocomplete-term" style="flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis;">
          ${findHighlightHtml(s.term, query)}
        </span>
        <span class="d-flex align-items-center gap-2" style="flex-shrink: 0;">
          <span class="badge ${sourceBadgeClass}">${s.source === "crypto" ? "crypto" : "dict"}</span>
          <span class="badge" style="background:${colors.bg}; color:${colors.fg}; border:1px solid ${colors.bd};">
            ${confPct}%
          </span>
        </span>
      `;

      li.addEventListener("mouseenter", () => setActiveSuggestionUI(i));
      li.addEventListener("click", () => chooseSuggestion(i));
      autocompleteList.appendChild(li);
    }

    if (suggestions.length) {
      autocompleteList.classList.add("open");
    } else {
      closeSuggestions();
    }
  }

  /* -------------------------
     Suggestion logic
  ------------------------- */
  async function computeSuggestions(query) {
    const q = String(query || "").trim();
    if (q.length < CONFIG.MIN_QUERY_LEN) return [];

    // Ensure dictionaries and fuse indices are ready.
    await ensureDictionariesLoaded();

    // Fuzzy search in both indices.
    const cryptoRes = cryptoFuse.search(q, { limit: CONFIG.FUSE_LIMIT_CRYPTO });
    const dictRes = dictFuse.search(q, { limit: CONFIG.FUSE_LIMIT_DICT });

    // Merge with dedupe and crypto priority.
    const byTerm = new Map(); // term -> candidate

    function upsertCandidate(source, term, freq, fuseScore) {
      const candidate = {
        term,
        source,
        freq: Number(freq) || 0,
        confidence01: computeConfidence({
          query: q,
          term,
          fuseScore,
          freq,
          source
        })
      };

      const existing = byTerm.get(term);
      if (!existing) {
        byTerm.set(term, candidate);
        return;
      }

      // Prefer crypto only when relevance is comparable.
      if (existing.source !== "crypto" && source === "crypto") {
        if ((candidate.confidence01 || 0) >= (existing.confidence01 || 0) - 0.03) {
          byTerm.set(term, candidate);
        }
        return;
      }

      if ((candidate.confidence01 || 0) > (existing.confidence01 || 0)) {
        byTerm.set(term, candidate);
      }
    }

    for (const r of cryptoRes || []) {
      const item = r.item || {};
      upsertCandidate("crypto", item.term, item.freq, r.score);
    }

    for (const r of dictRes || []) {
      const item = r.item || {};
      upsertCandidate("dict", item.term, item.freq, r.score);
    }

    const merged = [...byTerm.values()].filter(
      c => (c.confidence01 || 0) >= CONFIG.MIN_CONFIDENCE
    );
    // Stable ordering: if confidence ties, prefer crypto first.
    merged.sort((a, b) => {
      const d = (b.confidence01 || 0) - (a.confidence01 || 0);
      if (Math.abs(d) > 1e-9) return d;
      if (a.source === b.source) return a.term.localeCompare(b.term);
      return a.source === "crypto" ? -1 : 1;
    });

    return merged.slice(0, CONFIG.MAX_SUGGESTIONS);
  }

  const onInput = debounce(async () => {
    const value = String(chatInput.value || "");
    const caret = typeof chatInput.selectionStart === "number" ? chatInput.selectionStart : value.length;
    const { token } = getTokenRangeAtCaret(value, caret);
    const q = String(token || "").trim();

    if (!q || q.length < CONFIG.MIN_QUERY_LEN) {
      closeSuggestions();
      return;
    }

    // Render immediately a lightweight "loading" state.
    autocompleteList.innerHTML = `
      <li style="cursor:default; justify-content:flex-start;">
        Loading suggestions...
      </li>
    `;
    autocompleteList.classList.add("open");

    try {
      const suggestions = await computeSuggestions(q);
      renderSuggestions(suggestions, q);
    } catch (e) {
      console.error(e);
      autocompleteList.innerHTML = "";
      closeSuggestions();
    }
  }, CONFIG.DEBOUNCE_MS);

  /* -------------------------
     Event handlers
  ------------------------- */
  chatInput.addEventListener("input", onInput);

  // Close on outside click
  document.addEventListener("click", (e) => {
    if (!autocompleteList.classList.contains("open")) return;
    if (e.target === chatInput) return;
    if (autocompleteList.contains(e.target)) return;
    closeSuggestions();
  });

  chatInput.addEventListener("keydown", (e) => {
    if (!autocompleteList.classList.contains("open")) return;
    if (!currentSuggestions.length) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = activeIndex < 0 ? 0 : (activeIndex + 1) % currentSuggestions.length;
      setActiveSuggestionUI(next);
      return;
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      const next = activeIndex < 0 ? currentSuggestions.length - 1 : (activeIndex - 1 + currentSuggestions.length) % currentSuggestions.length;
      setActiveSuggestionUI(next);
      return;
    }

    if (e.key === "Escape") {
      e.preventDefault();
      closeSuggestions();
      return;
    }

    if (e.key === " ") {
      // Space means "finish token": close suggestions so the next token starts cleanly.
      closeSuggestions();
      return;
    }

    if (e.key === "Tab") {
      if (activeIndex >= 0) {
        e.preventDefault();
        chooseSuggestion(activeIndex);
      }
      return;
    }

    if (e.key === "Enter") {
      // If user picked a suggestion via arrows, set it before chat.js sends.
      if (activeIndex >= 0) {
        chooseSuggestion(activeIndex);
      }
      return;
    }
  });
}

