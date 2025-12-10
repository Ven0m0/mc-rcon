# -*- coding: utf-8 -*-
"""
Audit logging module using high-performance JSON serialization with fallback.
"""

from pathlib import Path
from typing import Any

from mcrconpy.pathclass import PathClass

try:
    import orjson
except ImportError:
    import json

    class orjson:
        @staticmethod
        def dumps(obj: Any) -> bytes:
            return json.dumps(obj).encode("utf-8")

        @staticmethod
        def loads(obj: bytes | str) -> Any:
            return json.loads(obj)

        JSONDecodeError = json.JSONDecodeError


class Audit:
    """
    Handles audit logging to a JSONL file.
    """

    LOG_DIR: str = PathClass.user_log_dir("mcrconpy")
    FILE_PATH: Path = Path(LOG_DIR) / "audit.jsonl"

    @staticmethod
    def to_save(data: dict[str, Any]) -> None:
        """
        Appends a record to the audit log.

        Args:
            data: Dictionary to serialize and save.
        """
        Path(Audit.LOG_DIR).mkdir(parents=True, exist_ok=True)
        # orjson.dumps returns bytes.
        with open(Audit.FILE_PATH, "ab") as f:
            f.write(orjson.dumps(data) + b"\n")

    @staticmethod
    def to_load() -> list[dict[str, Any]]:
        """
        Loads all audit records from the log file.

        Returns:
            list[dict]: List of audit records.
        """
        if not Audit.FILE_PATH.exists():
            return []

        results = []
        try:
            with open(Audit.FILE_PATH, "rb") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        results.append(orjson.loads(line))
        except (orjson.JSONDecodeError, OSError, ValueError):
            # Gracefully handle corruption or IO errors
            pass
        return results
