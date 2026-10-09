import pytest

from nagpur_today.rss_discovery import fetch_feed, parse_feed


def test_rss_returns_event_candidates_without_claiming_they_are_confirmed():
    xml = '''<?xml version="1.0"?><rss version="2.0"><channel>
      <item><title>Nagpur hosts a weekend theatre festival</title><link>https://news.example.org/story/1</link><pubDate>Fri, 09 Oct 2026 10:00:00 +0530</pubDate></item>
      <item><title>Road repair work begins today</title><link>https://news.example.org/story/2</link></item>
      <item><title>Nagpur music festival</title><link>http://news.example.org/story/3</link></item>
    </channel></rss>'''
    results = parse_feed(xml, "https://news.example.org/rss.xml", "Example News")
    assert len(results) == 1
    assert results[0]["title"] == "Nagpur hosts a weekend theatre festival"
    assert results[0]["review_status"] == "needs_event_date_and_location_verification"
    assert results[0]["source_url"] == "https://news.example.org/story/1"


def test_atom_feed_supported():
    xml = '''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Nagpur comedy show announced</title><link href="https://news.example.org/comedy"/><updated>2026-10-09T10:00:00Z</updated></entry></feed>'''
    results = parse_feed(xml, "https://news.example.org/atom.xml")
    assert len(results) == 1
    assert results[0]["source_url"] == "https://news.example.org/comedy"


def test_rss_feed_url_must_be_https():
    with pytest.raises(ValueError, match="HTTPS"):
        fetch_feed("http://news.example.org/rss.xml")
