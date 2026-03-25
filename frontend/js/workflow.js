/* =========================
   REAL TRACE (from backend /ask)
========================= */

const LAST_TRACE_STORAGE_KEY = "rag:last_trace";

function safeJsonParse(text) {
  try { return JSON.parse(text); } catch (_) { return null; }
}

function stepMeta(stepName) {
  // Backend trace steps: planner, fetcher, formatter, reasoner
  const map = {
    planner:   { agent: "PlannerAgent",   title: "Planning",          icon: "bi-diagram-3", color: "secondary" },
    fetcher:   { agent: "FetcherAgent",   title: "Data Retrieval",    icon: "bi-database",  color: "success" },
    formatter: { agent: "DataFormatter",  title: "Context Building",  icon: "bi-braces",    color: "primary" },
    reasoner:  { agent: "RAGAgent",       title: "Answer Generation", icon: "bi-chat-dots", color: "warning" }
  };
  return map[stepName] || { agent: "Agent", title: stepName, icon: "bi-cpu", color: "primary" };
}

function buildWorkflowData(last) {
  const trace = Array.isArray(last?.trace) ? last.trace : [];
  const totalMs = typeof last?.total_time_ms === "number" ? last.total_time_ms : null;

  const steps = trace.map(s => {
    const meta = stepMeta(s.step);
    const ok = s.status === "success";
    const timeMs = typeof s.time_ms === "number" ? s.time_ms : null;
    const details = [
      `Status: ${ok ? "Success" : "Error"}`,
      timeMs == null ? null : `Time: ${Math.round(timeMs)} ms`,
      s.error ? `Error: ${s.error}` : null
    ].filter(Boolean);

    return {
      agent: meta.agent,
      title: meta.title,
      description: last?.question ? `Processed question: "${last.question}"` : "Processed user request",
      details,
      color: ok ? meta.color : "danger",
      icon: ok ? meta.icon : "bi-exclamation-triangle"
    };
  });

  return {
    totalTime: totalMs == null ? "—" : `${(totalMs / 1000).toFixed(2)} seconds`,
    steps
  };
}


/* =========================
   RENDER LOGIC (Dynamic)
========================= */

const container = document.getElementById("stepsContainer");

function renderEmptyState() {
  container.innerHTML = `
    <div class="card border-warning">
      <div class="card-body">
        <div class="d-flex align-items-center gap-2 mb-2">
          <i class="bi bi-info-circle text-warning"></i>
          <div class="fw-semibold">No workflow trace yet</div>
        </div>
        <div class="text-muted small">
          Open the Chat page, ask a question, and then come back here to see the real backend trace.
        </div>
      </div>
    </div>
  `;
}

function renderWorkflow(workflowData) {
  container.innerHTML = "";

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
          The system processed the last user query through
          ${workflowData.steps.length} stages
          in ${workflowData.totalTime}.
        </p>
      </div>
    </div>
  `;
}

const last = safeJsonParse(localStorage.getItem(LAST_TRACE_STORAGE_KEY) || "");
if (!last?.trace) {
  renderEmptyState();
} else {
  renderWorkflow(buildWorkflowData(last));
}