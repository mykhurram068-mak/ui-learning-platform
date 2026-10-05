#!/usr/bin/env python3
"""
Single-Page SEO Fixer
----------------------
Point at one HTML file. It audits it, shows issues, and fixes them.
Usage:
    python fix_page.py --file courses/html/quest1/lesson1.html
    python fix_page.py --file courses/html/quest1/lesson1.html --apply
"""

import argparse
import os
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# DESCRIPTION FIXES (paste the exact one you want per page)
# ─────────────────────────────────────────────
DESC_FIXES = {
    "/courses/html/quest1/lesson1.html": "Learn how to create your first HTML header and paragraph. Understand basic HTML structure. Free lesson with live examples and practice challenges.",
    "/courses/html/quest1/lesson2.html": "Learn how to create hyperlinks in HTML. Understand anchor tags, relative vs absolute URLs, and build a simple navigation menu. Free lesson.",
    "/courses/html/quest1/lesson3.html": "Learn how to add images, videos, and audio to your web pages. Understand the img tag, alt text, and multimedia embedding. Free lesson.",
    "/courses/html/quest1/lesson4.html": "Learn how to organise data with HTML lists (ordered, unordered) and tables. Free beginner lesson with live examples and copy-paste code.",
    "/courses/html/quest1/lesson5.html": "Learn how to create interactive HTML forms. Understand input types, labels, buttons, and form submission. Free lesson with a live contact form.",
    "/courses/html/quest1/lesson6.html": "Learn semantic HTML tags: header, nav, main, article, section, footer. Free beginner lesson with examples and practice challenges.",
    "/courses/html/quest1/lesson7.html": "Learn CSS basics: inline styles, internal stylesheets, and external CSS. Free lesson with code examples and challenges.",
    "/courses/html/quest1/lesson8.html": "Learn the CSS Box Model: content, padding, border, margin. Free lesson with live examples of spacing and layout.",
    "/courses/html/quest1/lesson9.html": "Learn CSS Flexbox and Grid – modern layout systems. Free lesson with live Flexbox and Grid demos and examples.",
    "/courses/html/quest1/lesson10.html": "Build a personal bio page using HTML and CSS. Free capstone project applying semantic HTML, forms, Flexbox, and the box model.",
    "/courses/python/quest1/lesson1.html": "Learn how to write your first Python program. Understand print statements, variables, and basic data types. Free lesson with live examples.",
    "/courses/python/quest1/lesson2.html": "Learn how to store and work with data in Python. Understand variables, integers, floats, strings, and booleans. Free lesson.",
    "/courses/python/quest1/lesson3.html": "Learn the difference between Python lists and tuples. Master list methods, tuple immutability, and when to use each data structure.",
    "/courses/python/quest1/lesson4.html": "Learn how to control program flow with if, elif, and else statements. Make decisions in Python with hands-on examples and exercises.",
    "/courses/python/quest1/lesson5.html": "Learn how to repeat actions with for and while loops in Python. Free lesson with interactive loop examples.",
    "/courses/python/quest1/lesson6.html": "Learn how to define and use functions in Python. Understand parameters, return values, and code reuse with hands-on examples.",
    "/courses/python/quest1/lesson7.html": "Learn Python string methods: upper, lower, strip, replace, split, join, find, count, and f-string formatting. Free lesson.",
    "/courses/python/quest1/lesson8.html": "Learn Python dictionaries – key-value pairs. Create, access, update, delete, and iterate over dictionaries with practical examples.",
    "/courses/python/quest1/lesson9.html": "Learn how to handle errors in Python using try/except. Make your programs robust with exception handling and finally blocks.",
    "/courses/python/quest1/lesson10.html": "Build a functional calculator in Python. Free project applying functions, conditionals, loops, and error handling.",
    "/courses/ai/quest1/lesson1.html": "Learn the basics of Artificial Intelligence: Machine Learning, Deep Learning, and Symbolic AI. Run your first pattern recogniser in the browser.",
    "/courses/ai/quest1/lesson10.html": "Explore the future of AI and the ethical challenges it brings. Understand responsible AI, AGI, and the impact on society. Free lesson.",
    "/showcase.html": "See what students are building with MAK Studio courses. View projects, get inspired, and submit your own work.",
    "/navbar-snippet.html": "Free responsive navbar with hamburger mobile menu. Pure HTML/CSS/JS, works on desktop and mobile with smooth animations.",
    "/html-shorts.html": "Watch quick HTML tutorials in 60 seconds or less. Learn HTML tags, CSS, and more. Subscribe on YouTube for more tutorials.",
    "/python-shorts.html": "Watch quick Python tutorials in 60 seconds or less. Learn variables, loops, and functions. Free MAK Studio shorts.",
    "/courses/javascript/index.html": "Free JavaScript course for beginners. Learn variables, functions, loops, and DOM manipulation. Quest 1 starting now.",
    "/": "Free programming courses (HTML, Python, AI, JavaScript) with interactive demos and free UI snippets for developers.",
}

# ─────────────────────────────────────────────
# RELATED LINKS
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

def detect_topic(filepath):
    r = filepath.lower()
    if "javascript" in r: return "javascript"
    if "/python" in r or "python-" in r: return "python"
    if "/ai/" in r or "ai-" in r or "sentiment" in r or "classifier" in r: return "ai"
    if "/html/" in r or "html-" in r or "css" in r: return "html"
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

