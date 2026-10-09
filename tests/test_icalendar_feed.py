from pathlib import Path

import pytest

from nagpur_today.icalendar_feed import _parse_events, fetch_feed

FIXTURE = Path(__file__).parent / "fixtures" / "sample_calendar.ics"
FEED_URL = "https://organizer.example.org/events.ics"


def test_parses_one_off_event_and_skips_recurring_series():
    events = _parse_events(FIXTURE.read_text(encoding="utf-8"), FEED_URL)
    assert len(events) == 1
    event = events[0]
    assert event["title"] == "Community pottery workshop"
    assert event["starts_at"] == "2026-10-15T18:00:00+05:30"
    assert event["ends_at"] == "2026-10-15T19:30:00+05:30"
    assert event["source_url"] == "https://example.org/events/pottery-001"
    assert event["venue_name"] == "Dharampeth, Nagpur"
    assert "suitable for beginners" in event["description"]


def test_feed_url_must_be_https():
    with pytest.raises(ValueError, match="HTTPS"):
        fetch_feed("http://organizer.example.org/events.ics")
