"""Tests for data models."""

from __future__ import annotations

import time

import pytest

from mcrconpy.models import Command, User


def test_command_creation() -> None:
    """Test Command dataclass creation."""
    cmd = Command(command="list")

    assert cmd.command == "list"
    assert isinstance(cmd.timestamp, float)
    assert cmd.timestamp > 0


def test_command_to_dict() -> None:
    """Test Command serialization."""
    cmd = Command(command="say Hello", timestamp=1704067200.0)
    data = cmd.to_dict()

    assert data["command"] == "say Hello"
    assert data["timestamp"] == 1704067200.0


def test_command_immutable() -> None:
    """Test that Command is frozen (immutable)."""
    cmd = Command(command="list")

    with pytest.raises(AttributeError):
        cmd.command = "different"  # type: ignore[misc]


def test_user_initialization() -> None:
    """Test User dataclass initialization."""
    user = User()

    assert user.id == 1
    assert user.is_login is False
    assert user.commands == []
    assert user.start_session is None
    assert user.end_session is None
    assert user.seconds_session is None


def test_user_session_lifecycle() -> None:
    """Test user session start and end."""
    user = User()

    # Start session
    user.active_session()
    assert user.is_login is True
    assert user.start_session is not None

    time.sleep(0.01)

    # End session
    user.close_session()
    assert user.is_login is False
    assert user.end_session is not None
    assert user.seconds_session is not None
    assert user.seconds_session > 0


def test_user_password() -> None:
    """Test password setting and retrieval."""
    user = User()

    assert user.get_password() is None

    # Set password
    result = user.set_password("secret123")
    assert result is True
    assert user.get_password() == "secret123"

    # Set same password (no change)
    result = user.set_password("secret123")
    assert result is False


def test_user_register_command() -> None:
    """Test command registration."""
    user = User()

    user.register_command("list")
    user.register_command("time set day")

    assert len(user.commands) == 2
    assert user.commands[0].command == "list"
    assert user.commands[1].command == "time set day"


def test_user_to_dict() -> None:
    """Test User serialization."""
    user = User()
    user.active_session()
    user.register_command("list")
    user.close_session()

    data = user.to_dict()

    assert "start_session" in data
    assert "commands" in data
    assert "is_login" in data
    assert "end_session" in data
    assert "seconds_session" in data

    assert len(data["commands"]) == 1
    assert data["commands"][0]["command"] == "list"
