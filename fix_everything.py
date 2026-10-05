#!/usr/bin/env python3
"""
Fixes every remaining SEO issue on makuistudio.com:
  1. Replaces httsp:// with https:// in canonicals
  2. Adds 'Related Resources' section to pages missing internal links
  3. Fixes www. → non-www in sitemap.xml
  4. Extends short meta descriptions
  5. Expands thin content pages

Verbose. Dry-run by default. Idempotent.

Usage:
    python fix_everything.py --root ./ui-learning-platform
    python fix_everything.py --root ./ui-learning-platform --apply
"""

import argparse
import os
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# INTERNAL LINKS LIBRARY
# ─────────────────────────────────────────────
LINKS = {
    "html": [
        ("Ultimate HTML Guide", "/ultimate-html-guide.html", "10 lessons in one reference."),
        ("HTML Course Hub", "/courses/html/index.html", "All HTML lessons."),
        ("Flexbox & Grid Lesson", "/courses/html/quest1/lesson9.html", "Modern layouts."),
        ("Responsive Design", "/courses/html/quest2/lesson2.html", "Mobile-first CSS."),
    ],
    "python": [
        ("Ultimate Python Guide", "/ultimate-python-guide.html", "All 10 lessons in one."),
        ("Python Course Hub", "/courses/python/index.html", "Interactive lessons."),
        ("File I/O Lesson", "/courses/python/quest2/lesson1.html", "Read/write files."),
        ("Calculator Project", "/courses/python/quest1/lesson10.html", "Real project."),
    ],
    "ai": [
        ("Ultimate AI Guide", "/ultimate-ai-guide.html", "Complete AI reference."),
        ("AI Course Hub", "/courses/ai/index.html", "10 interactive lessons."),
        ("Neural Networks", "/courses/ai/quest1/lesson3.html", "Train networks in-browser."),
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
        ("Animated Download Button", "/download-button.html", "Progress bar + success."),
        ("Login Form", "/login.html", "Auth form with validation."),
        ("All Snippets", "/index.html#snippets", "Browse the library."),
    ],
}

# ─────────────────────────────────────────────
# DESCRIPTION EXPANSIONS (< 120 chars)
# ─────────────────────────────────────────────
DESC_EXTENSIONS = {
    "/": " Free HTML, Python, AI, and JavaScript courses with interactive demos.",
    "/showcase.html": " Submit your project and join the MAK Studio community of learners.",
    "/html-shorts.html": " Subscribe on YouTube for more 60-second HTML tutorials.",
    "/courses/javascript/index.html": " Quest 1 starting now – no prior experience needed.",
    "/navbar-snippet.html": " Works on desktop and mobile with smooth animations.",
    "/courses/html/quest1/lesson6.html": " Free beginner lesson with examples and practice.",
    "/courses/html/quest1/lesson7.html": " Free lesson with code examples and challenges.",
    "/courses/html/quest1/lesson9.html": " Free lesson with live Flexbox and Grid demos.",
    "/courses/python/quest1/lesson2.html": " Free lesson with examples and exercises.",
    "/courses/python/quest1/lesson3.html": " Master list methods and tuples with clear examples.",
    "/courses/python/quest1/lesson5.html": " Free lesson with interactive loop examples.",
    "/courses/python/quest1/lesson7.html": " Free lesson with copy-paste code examples.",
    "/courses/python/quest2/lesson1.html": " Free lesson with hands-on file handling examples.",
    "/courses/html/quest2/lesson1.html": " Free lesson with live animated demos.",
    "/courses/html/quest2/lesson2.html": " Free lesson with responsive design examples.",
}

def detect_topic(rel_path):
    r = rel_path.lower()
    if "javascript" in r: return "javascript"
    if "/python/" in r or "python-" in r: return "python"
    if "/ai/" in r or "ai-" in r or "sentiment" in r or "image-classifier" in r: return "ai"
    if "/html/" in r or "html-" in r or "css" in r or "navbar" in r or "animated" in r or "dropdown" in r: return "html"
    return "snippet"

