#!/usr/bin/env python3
"""
Bulk OG Image Fixer for makuistudio.com
----------------------------------------
For every .html file:
  - Adds og:image and twitter:image if missing
  - Replaces any og:image / twitter:image URL that 404s
  - Sets them all to the canonical social card

Idempotent. Dry-run by default.

Usage:
    python fix_og_images.py --root ./ui-learning-platform
    python fix_og_images.py --root ./ui-learning-platform --apply
"""

import argparse
import os
import re
import time

import requests
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
NEW_IMAGE_URL = "https://makuistudio.com/images/social-card.png"

HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; MAKStudioOGFix/1.0)"}

OG_IMAGE_PROP = "og:image"
TW_IMAGE_NAME = "twitter:image"

# ─────────────────────────────────────────────
# URL CHECK (cached)
# ─────────────────────────────────────────────
_url_cache = {}

def url_is_ok(url):
    """Return True if URL returns 200, False otherwise."""
    if url in _url_cache:
        return _url_cache[url]
    try:
        r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
        ok = (r.status_code == 200)
    except Exception:
        ok = False
    _url_cache[url] = ok
    time.sleep(0.2)  # polite
    return ok

# ─────────────────────────────────────────────
# MAIN LOGIC
# ─────────────────────────────────────────────
def ensure_meta(soup, attr_key, attr_val, content):
    """Ensure a meta tag exists with the right content. Return (changed, action)."""
    # Look for the tag
    existing = soup.find("meta", attrs={attr_key: attr_val})

    if existing is None:
        tag = soup.new_tag("meta")
        tag[attr_key] = attr_val
        tag["content"] = content
        # Insert at the end of <head> (before </head>)
        if soup.head:
            soup.head.append(tag)
            return True, "added"
        return False, "no_head"

    old_content = existing.get("content", "").strip()

    # If content is already correct, nothing to do
    if old_content == content:
        return False, "ok"

    # If content is empty or 404s, replace it
    if not old_content or not url_is_ok(old_content):
        existing["content"] = content
        return True, f"fixed ({old_content[:50]}... → correct)" if old_content else "fixed (empty)"

    return False, "ok"

def process_file(filepath, apply=False):
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    if not soup.head:
        return None

    # Fix og:image
    og_changed, og_action = ensure_meta(soup, "property", OG_IMAGE_PROP, NEW_IMAGE_URL)
    # Fix twitter:image
    tw_changed, tw_action = ensure_meta(soup, "name", TW_IMAGE_NAME, NEW_IMAGE_URL)

    if not og_changed and not tw_changed:
        return None

    if apply:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(str(soup))

    return {
        "og_action": og_action,
        "tw_action": tw_action,
    }

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Repo root folder")
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n🔍 Scanning {args.root}  [{mode}]")
    print(f"   Setting og:image → {NEW_IMAGE_URL}\n")
    print("=" * 72)

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    print(f"📄 Found {len(files)} HTML files\n")

    added = fixed = 0
    skipped = 0

    for fp in files:
        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        result = process_file(fp, apply=args.apply)

        if result is None:
            skipped += 1
            continue

        print(f"📄 {rel}")
        if result["og_action"] != "ok":
            print(f"   🖼️  og:image     {result['og_action']}")
            if result["og_action"].startswith("added"):
                added += 1
            else:
                fixed += 1
        if result["tw_action"] != "ok":
            print(f"   🐦  twitter:image {result['tw_action']}")
            if result["tw_action"].startswith("added"):
                added += 1
            else:
                fixed += 1

    print("\n" + "=" * 72)
    print("📊 Summary")
    print("=" * 72)
    print(f"   Files scanned:      {len(files)}")
    print(f"   Tags added:         {added}")
    print(f"   Tags fixed (404):   {fixed}")
    print(f"   Files unchanged:    {skipped}")

    if not args.apply and (added + fixed) > 0:
        print(f"\n💡 This was a DRY RUN. To apply:")
        print(f"     python fix_og_images.py --root {args.root} --apply")
    elif args.apply:
        print(f"\n✅ Changes written.")
        print(f"   Next:")
        print(f"     cd {args.root}")
        print(f"     git diff")
        print(f"     git add . && git commit -m 'Fix og:image and twitter:image tags'")
        print(f"     git push")

if __name__ == "__main__":
    main()