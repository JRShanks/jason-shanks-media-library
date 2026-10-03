# Jason Shanks Media Page — Clive Update Guide

Clive/Codex owns media maintenance. Start with [automation/RUNBOOK.md](automation/RUNBOOK.md) for shared lease, approved automatic publication, access boundaries, source coverage and repeat-run rules. Jason authorized automatic publication of verified additions on October 3, 2026.

This runbook explains how to research, add, feature, publish, and verify items on Jason Shanks's **Media & Appearances** page.

## System at a glance

- **Local repository:** `/Users/clive/Desktop/jason-shanks-media-library`
- **GitHub repository:** `JRShanks/jason-shanks-media-library`
- **Git branch:** `main`
- **Live Netlify site:** <https://jason-shanks-media.netlify.app/>
- **Live published data:** <https://jason-shanks-media.netlify.app/data/media_links.json>
- **Authoritative source data:** `data/media_links.json`
- **Netlify publish directory:** `public`
- **Squarespace integration:** `squarespace-loader.html` loads the Netlify-hosted data and assets
- **Deployment trigger:** a successful push to GitHub `main`; Netlify deploys automatically

The normal flow is:

```text
Research and verify
        ↓
Edit data/media_links.json
        ↓
Validate and build
        ↓
Inspect the generated diff
        ↓
Commit and push to GitHub main
        ↓
Netlify deploys automatically
        ↓
Verify the live JSON and rendered page
```

## Important rules

1. **Verify before publishing.** Prefer a canonical organizer, publisher, outlet, episode, event, or dedicated speaker page.
2. **Do not publish private details.** Never copy private calendar notes, email addresses, phone numbers, hotel details, reservation numbers, travel logistics, invitation-only instructions, or private correspondence into public data.
3. **Avoid duplicates.** Check both the exact URL and substantially identical coverage before adding anything.
4. **Use one record per meaningful public item.** A dedicated speaker page may be added alongside a general event page when it provides materially stronger evidence, but it should not be described as a separate appearance.
5. **Use the existing categories exactly.** Do not invent new category names.
6. **Only feature an item when Jason asks.** A feature change changes placement, not the appearance count.
7. **Do not report success until the live deployment is verified.** A successful local build or GitHub push is not enough.
8. **Preserve unrelated work.** Stop if the repository is unexpectedly dirty or behind the remote.

## Automation ownership

The two legacy OpenClaw media jobs were verified disabled on October 3, 2026. Keep them disabled. Parent task owns enabling replacement Clive schedules; the presence of these files does not prove recurrence is enabled. Target cadence: Tuesday 09:10 and first day of each month 09:00, America/Indiana/Indianapolis. Durable prompts are in automation/.

## Repository files

### Files edited by a normal media update

- `data/media_links.json` — authoritative public media records
- `public/data/media_links.json` — generated published copy
- `public/index.html` — generated standalone Netlify page
- `squarespace-embed.html` — generated self-contained Squarespace embed
- `squarespace-loader.html` — generated loader with cache-busting asset URLs

### Supporting workflow files

- `data/media_watchlist.json` — public-safe research leads that need future searching
- `data/media_candidates.json` — plausible public URLs that are not yet verified
- `MEDIA_MONITORING.md` — discovery and follow-up cadence
- `scripts/preflight.py` — repository, remote, branch, and push-auth checks
- `scripts/validate_data.py` — validates all three JSON data files
- `scripts/normalize.py` — deduplicates, normalizes, and sorts media records
- `scripts/build.py` — normalizes data and generates the public site and Squarespace files
- `scripts/verify_deploy.py` — verifies exact JSON, assets and live Squarespace loader
- `netlify.toml` — Netlify publish and cache/header configuration

## Step 1: Enter the repository and run preflight

```bash
cd /Users/clive/Desktop/jason-shanks-media-library
# Acquire the shared lease as documented in automation/RUNBOOK.md first.
python3 scripts/preflight.py
```

The preflight performs these checks:

- required files exist;
- the directory is a Git worktree;
- the current branch tracks `origin/main`;
- the worktree is clean;
- the local branch is neither ahead of nor behind `origin/main`;
- GitHub is reachable;
- a dry-run push succeeds.

If preflight fails, stop and resolve the cause before editing.

### Dirty-worktree rule

Do not use `--allow-dirty` to conceal pre-existing or unexplained changes. That option is only appropriate for a controlled manual check after the intended edits are already understood.

Useful read-only checks:

```bash
git status --short
git branch --show-current
git rev-list --left-right --count HEAD...origin/main
git diff
```

