"""Template for an approved Nagpur event source.

Copy this file to a source-specific module only after confirming an allowed
access method (API, RSS, iCalendar, approved export, manual submission, or
permitted page parsing). Keep source-specific parsing isolated here.
"""
from __future__ import annotations

from typing import Any

SOURCE_NAME = "Replace with source name"
SOURCE_HOME = "https://example.org/"


def fetch_events() -> list[dict[str, Any]]:
    """Return raw event records for this source.

    Implement only after checking terms, rate limits, attribution and source
    stability. Do not bypass access controls. Return an empty list until the
    connector is implemented and reviewed; do not ship fabricated records.
    """
    return []
