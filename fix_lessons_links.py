#!/usr/bin/env python3
"""Add related-resources section to lesson and snippet pages missing it."""

import os, re
from bs4 import BeautifulSoup

ROOT = "."
BASE = "https://makuistudio.com"

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

def detect_topic(rel):
    r = rel.lower()
    if "javascript" in r: return "javascript"
    if "/python" in r or "python-" in r: return "python"
    if "/ai" in r or "ai-" in r or "sentiment" in r or "classifier" in r: return "ai"
    if "/html" in r or "html-" in r or "css" in r: return "html"
    return "snippet"

def has_section(soup):
    return soup.find("section", class_="related-resources") is not None

def build(topic):
    items = ""
    for name, url, desc in TOPIC_LINKS.get(topic, TOPIC_LINKS["snippet"]):
        items += f'<a href="{url}" class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all"><div class="font-semibold text-white">{name}</div><div class="text-xs text-slate-400 mt-1">{desc}</div></a>'
    return f'''
<section class="related-resources bg-slate-900 border border-slate-800 rounded-3xl p-5" style="margin-top:2rem;">
  <h2 class="text-white font-bold mb-3">📚 Related Resources</h2>
  <p class="text-sm text-slate-400 mb-3">Continue learning with these free resources.</p>
  <div class="grid grid-cols-1 md:grid-cols-2 gap-3">{items}</div>
</section>'''

def main():
    files = []
    for dp, dirs, fns in os.walk(ROOT):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))

    updated = 0
    for fp in files:
        rel = os.path.relpath(fp, ROOT).replace("\\", "/")
        # Skip How-To pages (already done) and top-level guides
        if rel.startswith("how-to/"): continue
        if rel in ("index.html",): continue

        with open(fp, encoding="utf-8") as f: html = f.read()
        soup = BeautifulSoup(html, "html.parser")
        if has_section(soup): continue

        target = soup.find("main") or soup.find("body")
        if not target: continue

        topic = detect_topic(rel)
        target.append(BeautifulSoup(build(topic), "html.parser"))

        with open(fp, "w", encoding="utf-8") as f: f.write(str(soup))
        updated += 1
        print(f"✅ {rel}")

    print(f"\n📊 Updated {updated} pages.")

if __name__ == "__main__":
    main()