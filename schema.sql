-- SQLite schema. Kept in sync with src/nagpur_today/storage.py.
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
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'published', 'cancelled', 'rejected', 'expired')),
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
