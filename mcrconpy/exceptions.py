"""Exceptions for mcrconpy."""

from __future__ import annotations


class ErrorParameter(Exception):
    """Raised when invalid parameters are provided."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"Parameter Error: {msg}")


class SocketConnectionError(Exception):
    """Raised when socket connection fails."""

    def __init__(self, msg: str) -> None:
        super().__init__(f"Socket Connection Error: {msg}")


class ServerTimeOut(Exception):
    """Raised when server connection times out."""

    def __init__(self, msg: str = "Connection timed out.") -> None:
        super().__init__(msg)


class ServerError(Exception):
    """Raised when server socket error occurs."""

    def __init__(self, error: object) -> None:
        super().__init__(f"Server Socket Error: {error}")


class ServerAuthError(Exception):
    """Raised when authentication with server fails."""

    def __init__(self, msg: str = "Server Auth Error, check the password.") -> None:
        super().__init__(msg)


class AddressError(Exception):
    """Raised when IP address or port is invalid."""

    def __init__(self, msg: str = "IP address and PORT is incorrect.") -> None:
        super().__init__(msg)


class PasswordError(Exception):
    """Raised when password is missing or incorrect."""

    def __init__(
        self, msg: str = "Password has not been provided or is incorrect."
    ) -> None:
        super().__init__(msg)


__all__ = [
    "ErrorParameter",
    "SocketConnectionError",
    "ServerTimeOut",
    "ServerError",
    "ServerAuthError",
    "AddressError",
    "PasswordError",
]
