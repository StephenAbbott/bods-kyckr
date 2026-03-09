"""Date parsing and normalization utilities for BODS output."""

from __future__ import annotations

import re
from datetime import date, datetime

from dateutil import parser as dateutil_parser


def normalize_date(date_str: str | None) -> str | None:
    """Normalize various date formats to ISO 8601 (YYYY-MM-DD)."""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    if re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        return date_str

    if re.match(r"^\d{4}-\d{2}$", date_str):
        return date_str

    if re.match(r"^\d{4}$", date_str):
        return date_str

    # ISO 8601 with time component — extract date portion
    match = re.match(r"^(\d{4}-\d{2}-\d{2})T", date_str)
    if match:
        return match.group(1)

    # DD/MM/YYYY format
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{4})$", date_str)
    if match:
        day, month, year = match.groups()
        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"

    try:
        parsed = dateutil_parser.parse(date_str, dayfirst=True)
        return parsed.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        pass

    return None


def normalize_datetime(dt_str: str | None) -> str | None:
    """Normalize a datetime string to ISO 8601 format (YYYY-MM-DDTHH:MM:SSZ)."""
    if not dt_str or not dt_str.strip():
        return None

    dt_str = dt_str.strip()

    try:
        parsed = dateutil_parser.parse(dt_str)
        return parsed.strftime("%Y-%m-%dT%H:%M:%SZ")
    except (ValueError, TypeError):
        pass

    return None


def current_date_iso() -> str:
    """Return today's date in ISO format."""
    return date.today().isoformat()


def current_datetime_iso() -> str:
    """Return current UTC datetime in ISO format."""
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
