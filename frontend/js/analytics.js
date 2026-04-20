/* =========================
   CONFIG + STATE (real backend)
========================= */

const analyticsData = {
  // coin_id from backend (/market/top and /market/history/{coin_id})
  selectedCoinId: null,
  coins: [],
  labels: []
};

async function apiGet(path) {
  const res = await fetch(`${BACKEND_URL}${path}`, {
    method: "GET",
    headers: { Accept: "application/json" }
  });
  if (!res.ok) {
    const err = await parseJsonOrNull(res);
    throw new Error(err?.detail || `Request failed (${res.status})`);
  }
  clearGlobalError();
  return res.json();
}


/* =========================
   SELECT
========================= */

const select = document.getElementById("coinSelect");

function renderSelect() {
  select.innerHTML = analyticsData.coins.map(c => `
    <option value="${c.coin_id}"
      ${c.coin_id === analyticsData.selectedCoinId ? "selected" : ""}>
      ${c.name} (${c.symbol})
    </option>
  `).join("");
}


/* =========================
   TABLE
========================= */

const tableBody = document.getElementById("coinTable");

function renderTable() {
  tableBody.innerHTML = analyticsData.coins.map(c => `
    <tr>
      <td>
        <div class="fw-medium">${c.name}</div>
        <div class="text-muted small">${c.symbol}</div>
      </td>
      <td class="text-end fw-medium">${formatUsd(c.price_usd)}</td>
      <td class="text-end">
        <span class="${(c.change_24h_percent ?? 0) >= 0 ? 'text-success' : 'text-danger'} fw-medium">
          ${formatPercent(c.change_24h_percent)}
        </span>
      </td>
      <td class="text-end text-secondary">${formatUsdCompact(c.market_cap_usd)}</td>
      <td class="text-end text-secondary">${formatUsdCompact(c.volume_24h_usd)}</td>
    </tr>
  `).join("");
}


/* =========================
   CHARTS
========================= */

let priceChart;
let marketCapChart;

function renderCharts() {
  const coin = analyticsData.coins.find(c => c.coin_id === analyticsData.selectedCoinId);
  if (!coin) return;

  document.getElementById("priceChartTitle")
    .textContent = `Price Chart (${coin.symbol})`;

  if (priceChart) priceChart.destroy();
  if (marketCapChart) marketCapChart.destroy();

  priceChart = new Chart(
    document.getElementById("priceChart"),
    {
      type: "line",
      data: {
        labels: analyticsData.labels,
        datasets: [{
          label: "Price",
          data: coin.priceHistory ?? [],
          borderWidth: 2,
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    }
  );

  marketCapChart = new Chart(
    document.getElementById("marketCapChart"),
    {
      type: "bar",
      data: {
        labels: analyticsData.labels,
        datasets: [{
          label: "Market Cap (B$)",
          data: coin.marketCapHistory ?? [],
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    }
  );
}


/* =========================
   APPLY BUTTON
========================= */

document.getElementById("applyBtn").onclick = () => {
  analyticsData.selectedCoinId = select.value;
  loadSelectedCoinSeries().catch(e => {
    console.error(e);
    showGlobalError("Failed to update charts for the selected coin.");
  });
};


/* =========================
   INIT
========================= */

async function loadTopCoins() {
  const top = await apiGet(`/market/top?limit=10`);

  // Normalize to the fields we use in UI.
  analyticsData.coins = (Array.isArray(top) ? top : []).map(c => ({
    rank: c.rank,
    coin_id: c.coin_id,
    symbol: c.symbol,
    name: c.name,
    price_usd: c.price_usd,
    market_cap_usd: c.market_cap_usd,
    change_24h_percent: c.change_24h_percent,
    source: c.source,
    // will be filled by loadSelectedCoinSeries
    priceHistory: [],
    marketCapHistory: []
  }));

  if (!analyticsData.selectedCoinId && analyticsData.coins.length) {
    analyticsData.selectedCoinId = analyticsData.coins[0].coin_id;
  }

  renderSelect();
  renderTable();
}

function buildLabelsFromTimestamps(timestampsSec) {
  return timestampsSec.map(ts => {
    const d = new Date(ts * 1000);
    return d.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
  });
}

async function loadSelectedCoinSeries() {
  const coinId = analyticsData.selectedCoinId;
  if (!coinId) return;

  const hist = await apiGet(`/market/history/${encodeURIComponent(coinId)}?days=7`);
  const points = Array.isArray(hist?.prices) ? hist.prices : [];

  const timestamps = points.map(p => p.timestamp);
  const prices = points.map(p => p.price);
  analyticsData.labels = buildLabelsFromTimestamps(timestamps);

  const coin = analyticsData.coins.find(c => c.coin_id === coinId);
  if (coin) {
    coin.priceHistory = prices;

    // Backend does not provide market cap history in /market/history,
    // so we display current market cap repeated across the period.
    const capB = coin.market_cap_usd != null ? Number(coin.market_cap_usd) / 1e9 : null;
    coin.marketCapHistory = capB == null ? prices.map(() => null) : prices.map(() => capB);
  }

  renderCharts();
}

async function init() {
  try {
    await loadTopCoins();
    await loadSelectedCoinSeries();
  } catch (e) {
    console.error(e);
    showGlobalError("Failed to load analytics data from the backend.");
  }
}

init();
