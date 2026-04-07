#!/usr/bin/env python3
"""
Jason Shanks Media Library — Content Discovery Scraper

Searches multiple sources for media appearances by Jason Shanks,
then merges new finds into the master media_links.json database.

Requires environment variables for API access:
  YOUTUBE_API_KEY        — YouTube Data API v3 key
  GOOGLE_CSE_ID          — Google Custom Search Engine ID
  GOOGLE_CSE_API_KEY     — Google Custom Search API key

Usage:
  python scraper.py                  # full run (APIs + RSS)
  python scraper.py --rss-only       # skip API calls, RSS only
  python scraper.py --dry-run        # print new items, don't write
"""

import json
import os
import re
import sys
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = REPO_ROOT / "data" / "media_links.json"

SEARCH_QUERIES = [
    "Jason Shanks",
    "Jason Shanks Eucharistic Congress",
    "Jason Shanks interview",
    "Jason Shanks podcast",
    "Jason Shanks EWTN",
    "Jason Shanks Catholic",
    "Jason Shanks Relevant Radio",
    "Jason Shanks OSV",
    "Jason Shanks speaker",
    "Jason Shanks media",
]

RSS_FEEDS = [
    # Add real RSS feed URLs here as they are discovered
    # ("Source Name", "https://example.com/feed.xml"),
]