Expected branch and divergence before editing:

```text
main
0  0
```

## Step 2: Research the appearance

Search using Jason's exact name plus the outlet, host, event, title, topic, or platform.

Examples:

```text
"Jason Shanks" "outlet name"
"Jason Shanks" "host name"
"Jason Shanks" podcast
"Jason Shanks" radio
"Jason Shanks" keynote
site:example.org "Jason Shanks"
```

Useful sources include:

- official organizer or event pages;
- dedicated speaker pages;
- publisher or outlet pages;
- YouTube or Vimeo pages from the publisher;
- Apple Podcasts, Spotify, Omny, or the show's official episode page;
- diocesan and ministry websites;
- public LinkedIn, Instagram, Facebook, or Substack posts when normal visitors can open them;
- reputable articles or news coverage.

Prefer the original publisher over a repost or search-result snippet.

## Step 3: Verify the proposed record

Open the candidate URL and confirm that it supports every public field you intend to save:

- Jason is the correct person;
- title;
- source or outlet;
- publication, recording, or event date;
- category;
- description;
- tags;
- whether the item is a public promotion, recording, article, recognition, or delivered talk.

The URL must be accessible to a normal visitor. Do not use an Outlook link, private calendar link, authenticated file URL, expiring attachment URL, or local file path.

### Past talks without a public advertisement

Jason may explicitly ask to archive a talk even when no event-specific public promotion exists. In that case:

1. Use Jason's confirmation that the talk actually occurred.
2. Verify the exact title, date, organizer, and public-safe location from the calendar or event correspondence.
3. Link to a stable public organizer or chapter page.
4. Describe it as a **delivered talk**, not as a public advertisement.
5. Omit private logistics, contacts, transportation, reservations, and invitation details.

A calendar entry by itself proves scheduling, not delivery. Jason's confirmation supplies the completion evidence.

## Step 4: Check for duplicates

Search the source data before adding anything:

```bash
rg -n -i 'part of title|outlet name|distinctive URL text' data/media_links.json
```

Check for:

- the exact URL;
- a normalized form of the same URL;
- the same event or appearance under a different title;
- duplicate article syndications;
- both a general event page and a dedicated speaker page.

Rules:

- Skip an exact duplicate.
- Prefer the stronger canonical URL when two URLs represent the same thing.
- A dedicated speaker page can coexist with a general event page when it adds meaningful evidence.
- A video announcement and a written announcement may coexist as distinct media formats, but do not feature both unless Jason asks.

## Step 5: Edit the authoritative data

Edit `data/media_links.json`. Records are normalized into newest-first order by the build.

### Required schema

```json
{
  "title": "Exact public title",
  "url": "https://publisher.example/item",
  "category": "Talk",
  "source": "Publisher or organizer",
  "date": "2026-10-03",
  "description": "Concise, factual explanation of Jason's role or the content.",
  "tags": [
    "Primary topic",
    "Outlet or event",
    "Relevant theme"
  ],
  "verified": true
}
```

### Allowed categories

- `Video`
- `Podcast`
- `Radio`
- `Writing`
- `Talk`
- `Book`
- `Interview`
- `Recognition`

### Field guidance

- **title:** Use the official title where possible. For a calendar-confirmed delivered talk, use the exact speaker-agreement or program title.
- **url:** Use the canonical public URL without tracking parameters.
- **category:** Use one of the eight allowed values exactly.
- **source:** Name the publisher, outlet, conference, diocese, or organizer.
- **date:** Use `YYYY-MM-DD`. Prefer publication date for articles/recordings and event date for talks.
- **description:** Keep it factual, public-safe, and generally one or two sentences.
- **tags:** Use a short list of meaningful terms. The rendered card shows the first three tags.
- **verified:** Set to `true` only when the record has been verified.
- **featured:** Optional. Add `"featured": true` only when Jason explicitly requests it.

### Featured example

```json
{
  "title": "Example Keynote",
  "url": "https://example.org/speakers/jason-shanks",
  "category": "Talk",
  "source": "Example Conference",
  "date": "2026-10-03",
  "description": "Jason Shanks delivered the conference keynote.",
  "tags": ["Keynote", "Leadership", "Mission"],
  "verified": true,
  "featured": true
}
```

The generated Featured section contains six cards. Explicitly featured records are selected first, newest first; remaining slots are filled automatically with category variety and then recency.

## Step 6: Handle unverified leads correctly

### Calendar or correspondence leads

Put a redacted lead in `data/media_watchlist.json` when an appearance is scheduled or recorded but no public item is available yet.

