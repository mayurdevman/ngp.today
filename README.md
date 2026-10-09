# NGP Today — event ingestion starter

NGP Today is being aligned to the architecture used by the open-source [blr.today](https://github.com/blr-today) project. Intended domain: **ngp.today** (not registered or deployed by this starter): a static Jekyll website, source-specific ingestion scripts, standardized event records, a SQLite dataset, scheduled GitHub Actions and calendar feeds.

## Included

- `ARCHITECTURE_MAPPING.md` — upstream-to-Nagpur mapping, data flow, source approval checklist and implementation milestones.
- `src/nagpur_today/normalize.py` — validates required fields, normalizes dates to `Asia/Kolkata`, canonicalizes URLs and creates content hashes.
- `src/nagpur_today/storage.py` — SQLite schema initialization, upsert-by-canonical-URL, published-event export and basic Schema.org Event JSON-LD mapping.
- `sources/adapter_template.py` — a blank adapter contract for future source-specific collectors.
- `sources/source_registry.json` — source-by-source permission and integration register for local news, ticketing sites, official listings, social links and organiser calendars.
- `src/nagpur_today/link_intake.py` — safe intake queue for manually submitted public event/social URLs; validates and deduplicates links without fetching them.
- `data/manual_social_links.csv` — template for submitting social posts/reels and event page URLs for review.
- `src/nagpur_today/icalendar_feed.py` — connector for organizer-approved HTTPS iCalendar feeds, with fixture-based parsing tests. It is inactive unless approved feed URLs are configured.
- `schema.sql` — SQLite event storage schema.
- `website/` — minimal monochrome dark Jekyll website with search, date filters, source links and a GitHub Pages deployment workflow.
- `data/sample_events.csv` — fictional records for local tests only.

## Current status

Brand: **NGP Today**. Target domain: **ngp.today**. Domain availability and registration have not been confirmed.

No live Nagpur feed is configured yet. The iCalendar connector is implemented but remains inactive until an organizer-approved HTTPS feed is supplied in `NAGPUR_ICS_FEEDS`. Recurring iCalendar series are skipped pending recurrence expansion. Sample records are fictional and must never be published as real events. The deployment workflow is prepared but does not run until the repository is pushed to GitHub and Pages is enabled. It does not create a hosted database or configure calendar subscriptions.

## Run locally

Requires Python 3.11+.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
python -m pytest
python -m nagpur_today.cli import-csv data/sample_events.csv --output data/normalized_events.json
```

To ingest organizer-approved iCalendar feeds, set `NAGPUR_ICS_FEEDS` to a comma-separated list of HTTPS feed URLs, then run:

```bash
NAGPUR_ICS_FEEDS="https://organizer.example/events.ics" python -m nagpur_today.cli ingest-ical --db data/events.db
```

New events stay `pending` by default. For organizer feeds whose contents and reuse terms have been reviewed, set the GitHub Actions repository variable `NAGPUR_ICS_AUTO_PUBLISH` to `true` to publish feed events automatically; leave it unset to keep records pending. Export published events for a Jekyll website with `python -m nagpur_today.cli export-jekyll-json --db data/events.db --output website/_data/events.json`.

To test SQLite persistence with the fictional sample data:

```bash
python -m nagpur_today.cli store-csv data/sample_events.csv --db data/events.db
```

New records are `pending` by default. Public exports include only records explicitly marked `published`. Review pending records with `python -m nagpur_today.cli list-events --db data/events.db --status pending`. After verifying an event, publish it with `python -m nagpur_today.cli set-event-status "https://organizer.example/event" published --db data/events.db`; use `rejected` to keep it out of public listings. The CLI refuses to publish records marked as fictional sample data. To export the published records as Schema.org Event JSON-LD, run `python -m nagpur_today.cli export-jsonld --db data/events.db --output data/events.jsonld`.

The scheduled workflow persists the SQLite database and published JSON dataset back to the repository so approved-feed ingestion can survive between GitHub Actions runs. This requires repository Actions to have permission to write to the branch. Review branch-protection rules before enabling scheduled persistence; for a larger production service, replace repository commits with managed storage.

## Upstream repositories and licences

- Website: https://github.com/blr-today/website — AGPL-3.0-or-later.
- Ingestion: https://github.com/blr-today/ingest — GPL-3.0.
- Dataset: https://github.com/blr-today/dataset — ODbL-1.0.

Review the current licence files before porting source code. The ingestion repository says its `out/` and `fixtures/` content is not covered by its code licence; use the published dataset and comply with its ODbL terms if reusing that dataset.

## Next steps

1. Review the source registry and obtain permission/API/feed access from the highest-value organisers and platforms.
2. Enable a publisher RSS feed only after its terms permit automated retrieval and candidate discovery.
3. Add public social/event links to the manual intake CSV and review the workflow artifact.
4. Obtain an organizer-approved iCalendar feed and configure `NAGPUR_ICS_FEEDS`.
5. Create a GitHub repository and push this project to enable the prepared GitHub Pages deployment.
6. Add a proper web moderation interface and calendar subscription feeds before treating the site as a full automated service.

Source access, terms, rate limits, attribution and image-use rules must be checked before enabling each connector. Do not bypass access controls.

### Public social/event link intake

Add links to `data/manual_social_links.csv` with `url`, `source_name`, `submitted_by`, and `notes` columns. Run `python -m nagpur_today.cli intake-links data/manual_social_links.csv --output data/social_link_candidates.json`. It only validates and queues links; it does not access social platforms or publish an event. The workflow archives the review queue as an artifact.

### Article discovery from RSS

The optional `discover-rss` command builds a **manual review queue** from explicitly configured approved RSS/Atom feeds. It does not turn article publication dates into event dates or auto-publish news articles as events. Set `NGP_RSS_FEEDS` and optionally `NGP_RSS_FEED_NAMES`; no feeds are contacted by default.
