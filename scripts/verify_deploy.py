#!/usr/bin/env python3
"""Verify the deployed Netlify JSON reflects local public media data."""

import argparse
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parent.parent
LOCAL_PUBLIC_DATA = REPO_ROOT / "public" / "data" / "media_links.json"
DEFAULT_URL = "https://jason-shanks-media.netlify.app/data/media_links.json"


def load_local():
    with LOCAL_PUBLIC_DATA.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_remote(url):
    req = Request(url, headers={"User-Agent": "jason-media-library-deploy-verify/1.0"})
    with urlopen(req, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        return json.loads(response.read().decode("utf-8"))


def verified_urls(items):
    return {item.get("url") for item in items if item.get("url") and item.get("verified") is not False}


def main():
    parser = argparse.ArgumentParser(description="Verify deployed media data.")
    parser.add_argument("--url", default=DEFAULT_URL, help="Remote media_links.json URL")
    parser.add_argument(
        "--require-url",
        action="append",
        default=[],
        help="Specific URL that must be present remotely. May be used multiple times.",
    )
    args = parser.parse_args()

    try:
        local = load_local()
        remote = load_remote(args.url)
    except Exception as exc:
        print(f"ERROR: deploy verification failed to load data: {exc}")
        return 1

    local_urls = verified_urls(local)
    remote_urls = verified_urls(remote)
    missing = sorted(local_urls - remote_urls)
    required_missing = sorted(url for url in args.require_url if url not in remote_urls)

    if required_missing:
        print("ERROR: required URL(s) missing from deployed data:")
        for url in required_missing:
            print(f"  - {url}")
        return 1

    if missing:
        print(f"ERROR: deployed data is missing {len(missing)} local verified URL(s)")
        for url in missing[:10]:
            print(f"  - {url}")
        if len(missing) > 10:
            print(f"  ... {len(missing) - 10} more")
        return 1

    print(f"Deploy verification ok: {len(remote_urls)} deployed verified URL(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
