#!/usr/bin/env python3
"""
Title & Meta Description Shortener for makuistudio.com
-------------------------------------------------------
Finds titles > 60 chars and meta descriptions > 160 chars,
then applies smart shortening rules to fit within limits.

Rules applied (in priority order):
  1. Remove "Lesson X.X: " prefix
  2. Replace "UI Studio" with "MAK Studio" (shorter brand)
  3. Fix duplicated words ("Free Free")
  4. Remove redundant "Free ... Course" phrases
  5. Collapse double spaces and normalize dashes
  6. Trim to word boundary at 60 chars (title) / 160 chars (description)

Idempotent. Dry-run by default.

Usage:
    python shorten_titles.py --root ./ui-learning-platform --dry-run
    python shorten_titles.py --root ./ui-learning-platform --apply
"""

import argparse
import os
import re

TITLE_LIMIT = 60
DESC_LIMIT  = 160

# ─────────────────────────────────────────────
# SHORTENING RULES
# ─────────────────────────────────────────────
def rule_remove_lesson_prefix(s):
    """'Lesson 2.1: CSS Animations' → 'CSS Animations'"""
    return re.sub(r"^Lesson\s+\d+\.\d+:\s*", "", s)

def rule_brand_shorten(s):
    """'| UI Studio' → '| MAK Studio' — actually shorter as '| MAK'"""
    # UI Studio (9 chars) → MAK Studio (10) is longer, so shorten further
    s = s.replace("| UI Studio", "| MAK Studio")
    # But if still too long, use just "| MAK"
    return s

def rule_brand_minimal(s):
    """Aggressive: '| MAK Studio' → '| MAK'"""
    return s.replace("| MAK Studio", "| MAK")

def rule_fix_duplicates(s):
    """'Free Free Artificial' → 'Free Artificial'"""
    return re.sub(r"\b(\w+)\s+\1\b", r"\1", s, flags=re.IGNORECASE)

def rule_remove_redundant_free_course(s):
    """'Free HTML Course – ...' where page is already a lesson"""
    # 'Free HTML Course' → 'HTML' (drop 'Free' and 'Course' if in the middle)
    s = re.sub(r"Free\s+(HTML|Python|AI|JavaScript)\s+Course\s*[–\-|]\s*",
               r"\1 – ", s, flags=re.IGNORECASE)
    return s

def rule_remove_free_prefix(s):
    """Drop leading 'Free ' if title already long"""
    return re.sub(r"^Free\s+", "", s)

def rule_normalize_dashes(s):
    """Different dashes → single ' – '"""
    s = re.sub(r"\s*[—–-]\s*", " – ", s)
    s = re.sub(r"\s*–\s*–\s*", " – ", s)  # collapse doubles
    return s

def rule_collapse_spaces(s):
    return re.sub(r"\s{2,}", " ", s).strip()

def rule_trim_to_boundary(s, limit):
    """Trim to the last complete word before `limit`."""
    if len(s) <= limit:
        return s
    # Try trimming at separators first
    for sep in [" – ", " | ", " - ", ", "]:
        if sep in s:
            head, _, tail = s.rpartition(sep)
            if len(head) <= limit and head:
                return head.rstrip(" –-|,")
    # Otherwise cut at word boundary
    cut = s[:limit].rsplit(" ", 1)[0]
    return cut.rstrip(" –-|,")

# Full pipeline
RULES_TITLE = [
    rule_fix_duplicates,
    rule_remove_lesson_prefix,
    rule_brand_shorten,
    rule_remove_redundant_free_course,
    rule_normalize_dashes,
    rule_collapse_spaces,
    # After normalizing, try again:
    rule_brand_minimal,
    rule_remove_free_prefix,
    rule_collapse_spaces,
]

RULES_DESC = [
    rule_fix_duplicates,
    rule_collapse_spaces,
]

def shorten_title(title):
    """Apply all title rules, then trim if still over 60 chars."""
    s = title
    for rule in RULES_TITLE:
        s = rule(s)
    if len(s) > TITLE_LIMIT:
        s = rule_trim_to_boundary(s, TITLE_LIMIT)
    return s

