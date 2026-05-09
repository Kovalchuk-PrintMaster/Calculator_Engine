"""Internal adapter over top-level project paths.

Purpose:
    Hide direct dependency on `settings.paths` from the rest of the
    `calculator_engine` package.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from settings.paths import LOGS_DIR as _LOGS_DIR


class AppPathsAdapter:
    """Thin read-only adapter over external project paths."""

    @property
    def logs_dir(self) -> Path:
        return _LOGS_DIR


app_paths: Final[AppPathsAdapter] = AppPathsAdapter()

__all__ = ["AppPathsAdapter", "app_paths"]
