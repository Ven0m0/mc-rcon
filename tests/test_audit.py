"""Tests for audit logging."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from mcrconpy.audit import Audit


@pytest.fixture
def temp_audit_file(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create temporary audit file for testing."""
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / "test_audit.jsonl"

    # Monkey patch the Audit class to use temp file
    monkeypatch.setattr(Audit, "LOG_DIR", temp_dir)
    monkeypatch.setattr(Audit, "FILE_PATH", temp_file)

    yield temp_file

    # Cleanup
    if temp_file.exists():
        temp_file.unlink()
    Path(temp_dir).rmdir()


def test_audit_save_and_load(temp_audit_file: Path) -> None:
    """Test saving and loading audit records."""
    # Save records
    Audit.to_save({"command": "list", "timestamp": 123.456})
    Audit.to_save({"command": "say Hello", "timestamp": 789.012})

    # Load records
    records = Audit.to_load()

    assert len(records) == 2
    assert records[0]["command"] == "list"
    assert records[0]["timestamp"] == 123.456
    assert records[1]["command"] == "say Hello"


def test_audit_load_nonexistent_file(temp_audit_file: Path) -> None:
    """Test loading when file doesn't exist."""
    records = Audit.to_load()
    assert records == []


def test_audit_save_creates_directory(
    temp_audit_file: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that directory is created if it doesn't exist."""
    new_dir = temp_audit_file.parent / "subdir"
    new_file = new_dir / "audit.jsonl"

    monkeypatch.setattr(Audit, "LOG_DIR", str(new_dir))
    monkeypatch.setattr(Audit, "FILE_PATH", new_file)

    Audit.to_save({"test": "data"})

    assert new_dir.exists()
    assert new_file.exists()

    # Cleanup
    new_file.unlink()
    new_dir.rmdir()


def test_audit_handles_corrupted_lines(temp_audit_file: Path) -> None:
    """Test that corrupted lines are skipped gracefully."""
    # Write some valid and invalid JSON
    with temp_audit_file.open("w") as f:
        f.write('{"valid": "record1"}\n')
        f.write("invalid json here\n")
        f.write('{"valid": "record2"}\n')

    records = Audit.to_load()

    # Should only load valid records
    assert len(records) == 2
    assert records[0]["valid"] == "record1"
    assert records[1]["valid"] == "record2"
