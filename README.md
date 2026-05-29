# Jason Shanks Media Library

A self-updating, searchable media library that automatically discovers and publishes Jason Shanks' media appearances — videos, podcasts, articles, and conference talks.

---

## How It Works

```
OpenClaw scheduled jobs
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  scraper.py   │ ──▶ │ normalize.py  │ ──▶ │   build.py   │
  │ YouTube API   │     │ dedupe/clean  │     │ copy to public│
  │ Google CSE    │     │ categorize    │     │ gen sitemap   │
  │ RSS feeds     │     │ validate      │     │ optional commit│
  └──────────────┘     └──────────────┘     └──────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │   Netlify     │
                                              │ auto-deploys  │
                                              │ from GitHub   │
                                              └──────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │  Squarespace  │
                                              │  loader block │
                                              └──────────────┘
```

---

## Folder Structure

```
jason-shanks-media-library/
├── data/
│   └── media_links.json        ← Source-of-truth database
├── scripts/
│   ├── scraper.py              ← Content discovery
│   ├── normalize.py            ← Clean & dedupe
│   ├── validate_data.py        ← JSON/source-data validator
│   ├── preflight.py            ← Cron repo/auth preflight
│   ├── verify_deploy.py        ← Netlify deploy verification
│   └── build.py                ← Build pipeline
├── public/
│   ├── index.html              ← Media library page
│   ├── embed.js                ← Squarespace external renderer
│   ├── embed.css               ← Squarespace external styling
│   └── data/media_links.json   ← Published data
├── netlify.toml                ← Netlify config
├── requirements.txt            ← Python dependencies
└── README.md
```

---

## Setup Guide (Step-by-Step)

### 1. Create the GitHub Repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `jason-shanks-media-library`
3. Set to **Public** (required for free Netlify)
4. Click **Create repository**
5. Push this code:

```bash
cd jason-shanks-media-library
git init
git add -A
git commit -m "Initial commit: media library system"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/jason-shanks-media-library.git
git push -u origin main
```

### 2. Set Up API Keys

You need these for automated content discovery:

#### YouTube Data API v3
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use existing)
3. Enable **YouTube Data API v3**
4. Create an API key under **Credentials**

#### Google Custom Search Engine
1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Create a search engine that searches the entire web
3. Copy the **Search Engine ID**
4. Use the same Google Cloud API key (enable **Custom Search API**)

#### Add Secrets to OpenClaw
The scheduled OpenClaw jobs load `/Users/clive/.openclaw/secrets/tokens.env`.
Add these optional discovery secrets there when API-backed search is desired:

   - `YOUTUBE_API_KEY` — your YouTube API key
   - `GOOGLE_CSE_API_KEY` — your Google API key
   - `GOOGLE_CSE_ID` — your Custom Search Engine ID

GitHub push auth should also be available through `GITHUB_TOKEN`, `GH_TOKEN`, or `/Users/clive/.openclaw/secrets/github-token`.

### 3. Connect Netlify

1. Go to [app.netlify.com](https://app.netlify.com/)
2. Click **Add new site** → **Import an existing project**
3. Connect your GitHub account and select the repo
4. Netlify will auto-detect settings from `netlify.toml`:
   - **Build command:** `python scripts/build.py --skip-scrape`
   - **Publish directory:** `public`
5. Click **Deploy site**
6. (Optional) Set a custom domain: `media.jasonrshanks.org`

### 4. Embed in Squarespace

#### Recommended: external loader Code Block

Paste the contents of `squarespace-loader.html` into the Squarespace Media & Appearances Code Block.

That loader is intentionally tiny and stable. Future media updates happen by updating `data/media_links.json`, running the build, and redeploying Netlify — the Squarespace block does not need to be rebuilt each time.

```html
<div id="jason-media-library"></div>
<link rel="stylesheet" href="https://jason-shanks-media.netlify.app/embed.css">
<script src="https://jason-shanks-media.netlify.app/embed.js" data-jml-container="jason-media-library" data-jml-data-url="https://jason-shanks-media.netlify.app/data/media_links.json" defer></script>
```

#### Alternative: iframe Embed

In Squarespace, add a **Code Block** and paste:

```html
<iframe
  src="https://YOUR-NETLIFY-SITE.netlify.app/?embed=true"
  width="100%"
  height="800"
  frameborder="0"
  style="border:none; border-radius:8px;"
  title="Jason Shanks Media Library"
></iframe>
```

The `?embed=true` parameter hides the header and footer so it blends into your Squarespace page.

#### Alternative: Link to Standalone Page

Simply add a link/button in Squarespace pointing to your Netlify URL.

---

## Adding Media Manually

Edit `data/media_links.json` directly on GitHub. Each entry follows this format:

```json
{
  "title": "Title of the appearance",
  "url": "https://full-url-to-content",
  "category": "Video",
  "source": "YouTube",
  "date": "2025-03-15",
  "description": "Brief description of the content.",
  "tags": ["tag1", "tag2"],
  "verified": true
}
```

**Categories:** `Video`, `Podcast`, `Radio`, `Writing`, `Talk`, `Book`, `Interview`, `Recognition`

After editing, Netlify will auto-redeploy within ~1 minute.

---

## How Automatic Updates Work

1. OpenClaw runs a weekly lightweight watchlist/calendar follow-up and a monthly broad media discovery scan.
2. Each cron run starts with `python3 scripts/preflight.py` to check the local repo, GitHub push authentication, and required build inputs before making edits.
3. The monthly broad scan searches exact-name, outlet-specific, platform, API-backed, and RSS sources.
4. Unverified automated discoveries go to `data/media_candidates.json`; verified public items are added to `data/media_links.json`; private calendar details stay out of public data.
5. The normalizer cleans and deduplicates, `scripts/validate_data.py` validates source JSON, then `scripts/build.py --skip-scrape` regenerates `public/`, `squarespace-embed.html`, and `squarespace-loader.html`.
6. Changes are committed and pushed in one batch; Netlify auto-deploys from GitHub. After deploy, `python3 scripts/verify_deploy.py` can confirm deployed JSON matches local public data. If push/deploy is blocked after new verified items are added, the cron reports the run as blocked/failed rather than successful.

**Note:** Auto-discovered items have `"verified": false` and won't appear on the public page until you set them to `true`. This prevents false positives from appearing publicly.

To manually trigger an update, run the corresponding OpenClaw cron or run the scripts locally after loading the OpenClaw secrets.

---

## Customization

- **Colors:** Edit the shared CSS in `scripts/build.py`, then rebuild
- **Search queries:** Edit the `SEARCH_QUERIES` list in `scripts/scraper.py`
- **RSS feeds:** Add feed URLs to the `RSS_FEEDS` list in `scripts/scraper.py`
- **Schedule:** Change the OpenClaw cron definitions in `/Users/clive/.openclaw/cron/jobs.json`

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Preflight a scheduled run
python3 scripts/preflight.py --skip-push-check

# Run the build pipeline
python scripts/build.py --skip-scrape

# Validate data only
python3 scripts/validate_data.py

# Serve locally
cd public && python -m http.server 8000
# Visit http://localhost:8000
```
