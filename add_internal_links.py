#!/usr/bin/env python3
"""
Adds a 'Related Resources' section to every snippet and lesson page
that lacks one. Uses topic-aware content.
Idempotent. Dry-run by default.
"""

import argparse
import os
import re
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# TOPIC-AWARE LINK LIBRARY
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
        ("Login Form", "/login.html", "Auth form with validation."),
        ("Password Generator", "/password-gen.html", "Secure passwords."),
        ("All Snippets", "/index.html#snippets", "Browse the library."),
    ],
}

def detect_topic(rel_path):
    r = rel_path.lower()
    if "javascript" in r: return "javascript"
    if "/python/" in r or "python-" in r: return "python"
    if "/ai/" in r or "ai-" in r or "sentiment" in r or "image-classifier" in r: return "ai"
    if "/html/" in r or "html-" in r or "css" in r or "navbar" in r or "animated" in r or "dropdown" in r: return "html"
    return "snippet"

def has_section(soup):
    return soup.find("section", class_="related-resources") is not None

def build_section(topic):
    items = ""
    for name, url, desc in LINKS.get(topic, LINKS["snippet"]):
        items += f"""
        <a href="{url}" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
            <div class="font-semibold text-white">{name}</div>
            <div class="text-xs text-slate-400 mt-1">{desc}</div>
        </a>"""
    return f"""
<section class="related-resources" style="background:#0f172a; border:1px solid #334155; border-radius:1rem; padding:1.5rem; margin:2rem 0;">
    <h2 style="color:#fff; font-size:1.25rem; font-weight:700; margin-bottom:0.5rem;">📚 Related Resources</h2>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:1rem;">Continue learning with these free resources.</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:0.75rem;">{items}
    </div>
</section>
"""

def process(fp, root, apply=False):
    with open(fp, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    if has_section(soup):
        return None
    main = soup.find("main")
    if not main:
        return None
    rel = os.path.relpath(fp, root).replace("\\", "/")
    topic = detect_topic(rel)
    main.append(BeautifulSoup(build_section(topic), "html.parser"))
    if apply:
        with open(fp, "w", encoding="utf-8") as f:
            f.write(str(soup))
    return rel, topic

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args()

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    count = 0
    for fp in files:
        r = process(fp, args.root, apply=args.apply)
        if r:
            count += 1
            print(f"📄 {r[0]}  ({r[1]})")

    print(f"\n{'🔍 Would update' if not args.apply else '✅ Updated'} {count} pages.")
    if not args.apply:
        print("Run with --apply to write.")

if __name__ == "__main__":
    main()