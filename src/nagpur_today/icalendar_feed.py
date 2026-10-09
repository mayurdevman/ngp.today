"""Import organizer-published iCalendar feeds for Nagpur events.

Only configure feeds whose owner permits automated retrieval and reuse.
This adapter intentionally does not discover feeds or scrape ticketing sites.
"""
from __future__ import annotations

import os
import re
import urllib.request
from datetime import date, datetime, time, timezone
from typing import Any
from urllib.parse import urlencode, urlsplit, urlunsplit
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr

SOURCE_NAME = "Organizer iCalendar feed"
LOCAL_TZ = ZoneInfo("Asia/Kolkata")
MAX_FEED_BYTES = 5 * 1024 * 1024


def _unfold(text: str) -> list[str]:
    # RFC 5545 folded lines continue with a single leading space or tab.
    text = re.sub(r"\r?\n[ \t]", "", text)
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _unescape(value: str) -> str:
    return value.replace(r"\n", "\n").replace(r"\N", "\n").replace(r"\,", ",").replace(r"\;", ";").replace(r"\\", "\\").strip()


def _parse_dt(property_line: str) -> datetime:
    left, value = property_line.split(":", 1)
    params = {}
    pieces = left.split(";")
    for item in pieces[1:]:
        if "=" in item:
            key, val = item.split("=", 1)
            params[key.upper()] = val.strip('"')
    value = value.strip()
    if params.get("VALUE", "").upper() == "DATE" or re.fullmatch(r"\d{8}", value):
        d = datetime.strptime(value[:8], "%Y%m%d").date()
        return datetime.combine(d, time.min, tzinfo=LOCAL_TZ)
    if value.endswith("Z"):
        return datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).astimezone(LOCAL_TZ)
    dt = datetime.strptime(value, "%Y%m%dT%H%M%S" if len(value) >= 15 else "%Y%m%dT%H%M")
    tzid = params.get("TZID")
    try:
        zone = ZoneInfo(tzid) if tzid else LOCAL_TZ
    except Exception:
        zone = LOCAL_TZ
    return dt.replace(tzinfo=zone).astimezone(LOCAL_TZ)


def _parse_events(ics_text: str, feed_url: str) -> list[dict[str, Any]]:
    lines = _unfold(ics_text)
    blocks: list[list[str]] = []
    current: list[str] | None = None
    for line in lines:
        if line.strip().upper() == "BEGIN:VEVENT":
            current = []
        elif line.strip().upper() == "END:VEVENT":
            if current is not None:
                blocks.append(current)
            current = None
        elif current is not None and ":" in line:
            current.append(line)

    events = []
    for block in blocks:
        fields: dict[str, str] = {}
        for line in block:
            key = line.split(":", 1)[0].split(";", 1)[0].upper()
            fields[key] = line
        if "SUMMARY" not in fields or "DTSTART" not in fields:
            continue
        title = _unescape(fields["SUMMARY"].split(":", 1)[1])
        if not title:
            continue
        try:
            starts_at = _parse_dt(fields["DTSTART"]).isoformat()
            ends_at = _parse_dt(fields["DTEND"]).isoformat() if "DTEND" in fields else None
        except (ValueError, TypeError):
            continue
        # Recurring VEVENTs need recurrence expansion before publication. Avoid
        # silently dropping future occurrences or misrepresenting a series.
        if "RRULE" in fields or "RECURRENCE-ID" in fields:
            continue
        def value(name: str) -> str:
            return _unescape(fields[name].split(":", 1)[1]) if name in fields else ""
        event_url = value("URL")
        uid = value("UID")
        if not event_url:
            # A stable pointer back to the feed entry; organizers should provide
            # URL for a direct event page whenever possible.
            parts = urlsplit(feed_url)
            event_url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode({"event_uid": uid}) if uid else "", ""))
        location = value("LOCATION")
        events.append({
            "title": title,
            "starts_at": starts_at,
            "ends_at": ends_at,
            "source_url": event_url,
            "description": value("DESCRIPTION"),
            "venue_name": location or None,
            "category": "Community",
            "organizer_name": value("ORGANIZER") or None,
            "source_event_id": uid or None,
            "source_name": SOURCE_NAME,
            "feed_url": feed_url,
        })
    return events


def fetch_feed(feed_url: str, timeout: int = 15) -> list[dict[str, Any]]:
    parts = urlsplit(feed_url)
    if parts.scheme != "https" or not parts.netloc:
        raise ValueError("iCalendar feed URL must use HTTPS")
    request = urllib.request.Request(
        feed_url,
        headers={"User-Agent": "NagpurTodayEventIndexer/0.1 (+organizer feed import)"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = response.read(MAX_FEED_BYTES + 1)
    if len(payload) > MAX_FEED_BYTES:
        raise ValueError(f"Feed exceeds {MAX_FEED_BYTES} bytes")
    text = payload.decode("utf-8-sig")
    if "BEGIN:VCALENDAR" not in text.upper():
        raise ValueError("Response does not appear to be an iCalendar feed")
    return _parse_events(text, feed_url)


def fetch_events() -> list[dict[str, Any]]:
    """Fetch only explicitly configured, approved HTTPS feeds.

    Set NAGPUR_ICS_FEEDS to comma-separated feed URLs. No URLs are configured
    by default so no external source is contacted until an organizer feed is approved.
    """
    feeds = [item.strip() for item in os.getenv("NAGPUR_ICS_FEEDS", "").split(",") if item.strip()]
    events = []
    for feed_url in feeds:
        events.extend(fetch_feed(feed_url))
    return events
