import sqlite3

from nagpur_today.normalize import normalize_record
from nagpur_today.storage import connect, export_events, to_schema_org, upsert_events


def record(title="Test event", url="https://example.org/events/1"):
    return normalize_record({
        "title": title,
        "starts_at": "2026-11-14T11:00:00+05:30",
        "source_url": url,
    }, source_name="test")


def test_sqlite_upsert_deduplicates_by_canonical_url(tmp_path):
    db = tmp_path / "events.db"
    with connect(db) as connection:
        assert upsert_events(connection, [record()]) == 1
        assert upsert_events(connection, [record(title="Updated title")]) == 1
        rows = connection.execute("SELECT title FROM events").fetchall()
        assert len(rows) == 1
        assert rows[0]["title"] == "Updated title"


def test_only_published_events_export_by_default(tmp_path):
    with connect(tmp_path / "events.db") as connection:
        upsert_events(connection, [record()])
        assert export_events(connection) == []
        connection.execute("UPDATE events SET status='published'")
        connection.commit()
        published = export_events(connection)
        assert len(published) == 1
        assert published[0]["city"] == "Nagpur"


def test_schema_org_export_has_required_event_fields():
    event = record()
    structured = to_schema_org(event)
    assert structured["@type"] == "Event"
    assert structured["name"] == "Test event"
    assert structured["startDate"].endswith("+05:30")
    assert structured["location"]["address"]["addressLocality"] == "Nagpur"


def test_approved_feed_can_publish_events_automatically(tmp_path):
    with connect(tmp_path / "approved.db") as connection:
        upsert_events(connection, [record()], status="published")
        published = export_events(connection)
        assert len(published) == 1
        assert published[0]["title"] == "Test event"


def test_invalid_event_status_is_rejected(tmp_path):
    with connect(tmp_path / "invalid.db") as connection:
        try:
            upsert_events(connection, [record()], status="live")
        except ValueError as exc:
            assert "status must be" in str(exc)
        else:
            raise AssertionError("Invalid status should have been rejected")
