"""Small SQLite store for normalized event records."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_url TEXT NOT NULL UNIQUE,
    source_url TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    category TEXT NOT NULL DEFAULT 'Community',
    starts_at TEXT NOT NULL,
    ends_at TEXT,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    venue_name TEXT,
    neighbourhood TEXT,
    city TEXT NOT NULL DEFAULT 'Nagpur',
    price_label TEXT,
    organizer_name TEXT,
    content_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    is_fictional INTEGER NOT NULL DEFAULT 0,
    raw_json TEXT NOT NULL,
    first_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS events_starts_status_idx ON events(starts_at, status);
CREATE INDEX IF NOT EXISTS events_category_starts_idx ON events(category, starts_at);
CREATE INDEX IF NOT EXISTS events_neighbourhood_starts_idx ON events(neighbourhood, starts_at);
CREATE INDEX IF NOT EXISTS events_content_hash_idx ON events(content_hash);
"""


def connect(path: str | Path) -> sqlite3.Connection:
    db_path = Path(path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    connection.executescript(SCHEMA)
    return connection


def upsert_events(connection: sqlite3.Connection, events: Iterable[dict], status: str = "pending") -> int:
    """Insert/update by canonical URL; return number of processed records.

    ``status`` applies to new records. Existing review status is preserved unless
    the caller explicitly requests publication of an approved source feed.
    """
    if status not in {"pending", "published"}:
        raise ValueError("status must be 'pending' or 'published'")
    count = 0
    for event in events:
        connection.execute(
            """INSERT INTO events (
                canonical_url, source_url, source_name, title, description,
                category, starts_at, ends_at, venue_name, neighbourhood, city,
                price_label, organizer_name, content_hash, is_fictional, raw_json, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(canonical_url) DO UPDATE SET
                source_url=excluded.source_url,
                source_name=excluded.source_name,
                title=excluded.title,
                description=excluded.description,
                category=excluded.category,
                starts_at=excluded.starts_at,
                ends_at=excluded.ends_at,
                venue_name=excluded.venue_name,
                neighbourhood=excluded.neighbourhood,
                city=excluded.city,
                price_label=excluded.price_label,
                organizer_name=excluded.organizer_name,
                content_hash=excluded.content_hash,
                is_fictional=excluded.is_fictional,
                raw_json=excluded.raw_json,
                status=CASE WHEN ? = 'published' THEN 'published' ELSE events.status END,
                last_seen_at=CURRENT_TIMESTAMP,
                updated_at=CURRENT_TIMESTAMP""",
            (
                event["canonical_url"], event["source_url"], event.get("source_name", "unknown"),
                event["title"], event.get("description", ""), event.get("category", "Community"),
                event["starts_at"], event.get("ends_at"), event.get("venue_name"),
                event.get("neighbourhood"), event.get("city", "Nagpur"), event.get("price_label"),
                event.get("organizer_name"), event["content_hash"], int(event.get("is_fictional", False)),
                json.dumps(event, ensure_ascii=False, sort_keys=True), status, status,
            ),
        )
        count += 1
    connection.commit()
    return count


def export_events(connection: sqlite3.Connection, status: str = "published") -> list[dict]:
    """Return stored normalized records for a chosen status."""
    rows = connection.execute(
        "SELECT raw_json FROM events WHERE status = ? ORDER BY starts_at", (status,)
    ).fetchall()
    return [json.loads(row["raw_json"]) for row in rows]


def to_schema_org(event: dict) -> dict:
    """Map a normalized record to a basic Schema.org Event JSON-LD object."""
    result = {
        "@context": "https://schema.org",
        "@type": "Event",
        "name": event["title"],
        "startDate": event["starts_at"],
        "url": event.get("source_url"),
        "eventStatus": "https://schema.org/EventScheduled",
        "location": {
            "@type": "Place",
            "name": event.get("venue_name") or event.get("neighbourhood") or "Nagpur",
            "address": {
                "@type": "PostalAddress",
                "addressLocality": "Nagpur",
                "addressRegion": "Maharashtra",
                "addressCountry": "IN",
            },
        },
    }
    if event.get("ends_at"):
        result["endDate"] = event["ends_at"]
    if event.get("description"):
        result["description"] = event["description"]
    if event.get("image_url"):
        result["image"] = event["image_url"]
    if event.get("organizer_name"):
        result["organizer"] = {"@type": "Organization", "name": event["organizer_name"]}
    if event.get("price_label"):
        result["offers"] = {"@type": "Offer", "description": event["price_label"], "url": event.get("source_url")}
    return result
