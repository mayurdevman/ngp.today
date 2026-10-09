from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from dateutil.parser import isoparse, parse

TRACKING_KEYS = {"fbclid", "gclid", "mc_cid", "mc_eid"}


def canonicalize_url(url: str) -> str:
    """Remove common tracking params and fragments without guessing URL equivalence."""
    parts = urlsplit(url.strip())
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
             if not k.lower().startswith("utm_") and k.lower() not in TRACKING_KEYS]
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))


def parse_datetime(value: str) -> str:
    """Parse a date/time and return ISO 8601; source adapters must supply timezone when known."""
    dt = isoparse(value) if re.match(r"^\d{4}-\d\d-\d\dT", value) else parse(value, dayfirst=True)
    if not isinstance(dt, datetime):
        raise ValueError(f"Invalid event datetime: {value}")
    if dt.tzinfo is None:
        # Nagpur's local timezone. Store the offset explicitly for consistent sorting.
        from zoneinfo import ZoneInfo
        dt = dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
    return dt.isoformat()


def content_hash(record: dict) -> str:
    stable = {
        "title": re.sub(r"\s+", " ", record["title"]).strip().casefold(),
        "starts_at": record["starts_at"],
        "venue": re.sub(r"\s+", " ", (record.get("venue_name") or "")).strip().casefold(),
    }
    payload = json.dumps(stable, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalize_record(raw: dict, source_name: str = "CSV import") -> dict:
    required = ("title", "starts_at", "source_url")
    missing = [key for key in required if not str(raw.get(key, "")).strip()]
    if missing:
        raise ValueError(f"Missing required fields: {', '.join(missing)}")

    source_url = str(raw["source_url"]).strip()
    if not source_url.startswith(("https://", "http://")):
        raise ValueError("source_url must be an http(s) URL")

    record = {
        "title": re.sub(r"\s+", " ", str(raw["title"])).strip(),
        "description": str(raw.get("description", "")).strip(),
        "category": str(raw.get("category", "Community")).strip() or "Community",
        "starts_at": parse_datetime(str(raw["starts_at"]).strip()),
        "ends_at": parse_datetime(str(raw["ends_at"]).strip()) if str(raw.get("ends_at", "")).strip() else None,
        "source_url": source_url,
        "canonical_url": canonicalize_url(source_url),
        "venue_name": str(raw.get("venue_name", "")).strip() or None,
        "neighbourhood": str(raw.get("neighbourhood", "")).strip() or None,
        "city": "Nagpur",
        "price_label": str(raw.get("price_label", "")).strip() or None,
        "organizer_name": str(raw.get("organizer_name", "")).strip() or None,
        "image_url": str(raw.get("image_url", "")).strip() or None,
        "source_event_id": str(raw.get("source_event_id", "")).strip() or None,
        "feed_url": str(raw.get("feed_url", "")).strip() or None,
        "source_name": str(raw.get("source_name", source_name)).strip() or source_name,
        "is_fictional": str(raw.get("is_fictional", "false")).strip().lower() in {"true", "1", "yes"},
    }
    record["content_hash"] = content_hash(record)
    return record
