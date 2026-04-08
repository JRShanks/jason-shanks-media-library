#!/usr/bin/env python3
"""
Jason Shanks Media Library — Normalize & Clean

Reads media_links.json and:
  1. Deduplicates entries by normalized URL
  2. Cleans and normalizes titles
  3. Re-categorizes items using keyword rules
  4. Sorts by date (newest first)
  5. Flags items missing key fields

Usage:
  python normalize.py             # normalize in-place
  python normalize.py --check     # report issues without modifying
"""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "media_links.json"

# ---------------------------------------------------------------------------
# URL normalization
# ---------------------------------------------------------------------------

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Canonicalize a URL for deduplication.

    Preserves query strings for sites that need them (YouTube, Apple Podcasts, etc.)
    but strips common tracking parameters.
    """
    parsed = urlparse(url)
    # For YouTube and similar sites, the query string IS the identity
    if parsed.query:
        from urllib.parse import parse_qs, urlencode
        params = parse_qs(parsed.query, keep_blank_values=True)
        # Remove tracking params only
        cleaned_params = {
            k: v for k, v in params.items()
            if k.lower() not in TRACKING_PARAMS
        }
        query = urlencode(cleaned_params, doseq=True)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            clean += f"?{query}"
    else:
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return clean.rstrip("/").lower()


# ---------------------------------------------------------------------------
# Title normalization
# ---------------------------------------------------------------------------

def normalize_title(title: str) -> str:
    """Clean up a title string."""
    # Remove extra whitespace
    title = re.sub(r"\s+", " ", title).strip()
    # Remove trailing " - Source Name" patterns if redundant
    title = re.sub(r"\s*[-|]\s*(YouTube|EWTN|Vimeo)\s*$", "", title, flags=re.IGNORECASE)
    return title


# ---------------------------------------------------------------------------
# Category rules (same as scraper — kept in sync)
# ---------------------------------------------------------------------------

CATEGORY_RULES = {
    "Video": [
        "youtube.com", "youtu.be", "vimeo.com", "ewtn.com/tv",
        "video", "watch", "livestream",
    ],
    "Podcast": [
        "podcast", "episode", "listen",
        "spotify.com", "apple.com/podcast",
        "anchor.fm", "soundcloud.com", "podbean.com",
    ],
    "Radio": [
        "radio", "relevantradio.com", "sirius", "am ", "fm ",
        "radio interview", "on air", "broadcast",
    ],
    "Writing": [
        "article", "news", "opinion", "column", "wrote", "writing",
        "osvnews.com", "ncronline.org", "americamagazine.org",
        "catholicnewsagency.com", "pillar", "blog", "essay",
        "editorial", "op-ed", "publication",
    ],
    "Talk": [
        "conference", "congress", "summit", "keynote", "talk",
        "panel", "symposium", "event", "speech", "address",
    ],
}


def recategorize(item: dict) -> str:
    """Re-derive category from URL + title + description."""
    # Don't override manually verified items that already have a category
    if item.get("verified") and item.get("category"):
        return item["category"]
    combined = f"{item.get('title', '')} {item.get('url', '')} {item.get('description', '')}".lower()
    scores = {}
    for cat, keywords in CATEGORY_RULES.items():
        scores[cat] = sum(1 for kw in keywords if kw in combined)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else item.get("category", "Article")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

REQUIRED_FIELDS = {"title", "url", "category", "source", "date", "description", "tags", "verified"}


def validate_item(item: dict, index: int) -> list[str]:
    """Return a list of issues for a given item."""
    issues = []
    missing = REQUIRED_FIELDS - set(item.keys())
    if missing:
        issues.append(f"Item {index}: missing fields: {missing}")
    if not item.get("title"):
        issues.append(f"Item {index}: empty title")
    if not item.get("url"):
        issues.append(f"Item {index}: empty URL")
    if item.get("date") and not re.match(r"\d{4}-\d{2}-\d{2}", item["date"]):
        issues.append(f"Item {index}: date '{item['date']}' is not YYYY-MM-DD")
    if item.get("category") not in ("Video", "Podcast", "Radio", "Writing", "Talk", "Book"):
        issues.append(f"Item {index}: invalid category '{item.get('category')}'")
    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def normalize(check_only: bool = False):
    if not DATA_FILE.exists():
        print(f"ERROR: {DATA_FILE} not found")
        return 1

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)

    print(f"Loaded {len(items)} items")

    # --- Deduplicate ---
    seen = {}
    unique = []
    dupes = 0
    for item in items:
        norm = normalize_url(item.get("url", ""))
        if norm in seen:
            dupes += 1
            print(f"  DUPE: {item.get('title', '?')[:60]}")
            # Merge: prefer the verified version
            if item.get("verified") and not seen[norm].get("verified"):
                # Replace the existing one
                for i, u in enumerate(unique):
                    if normalize_url(u["url"]) == norm:
                        unique[i] = item
                        break
        else:
            seen[norm] = item
            unique.append(item)

    if dupes:
        print(f"  Removed {dupes} duplicates")

    # --- Normalize each item ---
    all_issues = []
    for i, item in enumerate(unique):
        # Normalize title
        if item.get("title"):
            item["title"] = normalize_title(item["title"])

        # Ensure all required fields exist
        item.setdefault("description", "")
        item.setdefault("tags", [])
        item.setdefault("verified", False)
        item.setdefault("date", "")
        item.setdefault("source", "")
        item.setdefault("category", "Writing")

        # Re-categorize
        item["category"] = recategorize(item)

        # Validate
        issues = validate_item(item, i)
        all_issues.extend(issues)

    # --- Sort by date (newest first), empty dates last ---
    unique.sort(key=lambda x: x.get("date", "") or "0000-00-00", reverse=True)

    # --- Report ---
    if all_issues:
        print(f"\n{len(all_issues)} issues found:")
        for issue in all_issues:
            print(f"  ⚠ {issue}")
    else:
        print("No issues found")

    print(f"\nFinal count: {len(unique)} items")

    if check_only:
        print("CHECK ONLY — no changes written")
        return 1 if all_issues else 0

    # Write back
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(unique, f, indent=2, ensure_ascii=False)
    print(f"Saved normalized data to {DATA_FILE}")
    return 0


if __name__ == "__main__":
    check = "--check" in sys.argv
    sys.exit(normalize(check_only=check))