Typical fields:

```json
{
  "outlet": "Example Outlet",
  "title_hint": "Jason Shanks interview",
  "medium": "Podcast",
  "recording_date": "2026-10-03",
  "calendar_summary": "Redacted calendar-derived interview lead.",
  "status": "watching",
  "found_url": null,
  "last_checked_at": "2026-10-03",
  "next_check_date": "2026-10-10",
  "search_queries": [
    "\"Jason Shanks\" \"Example Outlet\"",
    "site:example.org \"Jason Shanks\""
  ],
  "notes": "Public-safe notes only."
}
```

Allowed watchlist statuses:

- `watching`
- `candidate`
- `found`
- `added`
- `ignored`

A `watching` lead must have `next_check_date`. A `found` or `added` lead must have a valid `found_url`.

### Public candidates that are not yet verified

Put plausible public URLs in `data/media_candidates.json`:

```json
{
  "title": "Possible episode or promotion",
  "url": "https://example.org/possible-item",
  "source": "Example Outlet",
  "discovered_at": "2026-10-03",
  "status": "needs-review",
  "notes": "Why it may be relevant and what still needs verification."
}
```

Allowed candidate statuses:

- `needs-review`
- `verified`
- `rejected`
- `added`

Do not copy a candidate URL into `media_links.json` until relevance and public accessibility are verified.

## Step 7: Validate and build

Run:

```bash
python3 scripts/validate_data.py
python3 scripts/build.py --skip-scrape
git diff --check
git status --short
git diff --stat
git diff
```

Use `--skip-scrape` when the discovery work is already complete. It normalizes, validates, and builds without starting a new automated web scrape.

The build should report:

- total media-item count;
- category counts;
- successful validation;
- generated `public/index.html`;
- generated `public/data/media_links.json`;
- generated Squarespace files;
- no diff-check errors.

### Inspect the expected result

For a new item:

- total item count should increase by one;
- the appropriate category count should increase by one;
- the new card should appear in generated `public/index.html`;
- the new record should appear in `public/data/media_links.json`.

For a feature-only change:

- total item count should not change;
- category counts should not change;
- the expected card should appear in the generated Featured section with class `jml-featured`.

Useful checks:

```bash
rg -n -C 3 'Exact Title' public/index.html
rg -n -C 3 'Exact Title' public/data/media_links.json
rg -n -C 8 'Exact Title' squarespace-embed.html
```

## Step 8: Commit only the intended files

Review the final diff first. Then stage tracked source and generated files:

```bash
git add data/media_links.json data/media_watchlist.json data/media_candidates.json public/index.html public/embed.css public/embed.js public/data/media_links.json public/build-manifest.json squarespace-embed.html squarespace-loader.html
git status --short
git diff --cached --check
git diff --cached --stat
```

For a new documentation file, add it explicitly:

```bash
git add MEDIA_PAGE_UPDATE_GUIDE.md
```

Commit with a concise description:

```bash
git commit -m "Add Example Outlet interview"
```

Then push:

```bash
git push origin HEAD:main
```

The push to `main` is the Netlify deployment trigger. A Netlify CLI command or `NETLIFY_AUTH_TOKEN` is not normally required.

## Step 9: Verify the Netlify deployment

First run the repository verifier:

```bash
python3 scripts/verify_deploy.py
```

For a new URL, require the exact URL:

```bash
python3 scripts/verify_deploy.py \
  --require-url 'https://publisher.example/item'
```

The verifier requires exact complete JSON equality, exact generated HTML/CSS/JS/build manifest, and the actual Squarespace loader integration. Changed metadata, featured status, missing records, extra records and stale assets fail verification.

### Verify changed fields

```bash
curl -fsS 'https://jason-shanks-media.netlify.app/data/media_links.json?verify=UNIQUE' \
  | jq '.[] | select(.url=="https://publisher.example/item")'
```

Confirm the deployed record contains the expected:

- title;
- category;
- source;
- date;
- description;
- tags;
- `verified` value;
- `featured` value, when requested.

### Verify the rendered page

```bash
curl -fsS 'https://jason-shanks-media.netlify.app/?verify=UNIQUE' \
  | rg -n -C 3 'Exact Title'
```

For a featured item, verify that the live HTML contains the title inside the Featured section and that the card has the `jml-featured` class.

### Deployment delay

Immediately after a push, the live site may still serve the prior build. A first stale result usually means Netlify is still deploying.

Use a bounded retry—do not wait indefinitely:

