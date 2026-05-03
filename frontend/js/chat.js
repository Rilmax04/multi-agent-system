/* =========================
   CONFIG
========================= */

const LAST_TRACE_STORAGE_KEY = "rag:last_trace";
const CHAT_MESSAGES_STORAGE_KEY = "rag:chat_messages";

/* =========================
   CHAT STATE
========================= */

let messages = [
  {
    id: 1,
    type: "ai",
    content:
      "Hello! I'm your cryptocurrency analysis assistant. Ask me anything about crypto markets, prices, trends, or specific coins."
  }
];

function getPersistableMessages(msgs) {
  // Do not persist transient UI states.
  return (Array.isArray(msgs) ? msgs : []).filter(m => m?.content !== "loading");
}

function persistMessages() {
  try {
    localStorage.setItem(
      CHAT_MESSAGES_STORAGE_KEY,
      JSON.stringify(getPersistableMessages(messages))
    );
  } catch (_) {}
}

function restoreMessages() {
  const saved = safeJsonParse(localStorage.getItem(CHAT_MESSAGES_STORAGE_KEY) || "");
  if (Array.isArray(saved) && saved.length) {
    messages = saved;
  }
}

const FALLBACK_SUGGESTED_ACTIONS = [
  { label: "Сравни текущие цены BTC и ETH", icon: "bi-arrow-left-right" },
  { label: "Покажи топ-5 криптовалют по капитализации", icon: "bi-graph-up" },
  { label: "Как менялась цена Bitcoin за последние 7 дней?", icon: "bi-activity" }
];

/* =========================
   MARKET DATA (real backend)
========================= */

let marketData = null;

async function fetchMarketSnapshot({ coins = ["bitcoin", "ethereum"], source = null } = {}) {
  const params = new URLSearchParams();
  params.set("coins", coins.join(","));
  if (source) params.set("source", source);

  const res = await fetch(`${BACKEND_URL}/market/prices?${params.toString()}`, {
    method: "GET",
    headers: { Accept: "application/json" }
  });
  if (!res.ok) {
    const err = await parseJsonOrNull(res);
    throw new Error(err?.detail || `Market request failed (${res.status})`);
  }
  clearGlobalError();
  return res.json();
}


/* =========================
   CHAT RENDER
========================= */

const chatBox = document.getElementById("chatMessages");

function renderMessages() {
  chatBox.innerHTML = "";
  messages.forEach(msg => {
    const wrapper = document.createElement("div");
    wrapper.className = "d-flex " + (msg.type === "user"
      ? "justify-content-end"
      : "justify-content-start");

    const bubble = document.createElement("div");
    bubble.className = "message " + (msg.type === "user"
      ? "message-user"
      : "message-ai");

    if (msg.content === "loading") {
      bubble.innerHTML = '<div class="loader"></div>';
    } else if (msg.type === "user") {
      bubble.textContent = msg.content;
    } else {
      bubble.innerHTML = marked.parse(msg.content);
    }

    wrapper.appendChild(bubble);
    chatBox.appendChild(wrapper);
  });
  chatBox.scrollTop = chatBox.scrollHeight;
}


/* =========================
   SEND MESSAGE
========================= */

async function sendMessage() {
  const input = document.getElementById("chatInput");
  const text = input.value.trim();
  if (!text) return;

  messages.push({
    id: Date.now(),
    type: "user",
    content: text
  });
  persistMessages();

  input.value = "";
  renderMessages();

  const loadingId = Date.now() + 100;

  messages.push({
    id: loadingId,
    type: "ai",
    content: "loading"
  });

  renderMessages();

  try {
    const res = await fetch(`${BACKEND_URL}/ask`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: JSON.stringify({ question: text })
    });

    let aiContent = "";

    if (res.ok) {
      const data = await parseJsonOrNull(res);
      aiContent = data.answer ?? "";
      clearGlobalError();

      // Save last trace for Workflow page (real backend data)
      try {
        const payload = {
          question: text,
          answer: data.answer ?? "",
          total_time_ms: data.total_time_ms ?? null,
          trace: data.trace ?? null,
          saved_at: Date.now()
        };
        localStorage.setItem(LAST_TRACE_STORAGE_KEY, JSON.stringify(payload));
      } catch (_) {}
    } else if (res.status === 422) {
      const data = await parseJsonOrNull(res);
      const detail = data?.detail;

      if (Array.isArray(detail) && detail.length) {
        aiContent = `Validation Error: ${detail.map(d => d.msg).join("; ")}`;
      } else {
        aiContent = "Validation Error";
      }
      showGlobalError("Could not process the request. Please check the input data.");
    } else {
      const data = await parseJsonOrNull(res);
      aiContent = data?.detail || `Request failed with status ${res.status}`;
      showGlobalError(aiContent || "The backend returned an invalid response.");
    }

    messages = messages.filter(msg => msg.id !== loadingId);
    messages.push({
      id: Date.now() + 1,
      type: "ai",
      content: aiContent || "Ответ не сформирован"
    });
    persistMessages();

    renderMessages();
    refreshSuggestedActions();
  } catch (err) {
    console.error(err);
    showGlobalError("Backend service is unavailable. Please try again later.");

    messages = messages.filter(msg => msg.id !== loadingId);
    messages.push({
      id: Date.now() + 1,
      type: "ai",
      content: "Ошибка связи с бэкендом. Попробуйте ещё раз."
    });
    persistMessages();

    renderMessages();
    refreshSuggestedActions();
  }
}

