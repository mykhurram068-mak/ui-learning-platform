// navbar.js
(function() {
    const navbarHTML = `
    <style>
        /* Ensure everything starts hidden */
        .dropdown-nav-content { display: none; }
        .dropdown-category-content { display: none; }

        /* ===== MODERN DROPDOWN STYLING ===== */
        .dropdown-nav { position: relative; }

        .dropdown-nav-content {
            position: absolute;
            top: calc(100% + 8px);
            left: 0;
            min-width: 280px;
            background: rgba(15, 23, 42, 0.98);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(51, 65, 85, 0.7);
            border-radius: 14px;
            padding: 8px;
            list-style: none;
            margin: 0;
            z-index: 100;
            box-shadow:
                0 20px 50px rgba(0, 0, 0, 0.5),
                0 0 0 1px rgba(59, 130, 246, 0.05);
            max-height: 75vh;
            overflow-y: auto;
            animation: dropIn 0.18s cubic-bezier(0.16, 1, 0.3, 1);
        }

        @keyframes dropIn {
            from { opacity: 0; transform: translateY(-6px) scale(0.98); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
        }

        /* Custom scrollbar inside dropdown */
        .dropdown-nav-content::-webkit-scrollbar { width: 6px; }
        .dropdown-nav-content::-webkit-scrollbar-track { background: transparent; }
        .dropdown-nav-content::-webkit-scrollbar-thumb {
            background: #334155;
            border-radius: 3px;
        }
        .dropdown-nav-content::-webkit-scrollbar-thumb:hover { background: #475569; }

        /* ===== LEVEL 2: CATEGORY BUTTONS ===== */
        .dropdown-category { list-style: none; }

        .dropdown-category-btn {
            display: flex !important;
            align-items: center;
            justify-content: space-between;
            padding: 10px 14px !important;
            color: #cbd5e1 !important;
            text-decoration: none;
            font-size: 0.85rem !important;
            font-weight: 600;
            transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
            cursor: pointer;
            border-radius: 8px;
            margin: 2px 0;
        }

        .dropdown-category-btn:hover {
            background: rgba(59, 130, 246, 0.12) !important;
            color: #60a5fa !important;
        }

        .dropdown-category-btn::after {
            content: '▸';
            font-size: 0.7rem;
            color: #64748b;
            transition: transform 0.2s ease;
            margin-left: 8px;
        }

        .dropdown-category-btn.open::after {
            transform: rotate(90deg);
            color: #60a5fa;
        }

        /* ===== LEVEL 3: SUB-LINKS ===== */
        .dropdown-category-content {
            list-style: none;
            margin: 4px 0 8px 0;
            padding: 6px 0 6px 10px;
            background: rgba(30, 41, 59, 0.5);
            border-left: 2px solid #334155;
            border-radius: 0 8px 8px 0;
        }

        .dropdown-category-content a {
            display: block;
            padding: 7px 14px;
            color: #94a3b8;
            text-decoration: none;
            font-size: 0.8rem;
            font-weight: 500;
            border-radius: 6px;
            transition: all 0.15s ease;
            line-height: 1.4;
        }

        .dropdown-category-content a:hover {
            background: rgba(59, 130, 246, 0.15);
            color: #93c5fd;
            padding-left: 18px;
        }

        /* ===== REGULAR LINKS ===== */
        .dropdown-nav-content > li > a:not(.dropdown-category-btn) {
            display: block;
            padding: 10px 14px;
            color: #cbd5e1;
            text-decoration: none;
            font-size: 0.85rem;
            font-weight: 600;
            border-radius: 8px;
            transition: all 0.2s ease;
        }

        .dropdown-nav-content > li > a:not(.dropdown-category-btn):hover {
            background: rgba(59, 130, 246, 0.12);
            color: #60a5fa;
        }

        /* ===== WIDER PROJECTS DROPDOWN ===== */
        .dropdown-projects .dropdown-nav-content {
            min-width: 340px;
        }

        /* ===== MOBILE ADJUSTMENTS ===== */
        @media (max-width: 768px) {
            .dropdown-nav-content {
                position: static;
                min-width: 100% !important;
                width: 100%;
                background: rgba(15, 23, 42, 0.9);
                border: none;
                border-radius: 10px;
                box-shadow: none;
                padding: 4px;
                margin: 4px 0 8px 0;
                max-height: none;
                overflow: visible;
                animation: none;
            }

            .dropdown-category-btn {
                padding: 12px 14px !important;
                font-size: 0.88rem !important;
            }

            .dropdown-category-content a {
                padding: 10px 14px;
                font-size: 0.83rem;
            }
        }
    </style>

    <header class="p-5 flex justify-between items-center border-b border-gray-800 sticky top-0 z-50">
   
        <button class="hamburger" id="hamburgerBtn" aria-label="Menu">
            <span></span>
            <span></span>
            <span></span>
        </button>

        <ul class="nav-menu" id="navMenuList">
            <li><a href="/index.html">Home</a></li>

            <!-- ==================== SNIPPETS ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Snippets ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🎨 UI Components</a>
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
                        <a href="#" class="dropdown-category-btn">📝 Forms & Input</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/login.html">🔐 Login Form</a></li>
                            <li><a href="/otp-verification.html">🔐 OTP Verification</a></li>
                            <li><a href="/download-button.html">⬇️ Download Button</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚡ Interactive</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/toast-notifications.html">🔔 Toast Notifications</a></li>
                            <li><a href="/darkmode.html">🌙 Dark Mode</a></li>
                            <li><a href="/ai-analyser.html">💬 Sentiment Analyser</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🔧 Utilities</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/password-gen.html">🔐 Password Generator</a></li>
                        </ul>
                    </li>
               <!--</ul>
            </li>-->

            <!-- ==================== CODE SNIPPETS ==================== -->
           
                    <!-- 🟨 HTML Snippets -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🟨 HTML Snippets</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/code/html/html-boilerplate.html">🧱 HTML Boilerplate</a></li>
                            <li><a href="/code/html/html-forms.html">📋 Forms & Inputs</a></li>
                            <li><a href="/code/html/html-semantic-layout.html">🖼️ Semantic Layouts</a></li>
                            <li><a href="/code/html/html-dialog-popover.html">🎬 Dialog & Popover</a></li>
                            <li><a href="/code/html/html-permissions.html">📍 Permissions Elements</a></li>
                            <li><a href="/code/html/reference/index.html">📖 HTML Reference</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/code/html/index.html" style="color: #60a5fa; font-weight: 700;">→ View all HTML Snippets</a>
                            </li>
                        </ul>
                    </li>
            
                    <!-- 🎨 CSS Snippets -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🎨 CSS Snippets</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/code/css/css-center-a-div.html">🎯 Center a Div</a></li>
                            <li><a href="/code/css/css-autofit-grid.html">📐 Auto-fit Grid</a></li>
                            <li><a href="/code/css/css-has-selector.html">🌈 :has() Selector</a></li>
                            <li><a href="/code/css/css-container-queries.html">📦 Container Queries</a></li>
                            <li><a href="/code/css/css-clamp-fluid-type.html">📏 Fluid Typography</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/code/css/index.html" style="color: #60a5fa; font-weight: 700;">→ View all CSS Snippets</a>
                            </li>
                        </ul>
                    </li>
            
                    <!-- 🐍 Python Snippets -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🐍 Python Snippets</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/python-list-comprehension.html">📝 List Comprehension</a></li>
                            <li><a href="/code/python/python-decorators.html">🎁 Decorators</a></li>
                            <li><a href="/code/python/python-dataclass.html">🏷️ Dataclass</a></li>
                            <li><a href="/code/python/python-uv-ruff.html">🔧 Modern Toolchain</a></li>
                            <li><a href="/code/python/python-context-managers.html">📂 Context Managers</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/code/python/index.html" style="color: #60a5fa; font-weight: 700;">→ View all Python Snippets</a>
                            </li>
                        </ul>
                    </li>
            
                    <!-- ⚡ JavaScript Snippets -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚡ JavaScript Snippets</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/code/js/js-debounce-throttle.html">⏱️ Debounce & Throttle</a></li>
                            <li><a href="/code/js/js-optional-chaining.html">🔗 Optional Chaining</a></li>
                            <li><a href="/code/js/js-abortcontroller.html">🚫 AbortController</a></li>
                            <li><a href="/code/js/js-structuredclone.html">📋 structuredClone</a></li>
                            <li><a href="/code/js/js-array-methods.html">📚 Array Methods</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/code/js/index.html" style="color: #60a5fa; font-weight: 700;">→ View all JS Snippets</a>
                            </li>
                        </ul>
                    </li>
                </ul>
            </li>

            <!-- ==================== GUIDES ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Guides ▼</a>
                <ul class="dropdown-nav-content">
           
                    <!-- 🟨 Languages -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🟨 Languages</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/ultimate-html-guide.html">🌐 HTML Guide</a></li>
                            <li><a href="/ultimate-python-guide.html">🐍 Python Guide</a></li>
                            <li><a href="/ultimate-ai-guide.html">🤖 AI Guide</a></li>
                            <li><a href="/how-to/what-is-typescript.html">🟦 TypeScript Guide</a></li>
                        </ul>
                    </li>
           
                    <!-- ⚛️ Frameworks & Concepts (5 + View all) -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚛️ Frameworks & Concepts</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/what-is-react.html">⚛️ React Guide</a></li>
                            <li><a href="/how-to/what-is-nextjs.html">⚫ Next.js Guide</a></li>
                            <li><a href="/how-to/what-is-tailwind-css.html">🎨 Tailwind CSS Guide</a></li>
                            <li><a href="/how-to/what-is-django.html">🐍 Django Guide</a></li>
                            <li><a href="/how-to/what-is-streamlit.html">📊 Streamlit Guide</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/frameworks-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all Frameworks & Concepts</a>
                            </li>
                        </ul>
                    </li>
           
                    <!-- ⚔️ Comparisons (5 + View all) -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚔️ Comparisons</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/react-vs-vue.html">⚛️ React vs Vue</a></li>
                            <li><a href="/how-to/nextjs-vs-remix.html">⚫ Next.js vs Remix</a></li>
                            <li><a href="/how-to/bun-vs-node.html">🥟 Bun vs Node.js</a></li>
                            <li><a href="/how-to/tailwind-vs-bootstrap.html">🎨 Tailwind vs Bootstrap</a></li>
                            <li><a href="/how-to/streamlit-vs-gradio.html">📊 Streamlit vs Gradio</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/comparisons.html" style="color: #60a5fa; font-weight: 700;">→ View all Comparisons</a>
                            </li>
                        </ul>
                    </li>

                    <!-- 🗺️ Roadmaps -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🗺️ Roadmaps</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/roadmaps/frontend-developer.html">🎨 Frontend Roadmap</a></li>
                            <li><a href="/roadmaps/python-developer.html">🐍 Python Roadmap</a></li>
                            <li><a href="/roadmaps/ai-engineer.html">🤖 AI Engineer Roadmap</a></li>
                            <li><a href="/roadmaps/nodejs-developer.html">🟢 Node.js Roadmap</a></li>
                        </ul>
                    </li>
                </ul>
            </li>
           
            <!-- ==================== HOW-TO ==================== -->
            <li class="dropdown-nav">
                <a href="/how-to/index.html" class="dropbtn-nav">How-to ▼</a>
                <ul class="dropdown-nav-content">

                    <!-- 🛠️ Setup -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🛠️ Setup</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/install-vs-code.html">💻 Install VS Code</a></li>
                            <li><a href="/how-to/install-python.html">🐍 Install Python</a></li>
                            <li><a href="/how-to/install-nodejs.html">🟢 Install Node.js</a></li>
                            <li><a href="/how-to/install-git.html">🌿 Install Git</a></li>
                            <li><a href="/how-to/install-java.html">☕ Install Java</a></li>
                            <li><a href="/how-to/install-docker.html">🐳 Install Docker</a></li>
                            <li><a href="/how-to/install-bun.html">🥟 Install Bun</a></li>
                            <li><a href="/how-to/install-postgresql.html">🐘 Install PostgreSQL</a></li>
                            <li><a href="/how-to/install-pnpm.html">📦 Install pnpm</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/setup-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all 12 Setup Guides</a>
                            </li>
                        </ul>
                    </li>

                    <!-- 🚀 First Steps -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🚀 First Steps</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/run-first-html-file.html">📄 Run First HTML File</a></li>
                            <li><a href="/how-to/command-line-basics.html">⌨️ Command Line Basics</a></li>
                            <li><a href="/how-to/write-first-html-page.html">📝 Write First HTML Page</a></li>
                        </ul>
                    </li>  
               
                    <!-- 🐍 Python & Streamlit -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🐍 Python & Streamlit</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/install-pytube.html">📥 Install PyTube</a></li>
                            <li><a href="/how-to/streamlit-python-app.html">📊 Streamlit Python App</a></li>
                            <li><a href="/how-to/streamlit-dashboard.html">📈 Streamlit Dashboard</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/python-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all 6 Python Guides</a>
                            </li>
                        </ul>
                    </li>

                    <!-- 🟢 Node.js -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🟢 Node.js</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/read-json-nodejs.html">📄 Read & Write JSON</a></li>
                            <li><a href="/how-to/nodejs-dotenv.html">🔐 Environment Variables</a></li>
                            <li><a href="/how-to/nodejs-fs-module.html">🗂️ fs Module Guide</a></li>
                            <li><a href="/how-to/nodejs-jwt.html">🔑 JWT Authentication</a></li>
                            <li><a href="/how-to/nodejs-postgresql.html">🐘 Node.js + PostgreSQL</a></li>
                            <li><a href="/how-to/deploy-nodejs.html">🚀 Deploy Node.js App</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/nodejs-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all 12 Node.js Guides</a>
                            </li>
                        </ul>
                    </li>

                    <!-- ⚫ Next.js -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">⚫ Next.js</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/create-nextjs-app.html">⚫ Create a Next.js App</a></li>
                            <li><a href="/how-to/nextjs-routing.html">🛣️ Next.js Routing</a></li>
                            <li><a href="/how-to/nextjs-server-vs-client.html">⚡ Server vs Client Components</a></li>
                            <li><a href="/how-to/nextjs-authentication.html">🔑 Next.js Authentication</a></li>
                            <li><a href="/how-to/fetch-data-nextjs.html">📥 Fetch Data in Next.js</a></li>
                            <li><a href="/how-to/deploy-nextjs-vercel.html">🚀 Deploy to Vercel</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/nextjs-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all 8 Next.js Guides</a>
                            </li>
                        </ul>
                    </li>

                    <!-- 💻 Web Dev -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">💻 Web Dev</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/first-react-component.html">⚛️ First React Component</a></li>
                            <li><a href="/how-to/react-state-management.html">🔄 React State Management</a></li>
                            <li><a href="/how-to/first-nextjs-app.html">⚫ First Next.js App</a></li>
                            <li><a href="/how-to/what-is-tailwind-css.html">🎨 What Is Tailwind CSS</a></li>
                            <li><a href="/how-to/fix-cannot-find-module.html">🔧 Fix "Cannot Find Module"</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/web-dev-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all Developer Guides</a>
                            </li>
                        </ul>
                    </li>

                    <!-- 🔌 API & AI -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🔌 API & AI</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/build-first-api.html">🔨 Build First API</a></li>
                            <li><a href="/how-to/openai-api-setup.html">🤖 OpenAI API Setup</a></li>
                            <li><a href="/how-to/build-ai-chatbot.html">💬 Build AI Chatbot</a></li>
                            <li><a href="/how-to/what-is-rag.html">🧠 What is RAG?</a></li>
                        </ul>
                    </li>

                    <!-- 🌍 Publishing -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🌍 Publishing</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/publish-website-free.html">🚀 Publish Website Free</a></li>
                            <li><a href="/how-to/get-free-domain.html">🌐 Get Free Domain</a></li>
                            <li><a href="/how-to/deploy-with-netlify.html">⚡ Deploy with Netlify</a></li>
                            <li><a href="/how-to/deploy-with-vercel.html">⚡ Deploy with Vercel</a></li>
                        </ul>
                    </li>

                    <!-- 📊 Math & Health -->
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📊 Math & Health</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/how-to/calculate-percentage-increase.html">📈 Calculate % Increase</a></li>
                            <li><a href="/how-to/calculate-percentage-decrease.html">📉 Calculate % Decrease</a></li>
                            <li><a href="/how-to/calculate-percentage-difference.html">📐 Calculate % Difference</a></li>
                            <li><a href="/how-to/calculate-bmi.html">⚖️ Calculate BMI</a></li>
                            <li><a href="/how-to/bmi-chart.html">📊 BMI Chart</a></li>
                            <li><a href="/how-to/how-many-calories-a-day.html">🔥 Calories a Day</a></li>
                            <li><a href="/how-to/what-is-tdee.html">📈 What Is TDEE</a></li>
                            <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                                <a href="/how-to/math-guides.html" style="color: #60a5fa; font-weight: 700;">→ View all Math & Health Guides</a>
                            </li>
                        </ul>
                    </li>

                </ul>
            </li>

            <li><a href="/courses/index.html">Courses</a></li>

            <!-- ==================== TOOLS ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Tools ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📊 Calculators</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/best-free-developer-tools.html">⭐ Best Free Dev Tools</a></li>
                            <li><a href="/tools/bmi-calculator.html">⚖️ BMI Calculator</a></li>
                            <li><a href="/tools/bmi-by-height.html">📏 BMI by Height</a></li>
                            <li><a href="/tools/age-calculator.html">🎂 Age Calculator</a></li>
                            <li><a href="/tools/age-calculator-by-year.html">📅 Age by Birth Year</a></li>
                            <li><a href="/tools/percentage-calculator.html">📊 Percentage Calculator</a></li>
                            <li><a href="/tools/unit-converter.html">📏 Unit Converter</a></li>
                            <li><a href="/tools/calorie-calculator.html">🔥 Calorie Calculator</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">💰 Finance</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/income-tax-calculator.html">💰 Income Tax</a></li>
                            <li><a href="/tools/loan-emi-calculator.html">🏦 Loan EMI</a></li>
                            <li><a href="/tools/zakat-calculator.html">🤲 Zakat</a></li>
                            <li><a href="/tools/compound-interest-calculator.html">📈 Compound Interest</a></li>
                            <li><a href="/tools/currency-converter.html">💱 Currency Converter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">✍️ Writing & Code</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/word-counter.html">📝 Word Counter</a></li>
                            <li><a href="/tools/json-formatter.html">🧩 JSON Formatter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">💻 Developer Tools</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/regex-tester.html">🔍 Regex Tester</a></li>
                            <li><a href="/tools/base64-encoder.html">🔐 Base64 Encoder</a></li>
                            <li><a href="/tools/timestamp-converter.html">⏱️ Timestamp Converter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🔧 Utilities</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/tools/qr-code-generator.html">📱 QR Code Generator</a></li>
                        </ul>
                    </li>
                    <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                        <a href="/tools/index.html" style="color: #60a5fa;">🛠️ View All Tools →</a>
                    </li>
                </ul>
            </li>

            <!-- ==================== PROJECTS ==================== -->
            <li class="dropdown-nav dropdown-projects">
                <a href="#" class="dropbtn-nav">Projects ▼</a>
                <ul class="dropdown-nav-content">
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📐 Math & Money</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/projects/build-bmi-calculator.html">⚖️ BMI Calculator</a></li>
                            <li><a href="/projects/build-age-calculator.html">🎂 Age Calculator</a></li>
                            <li><a href="/projects/build-percentage-calculator.html">📊 Percentage Calculator</a></li>
                            <li><a href="/projects/build-unit-converter.html">📏 Unit Converter</a></li>
                            <li><a href="/projects/build-loan-calculator.html">🏦 Loan EMI Calculator</a></li>
                            <li><a href="/projects/build-compound-interest.html">📈 Compound Interest</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">📝 Text & Content</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/projects/build-word-counter.html">📝 Word Counter</a></li>
                            <li><a href="/projects/build-qr-generator.html">📱 QR Code Generator</a></li>
                            <li><a href="/projects/build-password-generator.html">🔐 Password Generator</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🧩 Developer Tools</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/projects/build-json-formatter.html">🧩 JSON Formatter</a></li>
                            <li><a href="/projects/build-regex-tester.html">🔍 Regex Tester</a></li>
                            <li><a href="/projects/build-base64-encoder.html">🔐 Base64 Encoder</a></li>
                            <li><a href="/projects/build-timestamp-converter.html">⏱️ Timestamp Converter</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🛠️ Full Apps</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/projects/build-todo-list.html">✅ To-Do List App</a></li>
                            <li><a href="/projects/build-weather-app.html">🌦️ Weather App</a></li>
                            <li><a href="/projects/build-portfolio-website.html">🎨 Portfolio Website</a></li>
                        </ul>
                    </li>
                    <li class="dropdown-category">
                        <a href="#" class="dropdown-category-btn">🐍 Python & Streamlit</a>
                        <ul class="dropdown-category-content">
                            <li><a href="/projects/build-python-calculator.html">🐍 Python Calculator</a></li>
                            <li><a href="/projects/build-streamlit-dashboard.html">📊 Streamlit Dashboard</a></li>
                        </ul>
                    </li>
                    <li style="border-top: 1px solid #1e293b; margin-top: 6px; padding-top: 6px;">
                        <a href="/projects/index.html" style="color: #60a5fa;">📚 View All Projects →</a>
                    </li>
                </ul>
            </li>

            <!-- ==================== SHORTS ==================== -->
            <li class="dropdown-nav">
                <a href="#" class="dropbtn-nav">Shorts ▼</a>
                <ul class="dropdown-nav-content">
                    <li><a href="/html-shorts.html">📱 HTML Shorts</a></li>
                    <li><a href="/python-shorts.html">🐍 Python Shorts</a></li>
                </ul>
            </li>

            <li><a href="/questions.html">❓ FAQ</a></li>
            <li><a href="/showcase.html">Showcase</a></li>
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
                document.querySelectorAll('.dropdown-category-btn').forEach(function(b) {
                    b.classList.remove('open');
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

                // Close all main dropdowns and reset category states
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-btn').forEach(function(b) {
                    b.classList.remove('open');
                });

                // Toggle clicked
                if (!isOpen) {
                    content.style.display = 'block';
                }
            });
        });

        // ====== LEVEL 2: Category click (opens sub-links) ======
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
                parentDropdown.querySelectorAll('.dropdown-category-btn').forEach(function(b) {
                    b.classList.remove('open');
                });

                // Open clicked category
                if (!isOpen) {
                    content.style.display = 'block';
                    this.classList.add('open');
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
                document.querySelectorAll('.dropdown-category-btn').forEach(function(b) {
                    b.classList.remove('open');
                });
            }
        });

        // ====== CLOSE when a real link is clicked ======
        document.querySelectorAll('.dropdown-nav-content a:not(.dropdown-category-btn)').forEach(function(link) {
            link.addEventListener('click', function() {
                document.querySelectorAll('.dropdown-nav-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-content').forEach(function(c) {
                    c.style.display = 'none';
                });
                document.querySelectorAll('.dropdown-category-btn').forEach(function(b) {
                    b.classList.remove('open');
                });
            });
        });
    }
})();
