#!/usr/bin/env python3
"""
Bulk Canonical URL Fixer
-------------------------
Scans all .html files in a folder, finds the canonical link,
and replaces any github.io URL with the correct makuistudio.com URL.

Usage:
    python fix_canonicals.py --root ./ui-learning-platform --old https://mykhurram068-mak.github.io/ui-learning-platform --new https://makuistudio.com
"""

import argparse
import os
import re

# Matches canonical link tags
CANONICAL_REGEX = re.compile(
    r'<link\s+rel=["\']canonical["\']\s+href=["\']([^"\']+)["\']',
    re.IGNORECASE
)

def fix_file(filepath, old_base, new_base):
    """Replace github.io canonical with makuistudio.com."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    changed = False

    def replace_canonical(match):
        nonlocal changed
        url = match.group(1)
        if old_base in url:
            new_url = url.replace(old_base, new_base)
            changed = True
            print(f"   ✅ {os.path.basename(filepath)}")
            print(f"      OLD: {url}")
            print(f"      NEW: {new_url}")
            return match.group(0).replace(url, new_url)
        return match.group(0)

    content = CANONICAL_REGEX.sub(replace_canonical, content)

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    return changed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Repo root folder")
    parser.add_argument("--old", default="https://mykhurram068-mak.github.io/ui-learning-platform",
                        help="Old base URL to replace")
    parser.add_argument("--new", default="https://makuistudio.com",
                        help="New base URL")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, don't write")
    args = parser.parse_args()

    old_base = args.old.rstrip("/")
    new_base = args.new.rstrip("/")

    print(f"🔍 Scanning {args.root} for wrong canonicals...\n")
    print(f"   OLD: {old_base}")
    print(f"   NEW: {new_base}\n")

    fixed = 0
    total = 0

    for dirpath, dirs, files in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for filename in files:
            if not filename.endswith(".html"):
                continue
            total += 1
            filepath = os.path.join(dirpath, filename)

            if args.dry_run:
                # Just report what WOULD change
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                matches = CANONICAL_REGEX.findall(content)
                for url in matches:
                    if old_base in url:
                        print(f"   🔧 WOULD FIX: {filepath}")
                        fixed += 1
            else:
                if fix_file(filepath, old_base, new_base):
                    fixed += 1

    print(f"\n{'🔍 DRY RUN — no files changed.' if args.dry_run else '✅ Done.'}")
    print(f"   Files scanned:  {total}")
    print(f"   Files fixed:    {fixed}")

    if not args.dry_run and fixed > 0:
        print("\n📋 Next steps:")
        print("1. Run 'git diff' to review the changes")
        print("2. Run 'git add . && git commit -m \"Fix canonical URLs\"'")
        print("3. Run 'git push'")
        print("4. Resubmit sitemap in Google Search Console")

if __name__ == "__main__":
    main()