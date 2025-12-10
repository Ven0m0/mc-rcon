"""Models for User and Command tracking with dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mcrconpy.utils import get_timestamp


@dataclass(frozen=True)
class Command:
    """Represents an executed command with timestamp.

    Attributes:
        command: The command string that was executed.
        timestamp: UTC timestamp when command was executed.
    """

    command: str
    timestamp: float = field(default_factory=get_timestamp)

    def to_dict(self) -> dict[str, float | str]:
        """Serialize to dictionary.

        Returns:
            dict: Command data with command text and timestamp.
        """
        return {"command": self.command, "timestamp": self.timestamp}

    def __str__(self) -> str:
        """Human-readable string representation."""
        cmd_preview = self.command[:10]
        return f"[{self.timestamp}] {cmd_preview}"


@dataclass
class User:
    """RCON user session with command history and timing.

    Attributes:
        id: User identifier (always 1 for RCON).
        commands: List of executed commands.
        is_login: Whether user is currently authenticated.
        start_session: Session start timestamp (UTC).
        end_session: Session end timestamp (UTC).
        seconds_session: Total session duration in seconds.
    """

    id: int = 1
    commands: list[Command] = field(default_factory=list)
    is_login: bool = False
    start_session: float | None = None
    end_session: float | None = None
    seconds_session: float | None = None
    _password: str | None = field(default=None, repr=False)

    def active_session(self) -> None:
        """Start the session timer and mark user as logged in."""
        self.is_login = True
        self.start_session = get_timestamp()

    def close_session(self) -> None:
        """End the session timer and calculate duration."""
        self.is_login = False
        self.end_session = get_timestamp()
        self.calculate_duration()

    def calculate_duration(self) -> None:
        """Calculate session duration from start/end timestamps."""
        if self.start_session is not None and self.end_session is not None:
            self.seconds_session = self.end_session - self.start_session
        else:
            self.seconds_session = None

    def set_password(self, passwd: str) -> bool:
        """Update password if different from current.

        Args:
            passwd: New password to set.

        Returns:
            bool: True if password was changed, False otherwise.
        """
        if passwd and passwd != self._password:
            self._password = passwd
            return True
        return False

    def get_password(self) -> str | None:
        """Get current password.

        Returns:
            str | None: Current password or None if not set.
        """
        return self._password

    def register_command(self, cmd: str) -> None:
        """Record a command execution.

        Args:
            cmd: Command string to record.
        """
        self.commands.append(Command(command=cmd))

    def to_dict(self) -> dict[str, Any]:
        """Serialize user session data.

        Returns:
            dict: Session data including commands, timestamps, and status.
        """
        start_us: int | None = None
        if self.start_session is not None:
            # Convert to microseconds for backwards compatibility
            start_us = int(self.start_session * 1_000_000)

        return {
            "start_session": start_us,
            "commands": [cmd.to_dict() for cmd in self.commands],
            "is_login": self.is_login,
            "end_session": self.end_session,
            "seconds_session": self.seconds_session,
        }

    def __str__(self) -> str:
        """Human-readable string representation."""
        start_str = f"{self.start_session:.2f}" if self.start_session else "N/A"
        return f"User: is_login={self.is_login}, Session={start_str}"


__all__ = ["Command", "User"]
