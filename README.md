# Jason Shanks Media Library

A self-updating, searchable media library that automatically discovers and publishes Jason Shanks' media appearances — videos, podcasts, articles, and conference talks.

---

## How It Works

```
Weekly (GitHub Actions)
  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  scraper.py   │ ──▶ │ normalize.py  │ ──▶ │   build.py   │
  │ YouTube API   │     │ dedupe/clean  │     │ copy to public│
  │ Google CSE    │     │ categorize    │     │ gen sitemap   │
  │ RSS feeds     │     │ validate      │     │ git commit    │
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
                                              │  iframe embed │
                                              └──────────────┘
```

---

## Folder Structure

```
jason-shanks-media-library/
├── .github/workflows/
│   └── update-media.yml        ← Weekly automation
├── data/
│   └── media_links.json        ← Source-of-truth database
├── scripts/
│   ├── scraper.py              ← Content discovery
│   ├── normalize.py            ← Clean & dedupe
│   └── build.py                ← Build pipeline
├── public/
│   ├── index.html              ← Media library page
│   ├── app.js                  ← Search/filter logic
│   └── styles.css              ← Styling
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

#### Add Secrets to GitHub
1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   - `YOUTUBE_API_KEY` — your YouTube API key
   - `GOOGLE_CSE_API_KEY` — your Google API key
   - `GOOGLE_CSE_ID` — your Custom Search Engine ID

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

#### Option A: iframe Embed (Recommended)

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

#### Option B: Link to Standalone Page

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

**Categories:** `Video`, `Podcast`, `Article`, `Talk`

After editing, Netlify will auto-redeploy within ~1 minute.

---

## How Automatic Updates Work

1. **Every Monday at 6 AM UTC**, GitHub Actions runs the workflow
2. The scraper searches YouTube, Google, and RSS feeds for new content
3. New items are added to `media_links.json` with `"verified": false`
4. The normalizer cleans and deduplicates
5. Changes are committed and pushed
6. Netlify auto-deploys the updated site

**Note:** Auto-discovered items have `"verified": false` and won't appear on the public page until you set them to `true`. This prevents false positives from appearing publicly.

To manually trigger an update: go to **Actions** → **Update Media Library** → **Run workflow**.

---

## Customization

- **Colors:** Edit CSS variables at the top of `public/styles.css`
- **Search queries:** Edit the `SEARCH_QUERIES` list in `scripts/scraper.py`
- **RSS feeds:** Add feed URLs to the `RSS_FEEDS` list in `scripts/scraper.py`
- **Schedule:** Change the cron in `.github/workflows/update-media.yml`

---

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the build pipeline
python scripts/build.py --skip-scrape

# Serve locally
cd public && python -m http.server 8000
# Visit http://localhost:8000
```
