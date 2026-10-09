# NGP Today — blr.today architecture mapping

This project uses the public blr.today repositories as an architectural reference, not as a blind copy. Confirm the current upstream files and licence before porting code.

## Upstream reference

- Website: https://github.com/blr-today/website (Jekyll; AGPL-3.0-or-later)
- Ingestion: https://github.com/blr-today/ingest (Python-based pipeline; GPL-3.0)
- Dataset: https://github.com/blr-today/dataset (published dataset; ODbL-1.0)

Read the licence files before copying code or reusing the upstream dataset. The upstream ingestion README explicitly says its `out/` and `fixtures/` content is not covered by the code licence; use the published dataset and comply with ODbL if reusing it.

## Architectural mapping

| blr.today concept | NGP Today implementation | Status |
|---|---|---|
| Jekyll website | A minimal monochrome dark Jekyll site with search, date filters and source links | Starter implemented; requires deploy |
| Source-specific ingestion scripts | One adapter module per approved Nagpur source | Adapter contract scaffolded |
| Event cleanup and enrichment | Normalize timestamps to `Asia/Kolkata`, canonicalize URLs, retain source attribution, validate required fields | Implemented in starter |
| Schema.org/Event output | Normalized JSON records with a JSON-LD export path planned | Basic JSON-LD export command scaffolded; not yet connected to website |
| SQLite database | Local SQLite store for normalized events, unique canonical URLs and content-hash duplicate checks | Implemented in starter |
| GitHub Actions every four hours | Scheduled ingestion, Jekyll build and GitHub Pages deployment | Configured; requires GitHub repository, approved feeds and optional auto-publish setting |
| Calendar feeds | Generate `.ics` feeds from published SQLite records | Not implemented |
| Event curation | Review queue/status before public publication | Schema supports status; admin UI not implemented |

## Data flow

1. A scheduled job invokes only source adapters that have been reviewed and approved.
2. Each adapter returns raw event dictionaries with a stable source name and original URL.
3. Normalization validates the record, standardizes date/time and strips common tracking parameters.
4. SQLite upserts on canonical URL and records content hashes for duplicate review.
5. Events remain `pending` until source quality and publishing rules are configured.
6. A later site build reads published records and generates event pages and calendar feeds.

## Why SQLite first

The reference project publishes a SQLite event database and rebuilds it on a schedule. For an early city directory with batch ingestion and a mostly static frontend, SQLite avoids operating a separate database service. Move to a server database only if we need concurrent user submissions, moderation workflows, frequent writes, or API-backed interactions that justify it.

## Source approval checklist

Before enabling a source, record:

- Official source URL and owner/contact where known.
- Access method: API, RSS, iCalendar, approved export, manual submission, or permitted page parsing.
- Terms, robots guidance, rate limits, attribution and image-use rules.
- How the adapter identifies Nagpur events and handles multi-date events.
- Tests for missing fields, changed HTML/data formats, cancellations and duplicate listings.
- Last successful run and source health reporting.

Do not bypass access controls or publish an event solely because it appears in a search result. Retain the original source URL and verify dates before publication.

## Next milestones

1. Review the upstream website's Jekyll data plugin and calendar routes; decide what to port under AGPL compliance.
2. Approve the first event source and implement its adapter in `sources/`.
3. Add SQLite-to-JSON-LD output and connect the website build.
4. Add iCalendar feeds and a basic event moderation workflow.
5. Deploy to a free static host and enable scheduled GitHub Actions after repository setup.
