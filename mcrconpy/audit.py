"""Audit logging module using high-performance orjson serialization."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator

from mcrconpy.pathclass import PathClass

try:
    import orjson  # type: ignore[import-not-found]

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False
    import json


class Audit:
    """JSONL audit logger with orjson optimization.

    Logs are stored as newline-delimited JSON (JSONL) for easy streaming
    and append-only operations. Uses orjson when available for 6x faster
    serialization compared to stdlib json.
    """

    LOG_DIR: str = PathClass.user_log_dir("mcrconpy")
    FILE_PATH: Path = Path(LOG_DIR) / "audit.jsonl"

    @staticmethod
    def to_save(data: dict[str, Any]) -> None:
        """Append a record to the audit log.

        Args:
            data: Dictionary to serialize and save as JSONL entry.

        Raises:
            OSError: If file cannot be written.
            TypeError: If data is not JSON-serializable.
        """
        try:
            Path(Audit.LOG_DIR).mkdir(parents=True, exist_ok=True)

            if HAS_ORJSON:
                serialized = orjson.dumps(data)
            else:
                serialized = json.dumps(data).encode("utf-8")

            with Path(Audit.FILE_PATH).open("ab") as f:
                f.write(serialized + b"\n")
        except (OSError, TypeError) as e:
            raise OSError(f"Failed to write audit log: {e}") from e

    @staticmethod
    def to_load_iter() -> Iterator[dict[str, Any]]:
        """Stream audit records one at a time (memory-efficient).

        Yields:
            dict: Individual audit record.

        Note:
            Gracefully handles corrupted lines by skipping them.
            This is the preferred method for large audit logs.
        """
        file_path = Path(Audit.FILE_PATH)
        if not file_path.exists():
            return

        try:
            with file_path.open("rb") as f:
                for line_bytes in f:
                    line_bytes = line_bytes.strip()
                    if not line_bytes:
                        continue

                    try:
                        if HAS_ORJSON:
                            record = orjson.loads(line_bytes)
                        else:
                            record = json.loads(line_bytes.decode("utf-8"))

                        if isinstance(record, dict):
                            yield record
                    except (ValueError, UnicodeDecodeError):
                        # Skip corrupted lines
                        continue
        except OSError:
            # Stop iteration on file read errors
            return

    @staticmethod
    def to_load() -> list[dict[str, Any]]:
        """Load all audit records from the log file.

        Returns:
            list[dict]: List of audit records. Returns empty list if file
                doesn't exist or contains invalid JSON.

        Warning:
            For large audit logs, prefer to_load_iter() to avoid loading
            all records into memory at once.

        Note:
            Gracefully handles corrupted lines by skipping them.
        """
        return list(Audit.to_load_iter())


__all__ = ["Audit"]
