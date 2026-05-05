# Media Monitoring Workflow

Goal: keep Jason's Media & Appearances page current, including smaller podcasts/radio/videos that may not appear in major-source searches.

## Calendar-driven watchlist

Media appearances often begin as calendar events before they are published. Use calendar scans to create leads in `data/media_watchlist.json`.

Calendar events should be considered media leads when they include words/outlets such as:

- podcast, radio, interview, recording, record, guest, show, media, livestream, webinar
- Legatus, Ave Maria Radio, EWTN, Relevant Radio, OSV, Eucharistic, Franciscan, Catholic Connection, etc.

For each lead, store:

- outlet
- title hint / calendar summary
- medium
- recording date
- search queries
- status: `watching`, `found`, `added`, `ignored`
- notes

## Follow-up cadence

Publication timing is uncertain, so search repeatedly:

- 1 week after recording
- 2–3 weeks after recording
- monthly for 3 months
- again at quarterly review if still not found

## Search strategy

Do not search only large Catholic media sources. Use exact-name and outlet-specific searches:

- `"Jason Shanks" "<outlet>"`
- `"Jason Shanks" "<host>"`
- `"Jason Shanks" podcast`
- `"Jason Shanks" radio`
- `site:<outlet-domain> "Jason Shanks"`
- YouTube, Apple Podcasts, Spotify, Listen Notes, Podtail, podcast/radio pages, Substack, diocesan pages, and small show websites.

When found, add to `data/media_links.json`, mark verified after checking the link opens, rebuild, and push.
