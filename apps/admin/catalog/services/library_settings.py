from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LibrarySettings:
    base_url: str
    token: str
    timeout_seconds: float
    verify_ssl: bool


def _as_bool(value: str | None, *, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_library_settings() -> LibrarySettings:
    return LibrarySettings(
        base_url=os.getenv("CALC_LIBRARY_BASE_URL", "").strip().rstrip("/"),
        token=os.getenv("CALC_LIBRARY_TOKEN", "").strip(),
        timeout_seconds=float(os.getenv("CALC_LIBRARY_TIMEOUT_SECONDS", "10")),
        verify_ssl=_as_bool(
            os.getenv("CALC_LIBRARY_VERIFY_SSL"),
            default=True,
        ),
    )