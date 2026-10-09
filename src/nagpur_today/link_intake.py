"""Create a review queue from manually submitted public event/social links.

This module deliberately does not fetch the submitted URL or scrape a social
platform. A reviewer verifies the original post and records event details before
it can be normalized and published.
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {"fbclid", "gclid", "igshid", "mc_cid", "mc_eid"}


def canonicalize_public_url(value: str) -> str:
    raw = (value or "").strip()
    parts = urlsplit(raw)
    if parts.scheme.lower() != "https" or not parts.hostname:
        raise ValueError("URL must be a public HTTPS URL")
    if parts.username or parts.password:
        raise ValueError("URL must not contain embedded credentials")
    host = parts.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith((".localhost", ".local", ".internal")):
        raise ValueError("URL must point to a public host")
    # Reject IP literals; this intake tool is not a URL fetcher and expects public links.
    if re.fullmatch(r"[0-9.]+", host) or ":" in host:
        raise ValueError("Use a public hostname, not an IP address")
    filtered = [(key, val) for key, val in parse_qsl(parts.query, keep_blank_values=True) if key.lower() not in TRACKING_KEYS]
    return urlunsplit(("https", host, parts.path or "/", urlencode(filtered, doseq=True), ""))


def intake_links(input_path: Path) -> list[dict]:
    candidates: list[dict] = []
    seen: set[str] = set()
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "url" not in reader.fieldnames:
            raise ValueError("CSV must include a 'url' column")
        for line, row in enumerate(reader, start=2):
            raw_url = (row.get("url") or "").strip()
            if not raw_url:
                continue
            try:
                url = canonicalize_public_url(raw_url)
            except ValueError as exc:
                candidates.append({"input_line": line, "submitted_url": raw_url, "review_status": "rejected_invalid_url", "review_note": str(exc)})
                continue
            if url in seen:
                continue
            seen.add(url)
            candidates.append({
                "source_url": url,
                "source_name": (row.get("source_name") or "Community-submitted link").strip(),
                "submitted_by": (row.get("submitted_by") or "").strip(),
                "notes": (row.get("notes") or "").strip(),
                "review_status": "needs_manual_event_verification",
                "review_note": "Link received only; no page was fetched or scraped. Verify event title, date, venue, Nagpur relevance, source rights and original organiser link before publication.",
            })
    return candidates
