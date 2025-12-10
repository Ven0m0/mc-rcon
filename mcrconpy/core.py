# -*- coding: utf-8 -*-
"""
Core RCON implementation.
Consolidates packet handling, connection management, and client logic.
Includes both Synchronous and Asynchronous clients.
"""

from __future__ import annotations

import argparse
import asyncio
import enum
import os
import random
import socket
import struct
import sys
import typing as t
from types import TracebackType
from typing import Optional, Any

# --- Exceptions ---


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


# --- Packet Handling ---


class Packet:
    """
    RCON Packet Structure and handling.
    """

    SERVERDATA_RESPONSE_VALUE: int = 0
    SERVERDATA_EXECCOMMAND: int = 2
    SERVERDATA_AUTH: int = 3
    _PAD: bytes = b"\x00\x00"

    @staticmethod
    def build(req_id: int, packet_type: int, data: str | bytes) -> bytes:
        """Constructs an RCON packet."""
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
        """Reads the length field from the start of a packet header."""
        if len(data) < 4:
            return 0
        try:
            return struct.unpack("<i", data[:4])[0]
        except struct.error:
            return 0

    @staticmethod
    def decode(data: bytes) -> tuple[int, int, int, str]:
        """Decodes raw packet bytes."""
        if len(data) < 14:
            return ()  # type: ignore

        try:
            length, req_id, packet_type = struct.unpack("<iii", data[:12])
            body_bytes = data[12:-2]
            body = body_bytes.decode("ascii")
            return length, req_id, packet_type, body
        except (struct.error, UnicodeDecodeError):
            return ()  # type: ignore


# --- Synchronous Client ---


class Rcon:
    """
    Synchronous RCON Client.
    """

    def __init__(self, address: str, port: int, password: str) -> None:
        self.address = address
        self.port = port
        self.password = password
        self.socket: Optional[socket.socket] = None
        self._logged_in = False

    def connect(self) -> None:
        """Establishes connection."""
        try:
            self.socket = socket.create_connection((self.address, self.port), timeout=10)
        except socket.timeout:
            raise ServerTimeOut()
        except socket.error as e:
            raise ServerError(e)

    def login(self) -> bool:
        """Authenticates with the server."""
        if self.socket is None:
            raise SocketConnectionError("Not connected.")

        packet = Packet.build(
            req_id=random.randint(0, 2147483647), packet_type=Packet.SERVERDATA_AUTH, data=self.password
        )

        self.socket.sendall(packet)

        # Read response
        # 1. Read Length (4 bytes)
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

    def command(self, cmd: str) -> Optional[str]:
        """Sends a command and waits for response."""
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
        """Helper to receive exact bytes."""
        data = b""
        while len(data) < n:
            chunk = self.socket.recv(n - len(data))
            if not chunk:
                break
            data += chunk
        return data

    def is_login(self) -> bool:
        return self._logged_in

    def close(self) -> None:
        if self.socket:
            self.socket.close()
            self.socket = None
        self._logged_in = False

    def __enter__(self) -> "Rcon":
        self.connect()
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


# --- Asynchronous Client ---


class MessageType(enum.IntEnum):
    LOGIN = 3
    COMMAND = 2
    RESPONSE = 0


class AsyncRcon:
    """
    Asynchronous RCON Client (optimized).
    """

    def __init__(self, host: str, port: int, password: str) -> None:
        self.host = host
        self.port = port
        self.password = password
        self._reader: t.Optional[asyncio.StreamReader] = None
        self._writer: t.Optional[asyncio.StreamWriter] = None
        self._ready = False

    async def __aenter__(self) -> "AsyncRcon":
        await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: t.Optional[type[BaseException]],
        exc: t.Optional[BaseException],
        tb: t.Optional[t.Any],
    ) -> None:
        await self.close()

    async def connect(self, timeout: float = 2.0) -> None:
        if self._ready:
            return
        try:
            self._reader, self._writer = await asyncio.wait_for(asyncio.open_connection(self.host, self.port), timeout)
        except (asyncio.TimeoutError, TimeoutError):
            raise ServerTimeOut("Connection timed out.")
        except Exception as e:
            raise SocketConnectionError(f"Connection failed: {e}")

        # Login
        await asyncio.wait_for(self._send_msg(MessageType.LOGIN, self.password), timeout)
        self._ready = True

    async def command(self, cmd: str, timeout: float = 2.0) -> str:
        if not self._ready:
            raise SocketConnectionError("Not connected")
        if len(cmd) > 1446:
            raise ValueError("Command too long.")

        msg, _ = await asyncio.wait_for(self._send_msg(MessageType.COMMAND, cmd), timeout)
        return msg

    async def _read_exact(self, n: int) -> bytes:
        if not self._reader:
            raise SocketConnectionError("Not connected")
        try:
            return await self._reader.readexactly(n)
        except asyncio.IncompleteReadError:
            raise SocketConnectionError("Connection closed unexpectedly.")

    async def _send_msg(self, msg_type: int, msg: str) -> tuple[str, int]:
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
        if self._writer:
            self._writer.close()
            try:
                await self._writer.wait_closed()
            except Exception:
                pass
        self._reader = None
        self._writer = None
        self._ready = False


# --- CLI Main ---


def main() -> None:
    parser = argparse.ArgumentParser(description="RCON Client")
    parser.add_argument("-a", "--address", required=True, help="Server Address")
    parser.add_argument("-p", "--port", type=int, default=25575, help="RCON Port")
    parser.add_argument("-P", "--password", required=True, help="RCON Password")
    parser.add_argument("--async-mode", action="store_true", help="Use Async Client")

    args = parser.parse_args()

    if args.async_mode:
        asyncio.run(_async_main(args))
    else:
        _sync_main(args)


def _sync_main(args):
    try:
        with Rcon(args.address, args.port, args.password) as client:
            print(f"Connected to {args.address}:{args.port} (Sync)")
            while True:
                try:
                    cmd = input(">>")
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


async def _async_main(args):
    try:
        async with AsyncRcon(args.address, args.port, args.password) as client:
            print(f"Connected to {args.address}:{args.port} (Async)")
            # Simple async REPL logic (blocking input is tricky in pure async without libs)
            # For simplicity, we'll use a thread executor for input or just blocking input
            # since this is a basic CLI wrapper.
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


if __name__ == "__main__":
    main()