# Category detection keywords
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

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("scraper")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_existing() -> list[dict]:
    """Load the current media database."""
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def save_database(items: list[dict]) -> None:
    """Write the media database back to disk."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2, ensure_ascii=False)
    log.info("Saved %d items to %s", len(items), DATA_FILE)


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "ref", "source", "mc_cid", "mc_eid",
}


def normalize_url(url: str) -> str:
    """Strip tracking params and normalize the URL for dedup.

    Preserves meaningful query strings (e.g. YouTube ?v=, Apple Podcasts ?i=).
    """
    from urllib.parse import parse_qs, urlencode
    parsed = urlparse(url)
    if parsed.query:
        params = parse_qs(parsed.query, keep_blank_values=True)
        cleaned = {k: v for k, v in params.items() if k.lower() not in TRACKING_PARAMS}
        query = urlencode(cleaned, doseq=True)
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if query:
            clean += f"?{query}"
    else:
        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return clean.rstrip("/").lower()


def existing_urls(items: list[dict]) -> set:
    """Build a set of normalized URLs already in the database."""
    return {normalize_url(item["url"]) for item in items}


def guess_category(title: str, url: str, description: str = "") -> str:
    """Automatically categorize based on URL and text content."""
    combined = f"{title} {url} {description}".lower()
    scores = {}
    for cat, keywords in CATEGORY_RULES.items():
        scores[cat] = sum(1 for kw in keywords if kw in combined)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Writing"


def guess_source(url: str) -> str:
    """Extract a human-readable source name from the URL."""
    domain = urlparse(url).netloc.lower().replace("www.", "")
    source_map = {
        "youtube.com": "YouTube",
        "youtu.be": "YouTube",
        "ewtn.com": "EWTN",
        "relevantradio.com": "Relevant Radio",
        "osvnews.com": "OSV News",
        "ncronline.org": "National Catholic Reporter",
        "americamagazine.org": "America Magazine",
        "catholicnewsagency.com": "Catholic News Agency",
        "pillarcatholic.com": "The Pillar",
        "spotify.com": "Spotify",
        "apple.com": "Apple Podcasts",
        "vimeo.com": "Vimeo",
    }
    for pattern, name in source_map.items():
        if pattern in domain:
            return name
    # Fallback: use the domain itself
    return domain.split(".")[0].title()


def make_item(
    title: str,
    url: str,
    description: str = "",
    date: str = "",
    tags: list[str] | None = None,
    verified: bool = False,
) -> dict:
    """Create a properly structured media item."""
    return {
        "title": title.strip(),
        "url": url.strip(),
        "category": guess_category(title, url, description),
        "source": guess_source(url),
        "date": date or datetime.now().strftime("%Y-%m-%d"),
        "description": description.strip(),
        "tags": tags or [],
        "verified": verified,
    }

# ---------------------------------------------------------------------------
# YouTube Data API
# ---------------------------------------------------------------------------

def search_youtube(queries: list[str], max_per_query: int = 10) -> list[dict]:
    """Search YouTube for Jason Shanks content via the Data API v3."""
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    if not api_key:
        log.warning("YOUTUBE_API_KEY not set — skipping YouTube search")
        return []

    try:
        import requests
    except ImportError:
        log.error("requests library not installed — pip install requests")
        return []

    results = []
    seen_ids = set()
    endpoint = "https://www.googleapis.com/youtube/v3/search"

    for query in queries:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": max_per_query,
            "order": "date",
            "key": api_key,
        }
        try:
            resp = requests.get(endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error("YouTube API error for '%s': %s", query, e)
            continue

        for item in data.get("items", []):
            vid_id = item["id"].get("videoId", "")
            if not vid_id or vid_id in seen_ids:
                continue
            seen_ids.add(vid_id)
            snippet = item["snippet"]
            results.append(make_item(
                title=snippet.get("title", ""),
                url=f"https://www.youtube.com/watch?v={vid_id}",
                description=snippet.get("description", "")[:300],
                date=snippet.get("publishedAt", "")[:10],
                tags=["YouTube"],
                verified=False,
            ))
        log.info("YouTube: found %d results for '%s'", len(data.get("items", [])), query)

    return results

# ---------------------------------------------------------------------------
# Google Custom Search API
# ---------------------------------------------------------------------------

def search_google_cse(queries: list[str], max_per_query: int = 10) -> list[dict]:
    """Search the web via Google Custom Search Engine."""
    api_key = os.environ.get("GOOGLE_CSE_API_KEY", "")
    cse_id = os.environ.get("GOOGLE_CSE_ID", "")
    if not api_key or not cse_id:
        log.warning("Google CSE credentials not set — skipping web search")
        return []

    try:
        import requests
    except ImportError:
        log.error("requests library not installed")
        return []

    results = []
    seen_urls = set()
    endpoint = "https://www.googleapis.com/customsearch/v1"

    for query in queries:
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": query,
            "num": min(max_per_query, 10),
        }
        try:
            resp = requests.get(endpoint, params=params, timeout=15)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            log.error("Google CSE error for '%s': %s", query, e)
            continue

        for item in data.get("items", []):
            url = item.get("link", "")
            norm = normalize_url(url)
            if not url or norm in seen_urls:
                continue
            seen_urls.add(norm)
            results.append(make_item(
                title=item.get("title", ""),
                url=url,
                description=item.get("snippet", "")[:300],
                tags=["web-search"],
                verified=False,
            ))
        log.info("Google CSE: found %d results for '%s'", len(data.get("items", [])), query)

    return results

# ---------------------------------------------------------------------------
# RSS Feeds
# ---------------------------------------------------------------------------

def search_rss_feeds() -> list[dict]:
    """Parse configured RSS feeds for mentions of Jason Shanks."""
    if not RSS_FEEDS:
        log.info("No RSS feeds configured — skipping")
        return []

    try:
        import feedparser
    except ImportError:
        log.warning("feedparser not installed — pip install feedparser — skipping RSS")
        return []

    results = []
    name_pattern = re.compile(r"jason\s+shanks", re.IGNORECASE)

    for source_name, feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
        except Exception as e:
            log.error("RSS error for %s: %s", source_name, e)
            continue

        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            if name_pattern.search(title) or name_pattern.search(summary):
                pub_date = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        pub_date = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d")
                    except Exception:
                        pass
                results.append(make_item(
                    title=title,
                    url=link,
                    description=summary[:300],
                    date=pub_date,
                    tags=[source_name, "RSS"],
                    verified=False,
                ))
        log.info("RSS [%s]: checked %d entries", source_name, len(feed.entries))

    return results

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def merge_new_items(existing: list[dict], new_items: list[dict]) -> tuple[list[dict], int]:
    """Merge new items into the existing database, deduplicating by URL."""
    known = existing_urls(existing)
    added = 0
    for item in new_items:
        norm = normalize_url(item["url"])
        if norm not in known:
            known.add(norm)
            existing.append(item)
            added += 1
            log.info("  + NEW: %s", item["title"][:80])
    return existing, added


def main():
    dry_run = "--dry-run" in sys.argv
    rss_only = "--rss-only" in sys.argv

    log.info("=" * 60)
    log.info("Jason Shanks Media Scraper — %s", datetime.now().isoformat())
    log.info("=" * 60)

    existing = load_existing()
    log.info("Loaded %d existing items", len(existing))

    all_new = []

    if not rss_only:
        # YouTube
        log.info("--- YouTube Search ---")
        yt_results = search_youtube(SEARCH_QUERIES[:5])
        all_new.extend(yt_results)

        # Google Custom Search
        log.info("--- Google Custom Search ---")
        gcs_results = search_google_cse(SEARCH_QUERIES)
        all_new.extend(gcs_results)

    # RSS
    log.info("--- RSS Feeds ---")
    rss_results = search_rss_feeds()
    all_new.extend(rss_results)

    log.info("Total new candidates: %d", len(all_new))

    merged, added_count = merge_new_items(existing, all_new)

    if dry_run:
        log.info("DRY RUN — would have added %d new items", added_count)
    else:
        if added_count > 0:
            save_database(merged)
            log.info("Added %d new items (total: %d)", added_count, len(merged))
        else:
            log.info("No new items found")

    log.info("Done.")
    return added_count


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