def audit_page(filepath, rel_url):
    """Return a list of issues found on this page."""
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    issues = []
    soup = BeautifulSoup(html, "html.parser")

    # Title
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""
    if not title:
        issues.append("❌ Missing title")
    elif len(title) > 60:
        issues.append(f"⚠️  Title too long ({len(title)} chars)")
    elif len(title) < 20:
        issues.append(f"⚠️  Title too short ({len(title)} chars)")

    # Description
    meta = soup.find("meta", attrs={"name": "description"})
    desc = meta.get("content", "").strip() if meta else ""
    if not desc:
        issues.append("❌ Missing meta description")
    elif len(desc) > 160:
        issues.append(f"⚠️  Description too long ({len(desc)} chars)")
    elif len(desc) < 120:
        issues.append(f"⚠️  Description too short ({len(desc)} chars)")

    # H1s
    h1_count = len(soup.find_all("h1"))
    if h1_count == 0:
        issues.append("❌ Missing H1")
    elif h1_count > 1:
        issues.append(f"⚠️  Multiple H1s ({h1_count})")

    # Canonical
    canon = soup.find("link", attrs={"rel": "canonical"})
    if not canon:
        issues.append("❌ Missing canonical")
    elif canon.get("href") and "httsp" in canon["href"]:
        issues.append("❌ Canonical has httsp typo")
    elif canon.get("href") and "github.io" in canon["href"]:
        issues.append("❌ Canonical points to github.io")

    # OG tags
    for prop in ["og:title", "og:description", "og:image"]:
        if not soup.find("meta", attrs={"property": prop}):
            issues.append(f"❌ Missing {prop}")
    if not soup.find("meta", attrs={"name": "twitter:image"}):
        issues.append("❌ Missing twitter:image")

    # JSON-LD
    if not soup.find("script", attrs={"type": "application/ld+json"}):
        issues.append("❌ Missing JSON-LD")

    # Internal links
    internal = 0
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        if href.startswith("/"):
            internal += 1
    if internal < 3:
        issues.append(f"⚠️  Few internal links ({internal})")

    # Related resources
    if not soup.find("section", class_="related-resources"):
        issues.append("⚠️  No related-resources section")

    # Word count
    for tag in soup(["script", "style"]):
        tag.decompose()
    words = len(re.findall(r"\w+", soup.get_text(" ", strip=True)))
    if words < 300:
        issues.append(f"⚠️  Thin content ({words} words)")

    return issues

def fix_page(filepath, rel_url, apply=False):
    with open(filepath, encoding="utf-8") as f:
        html = f.read()

    original = html
    changes = []

    # ─── 1. Fix httsp typo ──────────────────
    if "httsp://" in html:
        html = html.replace("httsp://", "https://")
        changes.append("Fixed httsp:// typo")

    # ─── 2. Fix multiple H1s ────────────────
    h1_matches = list(re.finditer(r"<h1([^>]*)>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL))
    if len(h1_matches) > 1:
        for m in reversed(h1_matches[1:]):
            old = m.group(0)
            new = old.replace("<h1", "<h2", 1).replace("</h1>", "</h2>", 1)
            html = html[:m.start()] + new + html[m.end():]
        changes.append(f"Converted {len(h1_matches)-1} extra H1(s) to H2")

    # ─── 3. Extend meta description ─────────
    if rel_url in DESC_FIXES:
        m = re.search(r'(<meta\s+name=["\']description["\']\s+content=["\'])([^"\']+)(["\'])', html, re.IGNORECASE)
        if m:
            current = m.group(2)
            if len(current) < 120:
                new_desc = DESC_FIXES[rel_url]
                if len(new_desc) > 160:
                    new_desc = new_desc[:157].rsplit(" ", 1)[0] + "..."
                html = html.replace(m.group(0), f"{m.group(1)}{new_desc}{m.group(3)}")
                changes.append(f"Extended description ({len(current)} → {len(new_desc)})")

    # ─── 4. Add related-resources ───────────
    soup = BeautifulSoup(html, "html.parser")
    if not soup.find("section", class_="related-resources"):
        target = soup.find("main") or soup.find("body")
        if target:
            topic = detect_topic(rel_url)
            target.append(BeautifulSoup(build_related_section(topic), "html.parser"))
            html = str(soup)
            changes.append(f"Added related-resources ({topic})")

    # ─── Save ────────────────────────────────
    if apply and html != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    return changes

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Path to the HTML file")
    parser.add_argument("--apply", action="store_true", help="Write changes")
    parser.add_argument("--root", default=".", help="Repo root (for relative URL calc)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        return

    rel = "/" + os.path.relpath(args.file, args.root).replace("\\", "/").lstrip("/")
    if rel == "/index.html":
        rel = "/"

    print(f"\n{'='*65}")
    print(f"📄 {args.file}")
    print(f"   URL path: {rel}")
    print(f"{'='*65}\n")

    # ─── Audit ──────────────────────────────
    print("🔍 AUDIT:\n")
    issues = audit_page(args.file, rel)
    if not issues:
        print("   ✅ No issues found!")
    else:
        for issue in issues:
            print(f"   {issue}")

    # ─── Fix ────────────────────────────────
    print(f"\n{'='*65}")
    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"🔧 FIXES [{mode}]:\n")

    changes = fix_page(args.file, rel, apply=args.apply)
    if not changes:
        print("   ✅ Nothing to fix — page already clean.")
    else:
        for c in changes:
            print(f"   ✅ {c}")

    print(f"\n{'='*65}")
    if not args.apply and changes:
        print(f"💡 To apply these fixes:")
        print(f"   python fix_page.py --file {args.file} --apply")
    elif args.apply and changes:
        print(f"✅ Changes written to disk.")
        print(f"\n📋 Next:")
        print(f"   git diff {args.file}")
        print(f"   git add {args.file}")
        print(f"   git commit -m 'Fix SEO for {os.path.basename(args.file)}'")
    print()

if __name__ == "__main__":
    main()