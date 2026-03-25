const links = document.querySelectorAll(".navbar-tabs a");

links.forEach(link => {
  if (link.href === window.location.href) {
    link.classList.add("active");
  }
});