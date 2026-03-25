/* =========================
   MOCK JSON WITH CHART DATA
========================= */

const analyticsData = {
  selectedCoin: "BTC",

  coins: [
    {
      name: "Bitcoin",
      symbol: "BTC",
      price: "$45,234.50",
      change: "+2.3%",
      marketCap: "$884.5B",
      volume: "$28.3B",
      positive: true,
      priceHistory: [42000, 42500, 43000, 43800, 44100, 44700, 45234],
      marketCapHistory: [820, 830, 845, 860, 870, 880, 884]
    },
    {
      name: "Ethereum",
      symbol: "ETH",
      price: "$2,456.30",
      change: "+1.8%",
      marketCap: "$295.2B",
      volume: "$15.7B",
      positive: true,
      priceHistory: [2100, 2180, 2230, 2300, 2360, 2410, 2456],
      marketCapHistory: [250, 258, 265, 272, 280, 289, 295]
    },
    {
      name: "Cardano",
      symbol: "ADA",
      price: "$0.54",
      change: "-0.5%",
      marketCap: "$18.9B",
      volume: "$324.5M",
      positive: false,
      priceHistory: [0.60, 0.59, 0.58, 0.57, 0.56, 0.55, 0.54],
      marketCapHistory: [22, 21.5, 21, 20.4, 19.8, 19.2, 18.9]
    },
    {
      name: "Solana",
      symbol: "SOL",
      price: "$98.45",
      change: "+4.2%",
      marketCap: "$41.2B",
      volume: "$2.1B",
      positive: true,
      priceHistory: [82, 85, 88, 90, 94, 96, 98],
      marketCapHistory: [32, 34, 36, 37.5, 39, 40.5, 41.2]
    },
    {
      name: "Ripple",
      symbol: "XRP",
      price: "$0.62",
      change: "-1.2%",
      marketCap: "$33.5B",
      volume: "$1.8B",
      positive: false,
      priceHistory: [0.70, 0.69, 0.67, 0.66, 0.65, 0.63, 0.62],
      marketCapHistory: [38, 37, 36, 35.5, 34.7, 34, 33.5]
    }
  ],

  labels: ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
};


/* =========================
   SELECT
========================= */

const select = document.getElementById("coinSelect");

function renderSelect() {
  select.innerHTML = analyticsData.coins.map(c => `
    <option value="${c.symbol}"
      ${c.symbol === analyticsData.selectedCoin ? "selected" : ""}>
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
      <td class="text-end fw-medium">${c.price}</td>
      <td class="text-end">
        <span class="${c.positive ? 'text-success' : 'text-danger'} fw-medium">
          ${c.change}
        </span>
      </td>
      <td class="text-end text-secondary">${c.marketCap}</td>
      <td class="text-end text-secondary">${c.volume}</td>
    </tr>
  `).join("");
}


/* =========================
   CHARTS
========================= */

let priceChart;
let marketCapChart;

function renderCharts() {
  const coin = analyticsData.coins.find(
    c => c.symbol === analyticsData.selectedCoin
  );

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
          data: coin.priceHistory,
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
          data: coin.marketCapHistory,
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
  analyticsData.selectedCoin = select.value;
  renderCharts();
};


/* =========================
   INIT
========================= */

renderSelect();
renderTable();
renderCharts();