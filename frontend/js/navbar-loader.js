function setActiveNavbarLink() {
  const links = document.querySelectorAll(".navbar-tabs a");

  links.forEach(link => {
    if (window.location.pathname.includes(link.getAttribute("href"))) {
      link.classList.add("active");
    }
  });
}

fetch("navbar.html")
  .then(res => res.text())
  .then(html => {
    document.getElementById("navbar").innerHTML = html;
    setActiveNavbarLink();
  });
