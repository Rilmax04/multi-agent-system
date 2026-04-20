function getGlobalErrorBanner() {
  return document.getElementById("globalErrorBanner");
}

function showGlobalError(message = "Something went wrong. Please try again.") {
  const banner = getGlobalErrorBanner();
  if (!banner) return;

  banner.textContent = message;
  banner.classList.remove("d-none");
}

function clearGlobalError() {
  const banner = getGlobalErrorBanner();
  if (!banner) return;

  banner.textContent = "";
  banner.classList.add("d-none");
}
