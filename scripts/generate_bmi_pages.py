#!/usr/bin/env python3
"""
Generate BMI-by-height pages.
Run: python3 scripts/generate_bmi_pages.py
Output: 17 pages in /tools/bmi-{ft}-ft-{in}.html
"""

from string import Template
from pathlib import Path

SITE = "https://makuistudio.com"
BRAND = "MAK Studio"
CURRENT_YEAR = 2026
OUTPUT_DIR = Path(__file__).parent.parent / "tools"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

LB_PER_KG = 2.20462

def bmi_category(bmi):
    if bmi < 18.5: return ("Underweight", "cat-under")
    if bmi < 25:   return ("Normal weight", "cat-normal")
    if bmi < 30:   return ("Overweight", "cat-over")
    if bmi < 35:   return ("Obese Class I", "cat-obese1")
    if bmi < 40:   return ("Obese Class II", "cat-obese2")
    return ("Obese Class III", "cat-obese3")

def get_heights():
    heights = []
    for total_in in range(60, 77):  # 5'0" through 6'4"
        ft = total_in // 12
        inch = total_in % 12
        cm = round(total_in * 2.54, 1)
        heights.append({
            'ft': ft,
            'in': inch,
            'total_in': total_in,
            'cm': cm,
            'label': f"{ft}'{inch}\"" if inch > 0 else f"{ft}'0\"",
            'slug': f"bmi-{ft}-ft-{inch}",
        })
    return heights

def build_weight_rows(height):
    h_m = height['total_in'] * 0.0254
    min_lb = 18.5 * h_m * h_m * LB_PER_KG
    max_lb = 24.9 * h_m * h_m * LB_PER_KG
    bmi40_lb = 40 * h_m * h_m * LB_PER_KG

    start_lb = max(80, (int(min_lb / 10) - 3) * 10)
    end_lb = (int(bmi40_lb / 10) + 2) * 10

    rows = []
    for lb in range(start_lb, end_lb + 1, 10):
        kg = lb / LB_PER_KG
        bmi = kg / (h_m * h_m)
        cat, cls = bmi_category(bmi)
        rows.append(f'                    <tr><td>{lb}</td><td>{kg:.1f}</td><td class="{cls}">{bmi:.1f}</td><td class="{cls}">{cat}</td></tr>')
    return '\n'.join(rows), min_lb, max_lb

