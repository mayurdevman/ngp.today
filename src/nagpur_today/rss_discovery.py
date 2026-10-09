"""Discover possible event articles from explicitly configured HTTPS RSS/Atom feeds.

This is a candidate finder, not an event publisher. News articles rarely contain a
reliable event start time; all candidates require verification before becoming events.
Only configure feeds whose terms permit automated retrieval and this limited use.
"""
from __future__ import annotations

import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from urllib.parse import urlsplit

MAX_FEED_BYTES = 3 * 1024 * 1024
EVENT_TERMS = re.compile(
    r"\b(event|festival|exhibition|concert|gig|workshop|meetup|comedy|theatre|theater|"
    r"play|show|fair|mela|conference|summit|screening|performance|marathon|walkathon|"
    r"open mic|book launch|food fest|music fest|happening)\b",
    re.IGNORECASE,
)


def _text(node: ET.Element, *names: str) -> str:
    for name in names:
        child = node.find(name)
        if child is not None and child.text:
            return unescape(re.sub(r"<[^>]+>", " ", child.text)).strip()
    return ""


def parse_feed(xml_text: str, feed_url: str, source_name: str = "RSS feed") -> list[dict]:
    root = ET.fromstring(xml_text)
    entries = root.findall(".//item")
    atom_ns = "{http://www.w3.org/2005/Atom}"
    if not entries:
        entries = root.findall(f".//{atom_ns}entry")
    candidates = []
    seen = set()
    for entry in entries:
        title = _text(entry, "title", f"{atom_ns}title")
        if not title or not EVENT_TERMS.search(title):
            continue
        link = _text(entry, "link")
        if not link:
            for link_node in entry.findall(f"{atom_ns}link"):
                if link_node.get("rel", "alternate") == "alternate" and link_node.get("href"):
                    link = link_node.get("href", "")
                    break
        if not link or not link.startswith("https://") or link in seen:
            continue
        seen.add(link)
        candidates.append({
            "title": title,
            "source_url": link,
            "published_at": _text(entry, "pubDate", "published", "updated", f"{atom_ns}published", f"{atom_ns}updated"),
            "source_name": source_name,
            "feed_url": feed_url,
            "review_status": "needs_event_date_and_location_verification",
            "note": "Article matched event-related keywords; this is not yet a confirmed event listing.",
        })
    return candidates


def fetch_feed(feed_url: str, source_name: str = "RSS feed", timeout: int = 15) -> list[dict]:
    parts = urlsplit(feed_url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError("RSS/Atom feed URL must use HTTPS")
    request = urllib.request.Request(feed_url, headers={"User-Agent": "NGPTodayEventDiscovery/0.1 (+RSS candidate discovery)"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(MAX_FEED_BYTES + 1)
    if len(payload) > MAX_FEED_BYTES:
        raise ValueError(f"Feed exceeds {MAX_FEED_BYTES} bytes")
    return parse_feed(payload.decode("utf-8-sig"), feed_url, source_name)


def fetch_candidates() -> list[dict]:
    """Fetch configured feeds; no network requests occur when none are configured."""
    urls = [value.strip() for value in os.getenv("NGP_RSS_FEEDS", "").split(",") if value.strip()]
    names = [value.strip() for value in os.getenv("NGP_RSS_FEED_NAMES", "").split(",")]
    results = []
    seen = set()
    for index, url in enumerate(urls):
        name = names[index] if index < len(names) and names[index] else "RSS feed"
        for candidate in fetch_feed(url, name):
            if candidate["source_url"] not in seen:
                seen.add(candidate["source_url"])
                results.append(candidate)
    return results
