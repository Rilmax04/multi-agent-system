/* =========================
   CONFIG
========================= */

const BACKEND_URL = "http://127.0.0.1:8000";
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

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (_) {
    return null;
  }
}

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

const suggestedActions = [
  { label: "Compare BTC and ETH", icon: "bi-arrow-left-right" },
  { label: "Show top 5 coins", icon: "bi-graph-up" },
  { label: "Analyze volatility", icon: "bi-activity" }
];

/* =========================
   MARKET DATA (real backend)
========================= */

let marketData = null;

function formatUsdCompact(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2
  }).format(Number(value));
}

function formatUsd(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(Number(value));
}

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";
  const v = Number(value);
  const sign = v > 0 ? "+" : "";
  return `${sign}${v.toFixed(2)}%`;
}

async function fetchMarketSnapshot({ coins = ["bitcoin", "ethereum"], source = null } = {}) {
  const params = new URLSearchParams();
  params.set("coins", coins.join(","));
  if (source) params.set("source", source);

  const res = await fetch(`${BACKEND_URL}/market/prices?${params.toString()}`, {
    method: "GET",
    headers: { Accept: "application/json" }
  });
  if (!res.ok) {
    const err = await res.json().catch(() => null);
    throw new Error(err?.detail || `Market request failed (${res.status})`);
  }
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
      const data = await res.json();
      aiContent = data.answer ?? "";

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
      const data = await res.json().catch(() => null);
      const detail = data?.detail;

      if (Array.isArray(detail) && detail.length) {
        aiContent = `Validation Error: ${detail.map(d => d.msg).join("; ")}`;
      } else {
        aiContent = "Validation Error";
      }
    } else {
      const data = await res.json().catch(() => null);
      aiContent = data?.detail || `Request failed with status ${res.status}`;
    }

    messages = messages.filter(msg => msg.id !== loadingId);
    messages.push({
      id: Date.now() + 1,
      type: "ai",
      content: aiContent || "Ответ не сформирован"
    });
    persistMessages();

    renderMessages();
  } catch (err) {
    console.error(err);

    messages = messages.filter(msg => msg.id !== loadingId);
    messages.push({
      id: Date.now() + 1,
      type: "ai",
      content: "Ошибка связи с бэкендом. Попробуйте ещё раз."
    });
    persistMessages();

    renderMessages();
  }
}

document.getElementById("sendBtn").onclick = sendMessage;

document
  .getElementById("chatInput")
  .addEventListener("keypress", e => {
    if (e.key === "Enter") sendMessage();
  });


/* =========================
   SUGGESTED ACTIONS
========================= */

const actionsContainer = document.getElementById("suggestedActions");

suggestedActions.forEach(action => {
  const btn = document.createElement("button");
  btn.className = "btn btn-outline-secondary btn-sm d-flex align-items-center gap-2";

  btn.innerHTML = `
    <i class="bi ${action.icon}"></i>
    ${action.label}
  `;

  btn.onclick = () => {
    document.getElementById("chatInput").value = action.label;
  };

  actionsContainer.appendChild(btn);
});


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
        <span class="small fw-semibold ${c.positive ? 'text-success' : 'text-danger'}">
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
        <span class="fw-semibold text-success">Market Trend</span>
      </div>
      <div class="small text-success">
        ${marketData.trend}
      </div>
    </div>

    <div class="pt-3 border-top">
      <div class="d-flex justify-content-between small mb-2">
        <span class="text-secondary">Total Market Cap</span>
        <span class="fw-semibold">${marketData.stats.marketCap}</span>
      </div>
      <div class="d-flex justify-content-between small mb-2">
        <span class="text-secondary">24h Volume</span>
        <span class="fw-semibold">${marketData.stats.volume24h}</span>
      </div>
      <div class="d-flex justify-content-between small">
        <span class="text-secondary">BTC Dominance</span>
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
      const isPositive = (p.change_24h_percent ?? 0) >= 0;
      const symbol = p.coin_id === "bitcoin" ? "BTC" : p.coin_id === "ethereum" ? "ETH" : p.coin_id?.toUpperCase();
      const name = p.coin_id === "bitcoin" ? "Bitcoin" : p.coin_id === "ethereum" ? "Ethereum" : p.coin_id;
      return {
        name: `${name} (${symbol})`,
        change: formatPercent(p.change_24h_percent),
        price: formatUsd(p.price_usd),
        volume: formatUsdCompact(p.volume_24h_usd),
        positive: isPositive,
        marketCapUsd: p.market_cap_usd ?? null
      };
    });

    const totalMarketCap =
      (btc?.market_cap_usd ?? 0) + (eth?.market_cap_usd ?? 0);
    const totalVolume =
      (btc?.volume_24h_usd ?? 0) + (eth?.volume_24h_usd ?? 0);
    const btcDominance =
      totalMarketCap > 0 && btc?.market_cap_usd != null
        ? (btc.market_cap_usd / totalMarketCap) * 100
        : null;

    const avgChange =
      ((btc?.change_24h_percent ?? 0) + (eth?.change_24h_percent ?? 0)) / 2;
    const trend =
      avgChange > 0.5
        ? "Bullish momentum across major cryptocurrencies"
        : avgChange < -0.5
          ? "Bearish pressure across major cryptocurrencies"
          : "Mixed momentum across major cryptocurrencies";

    marketData = {
      coins,
      trend,
      stats: {
        marketCap: formatUsdCompact(totalMarketCap),
        volume24h: formatUsdCompact(totalVolume),
        dominance: btcDominance == null ? "—" : `${btcDominance.toFixed(1)}%`
      }
    };
  } catch (e) {
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