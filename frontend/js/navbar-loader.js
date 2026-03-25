fetch("navbar.html")
  .then(res => res.text())
  .then(data => {
    document.getElementById("navbar").innerHTML = data;
    const links = document.querySelectorAll(".navbar-tabs a");

    links.forEach(link => {
      if (window.location.pathname.includes(link.getAttribute("href"))) {
        link.classList.add("active");
      }
    });
  });