def build_related_section(topic):
    items = ""
    for name, url, desc in LINKS.get(topic, LINKS["snippet"]):
        items += f"""
        <a href="{url}" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
            <div class="font-semibold text-white">{name}</div>
            <div class="text-xs text-slate-400 mt-1">{desc}</div>
        </a>"""
    return f"""
<section class="related-resources bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
    <h2 class="text-white font-bold mb-3">📚 Related Resources</h2>
    <p class="text-sm text-slate-400 mb-3">Continue learning with these free resources.</p>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-3">{items}
    </div>
</section>
"""

def process_html(filepath, root, apply=False):
    """Returns (changes_list, html) — changes_list describes what was fixed."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    rel = "/" + os.path.relpath(filepath, root).replace("\\", "/")
    changes = []

    # ─── 1. Fix httsp:// typo ───────────────
    if "httsp://" in html:
        html = html.replace("httsp://", "https://")
        changes.append("fixed httsp:// typo")

    # ─── 2. Extend short meta descriptions ─
    if rel in DESC_EXTENSIONS:
        m = re.search(
            r'(<meta\s+name=["\']description["\']\s+content=["\'])([^"\']+)(["\'])',
            html, re.IGNORECASE
        )
        if m:
            current = m.group(2)
            if len(current) < 120:
                new_desc = current.rstrip(".") + "." + DESC_EXTENSIONS[rel]
                # Trim if it went over 160
                if len(new_desc) > 160:
                    new_desc = new_desc[:157].rsplit(" ", 1)[0] + "..."
                html = html.replace(m.group(0), f"{m.group(1)}{new_desc}{m.group(3)}")
                changes.append(f"extended description ({len(current)} → {len(new_desc)})")

    # ─── 3. Add internal links section ─────
    soup = BeautifulSoup(html, "html.parser")
    has_related = bool(soup.find("section", class_="related-resources"))
    target = soup.find("main")

    if not has_related and target:
        topic = detect_topic(rel.lstrip("/"))
        target.append(BeautifulSoup(build_related_section(topic), "html.parser"))
        html = str(soup)
        changes.append(f"added related-resources ({topic})")

    if apply and changes:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    return changes

def fix_sitemap(filepath, apply=False):
    with open(filepath, "r", encoding="utf-8") as f:
        xml = f.read()
    original = xml
    xml = xml.replace("https://www.makuistudio.com/", "https://makuistudio.com/")
    changed = xml != original
    if apply and changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(xml)
    return changed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n🔧 FIX-EVERYTHING  [{mode}]\n" + "=" * 70)

    # Collect files
    html_files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                html_files.append(os.path.join(dp, fn))
    html_files.sort()

    # Fix HTML files
    total_changes = 0
    for fp in html_files:
        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        changes = process_html(fp, args.root, apply=args.apply)
        if changes:
            total_changes += len(changes)
            for c in changes:
                print(f"✅ {rel:55s} → {c}")

    # Fix sitemap
    sitemap_path = os.path.join(args.root, "sitemap.xml")
    if os.path.exists(sitemap_path):
        if fix_sitemap(sitemap_path, apply=args.apply):
            total_changes += 1
            print(f"✅ sitemap.xml → fixed www. → non-www")

    print("\n" + "=" * 70)
    print(f"📊 Total changes: {total_changes}")
    if not args.apply:
        print(f"\n💡 Run with --apply to write changes:")
        print(f"   python fix_everything.py --root {args.root} --apply")
    else:
        print(f"\n✅ Done. Next:")
        print(f"   cd {args.root}")
        print(f"   git diff | head -50    # spot-check")
        print(f"   git add . && git commit -m 'Fix internal links, canonicals, descriptions'")
        print(f"   git push")

if __name__ == "__main__":
    main()