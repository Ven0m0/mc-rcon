"""Platform-independent path utilities using platformdirs."""

from __future__ import annotations

from typing import cast

import platformdirs  # type: ignore[import-not-found]


class PathClass:
    """Minimal path utilities wrapper for platformdirs.

    This class provides cross-platform path resolution for user directories.
    For general path operations, use pathlib.Path directly.
    """

    @staticmethod
    def user_config_dir(name: str) -> str:
        """Get platform-specific user config directory.

        Args:
            name: Application name.

        Returns:
            str: Path to user config directory.
        """
        return cast(str, platformdirs.user_config_dir(name))

    @staticmethod
    def user_log_dir(name: str) -> str:
        """Get platform-specific user log directory.

        Args:
            name: Application name.

        Returns:
            str: Path to user log directory.
        """
        return cast(str, platformdirs.user_log_dir(name))

    @staticmethod
    def user_data_dir(name: str) -> str:
        """Get platform-specific user data directory.

        Args:
            name: Application name.

        Returns:
            str: Path to user data directory.
        """
        return cast(str, platformdirs.user_data_dir(name))


__all__ = ["PathClass"]
