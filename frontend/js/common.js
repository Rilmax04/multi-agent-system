const BACKEND_URL = "http://127.0.0.1:8000";

function safeJsonParse(text) {
  try {
    return JSON.parse(text);
  } catch (_) {
    return null;
  }
}

function formatUsd(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2
  }).format(Number(value));
}

function formatUsdCompact(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2
  }).format(Number(value));
}

function formatPercent(value) {
  if (value == null || Number.isNaN(Number(value))) return "—";

  const numericValue = Number(value);
  const sign = numericValue > 0 ? "+" : "";

  return `${sign}${numericValue.toFixed(2)}%`;
}

async function parseJsonOrNull(response) {
  return response.json().catch(() => null);
}
