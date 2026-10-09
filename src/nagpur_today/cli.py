from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from .normalize import normalize_record
from .storage import connect, export_events, to_schema_org, upsert_events
from .icalendar_feed import fetch_events as fetch_icalendar_events
from .rss_discovery import fetch_candidates as fetch_rss_candidates
from .link_intake import intake_links


def import_csv(input_path: Path, output_path: Path) -> int:
    normalized = []
    errors = []
    with input_path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        for line_number, row in enumerate(reader, start=2):
            try:
                normalized.append(normalize_record(row, source_name=f"CSV:{input_path.name}"))
            except Exception as exc:  # report all row errors rather than silently skipping them
                errors.append({"line": line_number, "error": str(exc)})
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps({"events": normalized, "errors": errors}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Normalized {len(normalized)} event(s); {len(errors)} row error(s). Output: {output_path}")
    return 1 if errors else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="NGP Today ingestion tools")
    sub = parser.add_subparsers(dest="command", required=True)
    csv_parser = sub.add_parser("import-csv", help="normalize an approved CSV export")
    csv_parser.add_argument("input", type=Path)
    csv_parser.add_argument("--output", type=Path, default=Path("data/normalized_events.json"))
    store_parser = sub.add_parser("store-csv", help="normalize an approved CSV export and upsert it into SQLite")
    store_parser.add_argument("input", type=Path)
    store_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    ical_parser = sub.add_parser("ingest-ical", help="fetch explicitly configured, approved iCalendar feeds into SQLite")
    ical_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    ical_parser.add_argument("--publish-approved-feeds", action="store_true", help="publish events from explicitly approved organizer feeds automatically")
    rss_parser = sub.add_parser("discover-rss", help="collect event-related article candidates from approved RSS/Atom feeds for manual review")
    rss_parser.add_argument("--output", type=Path, default=Path("data/event_candidates.json"))
    links_parser = sub.add_parser("intake-links", help="queue submitted public event/social URLs for manual review without fetching them")
    links_parser.add_argument("input", type=Path, nargs="?", default=Path("data/manual_social_links.csv"))
    links_parser.add_argument("--output", type=Path, default=Path("data/social_link_candidates.json"))
    review_parser = sub.add_parser("list-events", help="list stored events for moderation")
    review_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    review_parser.add_argument("--status", choices=["pending", "published", "rejected", "all"], default="pending")
    review_parser.add_argument("--output", type=Path, default=None)
    status_parser = sub.add_parser("set-event-status", help="approve or reject an event by canonical URL")
    status_parser.add_argument("url", help="event source URL (tracking parameters are ignored)")
    status_parser.add_argument("status", choices=["pending", "published", "rejected"])
    status_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    export_parser = sub.add_parser("export-jsonld", help="export published SQLite events as Schema.org Event JSON-LD")
    export_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    export_parser.add_argument("--output", type=Path, default=Path("data/events.jsonld"))
    jekyll_parser = sub.add_parser("export-jekyll-json", help="export published events for a Jekyll site data file")
    jekyll_parser.add_argument("--db", type=Path, default=Path("data/events.db"))
    jekyll_parser.add_argument("--output", type=Path, default=Path("website/_data/events.json"))
    args = parser.parse_args()
    if args.command == "import-csv":
        raise SystemExit(import_csv(args.input, args.output))
    if args.command == "store-csv":
        normalized_path = args.db.with_suffix(".normalized.json")
        code = import_csv(args.input, normalized_path)
        if code:
            raise SystemExit(code)
        payload = json.loads(normalized_path.read_text(encoding="utf-8"))
        with connect(args.db) as connection:
            count = upsert_events(connection, payload["events"])
        print(f"Stored {count} event(s) in SQLite: {args.db}")
        raise SystemExit(0)
    if args.command == "ingest-ical":
        raw_events = fetch_icalendar_events()
        normalized = [normalize_record(event, source_name=event.get("source_name", "Organizer iCalendar feed")) for event in raw_events]
        with connect(args.db) as connection:
            status = "published" if args.publish_approved_feeds else "pending"
            count = upsert_events(connection, normalized, status=status)
        message = "published from approved feeds" if args.publish_approved_feeds else "left pending review"
        print(f"Fetched {len(raw_events)} event(s); processed {count} event(s); records {message}.")
        raise SystemExit(0)
    if args.command == "discover-rss":
        candidates = fetch_rss_candidates()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"candidates": candidates}, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Discovered {len(candidates)} candidate article(s); none were published. Output: {args.output}")
        raise SystemExit(0)
    if args.command == "intake-links":
        candidates = intake_links(args.input)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps({"candidates": candidates}, indent=2, ensure_ascii=False), encoding="utf-8")
        queued = sum(1 for item in candidates if item.get("review_status") == "needs_manual_event_verification")
        rejected = len(candidates) - queued
        print(f"Queued {queued} public link(s) for review; rejected {rejected}; nothing was fetched or published. Output: {args.output}")
        raise SystemExit(0)
    if args.command == "export-jekyll-json":
        with connect(args.db) as connection:
            events = export_events(connection, status="published")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(events, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Exported {len(events)} published event(s) for Jekyll: {args.output}")
        raise SystemExit(0)
    if args.command == "list-events":
        with connect(args.db) as connection:
            if args.status == "all":
                rows = connection.execute("SELECT id, title, starts_at, venue_name, source_name, source_url, status FROM events ORDER BY starts_at").fetchall()
            else:
                rows = connection.execute("SELECT id, title, starts_at, venue_name, source_name, source_url, status FROM events WHERE status=? ORDER BY starts_at", (args.status,)).fetchall()
            payload = [dict(row) for row in rows]
        rendered = json.dumps({"events": payload}, indent=2, ensure_ascii=False)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
            print(f"Listed {len(payload)} {args.status} event(s): {args.output}")
        else:
            print(rendered)
        raise SystemExit(0)
    if args.command == "set-event-status":
        from .normalize import canonicalize_url
        canonical_url = canonicalize_url(args.url)
        with connect(args.db) as connection:
            existing = connection.execute("SELECT title, is_fictional FROM events WHERE canonical_url=?", (canonical_url,)).fetchone()
            if existing is None:
                print("No event found for that canonical URL. Import it first, then set its status.")
                raise SystemExit(2)
            if args.status == "published" and existing["is_fictional"]:
                print("Refusing to publish fictional sample data. Replace it with a verified real event first.")
                raise SystemExit(2)
            connection.execute("UPDATE events SET status=?, updated_at=CURRENT_TIMESTAMP WHERE canonical_url=?", (args.status, canonical_url))
            connection.commit()
            row = connection.execute("SELECT title, status FROM events WHERE canonical_url=?", (canonical_url,)).fetchone()
        print(f"Updated event status: {row['title']} -> {row['status']}")
        raise SystemExit(0)
    if args.command == "export-jsonld":
        with connect(args.db) as connection:
            events = export_events(connection, status="published")
        output = {"@context": "https://schema.org", "@graph": [to_schema_org(event) for event in events]}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Exported {len(events)} published event(s) to {args.output}")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
