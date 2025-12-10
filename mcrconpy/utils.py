# -*- coding: utf-8 -*-
"""
Utility functions for timestamp and datetime management.
"""

from datetime import datetime, timedelta, timezone


def get_timestamp() -> float:
    """
    Returns the current UTC timestamp.
    """
    return datetime.now(timezone.utc).timestamp()


def from_timestamp(timestamp: float) -> datetime | None:
    """
    Gets datetime object from timestamp.

    Args:
        timestamp: float, timestamp.

    Returns:
        datetime: datetime instance from timestamp or None.
    """
    if isinstance(timestamp, float):
        return datetime.fromtimestamp(timestamp, timezone.utc)
    return None


def difference_times(start: float, end: float) -> timedelta | None:
    """
    Gets the difference between two timestamps.

    Args:
        start: float, start timestamp.
        end: float, end timestamp.

    Returns:
        timedelta: Difference between `end` and `start`.
    """
    if isinstance(start, float) and isinstance(end, float):
        # Timestamps are absolute, direct subtraction is safe
        return datetime.fromtimestamp(end, timezone.utc) - datetime.fromtimestamp(start, timezone.utc)
    return None