document.getElementById("sendBtn").onclick = sendMessage;

document
  .getElementById("chatInput")
  .addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });


/* =========================
   SUGGESTED ACTIONS (LLM + fallback)
========================= */

function getRecentUserQuestions(msgs, limit = 15) {
  const out = [];
  for (const m of msgs) {
    if (m?.type === "user" && m.content && m.content !== "loading") {
      const t = String(m.content).trim();
      if (t) out.push(t);
    }
  }
  return out.slice(-limit);
}

function iconForSuggestionIndex(i) {
  const icons = [
    "bi-arrow-left-right",
    "bi-graph-up",
    "bi-activity",
    "bi-lightbulb",
    "bi-search",
    "bi-currency-bitcoin"
  ];
  return icons[i % icons.length];
}

function renderSuggestedActionButtons(actions) {
  const actionsContainer = document.getElementById("suggestedActions");
  if (!actionsContainer) return;
  actionsContainer.innerHTML = "";
  for (const action of actions) {
    const btn = document.createElement("button");
    btn.className = "btn btn-outline-secondary btn-sm d-flex align-items-center gap-2";
    const icon = document.createElement("i");
    icon.className = `bi ${action.icon}`;
    btn.appendChild(icon);
    btn.appendChild(document.createTextNode(` ${action.label}`));
    btn.onclick = () => {
      document.getElementById("chatInput").value = action.label;
    };
    actionsContainer.appendChild(btn);
  }
}

async function refreshSuggestedActions() {
  const actionsContainer = document.getElementById("suggestedActions");
  if (!actionsContainer) return;
  actionsContainer.innerHTML =
    '<span class="text-muted small">Updating suggestions…</span>';
  try {
    const past = getRecentUserQuestions(messages);
    const res = await fetch(`${BACKEND_URL}/suggest`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: JSON.stringify({ past_questions: past })
    });
    if (!res.ok) throw new Error(`suggest ${res.status}`);
    const data = await parseJsonOrNull(res);
    clearGlobalError();
    const labels = Array.isArray(data.suggestions)
      ? data.suggestions.map(s => String(s).trim()).filter(Boolean).slice(0, 3)
      : [];
    const actions = labels.map((label, i) => ({
      label,
      icon: iconForSuggestionIndex(i)
    }));
    renderSuggestedActionButtons(
      actions.length >= 3 ? actions : FALLBACK_SUGGESTED_ACTIONS
    );
  } catch (err) {
    console.warn("Suggested actions:", err);
    showGlobalError("Failed to load suggested actions.");
    renderSuggestedActionButtons(FALLBACK_SUGGESTED_ACTIONS);
  }
}


/* =========================
   MARKET INFO RENDER
========================= */

const marketContainer = document.getElementById("marketInfo");