```bash
for attempt in 1 2 3 4 5 6; do
  if curl -fsS "https://jason-shanks-media.netlify.app/data/media_links.json?attempt=$attempt" \
    | jq -e '.[] | select(.url=="https://publisher.example/item")' >/dev/null; then
    echo "Deployment verified"
    break
  fi
  sleep 10
done
```

## Step 10: Confirm a clean final state

```bash
git status --short
git rev-list --left-right --count HEAD...origin/main
git rev-parse --short HEAD
```

Expected:

- no output from `git status --short`;
- `0  0` divergence from `origin/main`;
- a commit hash matching the published change.

Only then report completion with:

- the item title;
- category and date;
- whether it was featured;
- the live page URL;
- the published commit hash;
- any source limitation, such as a calendar-confirmed past talk without an event-specific public advertisement.

## Squarespace behavior

The Squarespace Media & Appearances page uses the small loader in `squarespace-loader.html`. It fetches:

- `https://jason-shanks-media.netlify.app/embed.css`
- `https://jason-shanks-media.netlify.app/embed.js`
- `https://jason-shanks-media.netlify.app/data/media_links.json`

The build updates cache-busting query values in the loader. Under the normal setup, the Squarespace Code Block does not need to be replaced for each new media item because it loads current Netlify-hosted assets and data.

Replace the Squarespace Code Block only if:

- the loader structure changes;
- the Netlify domain changes;
- the container ID changes;
- the embed implementation is redesigned.

## Troubleshooting

### `ERROR: worktree is dirty`

Run:

```bash
git status --short
git diff
```

Identify who owns the changes. Do not discard or overwrite unrelated work. If the changes are the intended media update and preflight is being rerun manually after editing, `python3 scripts/preflight.py --allow-dirty` may be used only after the changes are fully understood.

### Local branch is behind `origin/main`

Do not push over the remote. Fetch and reconcile carefully:

```bash
git fetch origin
git status
git log --oneline --decorate --graph --all -20
```

Preserve both local and remote work. Resolve conflicts deliberately.

### Push authentication fails

Use only independently approved existing GitHub access. Do not load OpenClaw secret files, copy browser sessions, or set up new persistent credentials. Stop and report the missing access route. Normal GitHub-triggered Netlify publication does not require a Netlify token.

### Validation fails

Read every reported issue. Common causes:

- missing required field;
- invalid category;
- duplicate URL;
- invalid date format;
- non-list `tags` value;
- `verified` is not Boolean;
- a candidate URL already exists in `media_links.json`;
- a `watching` lead lacks `next_check_date`;
- a `found` or `added` lead lacks `found_url`.

### Build changes more than expected

Inspect the complete diff. Expected generated changes commonly include:

- item and category counts;
- the new or updated card;
- footer date;
- content-fingerprint cache keys in `squarespace-loader.html`.

Stop if unrelated records, styles, scripts, or content changed unexpectedly.

### Deployment is stale

The strengthened verifier compares exact data and assets. Retry with `--attempts 6 --delay 10`. A failure after the bounded retries is a deployment blocker. Never mark success based only on the push or a scheduler receipt.

### New item is in JSON but not visible

Check:

- `verified` is `true`;
- category is valid;
- the build completed;
- `public/index.html` contains the card;
- the commit reached `origin/main`;
- Netlify finished deploying;
- browser or Squarespace cache has been bypassed with a unique query string.

### Featured item does not appear

Check:

- the source record contains `"featured": true`;
- the build ran after the edit;
- the live deployed JSON contains `"featured": true`;
- the live HTML shows the card with `jml-featured`;
- more than six explicit featured items are not competing for the six available slots.

## Final checklist

- [ ] Preflight passed before editing.
- [ ] Canonical public source was opened and verified.
- [ ] Jason's identity, title, date, source, category, and description were confirmed.
- [ ] Private details were excluded.
- [ ] Exact and substantive duplicates were checked.
- [ ] `data/media_links.json` was updated using the existing schema.
- [ ] `featured` was added only with Jason's approval.
- [ ] `scripts/validate_data.py` passed.
- [ ] `scripts/build.py --skip-scrape` passed.
- [ ] Generated count and category changes matched expectations.
- [ ] `git diff --check` passed.
- [ ] Only intended source and generated files were committed.
- [ ] The commit was pushed to `origin/main`.
- [ ] `scripts/verify_deploy.py` passed.
- [ ] Exact deployed fields were checked for updates to existing URLs.
- [ ] Requested featured cards were verified in the live Featured section.
- [ ] The final worktree is clean and aligned with `origin/main`.
