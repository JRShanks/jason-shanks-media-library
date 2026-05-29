#!/usr/bin/env python3
"""Validate media library JSON files."""

import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent.parent
MEDIA_FILE = REPO_ROOT / "data" / "media_links.json"
WATCHLIST_FILE = REPO_ROOT / "data" / "media_watchlist.json"
CANDIDATES_FILE = REPO_ROOT / "data" / "media_candidates.json"

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MEDIA_CATEGORIES = {"Video", "Podcast", "Radio", "Writing", "Talk", "Book", "Interview", "Recognition"}
WATCHLIST_STATUSES = {"watching", "candidate", "found", "added", "ignored"}
CANDIDATE_STATUSES = {"needs-review", "verified", "rejected", "added"}
REQUIRED_MEDIA_FIELDS = {"title", "url", "category", "source", "date", "description", "tags", "verified"}
REQUIRED_WATCHLIST_FIELDS = {"outlet", "title_hint", "medium", "status", "search_queries", "notes"}
REQUIRED_CANDIDATE_FIELDS = {"title", "url", "source", "discovered_at", "status", "notes"}


def load(path):
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def valid_url(value):
    parsed = urlparse(value or "")
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def check_date(issues, label, value, *, allow_empty=False):
    if not value:
        if not allow_empty:
            issues.append(f"{label}: missing date")
        return
    if not DATE_RE.match(value):
        issues.append(f"{label}: invalid date {value!r}")


def validate_media(items):
    issues = []
    seen_urls = set()
    for idx, item in enumerate(items):
        label = f"media[{idx}]"
        missing = REQUIRED_MEDIA_FIELDS - set(item)
        if missing:
            issues.append(f"{label}: missing fields {sorted(missing)}")
        if not item.get("title"):
            issues.append(f"{label}: empty title")
        url = item.get("url", "")
        if not valid_url(url):
            issues.append(f"{label}: invalid URL")
        if url in seen_urls:
            issues.append(f"{label}: duplicate URL {url}")
        seen_urls.add(url)
        if item.get("category") not in MEDIA_CATEGORIES:
            issues.append(f"{label}: invalid category {item.get('category')!r}")
        if not isinstance(item.get("tags", []), list):
            issues.append(f"{label}: tags must be a list")
        if not isinstance(item.get("verified", False), bool):
            issues.append(f"{label}: verified must be boolean")
        check_date(issues, label, item.get("date"), allow_empty=True)
    return issues


def validate_watchlist(items):
    issues = []
    seen_keys = set()
    for idx, item in enumerate(items):
        label = f"watchlist[{idx}]"
        missing = REQUIRED_WATCHLIST_FIELDS - set(item)
        if missing:
            issues.append(f"{label}: missing fields {sorted(missing)}")
        key = (item.get("outlet", ""), item.get("title_hint", ""), item.get("recording_date") or item.get("event_date") or "")
        if key in seen_keys:
            issues.append(f"{label}: duplicate lead key {key}")
        seen_keys.add(key)
        if item.get("status") not in WATCHLIST_STATUSES:
            issues.append(f"{label}: invalid status {item.get('status')!r}")
        if not isinstance(item.get("search_queries", []), list) or not item.get("search_queries"):
            issues.append(f"{label}: search_queries must be a non-empty list")
        for field in ("recording_date", "event_date", "last_checked_at", "next_check_date"):
            if field in item and item[field] is not None:
                check_date(issues, f"{label}.{field}", item[field], allow_empty=False)
        if item.get("status") in {"found", "added"} and not valid_url(item.get("found_url", "")):
            issues.append(f"{label}: found/added lead must have valid found_url")
        if item.get("status") == "watching" and not item.get("next_check_date"):
            issues.append(f"{label}: watching lead must have next_check_date")
    return issues


def validate_candidates(items, media_urls):
    issues = []
    seen_urls = set()
    for idx, item in enumerate(items):
        label = f"candidate[{idx}]"
        missing = REQUIRED_CANDIDATE_FIELDS - set(item)
        if missing:
            issues.append(f"{label}: missing fields {sorted(missing)}")
        url = item.get("url", "")
        if not valid_url(url):
            issues.append(f"{label}: invalid URL")
        if url in seen_urls:
            issues.append(f"{label}: duplicate candidate URL {url}")
        if url in media_urls:
            issues.append(f"{label}: URL already exists in media_links.json")
        seen_urls.add(url)
        if item.get("status") not in CANDIDATE_STATUSES:
            issues.append(f"{label}: invalid status {item.get('status')!r}")
        check_date(issues, f"{label}.discovered_at", item.get("discovered_at"), allow_empty=False)
    return issues


def main():
    media = load(MEDIA_FILE)
    watchlist = load(WATCHLIST_FILE)
    candidates = load(CANDIDATES_FILE)
    media_urls = {item.get("url", "") for item in media}

    issues = []
    issues.extend(validate_media(media))
    issues.extend(validate_watchlist(watchlist))
    issues.extend(validate_candidates(candidates, media_urls))

    if issues:
        print(f"{len(issues)} validation issue(s):")
        for issue in issues:
            print(f"  - {issue}")
        return 1

    print(
        "Validation ok: "
        f"{len(media)} media item(s), {len(watchlist)} watchlist lead(s), "
        f"{len(candidates)} candidate(s)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
