"""Core RCON implementation with sync and async clients.

This module provides both synchronous and asynchronous RCON clients
following the Source RCON Protocol specification.
"""

from __future__ import annotations

import argparse
import asyncio
import enum
import random
import socket
import struct
from contextlib import suppress
from typing import Any, cast

from mcrconpy.exceptions import (
    ErrorParameter,
    ServerAuthError,
    ServerError,
    ServerTimeOut,
    SocketConnectionError,
)

# --- Packet Handling ---


class Packet:
    """RCON packet builder and decoder.

    Implements the Source RCON Protocol packet format:
    - Size (int32): Packet length excluding this field
    - ID (int32): Request identifier
    - Type (int32): Packet type (AUTH=3, EXECCOMMAND=2, RESPONSE=0)
    - Body (null-terminated ASCII string)
    - Padding (null byte)
    """

    SERVERDATA_RESPONSE_VALUE: int = 0
    SERVERDATA_EXECCOMMAND: int = 2
    SERVERDATA_AUTH: int = 3
    _PAD: bytes = b"\x00\x00"

    @staticmethod
    def build(req_id: int, packet_type: int, data: str | bytes) -> bytes:
        """Build an RCON packet from components.

        Args:
            req_id: Request ID (0 to 2147483647).
            packet_type: Packet type constant.
            data: Payload as string or bytes.

        Returns:
            bytes: Complete RCON packet ready for transmission.

        Raises:
            ErrorParameter: If parameters are invalid.
        """
        if not isinstance(req_id, int) or req_id < 0:
            raise ErrorParameter("`req_id` must be a positive integer.")
        if not isinstance(packet_type, int):
            raise ErrorParameter("`packet_type` must be an integer.")

        payload: bytes
        if isinstance(data, str):
            payload = data.encode("ascii")
        elif isinstance(data, bytes):
            payload = data
        else:
            raise ErrorParameter("`data` must be string or bytes.")

        # Length = 4 (ID) + 4 (Type) + Len(Body) + 2 (Pad)
        length = 10 + len(payload)
        header = struct.pack("<iii", length, req_id, packet_type)
        return header + payload + Packet._PAD

    @staticmethod
    def read_length(data: bytes) -> int:
        """Extract packet length from header.

        Args:
            data: First 4 bytes of packet.

        Returns:
            int: Packet length or 0 if invalid.
        """
        if len(data) < 4:
            return 0
        try:
            return cast(int, struct.unpack("<i", data[:4])[0])
        except struct.error:
            return 0

    @staticmethod
    def decode(data: bytes) -> tuple[int, int, int, str]:
        """Decode raw packet bytes into components.

        Args:
            data: Complete packet data.

        Returns:
            tuple: (length, request_id, packet_type, body) or empty tuple
                if decoding fails.
        """
        if len(data) < 14:
            return ()  # type: ignore[return-value]

        try:
            length, req_id, packet_type = struct.unpack("<iii", data[:12])
            body_bytes = data[12:-2]
            body = body_bytes.decode("ascii")
            return length, req_id, packet_type, body
        except (struct.error, UnicodeDecodeError):
            return ()  # type: ignore[return-value]


# --- Synchronous Client ---