PAGE_TEMPLATE = Template('''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
    <title>$title</title>
    <meta name="description" content="$description">
    <meta name="keywords" content="bmi for $height_label, bmi $height_label, healthy weight for $height_label, $height_label bmi chart, bmi $cm cm">
    <meta name="author" content="$brand">
    <meta name="robots" content="index, follow">
    <meta property="og:title" content="$title">
    <meta property="og:description" content="$description">
    <meta property="og:type" content="article">
    <meta property="og:url" content="$url">
    <meta property="og:image" content="$site/images/social-card.png">
    <meta name="twitter:card" content="summary_large_image">
    <link href="../../favicon.png" rel="icon" type="image/png"/>
    <link rel="canonical" href="$url">

    <script type="application/ld+json">
    {"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":"What is a healthy weight for someone $height_label?","acceptedAnswer":{"@type":"Answer","text":"A healthy weight for someone $height_label tall is between $min_lb and $max_lb lbs ($min_kg to $max_kg kg)."}},{"@type":"Question","name":"What BMI is obese at $height_label?","acceptedAnswer":{"@type":"Answer","text":"At $height_label, obesity starts at BMI 30, which is approximately $obese_lb lbs."}},{"@type":"Question","name":"What BMI is underweight at $height_label?","acceptedAnswer":{"@type":"Answer","text":"At $height_label, a BMI below 18.5 is underweight — below $min_lb lbs."}}]}
    </script>

    <script src="https://cdn.tailwindcss.com"></script>
    <link href="../../style.css" rel="stylesheet"/>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <style>
        body { font-family: 'Inter', sans-serif; }
        .bmi-hero { background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); border-radius: 1.5rem; padding: 2rem 1.5rem; text-align: center; color: white; margin: 1rem 0; }
        .bmi-hero .big { font-size: clamp(2rem, 8vw, 3rem); font-weight: 900; line-height: 1.1; font-family: 'Courier New', monospace; }
        .bmi-hero .label { font-size: 0.85rem; letter-spacing: 0.1em; text-transform: uppercase; opacity: 0.95; font-weight: 700; margin-top: 0.5rem; }
        .info-card { background: #0f172a; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; text-align: center; }
        .info-card .val { color: #60a5fa; font-family: 'Courier New', monospace; font-size: 1.1rem; font-weight: 800; }
        .info-card .lbl { color: #94a3b8; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; font-weight: 700; margin-bottom: 4px; }
        .cat-under { color: #38bdf8; } .cat-normal { color: #4ade80; } .cat-over { color: #fbbf24; }
        .cat-obese1 { color: #fb923c; } .cat-obese2 { color: #f87171; } .cat-obese3 { color: #ef4444; }
        table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        th { background: #1e293b; color: #fff; padding: 10px; text-align: left; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.05em; }
        td { padding: 8px 10px; border-bottom: 1px solid #1e293b; font-family: 'Courier New', monospace; color: #cbd5e1; }
        tr:hover td { background: #1e293b; }
        .year-chip { display: inline-block; background: #0f172a; border: 1px solid #334155; color: #cbd5e1; padding: 6px 12px; border-radius: 8px; font-size: 0.82rem; margin: 3px; text-decoration: none; transition: 0.2s; }
        .year-chip:hover { border-color: #3b82f6; color: #60a5fa; }
        .back-link { display: inline-block; margin-top: 2rem; color: #3b82f6; text-decoration: none; }
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
            <span class="text-slate-400">BMI for $height_label</span>
        </div>

        <div class="space-y-2">
            <h2 class="text-xs font-bold text-blue-500 uppercase tracking-[0.2em]">BMI Calculator</h2>
            <h1 class="text-3xl font-black">BMI for $height_label ($cm cm)</h1>
            <p class="text-slate-400">Your healthy weight range at $height_label is <strong class="text-white">$min_lb – $max_lb lbs</strong> ($min_kg – $max_kg kg). Here's the full BMI chart for this height.</p>
        </div>

        <div class="bmi-hero">
            <div class="label">Healthy Weight Range</div>
            <div class="big">$min_lb – $max_lb lbs</div>
            <div class="label" style="margin-top: 0.75rem;">$min_kg – $max_kg kg</div>
        </div>

        <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div class="info-card"><div class="lbl">Height</div><div class="val">$height_label</div></div>
            <div class="info-card"><div class="lbl">In cm</div><div class="val">$cm</div></div>
            <div class="info-card"><div class="lbl">In inches</div><div class="val">$total_in</div></div>
            <div class="info-card"><div class="lbl">Healthy BMI</div><div class="val">18.5–24.9</div></div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">📊 BMI Chart for $height_label</h2>
            <p class="text-sm text-slate-400 mb-3">Find your weight below to see your BMI and category.</p>
            <div style="overflow-x:auto;">
            <table>
                <thead><tr><th>Weight (lb)</th><th>Weight (kg)</th><th>BMI</th><th>Category</th></tr></thead>
                <tbody>
$table_rows
                </tbody>
            </table>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🎯 BMI Categories</h2>
            <ul class="list-disc list-inside text-sm space-y-1 text-slate-300">
                <li><span class="cat-under">Underweight</span> — BMI below 18.5</li>
                <li><span class="cat-normal">Normal weight</span> — BMI 18.5 to 24.9</li>
                <li><span class="cat-over">Overweight</span> — BMI 25 to 29.9</li>
                <li><span class="cat-obese1">Obese Class I</span> — BMI 30 to 34.9</li>
                <li><span class="cat-obese2">Obese Class II</span> — BMI 35 to 39.9</li>
                <li><span class="cat-obese3">Obese Class III</span> — BMI 40 and above</li>
            </ul>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5 text-center">
            <h2 class="text-white font-bold mb-3">⚖️ Get Your Exact BMI</h2>
            <p class="text-sm text-slate-400 mb-4">Enter your exact height and weight for a personalised result with BMI Prime and healthy range.</p>
            <a href="/tools/bmi-calculator.html" class="inline-block bg-blue-500 hover:bg-blue-600 text-white font-bold py-2 px-6 rounded-xl transition-all">Open BMI Calculator →</a>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🔗 Nearby Heights</h2>
            <div>
$nearby_links
                <a href="/tools/bmi-by-height.html" class="year-chip">📚 All Heights</a>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">❓ Frequently Asked Questions</h2>
            <div class="space-y-3">
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">What is a healthy weight for someone $height_label?</summary>
                    <p class="mt-2 text-sm text-slate-300">A healthy weight for someone $height_label tall is between <strong>$min_lb and $max_lb lbs</strong> ($min_kg to $max_kg kg).</p>
                </details>
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">What BMI is obese at $height_label?</summary>
                    <p class="mt-2 text-sm text-slate-300">At $height_label, obesity starts at BMI 30 — approximately <strong>$obese_lb lbs</strong>.</p>
                </details>
                <details class="bg-slate-950 p-3 rounded-xl">
                    <summary class="cursor-pointer text-blue-400 font-medium text-sm">What BMI is underweight at $height_label?</summary>
                    <p class="mt-2 text-sm text-slate-300">At $height_label, a BMI below 18.5 is underweight — below <strong>$min_lb lbs</strong>.</p>
                </details>
            </div>
        </div>

        <section class="related-resources bg-slate-900 border border-slate-800 rounded-3xl p-5">
            <h2 class="text-white font-bold mb-3">🛠️ Related Tools</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                <a href="/tools/bmi-calculator.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">⚖️ BMI Calculator</div>
                    <div class="text-xs text-slate-400 mt-1">Exact BMI with healthy range.</div>
                </a>
                <a href="/tools/bmi-by-height.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">📏 BMI by Height</div>
                    <div class="text-xs text-slate-400 mt-1">All heights in one place.</div>
                </a>
                <a href="/tools/calorie-calculator.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">🔥 Calorie Calculator</div>
                    <div class="text-xs text-slate-400 mt-1">Daily calorie needs.</div>
                </a>
                <a href="/how-to/bmi-chart.html" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
                    <div class="font-semibold text-white">📊 BMI Chart Guide</div>
                    <div class="text-xs text-slate-400 mt-1">Complete reference chart.</div>
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
</html>''')

