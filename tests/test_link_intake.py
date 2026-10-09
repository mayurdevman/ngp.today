import csv
import json

import pytest

from nagpur_today.link_intake import canonicalize_public_url, intake_links


def test_social_url_intake_deduplicates_and_does_not_fetch(tmp_path):
    source = tmp_path / "links.csv"
    with source.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["url", "source_name", "submitted_by", "notes"])
        writer.writeheader()
        writer.writerow({"url": "https://www.instagram.com/reel/ABC/?igshid=123", "source_name": "Instagram"})
        writer.writerow({"url": "https://www.instagram.com/reel/ABC/", "source_name": "Instagram"})
        writer.writerow({"url": "http://example.org/event"})
    candidates = intake_links(source)
    assert len(candidates) == 2
    assert candidates[0]["source_url"] == "https://www.instagram.com/reel/ABC/"
    assert candidates[0]["review_status"] == "needs_manual_event_verification"
    assert "no page was fetched" in candidates[0]["review_note"]
    assert candidates[1]["review_status"] == "rejected_invalid_url"


def test_canonicalizer_rejects_credentials_and_local_hosts():
    with pytest.raises(ValueError):
        canonicalize_public_url("https://user:pass@example.com/event")
    with pytest.raises(ValueError):
        canonicalize_public_url("https://localhost/private")
    with pytest.raises(ValueError):
        canonicalize_public_url("https://127.0.0.1/private")


def test_csv_requires_url_column(tmp_path):
    source = tmp_path / "bad.csv"
    source.write_text("link,title\nhttps://example.org/e,Event\n", encoding="utf-8")
    with pytest.raises(ValueError, match="url"):
        intake_links(source)
