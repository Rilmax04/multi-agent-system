/* =========================
   MOCK JSON (backend later)
========================= */

const workflowData = {
  totalTime: "1.2 seconds",
  steps: [
    {
      agent: "ControllerAgent",
      title: "User Intent Detection",
      description: "Detected user intent: Query about Bitcoin price",
      details: [
        "Intent Type: Price Inquiry",
        "Confidence: 98%",
        "Entity Detected: Bitcoin (BTC)"
      ],
      color: "primary",
      icon: "bi-cpu"
    },
    {
      agent: "PlannerAgent",
      title: "Function Selection",
      description: "Selected necessary functions to retrieve data",
      details: [
        "Function 1: historical_prices(coin='BTC', period='24h')",
        "Function 2: market_cap(coin='BTC')",
        "Function 3: volume_data(coin='BTC')"
      ],
      color: "secondary",
      icon: "bi-diagram-3"
    },
    {
      agent: "FetcherAgent",
      title: "Data Retrieval",
      description: "Retrieved data from CoinGecko API",
      details: [
        "API Endpoint: /coins/bitcoin/market_data",
        "Response Time: 234ms",
        "Data Points Retrieved: 48",
        "Status: Success (200)"
      ],
      color: "success",
      icon: "bi-database"
    },
    {
      agent: "RAGAgent",
      title: "Answer Generation",
      description: "Generated natural language explanation",
      details: [
        "Context Retrieved: Market trends, historical data",
        "Template: Price summary with analysis",
        "Confidence Score: 95%"
      ],
      color: "warning",
      icon: "bi-chat-dots"
    }
  ]
};


/* =========================
   RENDER LOGIC (Dynamic)
========================= */

const container = document.getElementById("stepsContainer");

workflowData.steps.forEach((step, index) => {
  const wrapper = document.createElement("div");
  wrapper.className = "mb-4 position-relative";

  const detailsHTML = step.details
    .map(d => `
      <div class="d-flex align-items-start gap-2">
        <i class="bi bi-check-circle-fill text-${step.color} mt-1"></i>
        <span>${d}</span>
      </div>
    `)
    .join("");

  wrapper.innerHTML += `
    <div class="card border border-${step.color}" style="border-width: 1px 1px 1px 4px !important;">
      <div class="card-body">
        <div class="d-flex gap-3">

          <!-- ICON -->
          <div class="step-icon bg-${step.color}-subtle text-${step.color}">
            <i class="bi ${step.icon}"></i>
          </div>

          <!-- CONTENT -->
          <div class="flex-grow-1">

            <div class="d-flex align-items-center gap-2 mb-2">
              <span class="agent-badge bg-${step.color}-subtle text-${step.color}">
                ${step.agent}
              </span>
              <i class="bi bi-chevron-right text-muted"></i>
              <small class="text-muted">
                Step ${index + 1} of ${workflowData.steps.length}
              </small>
            </div>

            <h6 class="fw-semibold">${step.title}</h6>

            <p class="text-muted small">${step.description}</p>

            <div class="detail-box bg-${step.color}-subtle">
              ${detailsHTML}
            </div>

          </div>
        </div>
      </div>
    </div>
  `;

  container.appendChild(wrapper);
});


/* =========================
   SUMMARY CARD
========================= */

const summary = document.getElementById("summaryContainer");

summary.innerHTML = `
  <div class="card mt-4 border-primary">
    <div class="card-body">
      <div class="d-flex align-items-center gap-2 mb-2">
        <i class="bi bi-check-circle-fill text-success fs-4"></i>
        <h6 class="mb-0 fw-semibold">Process Complete</h6>
      </div>
      <p class="text-muted small mb-0">
        The system successfully processed the user query through
        ${workflowData.steps.length} agent stages,
        retrieving real-time data and generating an accurate response
        in ${workflowData.totalTime}.
      </p>
    </div>
  </div>
`;