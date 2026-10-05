// scripts/generate-age-pages.js
// Run: node scripts/generate-age-pages.js
// Output: 61 static pages in /tools/age-in-YYYY.html

const fs = require('fs');
const path = require('path');

const START_YEAR = 1950;
const END_YEAR = 2010;
const CURRENT_YEAR = 2026;
const OUTPUT_DIR = path.join(__dirname, '..', 'tools');

const SITE = 'https://makuistudio.com';
const BRAND = 'MAK Studio';

function getAge(birthYear) {
    return CURRENT_YEAR - birthYear;
}

function generatePage(year) {
    const age = getAge(year);
    const ageNext = age + 1;
    const agePrev = age - 1;
    const url = `${SITE}/tools/age-in-${year}.html`;
    const title = `How Old Am I If I Was Born in ${year}? | ${BRAND}`;
    const description = `If you were born in ${year}, you are ${age} years old in ${CURRENT_YEAR}. Get your exact age in years, months, days, and hours. Free age calculator.`;

    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>${title}</title>
    <meta name="description" content="${description}">
    <meta name="keywords" content="born in ${year}, how old if born in ${year}, age ${year}, ${year} to ${CURRENT_YEAR} age, age calculator">
    <meta name="author" content="${BRAND}">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="${title}">
    <meta property="og:description" content="${description}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="${url}">
    <meta property="og:image" content="${SITE}/images/social-card.png">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="${title}">
    <meta name="twitter:description" content="${description}">
    <link href="../../favicon.png" rel="icon" type="image/png"/>
    <link rel="canonical" href="${url}">

    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"How old am I if I was born in ${year}?","acceptedAnswer":{"@type":"Answer","text":"If you were born in ${year}, you are ${age} years old in ${CURRENT_YEAR}."}},{"@type":"Question","name":"What year will I turn 100 if born in ${year}?","acceptedAnswer":{"@type":"Answer","text":"If you were born in ${year}, you will turn 100 in ${year + 100}."}},{"@type":"Question","name":"What generation is someone born in ${year}?","acceptedAnswer":{"@type":"Answer","text":"People born in ${year} belong to ${getGeneration(year)}."}}]}
    </script>
    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"Home","item":"${SITE}/"},{"@type":"ListItem","position":2,"name":"Tools","item":"${SITE}/tools/index.html"},{"@type":"ListItem","position":3,"name":"Age in ${year}","item":"${url}"}]}
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="../../style.css" rel="stylesheet"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        pre { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 0.75rem; overflow-x: auto; font-size: 0.85rem; margin: 1rem 0; max-width: 100%; }
        .age-hero { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); border-radius: 1.5rem; padding: 2rem 1.5rem; text-align: center; color: white; margin: 1rem 0; }
        .age-hero .big { font-size: clamp(3rem, 12vw, 5rem); font-weight: 900; line-height: 1; font-family: 'Courier New', monospace; }
        .age-hero .label { font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.95; font-weight: 700; margin-top: 0.5rem; }
        .info-card { background: #0f172a; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; text-align: center; }
        .info-card .val { color: #60a5fa; font-family: 'Courier New', monospace; font-size: 1.25rem; font-weight: 800; }
        .info-card .lbl { color: #94a3b8; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; margin-bottom: 4px; }
        .year-chip { display: inline-block; background: #0f172a; border: 1px solid #334155; color: #cbd5e1; padding: 6px 12px; border-radius: 8px; font-size: 0.82rem; margin: 3px; text-decoration: none; transition: 0.2s; }
        .year-chip:hover { border-color: #3b82f6; color: #60a5fa; }
    </style>
</head>
<body class="pb-24 bg-slate-950 text-slate-300">
<nav class="navbar">
<div class="nav-container">
<a class="logo" href="../../index.html">✨ MAK UI Studio</a>
<div id="navbar-placeholder"></div>
<script src="../../navbar.js"></script>
</div>
</nav>
    <section class="p-8 text-center">
        <h2 class="text-4xl font-black uppercase mb-2">Master Code <br> On The Go</h2>
        <p class="text-slate-400 font-medium text-sm tracking-widest uppercase">Learn. Practice. Build.</p>
    </section>

    <main class="p-6 max-w-3xl mx-auto space-y-6">
        <div class="text-xs text-slate-500">
            <a href="/index.html" class="hover:text-blue-400">Home</a> ›
            <a href="/tools/index.html" class="hover:text-blue-400">Tools</a> ›
            <span class="text-slate-400">Age in ${year}</span>
        </div>

        <div class="space-y-2">
            <h2 class="text-xs font-bold text-blue-500 uppercase tracking-[0.2em]">Age Calculator</h2>
            <h1 class="text-3xl font-black">How Old Am I If I Was Born in ${year}?</h1>
            <p class="text-slate-400">If you were born in ${year}, you are <strong class="text-white">${age} years old</strong> in ${CURRENT_YEAR}. Here's the full breakdown — plus important milestones.</p>
        </div>

        <div class="age-hero">
            <div class="big">${age}</div>
            <div class="label">Years Old in ${CURRENT_YEAR}</div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="info-card">
                <div class="lbl">Born In</div>
                <div class="val">${year}</div>
            </div>
            <div class="info-card">
                <div class="lbl">Age Now</div>
                <div class="val">${age}</div>
            </div>
            <div class="info-card">
                <div class="lbl">Turned 18 in</div>
                <div class="val">${year + 18}</div>
            </div>
            <div class="info-card">
                <div class="lbl">Turns 100 in</div>
                <div class="val">${year + 100}</div>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">📅 Your Age at Each Milestone</h2>
            <ul class="list-disc list-inside text-sm space-y-2 text-slate-300">
                <li>Born in <strong>${year}</strong></li>
                <li>Started school (age 5) in <strong>${year + 5}</strong></li>
                <li>Became a teenager (age 13) in <strong>${year + 13}</strong></li>
                <li>Turned 18 (legal adult) in <strong>${year + 18}</strong></li>
                <li>Turned 21 in <strong>${year + 21}</strong></li>
                <li>Turned 30 in <strong>${year + 30}</strong></li>
                <li>Turned 40 in <strong>${year + 40}</strong></li>
                <li>Turned 50 in <strong>${year + 50}</strong></li>
                <li>Turned 65 (retirement age) in <strong>${year + 65}</strong></li>
                <li>Will turn 100 in <strong>${year + 100}</strong></li>
            </ul>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🎂 Your Generation</h2>
            <p class="text-sm text-slate-300">Someone born in <strong>${year}</strong> belongs to the <strong>${getGeneration(year)}</strong> generation.</p>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 text-center">
            <h2 class="text-white font-bold mb-3">🔢 Get Your Exact Age</h2>
            <p class="text-sm text-slate-400 mb-4">The age above is for someone born on Jan 1, ${year}. For your exact age in years, months, days, hours, and minutes, use our live calculator.</p>
            <a href="/tools/age-calculator.html" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-xl transition-all">Open Age Calculator →</a>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🔗 Nearby Years</h2>
            <div>
                ${agePrev >= 0 && year - 1 >= START_YEAR ? `<a href="/tools/age-in-${year - 1}.html" class="year-chip">← Born in ${year - 1}</a>` : ''}
                <a href="/tools/age-calculator-by-year.html" class="year-chip">📚 All Years</a>
                ${year + 1 <= END_YEAR ? `<a href="/tools/age-in-${year + 1}.html" class="year-chip">Born in ${year + 1} →</a>` : ''}
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">❓ Frequently Asked Questions</h2>
            <div class="space-y-3">
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">How old am I if I was born in ${year}?</summary>
                    <p class="mt-2 text-sm text-slate-300">You are <strong>${age} years old</strong> in ${CURRENT_YEAR} (if your birthday has already passed this year) or <strong>${agePrev} years old</strong> (if it hasn't).</p>
                </details>
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">What year will I turn 100 if born in ${year}?</summary>
                    <p class="mt-2 text-sm text-slate-300">You will turn 100 in <strong>${year + 100}</strong>.</p>
                </details>
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">What generation is someone born in ${year}?</summary>
                    <p class="mt-2 text-sm text-slate-300">People born in ${year} are part of the <strong>${getGeneration(year)}</strong> generation.</p>
                </details>
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">How many days have I been alive if born in ${year}?</summary>
                    <p class="mt-2 text-sm text-slate-300">Approximately ${(age * 365).toLocaleString()} days (varies based on leap years and your exact birth date).</p>
                </details>
            </div>
        </div>

        <section class="related-resources bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🛠️ More Tools</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <a href="/tools/age-calculator.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">🎂 Live Age Calculator</div>
                    <div class="text-xs text-slate-400 mt-1">Exact age plus birthday countdown.</div>
                </a>
                <a href="/tools/age-calculator-by-year.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">📅 All Years</div>
                    <div class="text-xs text-slate-400 mt-1">Age in any year from 1950 to 2010.</div>
                </a>
                <a href="/tools/bmi-calculator.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">⚖️ BMI Calculator</div>
                    <div class="text-xs text-slate-400 mt-1">Body Mass Index with healthy range.</div>
                </a>
                <a href="/tools/index.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">🛠️ All Tools</div>
                    <div class="text-xs text-slate-400 mt-1">Browse the full library.</div>
                </a>
            </div>
        </section>

        <a href="/tools/index.html" class="back-link">← All Tools</a>
    </main>

    <footer class="fixed bottom-0 left-0 right-0 bg-slate-950 border-t border-slate-800 px-8 py-4">
        <div class="flex justify-between items-center max-w-md mx-auto">
            <div class="flex flex-col items-center gap-1 text-blue-500">
                <i class="fa-solid fa-house text-xl"></i>
                <a href="/index.html"><span class="text-[10px] font-bold uppercase">Home</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500">
                <i class="fa-solid fa-book-open text-xl"></i>
                <a href="/courses/index.html"><span class="text-[10px] font-bold uppercase">Courses</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500">
                <i class="fa-solid fa-envelope text-xl"></i>
                <a href="/contact.html"><span class="text-[10px] font-bold uppercase">Contact</span></a>
            </div>
            <div class="flex flex-col items-center gap-1 text-slate-500">
                <i class="fa-solid fa-circle-user text-xl"></i>
                <span class="text-[10px] font-bold uppercase">Profile</span>
            </div>
        </div>
    </footer>
</body>
</html>`;
}

function getGeneration(year) {
    if (year <= 1945) return 'Silent Generation';
    if (year <= 1964) return 'Baby Boomer';
    if (year <= 1980) return 'Gen X';
    if (year <= 1996) return 'Millennial';
    if (year <= 2012) return 'Gen Z';
    return 'Gen Alpha';
}

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

// Generate all pages
let count = 0;
for (let year = START_YEAR; year <= END_YEAR; year++) {
    const html = generatePage(year);
    const filename = `age-in-${year}.html`;
    fs.writeFileSync(path.join(OUTPUT_DIR, filename), html);
    count++;
}

console.log(`✅ Generated ${count} pages in ${OUTPUT_DIR}`);
console.log(`📋 From age-in-${START_YEAR}.html to age-in-${END_YEAR}.html`);