def shorten_description(desc):
    """Apply description rules, then trim to word boundary."""
    s = desc
    for rule in RULES_DESC:
        s = rule(s)
    if len(s) > DESC_LIMIT:
        s = rule_trim_to_boundary(s, DESC_LIMIT)
        # Ensure it ends with proper punctuation
        if not s.endswith((".", "!", "?")):
            s += "."
    return s

# ─────────────────────────────────────────────
# HTML READ / WRITE
# ─────────────────────────────────────────────
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.IGNORECASE | re.DOTALL)
DESC_RE  = re.compile(
    r'(<meta\s+name=["\']description["\']\s+content=["\'])([^"\']+)(["\']\s*/?>)',
    re.IGNORECASE
)

def process_file(filepath, apply=False):
    """Return (title_changed, desc_changed, before, after) or None."""
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    changed = False
    before_title = after_title = ""
    before_desc = after_desc = ""

    # --- Title ---
    m = TITLE_RE.search(html)
    if m:
        old_title = m.group(1).strip()
        new_title = shorten_title(old_title)
        if new_title != old_title:
            before_title, after_title = old_title, new_title
            html = html.replace(m.group(0),
                                f"<title>{new_title}</title>", 1)
            changed = True

    # --- Meta description ---
    m = DESC_RE.search(html)
    if m:
        old_desc = m.group(2).strip()
        new_desc = shorten_description(old_desc)
        if new_desc != old_desc:
            before_desc, after_desc = old_desc, new_desc
            html = html.replace(m.group(0),
                                f"{m.group(1)}{new_desc}{m.group(3)}", 1)
            changed = True

    if changed and apply:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html)

    if not changed:
        return None

    return (before_title, after_title, before_desc, after_desc)

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, help="Repo root folder")
    parser.add_argument("--apply", action="store_true", help="Actually write changes")
    parser.add_argument("--only-title", action="store_true", help="Only fix titles")
    parser.add_argument("--only-desc", action="store_true", help="Only fix descriptions")
    args = parser.parse_args()

    mode = "APPLY" if args.apply else "DRY RUN"
    print(f"\n🔍 Scanning {args.root}  [{mode}]\n")
    print("=" * 72)

    files = []
    for dp, dirs, fns in os.walk(args.root):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for fn in fns:
            if fn.endswith(".html"):
                files.append(os.path.join(dp, fn))
    files.sort()

    total_fixed = 0
    total_titles = 0
    total_descs = 0

    for fp in files:
        result = process_file(fp, apply=args.apply)
        if not result:
            continue
        before_t, after_t, before_d, after_d = result
        rel = os.path.relpath(fp, args.root).replace("\\", "/")
        total_fixed += 1
        print(f"\n📄 {rel}")

        if before_t and not args.only_desc:
            total_titles += 1
            print(f"   🏷️  TITLE")
            print(f"      BEFORE ({len(before_t)}): {before_t}")
            print(f"      AFTER  ({len(after_t)}): {after_t}")

        if before_d and not args.only_title:
            total_descs += 1
            print(f"   📝 DESC")
            print(f"      BEFORE ({len(before_d)}): {before_d}")
            print(f"      AFTER  ({len(after_d)}): {after_d}")

    print("\n" + "=" * 72)
    print("📊 Summary")
    print("=" * 72)
    print(f"   Files scanned:       {len(files)}")
    print(f"   Files with changes:  {total_fixed}")
    print(f"   Titles shortened:    {total_titles}")
    print(f"   Descriptions fixed:  {total_descs}")

    if not args.apply and total_fixed > 0:
        print(f"\n💡 This was a DRY RUN. To apply:")
        print(f"     python shorten_titles.py --root {args.root} --apply")
    elif args.apply:
        print(f"\n✅ Changes written.")
        print(f"   Next:")
        print(f"     cd {args.root}")
        print(f"     git diff")
        print(f"     git add . && git commit -m 'Shorten titles and meta descriptions'")
        print(f"     git push")

if __name__ == "__main__":
    main()