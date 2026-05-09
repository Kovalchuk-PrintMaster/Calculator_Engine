# python -m settings.app_settings
"""
Centralized application settings loader.

Precedence (lowest → highest):
    1) Dataclass defaults in this module
    2) config/base.toml
    3) config/{ENV}.toml             # ENV from env var or default "dev"
    4) Environment variables (.env)  # highest priority

Використання:
    from settings.app_settings import settings as SET
    from config import paths as PATH
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field, replace
from typing import Any

# TOML reader (Python ≥ 3.11)
try:
    import tomllib
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Python >= 3.11 is required for tomllib") from exc

from .paths import CONFIG_DIR, PG_DSN, REDIS_URL  # дефолти з єдиного джерела


@dataclass(frozen=True)
class AppSettings:
    """Application settings.

    Attributes:
        env: "dev" | "prod" | "test".
        debug: Verbose/dev mode.
        app_name: Human-readable app name.

        postgres_dsn: SQLAlchemy/psycopg DSN for PostgreSQL.
        redis_url: Redis connection URL.
        s3_endpoint: S3-compatible endpoint.
        s3_bucket_backups: Bucket for DB backups/archives.

        cors_allow_origins: CORS allowlist (dev: ["*"]; звузити у проді).
    """

    # Core
    env: str = "dev"
    debug: bool = True
    app_name: str = "Calculator Engine"

    # Connections (дефолти беремо з paths.py)
    postgres_dsn: str = PG_DSN
    redis_url: str = REDIS_URL
    s3_endpoint: str = "https://s3.example.com"
    s3_bucket_backups: str = "calc-backups"

    # CORS
    cors_allow_origins: list[str] = field(default_factory=lambda: ["*"])


def _load_toml(path: str) -> dict[str, Any]:
    p = (CONFIG_DIR / path) if not str(path).startswith("/") else path
    try:
        with open(p, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    merged.update(override)
    return merged


def _apply_env_overrides(d: dict[str, Any]) -> dict[str, Any]:
    """Map environment vars to settings fields (highest priority)."""
    def _bool(val: str | None, default: bool) -> bool:
        if val is None:
            return default
        return val.strip().lower() in {"1", "true", "yes", "on"}

    out = dict(d)
    if "ENV" in os.environ:
        out["env"] = os.getenv("ENV", out.get("env", "dev"))
    if "DEBUG" in os.environ:
        out["debug"] = _bool(os.getenv("DEBUG"), out.get("debug", True))
    if "POSTGRES_DSN" in os.environ:
        out["postgres_dsn"] = os.getenv("POSTGRES_DSN", out.get("postgres_dsn", ""))
    if "REDIS_URL" in os.environ:
        out["redis_url"] = os.getenv("REDIS_URL", out.get("redis_url", ""))
    if "S3_ENDPOINT" in os.environ:
        out["s3_endpoint"] = os.getenv("S3_ENDPOINT", out.get("s3_endpoint", ""))
    if "S3_BUCKET_BACKUPS" in os.environ:
        out["s3_bucket_backups"] = os.getenv(
            "S3_BUCKET_BACKUPS",
            out.get("s3_bucket_backups", "")
        )
    return out


def load_settings() -> AppSettings:
    """Load settings with precedence: defaults < base.toml < {ENV}.toml < env vars."""
    merged = asdict(AppSettings())            # 1) defaults
    merged = _merge_dicts(merged, _load_toml("base.toml"))  # 2) base.toml
    env_name = os.getenv("ENV", merged.get("env", "dev"))
    merged = _merge_dicts(merged, _load_toml(f"{env_name}.toml"))  # 3) env.toml
    merged = _apply_env_overrides(merged)     # 4) env vars
    return replace(AppSettings(), **merged)


# Eager instance
settings = load_settings()
