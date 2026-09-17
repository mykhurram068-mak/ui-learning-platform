#!/usr/bin/env python3
"""
OG Image Checker
----------------
Finds every og:image meta tag in your repo and verifies the URL returns 200.
Reports broken references.

Usage:
    python check_og_images.py --root ./ui-learning-platform
"""

import argparse
import os
import re
import time
from urllib.parse import urljoin

import requests

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MAKStudioOGCheck/1.0)"}

OG_RE = re.compile(
    r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE
)
TWITTER_RE = re.compile(
    r'<meta\s+name=["\']twitter:image["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE
)

def check_url(url, cache):
    if url in cache:
        return cache[url]
    try:
        r = requests.head(url, headers=HEADERS, timeout=10, allow_redirects=True)
        status = r.status_code
    except Exception:
        status = "ERROR"
    cache[url] = status
    return status

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True)
    args = parser.parse_args()

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    print(f"📄 Scanning {len(files)} files...\n")

    url_cache = {}
    broken = []
    missing = []

    for fp in files:
        with open(fp, "r", encoding="utf-8") as f:
            html = f.read()

        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        found = OG_RE.findall(html) + TWITTER_RE.findall(html)

        if not found:
            missing.append(rel)
            continue

        for url in set(found):
            status = check_url(url, url_cache)
            if status != 200:
                broken.append((rel, url, status))
            time.sleep(0.3)  # polite

    print("=" * 72)
    print(f"❌ Pages with NO og:image/twitter:image: {len(missing)}")
    for rel in missing:
        print(f"   - {rel}")

    print()
    print(f"❌ Broken image URLs: {len(broken)}")
    for rel, url, status in broken:
        print(f"   [{status}] {url}")
        print(f"           on {rel}")

    if not missing and not broken:
        print("✅ All OG images present and resolving correctly.")
    else:
        print("\n💡 Fix the issues above, then re-run this script.")

if __name__ == "__main__":
    main()