# -*- coding: utf-8 -*-
"""
Exceptions for mcrconpy.
"""

from typing import Optional, Any


class ErrorParameter(Exception):
    def __init__(self, msg: str) -> None:
        super().__init__(f"Parameter Error: {msg}")


class SocketConnectionError(Exception):
    def __init__(self, msg: Any) -> None:
        super().__init__(f"Socket Connection Error: {msg}")


class ServerTimeOut(Exception):
    def __init__(self, msg: str = "Connection timed out.") -> None:
        super().__init__(msg)


class ServerError(Exception):
    def __init__(self, error: Any) -> None:
        super().__init__(f"Server Socket Error: {error}")


class ServerAuthError(Exception):
    def __init__(self, msg: str = "Server Auth Error, check the password.") -> None:
        super().__init__(msg)


class AddressError(Exception):
    def __init__(self, msg: str = "IP address and PORT is incorrect.") -> None:
        super().__init__(msg)


class PasswordError(Exception):
    def __init__(self, msg: str = "Password has not been provided or is incorrect.") -> None:
        super().__init__(msg)
