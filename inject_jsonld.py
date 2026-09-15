#!/usr/bin/env python3
"""
Bulk JSON-LD Injector for makuistudio.com
------------------------------------------
Scans all .html files and adds the correct schema.org JSON-LD
based on page type (lesson, course hub, homepage, FAQ, etc.).

Idempotent — skips pages that already have JSON-LD.

Usage:
    python inject_jsonld.py --root ./ui-learning-platform --dry-run
    python inject_jsonld.py --root ./ui-learning-platform
"""

import argparse
import json
import os
import re
from bs4 import BeautifulSoup

BASE_URL = "https://makuistudio.com"
PUBLISHER = {
    "@type": "Organization",
    "name": "MAK Studio",
    "url": BASE_URL,
    "logo": {
        "@type": "ImageObject",
        "url": f"{BASE_URL}/logo mak.jpg"
    }
}

COURSES = {
    "html":       {"name": "HTML & CSS Course",            "url": f"{BASE_URL}/courses/html/index.html"},
    "python":     {"name": "Python Programming Course",    "url": f"{BASE_URL}/courses/python/index.html"},
    "ai":         {"name": "Artificial Intelligence Course","url": f"{BASE_URL}/courses/ai/index.html"},
    "javascript": {"name": "JavaScript Course",            "url": f"{BASE_URL}/courses/javascript/index.html"},
}

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_title(soup):
    t = soup.find("title")
    return t.get_text(strip=True) if t else ""

def get_description(soup):
    m = soup.find("meta", attrs={"name": "description"})
    return m["content"].strip() if m and m.get("content") else ""

def get_canonical(soup, fallback):
    c = soup.find("link", rel="canonical")
    return c["href"].strip() if c and c.get("href") else fallback

def has_jsonld(soup):
    return soup.find("script", attrs={"type": "application/ld+json"}) is not None

def page_url(filepath, root):
    rel = os.path.relpath(filepath, root).replace("\\", "/")
    if rel == "index.html":
        return f"{BASE_URL}/"
    if rel.endswith("/index.html"):
        return f"{BASE_URL}/{rel[:-len('index.html')]}"
    return f"{BASE_URL}/{rel}"

def detect_type(rel_path):
    r = rel_path.lower()
    if re.search(r"courses/(html|python|ai|javascript)/quest\d+/lesson\d+\.html$", r):
        return "lesson"
    if r.endswith("courses/index.html"):
        return "courses_hub"
    if re.match(r"courses/(html|python|ai|javascript)/index\.html$", r):
        return "course_hub"
    if r == "index.html":
        return "homepage"
    if "ultimate-" in r and "guide" in r:
        return "guide"
    if "questions" in r:
        return "faq"
    if "contact" in r:
        return "contact"
    if "showcase" in r:
        return "showcase"
    if "shorts" in r:
        return "shorts"
    if "pro-pack" in r:
        return "product"
    return "snippet"

def course_from_path(rel_path):
    m = re.search(r"courses/(html|python|ai|javascript)/", rel_path.lower())
    return m.group(1) if m else None

