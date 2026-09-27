#!/usr/bin/env python3
"""
FIX ALL SEO ISSUES — one-shot script for makuistudio.com
Handles:
  1. Multiple H1s (keeps first, converts extras to H2)
  2. Short meta descriptions (<120 chars) on every affected page
  3. Missing internal links (adds related-resources section)
  4. Thin content (adds supplementary sections)
Idempotent. Dry-run by default.
"""

import argparse
import os
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# FULL DESCRIPTION MAP — every page with < 120 chars
# ─────────────────────────────────────────────
DESC_FIXES = {
    "/": "Free programming courses (HTML, Python, AI, JavaScript) with interactive demos and free UI snippets for developers.",
    "/showcase.html": "See what students are building with MAK Studio courses. View projects, get inspired, and submit your own work.",
    "/navbar-snippet.html": "Free responsive navbar with hamburger mobile menu. Pure HTML/CSS/JS, works on desktop and mobile with smooth animations.",
    "/html-shorts.html": "Watch quick HTML tutorials in 60 seconds or less. Learn HTML tags, CSS, and more. Subscribe on YouTube for more.",
    "/python-shorts.html": "Watch quick Python tutorials in 60 seconds or less. Learn variables, loops, and functions. Free MAK Studio shorts.",
    "/courses/javascript/index.html": "Free JavaScript course for beginners. Learn variables, functions, loops, and DOM manipulation. Quest 1 starting now.",
    "/courses/html/quest1/lesson6.html": "Learn semantic HTML tags: header, nav, main, article, section, footer. Free beginner lesson with examples and practice.",
    "/courses/html/quest1/lesson7.html": "Learn CSS basics: inline styles, internal stylesheets, and external CSS. Free lesson with code examples and challenges.",
    "/courses/html/quest1/lesson8.html": "Learn the CSS Box Model: content, padding, border, margin. Free lesson with live examples of spacing and layout.",
    "/courses/html/quest1/lesson9.html": "Learn CSS Flexbox and Grid – modern layout systems. Free lesson with live Flexbox and Grid demos and examples.",
    "/courses/python/quest1/lesson2.html": "Learn how to store and work with data in Python. Understand variables, integers, floats, strings, and booleans. Free lesson.",
    "/courses/python/quest1/lesson3.html": "Learn the difference between Python lists and tuples. Master list methods, tuple immutability, and when to use each data structure.",
    "/courses/python/quest1/lesson5.html": "Learn how to repeat actions with for and while loops in Python. Free lesson with interactive loop examples.",
    "/courses/python/quest1/lesson7.html": "Learn Python string methods: upper, lower, strip, replace, split, join, find, count, and f-string formatting. Free lesson.",
    "/courses/python/quest2/lesson1.html": "Learn how to read from and write to files in Python. Free lesson with hands-on file handling and exception examples.",
    "/courses/html/quest2/lesson1.html": "Learn CSS animations and transitions. Free lesson with live animated demos, keyframes, and interactive UI elements.",
    "/courses/html/quest2/lesson2.html": "Learn responsive design with CSS media queries. Free lesson with responsive design examples for mobile-first layouts.",
    "/courses/html/quest2/lesson3.html": "Master complex layouts with CSS Grid. Learn grid tracks, lines, template areas, gaps, and building advanced responsive layouts.",
    "/courses/index.html": "Free programming courses for beginners. Learn HTML, Python, AI, and JavaScript from scratch with interactive lessons and projects.",
    "/courses/html/index.html": "Free HTML course for beginners. Quest 1 complete (10 lessons). Quest 2 with animations, responsive design, CSS Grid, and more.",
}

# ─────────────────────────────────────────────
# RELATED LINKS LIBRARY
# ─────────────────────────────────────────────
TOPIC_LINKS = {
    "html": [
        ("Ultimate HTML Guide", "/ultimate-html-guide.html", "10 lessons in one reference."),
        ("HTML Course Hub", "/courses/html/index.html", "All HTML lessons."),
        ("Flexbox & Grid", "/courses/html/quest1/lesson9.html", "Modern layouts."),
        ("Responsive Design", "/courses/html/quest2/lesson2.html", "Mobile-first CSS."),
    ],
    "python": [
        ("Ultimate Python Guide", "/ultimate-python-guide.html", "Complete reference."),
        ("Python Course Hub", "/courses/python/index.html", "Interactive lessons."),
        ("File I/O", "/courses/python/quest2/lesson1.html", "Read/write files."),
        ("Calculator Project", "/courses/python/quest1/lesson10.html", "Real project."),
    ],
    "ai": [
        ("Ultimate AI Guide", "/ultimate-ai-guide.html", "Complete AI reference."),
        ("AI Course Hub", "/courses/ai/index.html", "10 interactive lessons."),
        ("Neural Networks", "/courses/ai/quest1/lesson3.html", "Train in-browser."),
        ("Chatbot Project", "/courses/ai/quest1/lesson9.html", "Conversational AI."),
    ],
    "javascript": [
        ("JavaScript Course Hub", "/courses/javascript/index.html", "10 lessons from zero."),
        ("Variables Lesson", "/courses/javascript/quest1/lesson2.html", "Data types."),
        ("Functions Lesson", "/courses/javascript/quest1/lesson6.html", "Reusable code."),
        ("DOM Manipulation", "/courses/javascript/quest1/lesson9.html", "Make pages interactive."),
    ],
    "snippet": [
        ("OTP Verification", "/otp-verification.html", "6-digit input with autofocus."),
        ("Download Button", "/download-button.html", "Progress bar + success."),
        ("Login Form", "/login.html", "Auth form with validation."),
        ("All Snippets", "/index.html#snippets", "Browse the library."),
    ],
}

