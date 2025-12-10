"""High-performance RCON client for Minecraft servers.

This package provides both synchronous and asynchronous RCON clients
with strict typing, modern Python features, and performance optimizations.

Example:
    >>> from mcrconpy import Rcon
    >>> with Rcon("localhost", 25575, "password") as client:
    ...     response = client.command("list")
    ...     print(response)
"""

from __future__ import annotations

from mcrconpy.audit import Audit
from mcrconpy.core import AsyncRcon, MessageType, Packet, Rcon
from mcrconpy.exceptions import (
    AddressError,
    ErrorParameter,
    PasswordError,
    ServerAuthError,
    ServerError,
    ServerTimeOut,
    SocketConnectionError,
)
from mcrconpy.models import Command, User
from mcrconpy.version import VERSION

# Legacy alias for backward compatibility
RconPy = Rcon

__version__ = VERSION
__all__ = [
    # Core classes
    "Rcon",
    "AsyncRcon",
    "Packet",
    "MessageType",
    # Models
    "Command",
    "User",
    # Audit
    "Audit",
    # Exceptions
    "ErrorParameter",
    "SocketConnectionError",
    "ServerTimeOut",
    "ServerError",
    "ServerAuthError",
    "AddressError",
    "PasswordError",
    # Legacy
    "RconPy",
    # Version
    "VERSION",
    "__version__",
]