def main():
    heights = get_heights()
    count = 0

    for i, h in enumerate(heights):
        table_rows, min_lb_raw, max_lb_raw = build_weight_rows(h)
        min_lb = int(round(min_lb_raw))
        max_lb = int(round(max_lb_raw))
        min_kg = round(min_lb_raw / LB_PER_KG, 1)
        max_kg = round(max_lb_raw / LB_PER_KG, 1)
        obese_lb = int(round(30 * (h['total_in'] * 0.0254) ** 2 * LB_PER_KG))

        # Nearby links
        nearby = []
        if i > 0:
            prev = heights[i - 1]
            nearby.append(f'<a href="/tools/{prev["slug"]}.html" class="year-chip">← {prev["label"]}</a>')
        if i < len(heights) - 1:
            nxt = heights[i + 1]
            nearby.append(f'<a href="/tools/{nxt["slug"]}.html" class="year-chip">{nxt["label"]} →</a>')
        nearby_links = '\n                '.join(nearby)

        url = f"{SITE}/tools/{h['slug']}.html"
        title = f'BMI for {h["label"]} — Healthy Weight Range & Chart | {BRAND}'
        description = f'Healthy weight range for someone {h["label"]} ({h["cm"]} cm) is {min_lb}–{max_lb} lbs. Full BMI chart for this height with common weights and categories.'

        html = PAGE_TEMPLATE.substitute(
            title=title,
            description=description,
            brand=BRAND,
            site=SITE,
            url=url,
            height_label=h['label'],
            cm=h['cm'],
            total_in=h['total_in'],
            min_lb=min_lb,
            max_lb=max_lb,
            min_kg=min_kg,
            max_kg=max_kg,
            obese_lb=obese_lb,
            table_rows=table_rows,
            nearby_links=nearby_links,
        )

        filepath = OUTPUT_DIR / f"{h['slug']}.html"
        filepath.write_text(html, encoding='utf-8')
        count += 1

    print(f"✅ Generated {count} BMI-by-height pages in {OUTPUT_DIR}")
    print(f"📋 From {heights[0]['slug']}.html to {heights[-1]['slug']}.html")

if __name__ == '__main__':
    main()