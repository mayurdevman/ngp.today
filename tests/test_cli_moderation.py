import sys

import pytest

from nagpur_today.cli import main
from nagpur_today.normalize import normalize_record
from nagpur_today.storage import connect, upsert_events, export_events


def _record(url="https://organizer.example/event-1", fictional=False):
    return normalize_record({
        "title": "Verified Nagpur workshop",
        "starts_at": "2026-11-14T11:00:00+05:30",
        "source_url": url,
        "venue_name": "Dharampeth",
        "is_fictional": fictional,
    }, source_name="moderation test")


def test_cli_can_publish_verified_event(tmp_path, monkeypatch, capsys):
    db = tmp_path / "events.db"
    with connect(db) as connection:
        upsert_events(connection, [_record()])

    monkeypatch.setattr(sys, "argv", ["nagpur-today", "set-event-status", "https://organizer.example/event-1?utm_source=test", "published", "--db", str(db)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
    assert "published" in capsys.readouterr().out
    with connect(db) as connection:
        assert len(export_events(connection, status="published")) == 1


def test_cli_refuses_to_publish_fictional_sample(tmp_path, monkeypatch, capsys):
    db = tmp_path / "events.db"
    with connect(db) as connection:
        upsert_events(connection, [_record(url="https://example.org/sample", fictional=True)])

    monkeypatch.setattr(sys, "argv", ["nagpur-today", "set-event-status", "https://example.org/sample", "published", "--db", str(db)])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
    assert "fictional sample data" in capsys.readouterr().out
    with connect(db) as connection:
        assert export_events(connection, status="published") == []