# ─────────────────────────────────────────────
# THIN CONTENT SUPPLEMENTS
# ─────────────────────────────────────────────
THIN_CONTENT = {
    "/showcase.html": """
<section class="about-showcase bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">How to Submit Your Project</h2>
  <ol class="list-decimal list-inside text-sm space-y-2 text-slate-300">
    <li>Complete any lesson project — the <a href="/courses/html/quest1/lesson10.html" class="text-blue-400 hover:underline">bio page</a> or <a href="/courses/python/quest1/lesson10.html" class="text-blue-400 hover:underline">calculator</a> are great first choices.</li>
    <li>Deploy your project for free using our <a href="/how-to/publish-website-free.html" class="text-blue-400 hover:underline">GitHub Pages guide</a>.</li>
    <li>Fill out the submission form with your project link and a short description.</li>
    <li>Your project appears on this page within 48 hours.</li>
  </ol>
  <p class="text-sm text-slate-400 mt-3">Submissions are free. No signup required. We accept any project that used a MAK Studio lesson as a starting point.</p>
</section>
""",
    "/contact.html": """
<section class="contact-faq bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">Before You Contact Us</h2>
  <div class="space-y-3 text-sm text-slate-300">
    <div>
      <p class="text-white font-medium">Stuck on a lesson?</p>
      <p class="text-xs text-slate-400">Check our <a href="/questions.html" class="text-blue-400 hover:underline">FAQ page</a> — most common questions are answered there.</p>
    </div>
    <div>
      <p class="text-white font-medium">Reporting a bug?</p>
      <p class="text-xs text-slate-400">Include the page URL and what you expected to happen. Screenshots help.</p>
    </div>
    <div>
      <p class="text-white font-medium">Suggesting a new snippet or lesson?</p>
      <p class="text-xs text-slate-400">We love ideas. Tell us the topic and why it would help other learners.</p>
    </div>
  </div>
  <p class="text-sm text-slate-400 mt-4">We reply within 1-2 business days.</p>
</section>
""",
    "/python-shorts.html": """
<section class="shorts-about bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">📺 About Python Shorts</h2>
  <p class="text-sm text-slate-300 mb-3">These 60-second tutorials cover one concept at a time — perfect for learning in small doses or reviewing something you already know.</p>
  <p class="text-sm text-slate-300 mb-3">Popular topics covered:</p>
  <ul class="list-disc list-inside text-sm space-y-1 text-slate-300">
    <li>Print statements and variables</li>
    <li>Lists, tuples, and dictionaries</li>
    <li>Loops and conditionals</li>
    <li>Functions and parameters</li>
    <li>File handling basics</li>
  </ul>
  <p class="text-sm text-slate-400 mt-3">Subscribe on YouTube to catch every new short as it drops.</p>
</section>
""",
    "/html-shorts.html": """
<section class="shorts-about bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">📺 About HTML Shorts</h2>
  <p class="text-sm text-slate-300 mb-3">Every HTML short teaches one tag or concept in under 60 seconds. Ideal for beginners who want to see how something works before diving into a full lesson.</p>
  <p class="text-sm text-slate-300 mb-3">Popular topics covered:</p>
  <ul class="list-disc list-inside text-sm space-y-1 text-slate-300">
    <li>Basic document structure</li>
    <li>Headings and paragraphs</li>
    <li>Links and navigation</li>
    <li>Images and alt text</li>
    <li>Forms and inputs</li>
  </ul>
  <p class="text-sm text-slate-400 mt-3">Watch the full collection on YouTube. New short every week.</p>
</section>
""",
    "/navbar-snippet.html": """
<section class="snippet-details bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">When to Use This Navbar</h2>
  <p class="text-sm text-slate-300 mb-3">This responsive navbar is the standard pattern for any modern website. Use it when you need:</p>
  <ul class="list-disc list-inside text-sm space-y-1 text-slate-300">
    <li>A mobile-friendly navigation that collapses on small screens</li>
    <li>A simple, accessible menu with keyboard support</li>
    <li>A navbar with no dependencies (pure HTML/CSS/JS)</li>
  </ul>
  <h3 class="text-white font-bold mt-4 mb-2 text-sm">Common Customizations</h3>
  <ul class="list-disc list-inside text-sm space-y-1 text-slate-300">
    <li>Change the background color in <code>.navbar { background: ... }</code></li>
    <li>Add more menu items by editing the <code>&lt;ul&gt;</code> list</li>
    <li>Change the hamburger icon size via <code>.hamburger span { width: ... }</code></li>
  </ul>
</section>
""",
}

