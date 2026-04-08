#!/usr/bin/env python3
"""
Jason Shanks Media Library — Static Site Generator

Reads data/media_links.json and generates public/index.html with all media
entries pre-rendered as static HTML. JavaScript enhances with search/filter
but is NOT required for core content to be visible.

Also generates squarespace-embed.html — a self-contained Code Block with
all entries baked in.

Usage:
  python build.py                # full pipeline
  python build.py --skip-scrape  # normalize + build only
  python build.py --commit       # auto-commit after build
"""

import html as html_mod
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

CATEGORIES = ["Video", "Podcast", "Radio", "Writing", "Talk", "Book"]
FEATURED_COUNT = 6


def esc(text):
    """HTML-escape a string."""
    return html_mod.escape(str(text or ""), quote=True)


def format_date(date_str):
    """Format YYYY-MM-DD to readable date."""
    if not date_str:
        return ""
    try:
        d = datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%b %d, %Y")
    except ValueError:
        return date_str


def load_items():
    """Load and sort verified media items."""
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        items = json.load(f)
    items = [i for i in items if i.get("verified") is not False]
    items.sort(key=lambda x: x.get("date", ""), reverse=True)
    return items


def render_card_html(item, extra_class=""):
    """Render a single media card as static HTML."""
    tags_html = ""
    raw_tags = [t for t in (item.get("tags") or [])
                if t and t not in ("web-search", "YouTube", "RSS")]
    for tag in raw_tags[:3]:
        tags_html += '<span class="jml-tag">{}</span>'.format(esc(tag))

    desc_html = ""
    if item.get("description"):
        desc_html = '<div class="jml-desc">{}</div>'.format(esc(item["description"]))

    date_html = ""
    if item.get("date"):
        date_html = '<span class="jml-date">{}</span>'.format(format_date(item["date"]))

    tags_wrap = '<div class="jml-tags">{}</div>'.format(tags_html) if tags_html else ""

    cat = esc(item.get("category", ""))
    cls = "{} {}".format("jml-card", extra_class).strip()

    return '''<a href="{url}" target="_blank" rel="noopener noreferrer" class="{cls}" data-category="{cat}">
  <div class="jml-card-top">
    <span class="jml-badge jml-badge-{cat}">{cat_text}</span>
    <span class="jml-source">{source}</span>
  </div>
  <div class="jml-title">{title}</div>
  {desc}
  <div class="jml-meta">{date}{tags}</div>
</a>'''.format(
        url=esc(item.get("url", "")),
        cls=cls,
        cat=cat,
        cat_text=cat,
        source=esc(item.get("source", "")),
        title=esc(item.get("title", "")),
        desc=desc_html,
        date=date_html,
        tags=tags_wrap,
    )


def pick_featured(items):
    """Select featured items: explicit featured flag first, then variety across categories."""
    featured = []
    seen_cats = set()
    # First: items explicitly marked as featured
    for item in items:
        if item.get("featured") and len(featured) < FEATURED_COUNT:
            featured.append(item)
            seen_cats.add(item.get("category", ""))
    # Then: fill remaining slots with category variety
    for item in items:
        cat = item.get("category", "")
        if item not in featured and cat not in seen_cats and len(featured) < FEATURED_COUNT:
            featured.append(item)
            seen_cats.add(cat)
    for item in items:
        if item not in featured and len(featured) < FEATURED_COUNT:
            featured.append(item)
    return featured


def count_by_category(items):
    """Count items per category."""
    counts = {}
    for item in items:
        cat = item.get("category", "Unknown")
        counts[cat] = counts.get(cat, 0) + 1
    return counts