# ─────────────────────────────────────────────
# JSON-LD BUILDERS
# ─────────────────────────────────────────────
def schema_homepage(title, desc, url):
    return [
        {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "name": "MAK Studio",
            "url": BASE_URL,
            "description": desc,
            "inLanguage": "en",
            "potentialAction": {
                "@type": "SearchAction",
                "target": f"{BASE_URL}/questions.html?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }
        },
        {
            "@context": "https://schema.org",
            "@type": "EducationalOrganization",
            "name": "MAK Studio",
            "url": BASE_URL,
            "description": desc,
            "logo": f"{BASE_URL}/logo mak.jpg",
            "sameAs": [
                "https://www.youtube.com/@khawajakhurramMAK",
                "https://github.com/mykhurram068-mak"
            ]
        }
    ]

def schema_lesson(title, desc, url, rel_path):
    course_slug = course_from_path(rel_path)
    course = COURSES.get(course_slug, {"name": "Course", "url": BASE_URL})
    lesson_match = re.search(r"lesson(\d+)\.html", rel_path)
    lesson_num = lesson_match.group(1) if lesson_match else "1"
    quest_match = re.search(r"quest(\d+)/", rel_path)
    quest_num = quest_match.group(1) if quest_match else "1"

    return [{
        "@context": "https://schema.org",
        "@type": "LearningResource",
        "name": title,
        "description": desc,
        "url": url,
        "learningResourceType": "Lesson",
        "educationalLevel": "Beginner",
        "inLanguage": "en",
        "isPartOf": {
            "@type": "Course",
            "name": course["name"],
            "url": course["url"],
            "provider": PUBLISHER
        },
        "position": int(lesson_num),
        "about": f"Quest {quest_num}, Lesson {lesson_num}"
    }]

def schema_course_hub(title, desc, url, rel_path):
    course_slug = course_from_path(rel_path)
    course = COURSES.get(course_slug, {"name": "Course", "url": url})
    return [{
        "@context": "https://schema.org",
        "@type": "Course",
        "name": course["name"],
        "description": desc,
        "url": url,
        "provider": PUBLISHER,
        "inLanguage": "en",
        "isAccessibleForFree": True,
        "courseMode": "online",
        "educationalLevel": "Beginner",
        "hasCourseInstance": {
            "@type": "CourseInstance",
            "courseMode": "online",
            "courseWorkload": "PT2H"
        }
    }]

def schema_courses_hub(title, desc, url):
    return [{
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "Free Programming Courses",
        "description": desc,
        "url": url,
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": i + 1,
                "item": {
                    "@type": "Course",
                    "name": c["name"],
                    "url": c["url"],
                    "provider": PUBLISHER,
                    "isAccessibleForFree": True
                }
            }
            for i, c in enumerate(COURSES.values())
        ]
    }]

def schema_guide(title, desc, url, rel_path):
    course_slug = course_from_path(rel_path) or rel_path.split("-")[1] if "-" in rel_path else "guide"
    return [{
        "@context": "https://schema.org",
        "@type": "TechArticle",
        "headline": title,
        "description": desc,
        "url": url,
        "inLanguage": "en",
        "author": PUBLISHER,
        "publisher": PUBLISHER,
        "articleSection": "Tutorial",
        "proficiencyLevel": "Beginner"
    }]

def schema_faq(title, desc, url, soup):
    """Parse FAQ items from the page's accordion structure."""
    questions = []
    for faq_item in soup.select(".faq-item"):
        q_el = faq_item.select_one(".question")
        a_el = faq_item.select_one(".answer")
        if not q_el or not a_el:
            continue
        q_text = q_el.get_text(strip=True)
        # Remove the "HTML" tag label at the start
        q_text = re.sub(r"^[A-Z]{2,4}\s+", "", q_text).strip()
        a_text = a_el.get_text(" ", strip=True)
        if q_text and a_text:
            questions.append({
                "@type": "Question",
                "name": q_text,
                "acceptedAnswer": {"@type": "Answer", "text": a_text[:500]}
            })

    # Fallback if no FAQ items parsed
    if not questions:
        questions.append({
            "@type": "Question",
            "name": "How do I start learning to code?",
            "acceptedAnswer": {
                "@type": "Answer",
                "text": "Start with our free HTML course, then move on to Python, JavaScript, and AI. All courses are free and require no signup."
            }
        })

    return [{
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": "en",
        "mainEntity": questions
    }]

def schema_contact(title, desc, url):
    return [{
        "@context": "https://schema.org",
        "@type": "ContactPage",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": "en"
    }]

def schema_showcase(title, desc, url):
    return [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": "en"
    }]

def schema_shorts(title, desc, url):
    return [{
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": title,
        "description": desc,
        "url": url,
        "inLanguage": "en",
        "about": {
            "@type": "Thing",
            "name": "Video Tutorials"
        }
    }]

def schema_product(title, desc, url):
    return [{
        "@context": "https://schema.org",
        "@type": "Product",
        "name": title,
        "description": desc,
        "url": url,
        "brand": PUBLISHER,
        "offers": {
            "@type": "Offer",
            "price": "7.00",
            "priceCurrency": "USD",
            "availability": "https://schema.org/InStock"
        }
    }]

