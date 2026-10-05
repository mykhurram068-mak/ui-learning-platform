#!/usr/bin/env python3
"""
Single-page SEO audit — for verifying new snippet pages.
Usage: python audit_one_page.py --url https://makuistudio.com/otp-verification.html
"""

import argparse
import re
import requests
from bs4 import BeautifulSoup

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MAKStudioSEO/1.0)"}

def audit(url):
    print(f"\n🔍 Auditing: {url}\n" + "=" * 60)
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
    except Exception as e:
        print(f"❌ Fetch failed: {e}")
        return

    soup = BeautifulSoup(r.text, "html.parser")
    issues = []

    # ── Title ───────────────────────────────
    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    print(f"📄 Title ({len(title)}): {title}")
    if not title:
        issues.append("Missing title")
    elif len(title) > 60:
        issues.append(f"Title too long ({len(title)})")
    elif len(title) < 20:
        issues.append(f"Title too short ({len(title)})")

    # ── Meta description ────────────────────
    m = soup.find("meta", attrs={"name": "description"})
    desc = m.get("content", "").strip() if m else ""
    print(f"📝 Description ({len(desc)}): {desc[:80]}...")
    if not desc:
        issues.append("Missing meta description")
    elif len(desc) > 160:
        issues.append(f"Description too long ({len(desc)})")
    elif len(desc) < 120:
        issues.append(f"Description short ({len(desc)})")

    # ── H1 ─────────────────────────────────
    h1s = soup.find_all("h1")
    print(f"🔤 H1 count: {len(h1s)}")
    if len(h1s) == 0:
        issues.append("Missing H1")
    elif len(h1s) > 1:
        issues.append(f"Multiple H1 ({len(h1s)})")

    # ── Canonical ──────────────────────────
    c = soup.find("link", attrs={"rel": "canonical"})
    canonical = c.get("href", "").strip() if c else ""
    print(f"🔗 Canonical: {canonical}")
    if not canonical:
        issues.append("Missing canonical")
    elif "github.io" in canonical:
        issues.append(f"Canonical points to github.io: {canonical}")
    elif not canonical.startswith("https://makuistudio.com"):
        issues.append(f"Canonical not on makuistudio.com: {canonical}")

    # ── Open Graph ─────────────────────────
    og_title = bool(soup.find("meta", attrs={"property": "og:title"}))
    og_desc  = bool(soup.find("meta", attrs={"property": "og:description"}))
    og_img   = bool(soup.find("meta", attrs={"property": "og:image"}))
    tw_img   = bool(soup.find("meta", attrs={"name": "twitter:image"}))
    print(f"🖼️  OG: title={og_title} desc={og_desc} img={og_img} twimg={tw_img}")
    if not og_title: issues.append("Missing og:title")
    if not og_desc:  issues.append("Missing og:description")
    if not og_img:   issues.append("Missing og:image")
    if not tw_img:   issues.append("Missing twitter:image")

    # ── JSON-LD ────────────────────────────
    jsonld_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    raw_match = "application/ld+json" in r.text
    print(f"📊 JSON-LD tags: {len(jsonld_tags)} (raw match: {raw_match})")
    if not jsonld_tags and not raw_match:
        issues.append("No JSON-LD")

    # ── Images ─────────────────────────────
    imgs = soup.find_all("img")
    missing_alt = [i for i in imgs if not i.get("alt")]
    print(f"🖼️  Images: {len(imgs)} (missing alt: {len(missing_alt)})")
    if missing_alt:
        issues.append(f"{len(missing_alt)} images missing alt")

    # ── Word count ─────────────────────────
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text(" ", strip=True)
    words = len(re.findall(r"\w+", text))
    print(f"📚 Word count: {words}")
    if words < 300:
        issues.append(f"Thin content ({words} words)")

    # ── Internal links ─────────────────────
    internal = 0
    for a in soup.find_all("a", href=True):
        h = a.get("href", "")
        if h.startswith("/") or "makuistudio.com" in h:
            internal += 1
    print(f"🔗 Internal links: {internal}")
    if internal < 3:
        issues.append(f"Few internal links ({internal})")

    # ── Verdict ────────────────────────────
    print("=" * 60)
    if not issues:
        print("✅ PASS — no SEO issues found.\n")
    else:
        print(f"⚠️  {len(issues)} issue(s):")
        for i in issues:
            print(f"   - {i}")
        print()

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    args = p.parse_args()
    audit(args.url)