# ===========================================================================
# CSS (shared between standalone page and Squarespace embed)
# ===========================================================================
SHARED_CSS = """
  /* ---------- Section Title ---------- */
  .jml-section-title { font-size: 1rem; font-weight: 600; color: #888;
    text-transform: uppercase; letter-spacing: .06em; margin-bottom: .6rem; }

  /* ---------- Featured Grid ---------- */
  .jml-featured-grid { display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: .75rem; margin-bottom: 1.5rem; }
  .jml-featured-grid .jml-card { border-left: 3px solid #1e3a5f; }

  /* ---------- Search & Filter Controls ---------- */
  .jml-controls { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: .5rem; align-items: center; }
  .jml-search { flex: 1 1 240px; padding: .55rem .9rem; font-size: .95rem; font-family: inherit;
    border: 1px solid #d4d4d4; border-radius: 6px; background: #fff; }
  .jml-search:focus { outline: none; border-color: #1e3a5f; box-shadow: 0 0 0 3px rgba(30,58,95,.1); }
  .jml-filters { display: flex; gap: .35rem; flex-wrap: wrap; }
  .jml-fbtn { padding: .4rem .8rem; font-size: .82rem; font-family: inherit; font-weight: 500;
    border: 1px solid #d4d4d4; border-radius: 20px; background: #fff; color: #555;
    cursor: pointer; transition: all .15s; }
  .jml-fbtn:hover { border-color: #333; color: #333; }
  .jml-fbtn.active { background: #1a1a2e; color: #fff; border-color: #1a1a2e; }
  .jml-fcount { font-weight: 400; opacity: .7; }
  .jml-stats { font-size: .8rem; color: #999; margin-bottom: .8rem; }

  /* ---------- Card Grid (2 columns on desktop) ---------- */
  .jml-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: .75rem; }

  /* ---------- Card Styles ---------- */
  .jml-card { display: flex; flex-direction: column; padding: 1rem 1.1rem;
    border: 1px solid #e8e8e8; border-radius: 6px;
    text-decoration: none !important; color: inherit !important; background: #fff;
    transition: box-shadow .2s, transform .15s; }
  .jml-card:hover { box-shadow: 0 3px 10px rgba(0,0,0,.08); transform: translateY(-1px); }
  .jml-card[hidden] { display: none; }
  .jml-card-top { display: flex; align-items: center; gap: .5rem; margin-bottom: .3rem; }
  .jml-badge { display: inline-block; font-size: .65rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: .04em; padding: .12rem .5rem; border-radius: 20px; color: #fff; }
  .jml-badge-Video { background: #dc2626; }
  .jml-badge-Podcast { background: #7c3aed; }
  .jml-badge-Radio { background: #2563eb; }
  .jml-badge-Writing { background: #059669; }
  .jml-badge-Talk { background: #d97706; }
  .jml-badge-Book { background: #92400e; }
  .jml-source { font-size: .78rem; color: #999; }
  .jml-title { font-size: 1rem; font-weight: 600; line-height: 1.35; margin-bottom: .2rem; }
  .jml-desc { font-size: .85rem; color: #777; margin-bottom: .4rem;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
  .jml-meta { display: flex; gap: .6rem; align-items: center; flex-wrap: wrap; margin-top: auto; }
  .jml-date { font-size: .78rem; color: #999; }
  .jml-tags { display: flex; gap: .3rem; flex-wrap: wrap; }
  .jml-tag { font-size: .7rem; padding: .08rem .45rem; background: #eef2ff; color: #3730a3; border-radius: 20px; }
  .jml-empty { text-align: center; padding: 2rem 1rem; color: #aaa; }

  /* ---------- CTA Banner ---------- */
  .jml-cta { display: flex; align-items: center; justify-content: space-between;
    padding: 1rem 1.25rem; margin-bottom: 1.2rem;
    background: linear-gradient(135deg, #1a1a2e 0%, #1e3a5f 100%);
    border-radius: 8px; color: #fff; text-decoration: none !important; gap: 1rem;
    transition: transform .15s, box-shadow .2s; }
  .jml-cta:hover { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(30,58,95,.3); }
  .jml-cta-text { flex: 1; }
  .jml-cta-title { font-size: 1.05rem; font-weight: 700; margin-bottom: .15rem; color: #fff !important; }
  .jml-cta-sub { font-size: .82rem; opacity: .85; color: #e0e0e0 !important; }
  .jml-cta-btn { padding: .5rem 1.2rem; background: #fff; color: #1a1a2e;
    font-weight: 600; font-size: .85rem; border-radius: 6px; white-space: nowrap;
    text-decoration: none !important; }

  /* ---------- Section Divider ---------- */
  .jml-divider { border: none; border-top: 1px solid #e5e7eb; margin: 1.5rem 0 1rem; }

  /* ---------- Mobile (single column, stacked controls) ---------- */
  @media (max-width: 680px) {
    .jml-controls { flex-direction: column; }
    .jml-search { width: 100%; }
    .jml-title { font-size: .92rem; }
    .jml-featured-grid { grid-template-columns: 1fr; }
    .jml-grid { grid-template-columns: 1fr; }
    .jml-cta { flex-direction: column; text-align: center; }
  }
"""

