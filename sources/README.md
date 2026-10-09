# Source adapters

Each adapter should expose `fetch_events() -> list[dict]` and return raw records in the normalized field vocabulary used by `nagpur_today.normalize.normalize_record`.

Only add an adapter after its source access method and reuse rules have been reviewed. Keep one source per module so a source change does not break other collectors.

Minimum fields:
- `title`
- `starts_at` (ISO 8601 preferred; timezone included when known)
- `source_url` (original event page, not a search URL)

Useful optional fields: `ends_at`, `description`, `category`, `venue_name`, `neighbourhood`, `price_label`, `organizer_name`, `image_url`, `source_event_id`.

Run adapter-specific tests against saved, permitted fixtures. Never use fictional fixtures as production listings.

## Organizer iCalendar feeds

A generic iCalendar feed reader is implemented in `src/nagpur_today/icalendar_feed.py`. It only requests explicitly configured HTTPS feed URLs from `NAGPUR_ICS_FEEDS`; there are no URLs configured by default. Configure only organizer feeds that are approved for automated retrieval and are scoped to Nagpur. One-off events are supported; recurring series are skipped until recurrence expansion is implemented. Each feed should include an event `URL` pointing to the original event page.

## RSS/Atom article discovery (review queue only)

`src/nagpur_today/rss_discovery.py` reads only explicitly configured HTTPS RSS/Atom feeds from `NGP_RSS_FEEDS` (comma-separated), with optional matching names in `NGP_RSS_FEED_NAMES`. Run `nagpur-today discover-rss --output data/event_candidates.json`. It matches event-related titles and stores only the headline, article URL, publication timestamp and review metadata. **It does not publish events.** News publication dates are not event dates; a human must verify the actual event date, venue, future status and original organizer link. Only configure feeds whose terms permit automated retrieval and this limited use. No feed is configured by default.

## Source permission register

- BookMyShow: no automated collector is enabled. Review the current platform terms and seek an authorized API/partnership or written permission before automated collection; manual public links can enter the review queue.
- District: do not scrape/crawl without express authorization; its terms restrict scraping, crawling and reuse of platform content. Seek written permission/API access.
- Scene: confirm the exact app/domain first, then review its terms and request a feed/API or permission before automated collection.
- Local news: prefer publisher-provided RSS/Atom feeds and keep the source article link. Treat articles as leads, not event records, until event date/location are verified. Check each publisher's terms and reuse rules.
- Independent organizers/venues: preferred first-party sources; request an iCalendar feed or permission to ingest their public event pages.


## Public social/event link intake

Use `data/manual_social_links.csv` to submit public Instagram reels/posts, Facebook event URLs, YouTube links, event pages or other source URLs. Run `nagpur-today intake-links data/manual_social_links.csv --output data/social_link_candidates.json`. The command validates HTTPS hostnames, removes common tracking parameters and deduplicates links. It **does not fetch the URLs, scrape the platforms, download media or publish events**. A reviewer must open each source through normal permitted access, verify event details and permissions, and then add a complete record through the reviewed event import workflow.

## Source registry

`source_registry.json` records known leads, access status and proposed integration method. Entries are intentionally disabled by default until permission and source quality are reviewed. Update the registry when source permission, API access or connector status changes.