def detect_topic(rel_path):
    r = rel_path.lower()
    if "javascript" in r: return "javascript"
    if "/python" in r or "python-" in r: return "python"
    if "/ai" in r or "ai-" in r or "sentiment" in r or "classifier" in r: return "ai"
    if "/html" in r or "html-" in r or "css" in r: return "html"
    return "snippet"

def build_related_section(topic):
    items = ""
    for name, url, desc in TOPIC_LINKS.get(topic, TOPIC_LINKS["snippet"]):
        items += f'<a href="{url}" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all"><div class="font-semibold text-white">{name}</div><div class="text-xs text-slate-400 mt-1">{desc}</div></a>'
    return f'''
<section class="related-resources bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">📚 Related Resources</h2>
  <p class="text-sm text-slate-400 mb-3">Continue learning with these free resources.</p>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">{items}</div>
</section>'''

def process_file(filepath, root, apply=False):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    rel = "/" + os.path.relpath(filepath, root).replace("\\", "/").lstrip("/")
    if rel == "/index.html":
        rel = "/"
    changes = []

    # ─── 1. Fix multiple H1s ────────────────
    h1_count = len(re.findall(r"<h1[\s>]", html, re.IGNORECASE))
    if h1_count > 1:
        # Replace all but the first H1 with H2
        def replace_later_h1s(match_obj):
            nonlocal h1_count
            if h1_count > 1:
                h1_count -= 1
                return match_obj.group(0).replace("h1", "h2").replace("H1", "H2")
            return match_obj.group(0)
        # Do it in reverse to preserve the first one
        h1_matches = list(re.finditer(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL))
        if len(h1_matches) > 1:
            # Convert all but the first
            for m in reversed(h1_matches[1:]):
                old = m.group(0)
                new = old.replace("<h1", "<h2", 1).replace("</h1>", "</h2>", 1)
                html = html[:m.start()] + new + html[m.end():]
            changes.append(f"fixed {len(h1_matches)-1} extra H1(s)")

    # ─── 2. Fix httsp typo ──────────────────
    if "httsp://" in html:
        html = html.replace("httsp://", "https://")
        changes.append("fixed httsp")

    # ─── 3. Extend short meta descriptions ──
    if rel in DESC_FIXES:
        m = re.search(r'(<meta\s+name=["\']description["\']\s+content=["\'])([^"\']+)(["\'])', html, re.IGNORECASE)
        if m:
            current = m.group(2)
            if len(current) < 120:
                new_desc = DESC_FIXES[rel]
                if len(new_desc) > 160:
                    new_desc = new_desc[:157].rsplit(" ", 1)[0] + "..."
                html = html.replace(m.group(0), f"{m.group(1)}{new_desc}{m.group(3)}")
                changes.append(f"desc {len(current)}→{len(new_desc)}")

    # ─── 4. Parse and add sections ──────────
    soup = BeautifulSoup(html, "html.parser")

    # Add related-resources if missing (skip How-To pages which already have it)
    if not soup.find("section", class_="related-resources"):
        target = soup.find("main") or soup.find("body")
        if target:
            topic = detect_topic(rel.lstrip("/"))
            target.append(BeautifulSoup(build_related_section(topic), "html.parser"))
            changes.append(f"added links ({topic})")

    # Add thin-content supplement if applicable
    if rel in THIN_CONTENT:
        # Check if it's already there
        marker = THIN_CONTENT[rel][:60].strip()[:30]
        if marker not in html:
            target = soup.find("main") or soup.find("body")
            if target:
                target.append(BeautifulSoup(THIN_CONTENT[rel], "html.parser"))
                changes.append(f"added thin-content section")

    html = str(soup)

    if apply and changes:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    return changes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n🔧 FIX ALL ISSUES  [{mode}]\n" + "=" * 70)

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    total = 0
    touched = 0
    for fp in files:
        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        changes = process_file(fp, args.root, apply=args.apply)
        if changes:
            touched += 1
            total += len(changes)
            print(f"✅ {rel}")
            for c in changes:
                print(f"     → {c}")

    print("\n" + "=" * 70)
    print(f"📊 Pages touched: {touched}   Total changes: {total}")

    if not args.apply:
        print(f"\n💡 This was a DRY RUN. To apply, run:")
        print(f"   python fix_all_issues.py --root {args.root} --apply")
    else:
        print(f"\n✅ Changes written.")
        print(f"\n📋 Next steps:")
        print(f"   1. cd {args.root}")
        print(f"   2. git diff | head -50     # spot-check")
        print(f"   3. git add . && git commit -m 'Fix all remaining SEO issues'")
        print(f"   4. git push")
        print(f"   5. Resubmit sitemap in Google Search Console")

if __name__ == "__main__":
    main()