# ===========================================================================
# JS (shared — progressive enhancement for search/filter)
# ===========================================================================
SHARED_JS = """
(function() {
  'use strict';
  var grid = document.getElementById('jml-grid');
  var search = document.getElementById('jml-search');
  var filtersEl = document.getElementById('jml-filters');
  var statsEl = document.getElementById('jml-stats');
  var cards = grid ? Array.prototype.slice.call(grid.querySelectorAll('.jml-card')) : [];
  var activeCat = 'All', query = '', total = cards.length;

  function norm(s) { return (s || '').toLowerCase(); }

  function apply() {
    var shown = 0, q = norm(query);
    cards.forEach(function(c) {
      var catOk = activeCat === 'All' || c.getAttribute('data-category') === activeCat;
      var txtOk = !q || norm(c.textContent).indexOf(q) !== -1;
      c.hidden = !(catOk && txtOk);
      if (catOk && txtOk) shown++;
    });
    statsEl.textContent = 'Showing ' + shown + ' of ' + total + ' appearances';
  }

  if (filtersEl) {
    filtersEl.addEventListener('click', function(e) {
      var btn = e.target.closest('.jml-fbtn');
      if (!btn) return;
      activeCat = btn.getAttribute('data-cat');
      var bs = filtersEl.querySelectorAll('.jml-fbtn');
      for (var i = 0; i < bs.length; i++) bs[i].classList.remove('active');
      btn.classList.add('active');
      apply();
    });
  }

  if (search) {
    var t;
    search.addEventListener('input', function() {
      clearTimeout(t);
      t = setTimeout(function() { query = search.value.trim(); apply(); }, 200);
    });
  }
})();
"""


def build_filter_buttons(counts):
    """Build HTML for category filter buttons."""
    html = '<button class="jml-fbtn active" data-cat="All">All</button>\n'
    for cat in CATEGORIES:
        count = counts.get(cat, 0)
        if count > 0:
            html += '      <button class="jml-fbtn" data-cat="{cat}">{cat} <span class="jml-fcount">({count})</span></button>\n'.format(
                cat=cat, count=count
            )
    return html


# CTA Banner for the book
CTA_BANNER = """<a href="https://www.amazon.com/dp/B09J36FDP5" target="_blank" rel="noopener noreferrer" class="jml-cta">
      <div class="jml-cta-text">
        <div class="jml-cta-title">The Foundations and Pillars of Evangelization</div>
        <div class="jml-cta-sub">By Jason Shanks &mdash; A foundational work defining evangelization through the documents of Vatican II</div>
      </div>
      <span class="jml-cta-btn">Buy the Book</span>
    </a>"""


