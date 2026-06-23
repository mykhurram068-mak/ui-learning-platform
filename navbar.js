// navbar.js
(function() {
  // Navbar HTML
  const navbarHTML = `
    <header class="p-5 flex justify-between items-center border-b border-gray-800 sticky top-0 bg-slate-950 z-50">
      <div class="logo-container">
        <!--<img src="logo mak.jpg" alt="mak" class="signature-logo">
        <span class="brand-name">CODE PATH</span>-->
      </div>
      
      <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
        <span></span>
        <span></span>
        <span></span>
      </button>
      <ul class="nav-menu" id="navMenuList">
        <li><a href="index.html">Home</a></li>
        <li><a href="loader.html">Loaders</a></li>
        <li><a href="login.html">Login</a></li>
        <li><a href="darkmode.html">Dark Mode</a></li>
        <li><a href="animated-cards.html">Cards</a></li>
        <li><a href="dropdown-menu.html">Cards</a></li>
        <li><a href="courses/index.html">Courses</a></li>
        <li><a href="pro-pack.html">Pro Pack</a></li>
      </ul>
      <!--
      <div class="flex items-center gap-3">
        <div class="bg-blue-500/10 border border-blue-500/20 px-3 py-1 rounded-full">
          <span class="text-[10px] font-bold text-blue-400">PRO ACCOUNT</span>
        </div>
      </div>
      -->
    </header>
  `;

  // Insert navbar into placeholder
  const placeholder = document.getElementById('navbar-placeholder');
  if (placeholder) {
    placeholder.innerHTML = navbarHTML;

    // Hamburger functionality
    const hamburger = document.getElementById('hamburgerBtn');
    const navMenu = document.getElementById('navMenuList');

    if (hamburger && navMenu) {
      hamburger.addEventListener('click', function(e) {
        e.stopPropagation();
        navMenu.classList.toggle('active');
      });

      document.querySelectorAll('.nav-menu a').forEach(function(link) {
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
  }
})();
