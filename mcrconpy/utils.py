"""Utility functions for timestamp and datetime management."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone


def get_timestamp() -> float:
    """Return the current UTC timestamp.

    Returns:
        float: Current UTC timestamp in seconds since epoch.
    """
    return datetime.now(timezone.utc).timestamp()


def from_timestamp(timestamp: float) -> datetime:
    """Convert Unix timestamp to datetime object.

    Args:
        timestamp: Unix timestamp in seconds since epoch.

    Returns:
        datetime: UTC datetime instance from timestamp.

    Raises:
        ValueError: If timestamp is invalid or out of range.
    """
    try:
        return datetime.fromtimestamp(timestamp, timezone.utc)
    except (OSError, OverflowError, ValueError) as e:
        raise ValueError(f"Invalid timestamp: {timestamp}") from e


def difference_times(start: float, end: float) -> timedelta:
    """Calculate the difference between two timestamps.

    Args:
        start: Start timestamp in seconds since epoch.
        end: End timestamp in seconds since epoch.

    Returns:
        timedelta: Difference between end and start timestamps.

    Raises:
        ValueError: If timestamps are invalid or end < start.
    """
    if end < start:
        raise ValueError(f"End timestamp ({end}) must be >= start timestamp ({start})")

    try:
        start_dt = datetime.fromtimestamp(start, timezone.utc)
        end_dt = datetime.fromtimestamp(end, timezone.utc)
        return end_dt - start_dt
    except (OSError, OverflowError, ValueError) as e:
        raise ValueError(f"Invalid timestamps: start={start}, end={end}") from e


__all__ = ["get_timestamp", "from_timestamp", "difference_times"]
