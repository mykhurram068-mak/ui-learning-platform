#!/usr/bin/env python3
"""
Thin Content Expander for makuistudio.com
------------------------------------------
Adds genuinely useful sections to thin pages:
  - "Related Resources" (internal links block)
  - "About this page" (contextual info)
  - "Next Steps" (clear CTA)

Content is topic-aware — it reads the page type and generates
relevant copy, not filler.

Idempotent. Dry-run by default.

Usage:
    python expand_thin_content.py --root ./ui-learning-platform
    python expand_thin_content.py --root ./ui-learning-platform --apply
"""

import argparse
import os
import re

from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# TOPIC-AWARE CONTENT LIBRARY
# ─────────────────────────────────────────────
# Each entry gives you real, useful copy for a page.

RESOURCES_BY_TOPIC = {
    "html": {
        "title": "📚 Continue Learning HTML",
        "intro": "Ready to go deeper? These free resources cover the next steps in your HTML journey.",
        "links": [
            ("Ultimate HTML Guide", "/ultimate-html-guide.html", "10 lessons in one long-form resource."),
            ("HTML Course Hub", "/courses/html/index.html", "All 10 HTML lessons with interactive demos."),
            ("Responsive Design Lesson", "/courses/html/quest2/lesson2.html", "Build mobile-first websites with media queries."),
            ("Flexbox & Grid Lesson", "/courses/html/quest1/lesson9.html", "Master modern layout systems."),
        ],
    },
    "css": {
        "title": "🎨 Explore More CSS Snippets",
        "intro": "These free CSS components pair well with what you just learned.",
        "links": [
            ("Animated Cards", "/animated-cards.html", "Hover effects and smooth transitions."),
            ("Dark Mode Toggle", "/darkmode.html", "CSS variables + localStorage theming."),
            ("CSS Loaders & Spinners", "/loader.html", "4 loading animations, no JavaScript required."),
            ("Dropdown Menu", "/dropdown-menu.html", "Pure CSS dropdown with mobile support."),
        ],
    },
    "python": {
        "title": "🐍 Continue Learning Python",
        "intro": "Go further with these free Python resources — from fundamentals to projects.",
        "links": [
            ("Ultimate Python Guide", "/ultimate-python-guide.html", "All 10 lessons in one reference."),
            ("Python Course Hub", "/courses/python/index.html", "Start from zero with interactive lessons."),
            ("File I/O Lesson", "/courses/python/quest2/lesson1.html", "Read and write files like a pro."),
            ("Calculator Project", "/courses/python/quest1/lesson10.html", "Build a real project with functions and loops."),
        ],
    },
    "ai": {
        "title": "🤖 Explore More AI Lessons",
        "intro": "Keep learning with these AI tutorials — from ML basics to building chatbots.",
        "links": [
            ("Ultimate AI Guide", "/ultimate-ai-guide.html", "Complete beginner-friendly reference."),
            ("AI Course Hub", "/courses/ai/index.html", "10 interactive lessons with TensorFlow.js."),
            ("Neural Networks Lesson", "/courses/ai/quest1/lesson3.html", "Build and train networks in your browser."),
            ("Chatbot Project", "/courses/ai/quest1/lesson9.html", "Create a conversational AI."),
        ],
    },
    "javascript": {
        "title": "⚡ Continue Learning JavaScript",
        "intro": "Level up your JS with these related lessons and projects.",
        "links": [
            ("JavaScript Course Hub", "/courses/javascript/index.html", "10 lessons from beginner to project."),
            ("Variables & Data Types", "/courses/javascript/quest1/lesson2.html", "Master the building blocks."),
            ("Functions Lesson", "/courses/javascript/quest1/lesson6.html", "Write reusable code."),
            ("DOM Manipulation", "/courses/javascript/quest1/lesson9.html", "Make pages interactive."),
        ],
    },
    "shorts": {
        "title": "📺 Watch the Video Series",
        "intro": "Prefer learning by watching? Subscribe to our YouTube channel for 60-second tutorials.",
        "links": [
            ("HTML Shorts", "/html-shorts.html", "Quick HTML tutorials in under a minute."),
            ("Python Shorts", "/python-shorts.html", "Bite-sized Python lessons."),
            ("AI Shorts", "/ai-shorts.html", "Quick AI concept explainers."),
            ("YouTube Channel", "https://www.youtube.com/@khawajakhurramMAK", "1.5K+ subscribers, 700+ videos."),
        ],
    },
    "contact": {
        "title": "🔗 Explore Free Resources",
        "intro": "While you're here, check out what else MAK Studio offers — all completely free.",
        "links": [
            ("Free Courses", "/courses/index.html", "HTML, Python, AI, and JavaScript."),
            ("UI Snippets", "/index.html#snippets", "Copy-paste components for your projects."),
            ("FAQ", "/questions.html", "Answers to common coding questions."),
            ("Project Showcase", "/showcase.html", "See what students have built."),
        ],
    },
    "showcase": {
        "title": "🚀 Ready to Build Your Own?",
        "intro": "Start a course and submit your project to the showcase.",
        "links": [
            ("Free Courses", "/courses/index.html", "Pick a language and start learning."),
            ("HTML Bio Page Project", "/courses/html/quest1/lesson10.html", "Great first project."),
            ("Python Calculator", "/courses/python/quest1/lesson10.html", "Apply Python fundamentals."),
            ("Sentiment Analyser", "/sentiment-analyser.html", "AI project with real output."),
        ],
    },
    "courses_hub": {
        "title": "🤔 Not Sure Where to Start?",
        "intro": "Each course is self-contained. Here's a quick guide:",
        "links": [
            ("HTML & CSS", "/courses/html/index.html", "Best for beginners — start here."),
            ("Python", "/courses/python/index.html", "Best for scripting and automation."),
            ("AI", "/courses/ai/index.html", "Best for understanding modern AI."),
            ("JavaScript", "/courses/javascript/index.html", "Best for interactive websites."),
        ],
    },
    "course_hub": {
        "title": "🎯 What You'll Learn",
        "intro": "This course is structured as 10 progressive lessons. By the end, you'll be able to:",
        "list": [
            "Understand core concepts with real code examples",
            "Build 2-3 complete projects from scratch",
            "Apply what you learn to your own work",
            "Continue to Quest 2 (intermediate level)",
        ],
    },
    "default": {
        "title": "📚 Related Resources",
        "intro": "Explore more free content from MAK Studio.",
        "links": [
            ("Free Courses", "/courses/index.html", "HTML, Python, AI, JavaScript."),
            ("UI Snippets", "/index.html#snippets", "Copy-paste components."),
            ("FAQ", "/questions.html", "Common coding questions."),
            ("Pro Pack", "/pro-pack.html", "15 premium components for $7."),
        ],
    },
}