# ===========================================================================
# Generate standalone index.html (Netlify)
# ===========================================================================
def generate_index_html(items):
    featured = pick_featured(items)
    counts = count_by_category(items)
    total = len(items)
    now = datetime.now().strftime("%Y-%m-%d")
    year = datetime.now().year

    featured_cards = "\n".join(render_card_html(item, "jml-featured") for item in featured)
    all_cards = "\n".join(render_card_html(item) for item in items)
    filter_buttons = build_filter_buttons(counts)

    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Media &amp; Appearances — Jason Shanks</title>
  <meta name="description" content="A living library of {total} media appearances by Jason Shanks — videos, podcasts, radio interviews, articles, and conference talks.">
  <meta property="og:title" content="Jason Shanks — Media &amp; Appearances">
  <meta property="og:description" content="{total} videos, podcasts, articles, and talks by and featuring Jason Shanks.">
  <meta property="og:type" content="website">
  <link rel="canonical" href="https://jason-shanks-media.netlify.app/">
  <style>
    :root {{
      --c-bg: #fafafa; --c-surface: #fff; --c-text: #1a1a2e;
      --c-muted: #6b7280; --c-accent: #1e3a5f;
      --c-border: #e5e7eb;
    }}
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
        "Helvetica Neue", Arial, sans-serif;
      background: var(--c-bg); color: var(--c-text); line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }}
    .jml-header {{
      background: var(--c-accent); color: #fff;
      padding: 2rem 1.5rem; text-align: center;
    }}
    .jml-header h1 {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -.02em; margin-bottom: .25rem; }}
    .jml-header p {{ font-size: .95rem; opacity: .85; }}
    .jml-wrap {{ max-width: 900px; margin: 1.5rem auto 0; padding: 0 1.5rem; }}
    .jml-footer {{
      text-align: center; padding: 2rem 1rem; font-size: .8rem;
      color: var(--c-muted); border-top: 1px solid var(--c-border); margin-top: 2rem;
    }}
    body.jml-embed .jml-header, body.jml-embed .jml-footer {{ display: none; }}
    body.jml-embed {{ background: transparent; }}
{shared_css}
  </style>
</head>
<body>

  <header class="jml-header">
    <h1>Media &amp; Appearances</h1>
    <p>Videos, podcasts, articles, and talks featuring Jason Shanks</p>
  </header>

  <div class="jml-wrap">

    {cta_banner}

    <div class="jml-controls">
      <input type="search" class="jml-search" id="jml-search"
             placeholder="Search {total} appearances…"
             aria-label="Search media library">
      <div class="jml-filters" id="jml-filters" role="group" aria-label="Filter by category">
      {filter_buttons}
      </div>
    </div>
    <div class="jml-stats" id="jml-stats" aria-live="polite">Showing {total} of {total} appearances</div>

    <h2 class="jml-section-title">Featured</h2>
    <div class="jml-featured-grid">
{featured_cards}
    </div>

    <hr class="jml-divider">

    <h2 class="jml-section-title">Browse All</h2>
    <main class="jml-grid" id="jml-grid">
{all_cards}
    </main>

  </div>

  <footer class="jml-footer">
    <p>&copy; {year} Jason Shanks &middot; Last updated {now}</p>
  </footer>

  <script>
{shared_js}
  </script>

</body>
</html>""".format(
        total=total,
        shared_css=SHARED_CSS,
        cta_banner=CTA_BANNER,
        featured_cards=featured_cards,
        filter_buttons=filter_buttons,
        all_cards=all_cards,
        year=year,
        now=now,
        shared_js=SHARED_JS,
    )


# ===========================================================================
# Generate Squarespace embed
# ===========================================================================
def generate_squarespace_embed(items):
    featured = pick_featured(items)
    counts = count_by_category(items)
    total = len(items)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    featured_cards = "\n".join(render_card_html(item, "jml-featured") for item in featured)
    all_cards = "\n".join(render_card_html(item) for item in items)
    filter_buttons = build_filter_buttons(counts)

    return """<!--
  JASON SHANKS MEDIA LIBRARY — Squarespace Code Block
  {total} pre-rendered media appearances. No external fetch required.
  Content is visible even if JavaScript is disabled.
  Generated: {now}
-->

<style>
  /* Break out of Squarespace Fluid Engine narrow Code Block */
  .jml-wrap {{
    font-family: inherit; color: inherit; box-sizing: border-box;
    width: 100vw;
    max-width: 1100px;
    margin-left: calc(-50vw + 50%);
    margin-right: calc(-50vw + 50%);
    padding: 0 2rem;
  }}
  /* Also override Squarespace parent constraints */
  .sqs-block-code .sqs-block-content,
  .fe-block .sqs-block-content {{
    max-width: 100% !important; width: 100% !important; overflow: visible !important;
  }}
{shared_css}
</style>

<div class="jml-wrap">

  {cta_banner}

  <div class="jml-controls">
    <input type="search" class="jml-search" id="jml-search" placeholder="Search {total} appearances…">
    <div class="jml-filters" id="jml-filters">
      {filter_buttons}
    </div>
  </div>
  <div class="jml-stats" id="jml-stats">Showing {total} of {total} appearances</div>

  <h2 class="jml-section-title">Featured</h2>
  <div class="jml-featured-grid">
{featured_cards}
  </div>

  <hr class="jml-divider">

  <h2 class="jml-section-title">Browse All</h2>
  <div class="jml-grid" id="jml-grid">
{all_cards}
  </div>

