"""Tests for RCON packet handling."""

from __future__ import annotations

import struct

import pytest

from mcrconpy.core import Packet
from mcrconpy.exceptions import ErrorParameter


def test_packet_build_with_string() -> None:
    """Test building packet with string data."""
    packet = Packet.build(123, Packet.SERVERDATA_AUTH, "password")

    assert isinstance(packet, bytes)
    assert len(packet) > 0

    # Verify structure
    length, req_id, pkt_type = struct.unpack("<iii", packet[:12])
    assert req_id == 123
    assert pkt_type == Packet.SERVERDATA_AUTH


def test_packet_build_with_bytes() -> None:
    """Test building packet with bytes data."""
    packet = Packet.build(456, Packet.SERVERDATA_EXECCOMMAND, b"list")

    assert isinstance(packet, bytes)

    length, req_id, pkt_type = struct.unpack("<iii", packet[:12])
    assert req_id == 456
    assert pkt_type == Packet.SERVERDATA_EXECCOMMAND


def test_packet_build_invalid_req_id() -> None:
    """Test that negative req_id raises error."""
    with pytest.raises(ErrorParameter, match="positive integer"):
        Packet.build(-1, Packet.SERVERDATA_AUTH, "data")


def test_packet_build_invalid_data_type() -> None:
    """Test that invalid data type raises error."""
    with pytest.raises(ErrorParameter, match="string or bytes"):
        Packet.build(1, Packet.SERVERDATA_AUTH, 12345)  # type: ignore[arg-type]


def test_packet_read_length() -> None:
    """Test reading packet length."""
    # Create a valid length header (14 bytes = minimal packet)
    length_bytes = struct.pack("<i", 14)

    length = Packet.read_length(length_bytes)
    assert length == 14


def test_packet_read_length_invalid() -> None:
    """Test reading invalid packet length."""
    # Too short
    length = Packet.read_length(b"\x00\x00")
    assert length == 0

    # Malformed
    length = Packet.read_length(b"")
    assert length == 0


def test_packet_decode() -> None:
    """Test decoding valid packet."""
    # Build a packet first
    original_packet = Packet.build(789, Packet.SERVERDATA_RESPONSE_VALUE, "response")

    # Decode it
    length, req_id, pkt_type, body = Packet.decode(original_packet)

    assert req_id == 789
    assert pkt_type == Packet.SERVERDATA_RESPONSE_VALUE
    assert body == "response"


def test_packet_decode_invalid_too_short() -> None:
    """Test decoding packet that's too short."""
    result = Packet.decode(b"\x00" * 10)
    assert result == ()


def test_packet_decode_invalid_data() -> None:
    """Test decoding corrupted packet."""
    result = Packet.decode(b"\xff" * 20)
    assert result == ()


def test_packet_constants() -> None:
    """Test that packet type constants are defined."""
    assert Packet.SERVERDATA_AUTH == 3
    assert Packet.SERVERDATA_EXECCOMMAND == 2
    assert Packet.SERVERDATA_RESPONSE_VALUE == 0
