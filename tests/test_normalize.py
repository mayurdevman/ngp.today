from nagpur_today.normalize import canonicalize_url, normalize_record


def test_canonicalize_removes_tracking_params():
    assert canonicalize_url("https://Example.org/event/?utm_source=x&id=2#top") == "https://example.org/event?id=2"


def test_normalize_sets_nagpur_timezone_and_marks_sample():
    record = normalize_record({
        "title": "  Sample event ",
        "starts_at": "2026-11-14 11:00",
        "source_url": "https://example.org/event?utm_medium=social",
        "is_fictional": "true",
    })
    assert record["title"] == "Sample event"
    assert record["city"] == "Nagpur"
    assert record["starts_at"].endswith("+05:30")
    assert record["is_fictional"] is True