</div>

<script>
{shared_js}
</script>""".format(
        total=total,
        now=now,
        shared_css=SHARED_CSS,
        cta_banner=CTA_BANNER,
        featured_cards=featured_cards,
        filter_buttons=filter_buttons,
        all_cards=all_cards,
        shared_js=SHARED_JS,
    )


# ===========================================================================
# Pipeline
# ===========================================================================
def run(cmd, label):
    print("\n" + "=" * 50)
    print("  " + label)
    print("=" * 50)
    result = subprocess.run(cmd, cwd=str(REPO_ROOT))
    if result.returncode != 0:
        print("  WARNING: {} exited with code {}".format(label, result.returncode))
        return False
    return True


def copy_data_to_public():
    PUBLIC_DATA.mkdir(parents=True, exist_ok=True)
    src = DATA_FILE
    dst = PUBLIC_DATA / "media_links.json"
    shutil.copy2(str(src), str(dst))
    print("  Copied {} -> {}".format(src.name, dst))


def generate_sitemap():
    sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://jason-shanks-media.netlify.app/</loc>
    <lastmod>{}</lastmod>
    <changefreq>weekly</changefreq>
  </url>
</urlset>
""".format(datetime.now().strftime("%Y-%m-%d"))
    path = PUBLIC_DIR / "sitemap.xml"
    path.write_text(sitemap)
    print("  Generated " + path.name)


def git_commit():
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True, text=True, cwd=str(REPO_ROOT),
    )
    if not result.stdout.strip():
        print("  No changes to commit")
        return
    subprocess.run(["git", "add", "-A"], cwd=str(REPO_ROOT))
    msg = "Auto-update media library — {}".format(datetime.now().strftime("%Y-%m-%d %H:%M"))
    subprocess.run(["git", "commit", "-m", msg], cwd=str(REPO_ROOT))
    print("  Committed: " + msg)


def main():
    skip_scrape = "--skip-scrape" in sys.argv
    do_commit = "--commit" in sys.argv

    print("Build started at " + datetime.now().isoformat())
    print("Repo root: " + str(REPO_ROOT))

    # Step 1: Scrape
    if not skip_scrape:
        run([sys.executable, str(SCRIPTS / "scraper.py")], "Step 1: Scraper")
    else:
        print("\nSkipping scraper (--skip-scrape)")

    # Step 2: Normalize
    normalizer = SCRIPTS / "normalize.py"
    if normalizer.exists():
        run([sys.executable, str(normalizer)], "Step 2: Normalize")
    else:
        print("\nSkipping normalizer (not found)")

    # Step 3: Build static site
    print("\n" + "=" * 50)
    print("  Step 3: Build static site (pre-render HTML)")
    print("=" * 50)

    items = load_items()
    print("  Loaded {} verified items".format(len(items)))

    # Generate pre-rendered index.html
    index_html = generate_index_html(items)
    index_path = PUBLIC_DIR / "index.html"
    index_path.write_text(index_html, encoding="utf-8")
    print("  Generated {} ({:,} bytes)".format(index_path.name, len(index_html)))

    # Generate Squarespace embed
    embed_html = generate_squarespace_embed(items)
    embed_path = REPO_ROOT / "squarespace-embed.html"
    embed_path.write_text(embed_html, encoding="utf-8")
    print("  Generated {} ({:,} bytes)".format(embed_path.name, len(embed_html)))

    copy_data_to_public()
    generate_sitemap()

    print("\n  Total items: {}".format(len(items)))
    for cat in CATEGORIES:
        c = sum(1 for i in items if i.get("category") == cat)
        if c:
            print("    {}: {}".format(cat, c))

    # Step 4: Commit
    if do_commit:
        print("\n" + "=" * 50)
        print("  Step 4: Git commit")
        print("=" * 50)
        git_commit()

    print("\nBuild complete at " + datetime.now().isoformat())


if __name__ == "__main__":
    main()
