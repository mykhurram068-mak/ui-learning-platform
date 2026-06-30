// navbar.js
(function() {
  // Navbar HTML with Snippets dropdown
  const navbarHTML = `
    <header class="p-5 flex justify-between items-center border-b border-gray-800 sticky top-0 bg-slate-950 z-50">
      <div class="logo-container">
      <!--  <img src="/logo mak.jpg" alt="mak" class="signature-logo">
        <span class="brand-name">CODE PATH</span>-->
      </div>
      <!--<div class="flex items-center gap-3">
        <div class="bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">
          <span class="text-[10px] font-bold text-blue-400">PRO ACCOUNT</span>
        </div>
      </div>-->
      <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
        <span></span>
        <span></span>
        <span></span>
      </button>
      <ul class="nav-menu" id="navMenuList">
        <li><a href="index.html">Home</a></li>
        <li class="dropdown-nav">
          <a href="#" class="dropbtn-nav">Snippets ▼</a>
          <ul class="dropdown-nav-content">
            <li><a href="animated-cards.html">🎴 Animated Cards</a></li>
            <li><a href="dropdown-menu.html">🔽 Dropdown Menu</a></li>
            <li><a href="pricing-matrix.html">💳 Glassmorphism Pricing Matrix</a></li>
            <li><a href="image-slider.html">🎠 Image Slider / Carousel</a></li>
            <li><a href="loader.html">⏳ Loaders</a></li>
            <li><a href="login.html">🔐 Login Form</a></li>
            <li><a href="darkmode.html">🌙 Dark Mode</a></li>
            <li><a href="navbar-snippet.html">📱 Navbar</a></li>
            <li><a href="/password-gen.html">🔐 Password Generator</a></li>
            <li><a href="/ai-analyser.html">💬 Sentiment Analyser</a></li>
            <li><a href="/ultimate-html-guide.html">📘 Ultimate HTML Guide</a></li>
          </ul>
        </li>
        <li><a href="courses/index.html">Courses</a></li>
        <li><a href="pro-pack.html">Pro Pack</a></li>
      </ul>
    </header>
  `;

  // Insert navbar into placeholder
  const placeholder = document.getElementById('navbar-placeholder');
  if (placeholder) {
    placeholder.innerHTML = navbarHTML;

    // ====== HAMBURGER MENU ======
    const hamburger = document.getElementById('hamburgerBtn');
    const navMenu = document.getElementById('navMenuList');

    if (hamburger && navMenu) {
      hamburger.addEventListener('click', function(e) {
        e.stopPropagation();
        navMenu.classList.toggle('active');
      });

      document.querySelectorAll('.nav-menu > li > a').forEach(function(link) {
        link.addEventListener('click', function() {
          navMenu.classList.remove('active');
        });
      });

      document.addEventListener('click', function(e) {
        if (!navMenu.contains(e.target) && !hamburger.contains(e.target)) {
          navMenu.classList.remove('active');
        }
      });
    }

    // ====== DROPDOWN NAV (Desktop) ======
    const dropdownNav = document.querySelector('.dropdown-nav');
    if (dropdownNav) {
      dropdownNav.addEventListener('mouseenter', function() {
        if (window.innerWidth > 768) {
          this.querySelector('.dropdown-nav-content').style.display = 'block';
        }
      });
      dropdownNav.addEventListener('mouseleave', function() {
        if (window.innerWidth > 768) {
          this.querySelector('.dropdown-nav-content').style.display = 'none';
        }
      });
    }

    // ====== DROPDOWN NAV (Mobile) ======
    const dropbtnNav = document.querySelector('.dropbtn-nav');
    if (dropbtnNav) {
      dropbtnNav.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
          e.preventDefault();
          const content = this.nextElementSibling;
          if (content.style.display === 'block') {
            content.style.display = 'none';
          } else {
            content.style.display = 'block';
          }
        }
      });
    }
  }
})();
