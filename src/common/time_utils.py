"""
Time Utilities
==============

IST (Indian Standard Time, UTC+5:30) for Indian market correlation.
All API timestamps use exact Indian clock time (no timezone suffix in output).
"""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def now_ist() -> datetime:
    """Return current time in IST (timezone-aware)."""
    return datetime.now(IST)


def now_ist_naive() -> datetime:
    """Return current Indian time as naive datetime for API responses.
    Serializes as e.g. 2026-02-13 15:45:00 (exact Indian time, no +05:30 suffix).
    """
    return datetime.now(IST).replace(tzinfo=None)
