"""Internal adapter over top-level app settings.

Purpose:
    Hide direct dependency on `settings.app_settings` from the rest of the
    `calculator_engine` package.

Why:
    - reduces coupling between package code and project-level settings layout;
    - makes future migration of settings source simpler;
    - gives one canonical import path inside the package.
"""

from __future__ import annotations

from typing import Final

from settings.app_settings import settings as _settings


class AppConfigAdapter:
    """Thin read-only adapter over external app settings."""

    @property
    def app_name(self) -> str:
        return _settings.app_name

    @property
    def env(self) -> str:
        return _settings.env

    @property
    def postgres_dsn(self) -> str:
        return _settings.postgres_dsn

    @property
    def redis_url(self) -> str:
        return _settings.redis_url

    @property
    def debug(self) -> bool:
        return _settings.debug


app_config: Final[AppConfigAdapter] = AppConfigAdapter()

__all__ = ["AppConfigAdapter", "app_config"]