def schema_snippet(title, desc, url, rel_path):
    name = os.path.basename(rel_path).replace(".html", "")
    return [{
        "@context": "https://schema.org",
        "@type": "SoftwareSourceCode",
        "name": title,
        "description": desc,
        "url": url,
        "codeSampleType": "full (compile ready) solution",
        "programmingLanguage": "HTML, CSS, JavaScript",
        "author": PUBLISHER,
        "publisher": PUBLISHER,
        "inLanguage": "en",
        "keywords": f"free snippet, {name}, html, css, javascript"
    }]

# ─────────────────────────────────────────────
# MAIN INJECTION LOGIC
# ─────────────────────────────────────────────
def build_jsonld(page_type, title, desc, url, rel_path, soup):
    if page_type == "homepage":
        return schema_homepage(title, desc, url)
    if page_type == "lesson":
        return schema_lesson(title, desc, url, rel_path)
    if page_type == "course_hub":
        return schema_course_hub(title, desc, url, rel_path)
    if page_type == "courses_hub":
        return schema_courses_hub(title, desc, url)
    if page_type == "guide":
        return schema_guide(title, desc, url, rel_path)
    if page_type == "faq":
        return schema_faq(title, desc, url, soup)
    if page_type == "contact":
        return schema_contact(title, desc, url)
    if page_type == "showcase":
        return schema_showcase(title, desc, url)
    if page_type == "shorts":
        return schema_shorts(title, desc, url)
    if page_type == "product":
        return schema_product(title, desc, url)
    return schema_snippet(title, desc, url, rel_path)

def inject_file(filepath, root, dry_run=False):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    if has_jsonld(soup):
        return "skipped"

    rel = os.path.relpath(filepath, root).replace("\\", "/")
    page_type = detect_type(rel)

    title = get_title(soup)
    desc = get_description(soup)
    url = get_canonical(soup, page_url(filepath, root))

    if not title or not desc:
        return "missing_meta"

    schemas = build_jsonld(page_type, title, desc, url, rel, soup)

    # Build the script tag(s)
    script_tags = ""
    for schema in schemas:
        json_str = json.dumps(schema, ensure_ascii=False, indent=2)
        script_tags += f'\n    <script type="application/ld+json">\n{json_str}\n    </script>'

    # Insert right before </head>
    if "</head>" not in html:
        return "no_head"

    new_html = html.replace("</head>", f"{script_tags}\n</head>", 1)

    if dry_run:
        print(f"   [{page_type:12}] {rel}")
        return "would_inject"

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_html)

    print(f"   [{page_type:12}] {rel}")
    return "injected"

# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Repo root folder")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()

    print(f"\n🔍 Scanning {args.root}")
    print(f"   Mode: {'DRY RUN (no writes)' if args.dry_run else 'LIVE (writing files)'}\n")

    stats = {"injected": 0, "would_inject": 0, "skipped": 0, "missing_meta": 0, "no_head": 0}
    files = []

    for dirpath, dirs, filenames in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".") and d != "node_modules"]
        for fn in filenames:
            if fn.endswith(".html"):
                files.append(os.path.join(dirpath, fn))

    files.sort()
    print(f"📄 Found {len(files)} HTML files\n")

    for fp in files:
        result = inject_file(fp, args.root, dry_run=args.dry_run)
        stats[result] = stats.get(result, 0) + 1

    print("\n" + "=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"   ✅ Injected:            {stats.get('injected', 0) + stats.get('would_inject', 0)}")
    print(f"   ⏭️  Skipped (had JSON-LD): {stats['skipped']}")
    print(f"   ⚠️  Missing meta tags:   {stats['missing_meta']}")
    print(f"   ❌ No </head> tag:       {stats['no_head']}")

    if args.dry_run:
        print("\n💡 Run without --dry-run to apply changes.")
    else:
        print("\n📋 Next steps:")
        print("   1. git diff  (review a few files)")
        print("   2. Validate with: https://validator.schema.org/")
        print("   3. git add . && git commit -m 'Add JSON-LD schema'")
        print("   4. git push")
        print("   5. Request re-indexing for key pages in GSC")

if __name__ == "__main__":
    main()