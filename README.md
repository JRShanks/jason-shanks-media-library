# Jason Shanks Media Library

Clive/Codex maintains Jason's existing Media & Appearances library. Jason authorized automatic publication of verified additions on October 3, 2026; uncertain discoveries stay candidates, and features/removals require separate instruction.

- Public personal page: https://jasonrshanks.com/media-appearances
- Embedded application: https://jason-shanks-media.netlify.app/
- Canonical source: `data/media_links.json`
- Repository: `JRShanks/jason-shanks-media-library`, branch `main`
- Hosting: locally generated `public/` committed to GitHub, automatically deployed by the existing Netlify integration.

The permanent Squarespace loader stays unchanged for normal updates.

Read [automation/RUNBOOK.md](automation/RUNBOOK.md) for scheduling handoff, source coverage, calendar access cutoff, shared lease, idempotency, publication and reporting. Read [MEDIA_PAGE_UPDATE_GUIDE.md](MEDIA_PAGE_UPDATE_GUIDE.md) for editorial/schema guidance and [MEDIA_MONITORING.md](MEDIA_MONITORING.md) for follow-up cadence. Weekly/monthly child prompts are in `automation/`.

## Local validation

```bash
python3 scripts/validate_data.py
python3 -m unittest discover -s tests
python3 scripts/build.py --skip-scrape
python3 scripts/verify_deploy.py --attempts 6 --delay 10
```

Build writes source normalization and generated artifacts. Run only in an authorized checkout after acquiring the shared lease and checking the worktree. Repeated unchanged builds preserve their fingerprint/timestamp. `preflight.py` fetches origin and checks push readiness; it is not a read-only operation.

Discovery is agent-led public research plus permitted calendar follow-up. `scripts/scraper.py` optionally supports YouTube and Google Custom Search using independently approved environment access; no RSS feeds are currently configured. Python `requests` and `feedparser` are optional scraper dependencies in `requirements.txt`. Missing search APIs are not evidence that discovery completed.

Watchlist and candidate files are intentionally public-safe working records in this public repository. Do not put raw calendar/private logistics in them. No private-storage migration is needed for completed public appearances.

The legacy OpenClaw media jobs remain disabled. Only parent-created and verified enabled replacement schedules establish recurrence; documentation alone does not.