function renderMarket() {
  if (!marketData) {
    marketContainer.innerHTML = `
      <div class="text-muted small">Loading market data…</div>
    `;
    return;
  }

  const coinsHTML = marketData.coins.map(c => `
    <div class="p-3 mb-3 market-card">
      <div class="d-flex justify-content-between mb-1">
        <span class="small text-secondary">${c.name}</span>
        <span class="small fw-semibold ${c.changeClass}">
          ${c.change}
        </span>
      </div>
      <div class="fs-4 fw-bold">${c.price}</div>
      <div class="small text-muted">24h Volume: ${c.volume}</div>
    </div>
  `).join("");

  marketContainer.innerHTML = `
    ${coinsHTML}

    <div class="p-3 mb-3 border border-success rounded bg-success-subtle">
      <div class="d-flex align-items-center gap-2 mb-2">
        <i class="bi bi-graph-up text-success"></i>
        <span class="fw-semibold text-success">BTC/ETH 24h Signal</span>
      </div>
      <div class="small text-success">
        ${marketData.trend}
      </div>
    </div>

    <div class="pt-3 border-top">
      <div class="d-flex justify-content-between small mb-2">
        <span class="text-secondary">BTC+ETH Market Cap</span>
        <span class="fw-semibold">${marketData.stats.marketCap}</span>
      </div>
      <div class="d-flex justify-content-between small mb-2">
        <span class="text-secondary">BTC+ETH 24h Volume</span>
        <span class="fw-semibold">${marketData.stats.volume24h}</span>
      </div>
      <div class="d-flex justify-content-between small">
        <span class="text-secondary">BTC Share of BTC+ETH Cap</span>
        <span class="fw-semibold">${marketData.stats.dominance}</span>
      </div>
    </div>
  `;
}


/* =========================
   INIT
========================= */

async function loadMarket() {
  marketData = null;
  renderMarket();

  try {
    const prices = await fetchMarketSnapshot({ coins: ["bitcoin", "ethereum"] });
    const btc = prices?.bitcoin;
    const eth = prices?.ethereum;
    const coins = [btc, eth].filter(Boolean).map(p => {
      const changeValue = Number(p.change_24h_percent);
      const changeClass = Number.isFinite(changeValue)
        ? changeValue >= 0 ? "text-success" : "text-danger"
        : "text-muted";
      const symbol = p.coin_id === "bitcoin" ? "BTC" : p.coin_id === "ethereum" ? "ETH" : p.coin_id?.toUpperCase();
      const name = p.coin_id === "bitcoin" ? "Bitcoin" : p.coin_id === "ethereum" ? "Ethereum" : p.coin_id;
      return {
        name: `${name} (${symbol})`,
        change: formatPercent(p.change_24h_percent),
        price: formatUsd(p.price_usd),
        volume: formatUsdCompact(p.volume_24h_usd),
        changeClass,
        marketCapUsd: p.market_cap_usd ?? null
      };
    });

    const capValues = [btc?.market_cap_usd, eth?.market_cap_usd]
      .map(Number)
      .filter(Number.isFinite);
    const volumeValues = [btc?.volume_24h_usd, eth?.volume_24h_usd]
      .map(Number)
      .filter(Number.isFinite);
    const changeValues = [btc?.change_24h_percent, eth?.change_24h_percent]
      .map(Number)
      .filter(Number.isFinite);

    const totalMarketCap = capValues.length === 2
      ? capValues.reduce((sum, value) => sum + value, 0)
      : null;
    const totalVolume = volumeValues.length === 2
      ? volumeValues.reduce((sum, value) => sum + value, 0)
      : null;
    const btcDominance =
      totalMarketCap > 0 && Number.isFinite(Number(btc?.market_cap_usd))
        ? (Number(btc.market_cap_usd) / totalMarketCap) * 100
        : null;

    const avgChange = changeValues.length
      ? changeValues.reduce((sum, value) => sum + value, 0) / changeValues.length
      : null;
    const trend =
      avgChange == null
        ? "24h change data is unavailable from the backend"
        : avgChange > 0.5
          ? "Positive average 24h change across BTC and ETH"
          : avgChange < -0.5
            ? "Negative average 24h change across BTC and ETH"
            : "Mixed or flat average 24h change across BTC and ETH";

    marketData = {
      coins,
      trend,
      stats: {
        marketCap: formatUsdCompact(totalMarketCap),
        volume24h: formatUsdCompact(totalVolume),
        dominance: btcDominance == null ? "—" : `${btcDominance.toFixed(1)}%`
      }
    };
    clearGlobalError();
  } catch (e) {
    showGlobalError("Failed to load market data.");
    marketData = {
      coins: [],
      trend: "Market data unavailable",
      stats: { marketCap: "—", volume24h: "—", dominance: "—" },
      error: String(e?.message || e)
    };
  }

  renderMarket();
}

restoreMessages();
renderMessages();
loadMarket();
refreshSuggestedActions();
