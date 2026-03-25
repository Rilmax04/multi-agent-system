/* =========================
   MOCK DATA (dynamic JSON)
========================= */

let messages = [
  {
    id: 1,
    type: "ai",
    content: "Hello! I'm your cryptocurrency analysis assistant. Ask me anything about crypto markets, prices, trends, or specific coins."
  },
  {
    id: 2,
    type: "user",
    content: "What is the current Bitcoin price?"
  },
  {
    id: 3,
    type: "ai",
    content: "Bitcoin (BTC) is currently trading at $45,234.50 USD, with a 24-hour change of +2.3%. The market cap is $884.5B and the 24-hour volume is $28.3B."
  }
];

const suggestedActions = [
  { label: "Compare BTC and ETH", icon: "bi-arrow-left-right" },
  { label: "Show top 5 coins", icon: "bi-graph-up" },
  { label: "Analyze volatility", icon: "bi-activity" }
];

const marketData = {
  coins: [
    {
      name: "Bitcoin (BTC)",
      change: "+2.3%",
      price: "$45,234.50",
      volume: "$28.3B",
      positive: true
    },
    {
      name: "Ethereum (ETH)",
      change: "+1.8%",
      price: "$2,456.30",
      volume: "$15.7B",
      positive: true
    }
  ],
  trend: "Bullish momentum across major cryptocurrencies",
  stats: {
    marketCap: "$1.82T",
    volume24h: "$89.4B",
    dominance: "48.6%"
  }
};


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
    bubble.className =
      "message " + (msg.type === "user"
        ? "message-user"
        : "message-ai");

    if (msg.content === "loading") {
      bubble.innerHTML = '<div class="loader"></div>';
    } else {
      bubble.textContent = msg.content;
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
    const res = await fetch("http://127.0.0.1:8000/ask", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json"
      },
      body: JSON.stringify({ question: text }) // TODO: markdown
    });

    let aiContent = "";

    if (res.ok) {
      const data = await res.json();
      aiContent = data.answer ?? "";
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

    renderMessages();
  } catch (err) {
    console.error(err);

    messages = messages.filter(msg => msg.id !== loadingId);
    messages.push({
      id: Date.now() + 1,
      type: "ai",
      content: "Ошибка связи с бэкендом. Попробуйте ещё раз."
    });

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

renderMessages();
renderMarket();