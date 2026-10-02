// navbar.js
(function() {
    // Navbar HTML with two-level collapsible dropdowns
    const navbarHTML = `
    <style>
        .dropdown-nav-content { display: none; }
        .dropdown-category-content { display: none; }
    </style>
    <header class="p-5 flex justify-between items-center border-b border-gray-800 sticky top-0 z-50">
        <div class="logo-container"></div>

        <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
            <span></span>
            <span></span>
            <span></span>
        </button>
        <ul class="nav-menu" id="navMenuList">
            <li><a href="/index.html">Home</a></li>

            <!-- ==================== SNIPPETS DROPDOWN ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Snippets ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🎨 UI Components ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/animated-cards.html">🎴 Animated Cards</a></li>
                            <li><a href="/dropdown-menu.html">🔽 Dropdown Menu</a></li>
                            <li><a href="/loader.html">⏳ Loaders</a></li>
                            <li><a href="/image-slider.html">↔️ Image Slider</a></li>
                            <li><a href="/pricing-matrix.html">🏷️ Pricing Matrix</a></li>
                            <li><a href="/navbar-snippet.html">📱 Navbar</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📝 Forms & Input ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/login.html">🔐 Login Form</a></li>
                            <li><a href="/otp-verification.html">🔐 OTP Verification</a></li>
                            <li><a href="/download-button.html">⬇️ Animated Download Button</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚡ Interactive ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/toast-notifications.html">🔔 Toast Notifications</a></li>
                            <li><a href="/darkmode.html">🌙 Dark Mode</a></li>
                            <li><a href="/ai-analyser.html">💬 Sentiment Analyser</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🔧 Utilities ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/password-gen.html">🔐 Password Generator</a></li>
                        </ul>
                    </li>
                </ul>
            </li>

            <!-- ==================== GUIDES DROPDOWN ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Guides ▼</a>
                <ul class="dropdown-nav-content">
                    <li><a href="/ultimate-html-guide.html">🌐 HTML Guide</a></li>
                    <li><a href="/ultimate-python-guide.html">🐍 Python Guide</a></li>
                    <li><a href="/ultimate-ai-guide.html">🤖 AI Guide</a></li>
                </ul>
            </li>

            <!-- ==================== HOW-TO DROPDOWN ==================== -->
            <li class="dropdown-nav">
                <a href="/how-to/index.html" class="dropbtn-nav">How-to ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🛠️ Setup ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/install-vs-code.html">🌐 Install VS Code</a></li>
                            <li><a href="/how-to/install-python.html">🐍 Install Python</a></li>
                            <li><a href="/how-to/install-pytube.html">📥 Install Pytube</a></li>
                            <li><a href="/how-to/install-nodejs.html">🟢 Install Node.js</a></li>
                            <li><a href="/how-to/install-git.html">🌿 Install Git</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🚀 First Steps ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/run-first-html-file.html">📄 Run First HTML File</a></li>
                            <li><a href="/how-to/command-line-basics.html">⌨️ Command Line Basics</a></li>
                            <li><a href="/how-to/write-first-html-page.html">📝 Write First HTML Page</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🌍 Publishing ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/publish-website-free.html">🚀 Publish Website Free</a></li>
                            <li><a href="/how-to/get-free-domain.html">🌐 Free Domain Name</a></li>
                            <li><a href="/how-to/deploy-with-netlify.html">⚡ Deploy with Netlify</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📊 Growth ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/add-google-analytics.html">📊 Add Google Analytics</a></li>
                            <li><a href="/how-to/seo-friendly-website.html">🔎 SEO-Friendly Website</a></li>
                            <li><a href="/how-to/calculate-percentage-increase.html">📊 Calculate Percentage Increase</a></li>
                            <li><a href="/how-to/calculate-percentage-decrease.html">📉 Calculate Percentage decrease</a></li>
                            <li><a href="/how-to/calculate-percentage-of-a-number.html">🔢 Calculate X% of a Number</a></li>
                            <li><a href="/how-to/calculate-bmi.html">⚖️ How to Calculate BMI</a></li>
                        </ul>
                    </li>
                </ul>
            </li>

            <li><a href="/courses/index.html">Courses</a></li>

            <!-- ==================== TOOLS DROPDOWN ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Tools ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📊 Calculators ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/bmi-calculator.html">⚖️ BMI Calculator</a></li>
                            <li><a href="/tools/calorie-calculator.html">🔥 Calorie Calculator</a></li>
                            <li><a href="/tools/age-calculator.html">🎂 Age Calculator</a></li>
                            <li><a href="/tools/percentage-calculator.html">📊 Percentage Calculator</a></li>
                            <li><a href="/tools/unit-converter.html">📏 Unit Converter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">💰 Finance ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/income-tax-calculator.html">💰 Income Tax Calculator</a></li>
                            <li><a href="/tools/loan-emi-calculator.html">🏦 Loan EMI Calculator</a></li>
                            <li><a href="/tools/zakat-calculator.html">🤲 Zakat Calculator</a></li>
                            <li><a href="/tools/compound-interest-calculator.html">📈 Compound Interest Calculator</a></li>
                            <li><a href="/tools/currency-converter.html">💱 Currency Converter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">✍️ Writing & Code ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/word-counter.html">📝 Word Counter</a></li>
                            
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">💻 Developer Tools ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/regex-tester.html">🔍 Regex Tester</a></li>
                            <li><a href="/tools/base64-encoder.html">🔐 Base64 Encoder/ Decoder</a></li>
                            <li><a href="/tools/timestamp-converter.html">⏱️ Unix Timestamp Converter</a></li>
                            <li><a href="/tools/json-formatter.html">🧩 JSON Formatter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🔧 Utilities ▸</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/qr-code-generator.html">📱 QR Code Generator</a></li>
                        </ul>
                    </li>

                    
                    <li style="border-top:1px solid #334155; margin-top:0.5rem; padding-top:0.5rem;">
                        <a href="/tools/index.html" style="color:#60a5fa; font-weight:700;">🛠️ View All Tools →</a>
                    </li>
                </ul>
            </li>

            <!-- ==================== SHORTS DROPDOWN ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Shorts ▼</a>
                <ul class="dropdown-nav-content">
                    <li><a href="/html-shorts.html">📱 HTML Shorts</a></li>
                    <li><a href="/python-shorts.html">🐍 Python Shorts</a></li>
                </ul>
            </li>

            <li><a href="/questions.html">❓ FAQ</a></li>
            <li><a href="/showcase.html">🚀 Showcase</a></li>
            <li><a href="/pro-pack.html">Pro Pack</a></li>
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

                // Close all dropdowns when hamburger toggles
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });
            });

            document.addEventListener('click', function(e) {
                if (!navMenu.contains(e.target) && !hamburger.contains(e.target)) {
                    navMenu.classList.remove('active');
                }
            });
        }

        // ====== LEVEL 1: Main dropdown click ======
        document.querySelectorAll('.dropbtn-nav').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const content = this.nextElementSibling;
                const isOpen = content.style.display === 'block';

                // Close all main dropdowns and nested categories
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });

                // Toggle clicked
                if (!isOpen) {
                    content.style.display = 'block';
                }
            });
        });

        // ====== LEVEL 2: Category click (opens sub-tools) ======
        document.querySelectorAll('.dropdown-category-btn').forEach(function(btn) {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();

                const content = this.nextElementSibling;
                const isOpen = content.style.display === 'block';

                // Close sibling categories within the same dropdown
                const parentDropdown = this.closest('.dropdown-nav-content');
                parentDropdown.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });

                // Toggle clicked
                if (!isOpen) {
                    content.style.display = 'block';
                }
            });
        });

        // ====== CLOSE everything when clicking outside ======
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.dropdown-nav')) {
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });
            }
        });

        // ====== CLOSE everything when a real link is clicked ======
        document.querySelectorAll('.dropdown-nav-content a:not(.dropdown-category-btn)').forEach(function(link) {
            link.addEventListener('click', function() {
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });
            });
        });
    }
})();
