"""Tests for utility functions."""

from __future__ import annotations

import time

import pytest

from mcrconpy.utils import difference_times, from_timestamp, get_timestamp


def test_get_timestamp() -> None:
    """Test timestamp generation."""
    ts1 = get_timestamp()
    time.sleep(0.01)
    ts2 = get_timestamp()

    assert isinstance(ts1, float)
    assert isinstance(ts2, float)
    assert ts2 > ts1


def test_from_timestamp() -> None:
    """Test timestamp to datetime conversion."""
    ts = 1704067200.0  # 2024-01-01 00:00:00 UTC
    dt = from_timestamp(ts)

    assert dt.year == 2024
    assert dt.month == 1
    assert dt.day == 1


def test_from_timestamp_invalid() -> None:
    """Test invalid timestamp handling."""
    with pytest.raises(ValueError, match="Invalid timestamp"):
        from_timestamp(1e20)  # Way too large


def test_difference_times() -> None:
    """Test time difference calculation."""
    start = 1704067200.0  # 2024-01-01 00:00:00 UTC
    end = 1704067260.0  # 2024-01-01 00:01:00 UTC

    delta = difference_times(start, end)

    assert delta.total_seconds() == 60.0


def test_difference_times_invalid_order() -> None:
    """Test that end must be >= start."""
    start = 100.0
    end = 50.0

    with pytest.raises(ValueError, match="must be >= start"):
        difference_times(start, end)


def test_difference_times_equal() -> None:
    """Test zero time difference."""
    ts = 1704067200.0
    delta = difference_times(ts, ts)

    assert delta.total_seconds() == 0.0
