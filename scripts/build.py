#!/usr/bin/env python3
"""
Jason Shanks Media Library — Build Pipeline

Orchestrates the full update cycle:
  1. Run scraper (discover new content)
  2. Run normalizer (dedupe, clean, validate)
  3. Copy data to public/ so Netlify can serve it
  4. (Optionally) commit changes to git

Usage:
  python build.py                # full pipeline
  python build.py --skip-scrape  # normalize + build only
  python build.py --commit       # auto-commit after build
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
DATA_FILE = REPO_ROOT / "data" / "media_links.json"
PUBLIC_DIR = REPO_ROOT / "public"
PUBLIC_DATA = PUBLIC_DIR / "data"


def run(cmd: list[str], label: str) -> bool:
    """Run a subprocess and return True on success."""
    print(f"\n{'='*50}")
    print(f"  {label}")
    print(f"{'='*50}")
    result = subprocess.run(cmd, cwd=REPO_ROOT)
    if result.returncode != 0:
        print(f"  WARNING: {label} exited with code {result.returncode}")
        return False
    return True


def copy_data_to_public():
    """Copy data/ into public/ so the static site can load it."""
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    src = DATA_FILE
    dst = PUBLIC_DATA / "media_links.json"
    shutil.copy2(src, dst)
    print(f"  Copied {src.name} → {dst}")


def generate_sitemap():
    """Generate a minimal sitemap.xml for SEO."""
    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://media.jasonrshanks.org/</loc>
    <lastmod>{datetime.now().strftime('%Y-%m-%d')}</lastmod>
    <changefreq>weekly</changefreq>
  </url>
</urlset>
"""
    path = PUBLIC_DIR / "sitemap.xml"
    path.write_text(sitemap)
    print(f"  Generated {path.name}")


def git_commit():
    """Stage and commit any changes."""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    if not result.stdout.strip():
        print("  No changes to commit")
        return

    subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT)
    msg = f"Auto-update media library — {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(["git", "commit", "-m", msg], cwd=REPO_ROOT)
    print(f"  Committed: {msg}")


def main():
    skip_scrape = "--skip-scrape" in sys.argv
    do_commit = "--commit" in sys.argv

    print(f"Build started at {datetime.now().isoformat()}")
    print(f"Repo root: {REPO_ROOT}")

    # Step 1: Scrape
    if not skip_scrape:
        run([sys.executable, str(SCRIPTS / "scraper.py")], "Step 1: Scraper")
    else:
        print("\nSkipping scraper (--skip-scrape)")

    # Step 2: Normalize
    run([sys.executable, str(SCRIPTS / "normalize.py")], "Step 2: Normalize")

    # Step 3: Copy data to public/
    print(f"\n{'='*50}")
    print("  Step 3: Build static site")
    print(f"{'='*50}")
    copy_data_to_public()
    generate_sitemap()

    # Step 4: Commit
    if do_commit:
        print(f"\n{'='*50}")
        print("  Step 4: Git commit")
        print(f"{'='*50}")
        git_commit()

    print(f"\nBuild complete at {datetime.now().isoformat()}")


if __name__ == "__main__":
    main()