# ─────────────────────────────────────────────
# PAGE TYPE DETECTION
# ─────────────────────────────────────────────
def detect_topic(rel_path, title):
    r = (rel_path + " " + title).lower()
    if "javascript" in r or " js " in r:
        return "javascript"
    if "python" in r:
        return "python"
    if "/ai" in r or " ai " in r or "machine" in r or "neural" in r:
        return "ai"
    if "shorts" in r:
        return "shorts"
    if "contact" in r:
        return "contact"
    if "showcase" in r:
        return "showcase"
    if rel_path == "courses/index.html":
        return "courses_hub"
    if re.match(r"courses/[^/]+/index\.html$", rel_path):
        return "course_hub"
    if "html" in r or "css" in r:
        return "html"
    return "default"

# ─────────────────────────────────────────────
# HTML BUILDERS
# ─────────────────────────────────────────────
def build_related_links(topic_data):
    links_html = ""
    for name, url, desc in topic_data["links"]:
        external = url.startswith("http")
        target = ' target="_blank" rel="noopener"' if external else ""
        links_html += f"""
        <a href="{url}"{target} class="block bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-blue-500/50 transition-all">
            <div class="font-semibold text-white">{name}</div>
            <div class="text-xs text-slate-400 mt-1">{desc}</div>
        </a>"""

    return f"""
<section class="related-resources" style="background:#0f172a; border:1px solid #334155; border-radius:1rem; padding:1.5rem; margin:2rem 0;">
    <h2 style="color:#fff; font-size:1.25rem; font-weight:700; margin-bottom:0.5rem;">{topic_data['title']}</h2>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:1rem;">{topic_data['intro']}</p>
    <div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:0.75rem;">{links_html}
    </div>
</section>
"""

def build_what_youll_learn(topic_data):
    items = "".join(f'<li style="color:#cbd5e1; margin-bottom:0.25rem;">{item}</li>'
                    for item in topic_data.get("list", []))
    return f"""
<section class="learning-outcomes" style="background:#0f172a; border:1px solid #334155; border-radius:1rem; padding:1.5rem; margin:2rem 0;">
    <h2 style="color:#fff; font-size:1.25rem; font-weight:700; margin-bottom:0.5rem;">{topic_data['title']}</h2>
    <p style="color:#94a3b8; font-size:0.9rem; margin-bottom:1rem;">{topic_data['intro']}</p>
    <ul style="list-style:disc; padding-left:1.5rem;">{items}</ul>
</section>
"""

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def has_expansion(soup):
    """Detect if the page already has our expansion block."""
    return soup.find("section", class_="related-resources") is not None \
        or soup.find("section", class_="learning-outcomes") is not None

def process_file(filepath, root, apply=False):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    if has_expansion(soup):
        return None

    main = soup.find("main")
    if not main:
        return None

    rel = os.path.relpath(filepath, root).replace("\\", "/")
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    topic = detect_topic(rel, title)
    topic_data = RESOURCES_BY_TOPIC.get(topic, RESOURCES_BY_TOPIC["default"])

    if topic == "course_hub":
        expansion_html = build_what_youll_learn(topic_data)
    else:
        expansion_html = build_related_links(topic_data)

    # Insert at end of <main>
    main.append(BeautifulSoup(expansion_html, "html.parser"))

    if apply:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(soup))

    return {
        "rel": rel,
        "topic": topic,
        "block": "related-resources" if topic != "course_hub" else "learning-outcomes",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n🔍 Scanning {args.root}  [{mode}]\n")

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    # Only touch thin pages (< 300 words in audit)
    # But we don't know word counts here — so we filter by absence of expansion
    # and rely on user to run against all. Alternatively, list the thin pages.
    THIN_PAGES = {
        "navbar-snippet.html",
        "html-shorts.html",
        "python-shorts.html",
        "contact.html",
        "showcase.html",
        "courses/index.html",
        "courses/html/index.html",
        "courses/python/index.html",
    }

    expanded = 0
    for fp in files:
        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        if rel not in THIN_PAGES:
            continue
        result = process_file(fp, args.root, apply=args.apply)
        if result:
            expanded += 1
            print(f"📄 {result['rel']}")
            print(f"   ➕ {result['block']} added (topic: {result['topic']})")

    print(f"\n📊 {expanded} pages {'would be' if not args.apply else 'were'} expanded.")

    if not args.apply and expanded > 0:
        print(f"\n💡 Run with --apply to write changes.")
    elif args.apply:
        print(f"\n✅ Done. Next:")
        print(f"   cd {args.root}")
        print(f"   git add . && git commit -m 'Expand thin pages with related-resources sections'")
        print(f"   git push")

if __name__ == "__main__":
    main()