class Rcon:
    """Synchronous RCON client with context manager support.

    Example:
        >>> with Rcon("localhost", 25575, "password") as client:
        ...     response = client.command("list")
        ...     print(response)
    """

    def __init__(self, address: str, port: int, password: str) -> None:
        """Initialize RCON client.

        Args:
            address: Server hostname or IP address.
            port: RCON port number.
            password: RCON password.
        """
        self.address = address
        self.port = port
        self.password = password
        self.socket: socket.socket | None = None
        self._logged_in = False

    def connect(self) -> None:
        """Establish TCP connection to server.

        Raises:
            ServerTimeOut: If connection times out.
            ServerError: If socket error occurs.
        """
        try:
            self.socket = socket.create_connection(
                (self.address, self.port), timeout=10
            )
        except TimeoutError as e:
            raise ServerTimeOut() from e
        except OSError as e:
            raise ServerError(e) from e

    def login(self) -> bool:
        """Authenticate with server.

        Returns:
            bool: True if authentication successful.

        Raises:
            SocketConnectionError: If not connected.
            ServerAuthError: If authentication fails.
        """
        if self.socket is None:
            raise SocketConnectionError("Not connected.")

        packet = Packet.build(
            req_id=random.randint(0, 2147483647),
            packet_type=Packet.SERVERDATA_AUTH,
            data=self.password,
        )

        self.socket.sendall(packet)

        # Read response
        length_bytes = self._recv_exact(4)
        if not length_bytes:
            raise SocketConnectionError("Connection closed during login.")

        length = Packet.read_length(length_bytes)
        payload = self._recv_exact(length)

        full_data = length_bytes + payload
        _, req_id, type_, body = Packet.decode(full_data)

        if req_id == -1:
            self._logged_in = False
            raise ServerAuthError("Authentication failed.")

        self._logged_in = True
        return True

    def command(self, cmd: str) -> str | None:
        """Send command and receive response.

        Args:
            cmd: Command to execute on server.

        Returns:
            str | None: Server response or None if not connected/error.
        """
        if not self._logged_in or self.socket is None:
            return None

        req_id = random.randint(0, 2147483647)
        packet = Packet.build(req_id, Packet.SERVERDATA_EXECCOMMAND, cmd)

        try:
            self.socket.sendall(packet)

            # Read response
            length_bytes = self._recv_exact(4)
            if not length_bytes:
                raise SocketConnectionError("Connection closed.")

            length = Packet.read_length(length_bytes)
            payload = self._recv_exact(length)

            _, rid, type_, body = Packet.decode(length_bytes + payload)
            return body
        except Exception:
            return None

    def _recv_exact(self, n: int) -> bytes:
        """Receive exact number of bytes from socket.

        Args:
            n: Number of bytes to receive.

        Returns:
            bytes: Received data (may be less than n if connection closed).
        """
        if self.socket is None:
            return b""

        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def is_login(self) -> bool:
        """Check if client is authenticated.

        Returns:
            bool: True if logged in.
        """
        return self._logged_in

    def close(self) -> None:
        """Close connection and reset state."""
        if self.socket:
            self.socket.close()
            self.socket = None
        self._logged_in = False

    def __enter__(self) -> Rcon:
        """Context manager entry: connect and login."""
        self.connect()
        self.login()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit: close connection."""
        self.close()


# --- Asynchronous Client ---


class MessageType(enum.IntEnum):
    """RCON message type constants."""

    LOGIN = 3
    COMMAND = 2
    RESPONSE = 0


class AsyncRcon:
    """Asynchronous RCON client with uvloop support.

    Example:
        >>> async with AsyncRcon("localhost", 25575, "password") as client:
        ...     response = await client.command("list")
        ...     print(response)
    """

    def __init__(self, host: str, port: int, password: str) -> None:
        """Initialize async RCON client.

        Args:
            host: Server hostname or IP address.
            port: RCON port number.
            password: RCON password.
        """
        self.host = host
        self.port = port
        self.password = password
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None
        self._ready = False

    async def __aenter__(self) -> AsyncRcon:
        """Async context manager entry: connect and login."""
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: Any,
    ) -> None:
        """Async context manager exit: close connection."""
        await self.close()

    async def connect(self, timeout: float = 2.0) -> None:
        """Establish connection and authenticate.

        Args:
            timeout: Connection timeout in seconds.

        Raises:
            ServerTimeOut: If connection times out.
            SocketConnectionError: If connection fails.
        """
        if self._ready:
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(
                asyncio.open_connection(self.host, self.port), timeout
            )
        except (asyncio.TimeoutError, TimeoutError) as e:
            raise ServerTimeOut("Connection timed out.") from e
        except Exception as e:
            raise SocketConnectionError(f"Connection failed: {e}") from e

        # Login
        await asyncio.wait_for(
            self._send_msg(MessageType.LOGIN, self.password), timeout
        )
        self._ready = True

    async def command(self, cmd: str, timeout: float = 2.0) -> str:
        """Send command and receive response.

        Args:
            cmd: Command to execute on server.
            timeout: Command timeout in seconds.

        Returns:
            str: Server response.

        Raises:
            SocketConnectionError: If not connected.
            ValueError: If command exceeds maximum length.
        """
        if not self._ready:
            raise SocketConnectionError("Not connected")
        if len(cmd) > 1446:
            raise ValueError("Command too long.")

        msg, _ = await asyncio.wait_for(
            self._send_msg(MessageType.COMMAND, cmd), timeout
        )
        return msg

    async def _read_exact(self, n: int) -> bytes:
        """Read exact number of bytes from stream.

        Args:
            n: Number of bytes to read.

        Returns:
            bytes: Received data.

        Raises:
            SocketConnectionError: If connection closed or not established.
        """
        if not self._reader:
            raise SocketConnectionError("Not connected")
        try:
            return await self._reader.readexactly(n)
        except asyncio.IncompleteReadError as e:
            raise SocketConnectionError("Connection closed unexpectedly.") from e

    async def _send_msg(self, msg_type: int, msg: str) -> tuple[str, int]:
        """Send message and receive response.

        Args:
            msg_type: Message type constant.
            msg: Message payload.

        Returns:
            tuple: (response_body, request_id).

        Raises:
            SocketConnectionError: If not connected.
            ServerAuthError: If authentication fails.
        """
        if not self._writer:
            raise SocketConnectionError("Not connected")

        req_id = random.randint(0, 2147483647)
        packet = Packet.build(req_id, int(msg_type), msg)

        self._writer.write(packet)
        await self._writer.drain()

        # Read length (4 bytes)
        length_bytes = await self._read_exact(4)
        length = Packet.read_length(length_bytes)

        # Read body
        data_bytes = await self._read_exact(length)

        _, rid, type_, body = Packet.decode(length_bytes + data_bytes)

        if rid == -1:
            raise ServerAuthError("Authentication failed.")

        return body, rid

    async def close(self) -> None:
        """Close connection and reset state."""
        if self._writer:
            self._writer.close()
            with suppress(Exception):
                await self._writer.wait_closed()
        self._reader = None
        self._writer = None
        self._ready = False


# --- CLI Main ---


def main() -> None:
    """CLI entry point for mcrcon command."""
    parser = argparse.ArgumentParser(description="RCON Client for Minecraft")
    parser.add_argument("-a", "--address", required=True, help="Server Address")
    parser.add_argument("-p", "--port", type=int, default=25575, help="RCON Port")
    parser.add_argument("-P", "--password", required=True, help="RCON Password")
    parser.add_argument("--async-mode", action="store_true", help="Use Async Client")

    args = parser.parse_args()

    if args.async_mode:
        asyncio.run(_async_main(args))
    else:
        _sync_main(args)


def _sync_main(args: argparse.Namespace) -> None:
    """Run synchronous REPL."""
    try:
        with Rcon(args.address, args.port, args.password) as client:
            print(f"Connected to {args.address}:{args.port} (Sync)")
            while True:
                try:
                    cmd = input(">> ")
                    if cmd.lower() in ("exit", "quit", "q"):
                        break
                    resp = client.command(cmd)
                    if resp:
                        print(resp)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
    except Exception as e:
        print(f"Error: {e}")


async def _async_main(args: argparse.Namespace) -> None:
    """Run asynchronous REPL."""
    try:
        async with AsyncRcon(args.address, args.port, args.password) as client:
            print(f"Connected to {args.address}:{args.port} (Async)")
            loop = asyncio.get_running_loop()
            while True:
                try:
                    cmd = await loop.run_in_executor(None, input, ">> ")
                    if cmd.lower() in ("exit", "quit", "q"):
                        break
                    resp = await client.command(cmd)
                    if resp:
                        print(resp)
                except KeyboardInterrupt:
                    print("\nExiting...")
                    break
    except Exception as e:
        print(f"Error: {e}")


__all__ = ["Packet", "Rcon", "AsyncRcon", "MessageType", "main"]


if __name__ == "__main__":
    main()
