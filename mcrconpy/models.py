# -*- coding: utf-8 -*-
"""
Models for User and Command tracking.
"""

from typing import Optional, List, Any
from mcrconpy.utils import (
    get_timestamp,
    from_timestamp,
    difference_times,
)


class Command:
    """
    Represents an executed command and its execution timestamp.
    """

    def __init__(self, command: str) -> None:
        self.command: str = command
        self.timestamp: float = get_timestamp()

    def to_dict(self) -> dict[str, Any]:
        return {"command": self.command, "timestamp": self.timestamp}

    def __str__(self) -> str:
        return f"{from_timestamp(self.timestamp)}, {self.command[:10]}"

    def __repr__(self) -> str:
        return f"<[ CMD: {self.__str__()} ]>"


class User:
    """
    Represents the RCON user session.
    """

    def __init__(self, password: Optional[str] = None) -> None:
        self.id: int = 1
        self._password: Optional[str] = password
        self.commands: List[Command] = []
        self.is_login: bool = False
        self.start_session: Optional[float] = None
        self.end_session: Optional[float] = None
        self.seconds_session: Optional[float] = None

    def active_session(self) -> None:
        """Starts the session timer."""
        self.is_login = True
        self.start_session = get_timestamp()

    def close_session(self) -> None:
        """Ends the session timer."""
        self.is_login = False
        self.end_session = get_timestamp()
        self.calculate_duration()

    def calculate_duration(self) -> None:
        """Calculates session duration."""
        if self.start_session is not None and self.end_session is not None:
            delta = difference_times(self.start_session, self.end_session)
            if delta:
                self.seconds_session = delta.total_seconds()
            else:
                self.seconds_session = None
        else:
            self.seconds_session = None

    def set_password(self, passwd: str) -> bool:
        """
        Sets a new password.
        """
        if passwd and passwd != self._password:
            self._password = passwd
            return True
        return False

    def get_password(self) -> Optional[str]:
        """Returns the current password."""
        return self._password

    def register_command(self, cmd: str) -> None:
        """Records a command."""
        self.commands.append(Command(command=cmd))

    def to_dict(self) -> dict[str, Any]:
        """Serializes user session data."""
        start = self.start_session
        if start is not None:
            # Converting to microseconds for legacy reason?
            # Original code: int(self.start_session * 1000000)
            start_us = int(start * 1_000_000)
        else:
            start_us = None  # type: ignore

        return {
            "start_session": start_us,
            "commands": [cmd.to_dict() for cmd in self.commands],
            "is_login": self.is_login,
            "end_session": self.end_session,
            "seconds_session": self.seconds_session,
        }

    def __str__(self) -> str:
        start_ts = from_timestamp(self.start_session) if self.start_session else "N/A"
        return f"User: is_login: {self.is_login}, Session: {start_ts}"

    def __repr__(self) -> str:
        return f"<[ {self.__str__()} ]>"
