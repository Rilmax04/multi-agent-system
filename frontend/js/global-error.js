const GLOBAL_ERROR_BANNER_ID = "globalErrorBanner";
const GLOBAL_ERROR_BANNER_HTML = `
  <div
    id="${GLOBAL_ERROR_BANNER_ID}"
    class="alert alert-danger d-none"
    role="alert"
  ></div>
`;

function ensureGlobalErrorBanner() {
  let banner = document.getElementById(GLOBAL_ERROR_BANNER_ID);
  if (banner) return banner;

  const pageShell = document.querySelector(".page-shell");
  if (!pageShell) return null;

  pageShell.insertAdjacentHTML("afterbegin", GLOBAL_ERROR_BANNER_HTML);
  banner = document.getElementById(GLOBAL_ERROR_BANNER_ID);

  return banner;
}

function getGlobalErrorBanner() {
  return ensureGlobalErrorBanner();
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

ensureGlobalErrorBanner();
