"""
Centralized application settings loader.

Precedence (lowest → highest):
    1) Dataclass defaults in this module
    2) config/base.toml
    3) config/{ENV}.toml             # ENV from env var or default "dev"
    4) Environment variables (.env)  # highest priority

We start with stdlib (tomllib + os.getenv) to keep bootstrap minimal.
Later we can swap to pydantic-settings without changing this public API.
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field, replace  # <-- field added
from typing import Any

# Standard TOML reader (Python ≥ 3.11)
try:
    import tomllib  # Python 3.11+
except Exception as exc:  # pragma: no cover
    raise RuntimeError("Python >= 3.11 is required for tomllib") from exc

from .paths import CONFIG_DIR  # central directory resolver


@dataclass(frozen=True)
class AppSettings:
    """Application settings.

    Attributes:
        env: Environment name: "dev" | "prod" | "test".
        debug: Verbose/dev mode.
        app_name: Human-readable app name.

        postgres_dsn: SQLAlchemy DSN for PostgreSQL.
        redis_url: Redis connection URL.
        s3_endpoint: S3-compatible endpoint.
        s3_bucket_backups: Bucket for DB backups/archives.

        cors_allow_origins: List of allowed origins for CORS (browser clients).
            Default "*" for dev; restrict in production (e.g., ["https://app.example.com"]).
    """

    # Core
    env: str = "dev"
    debug: bool = True
    app_name: str = "Calculator Engine"

    # Connections
    postgres_dsn: str = "postgresql+psycopg://user:pass@localhost:5432/app"
    redis_url: str = "redis://localhost:6379/0"
    s3_endpoint: str = "https://s3.example.com"
    s3_bucket_backups: str = "calc-backups"

    # CORS (dev default "*"; lock down in prod)
    cors_allow_origins: list[str] = field(default_factory=lambda: ["*"])


def _load_toml(path: str) -> dict[str, Any]:
    """Load TOML file if exists; return {} otherwise."""
    p = (CONFIG_DIR / path) if not str(path).startswith("/") else path
    try:
        with open(p, "rb") as fh:
            return tomllib.load(fh)
    except FileNotFoundError:
        return {}


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Shallow merge: override replaces base."""
    merged = dict(base)
    merged.update(override)
    return merged


def _apply_env_overrides(d: dict[str, Any]) -> dict[str, Any]:
    """Map env vars to settings fields (highest priority).

    Mapping:
        ENV               -> env
        DEBUG             -> debug (bool)
        POSTGRES_DSN      -> postgres_dsn
        REDIS_URL         -> redis_url
        S3_ENDPOINT       -> s3_endpoint
        S3_BUCKET_BACKUPS -> s3_bucket_backups

    NOTE:
        We intentionally do not parse list env vars for CORS here to keep
        bootstrap simple. If needed later, support CSV like:
            CORS_ALLOW_ORIGINS=https://a.com,https://b.com
    """

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
        out["s3_bucket_backups"] = os.getenv("S3_BUCKET_BACKUPS", out.get("s3_bucket_backups", ""))
    return out


def load_settings() -> AppSettings:
    """Load settings with precedence: defaults < base.toml < {ENV}.toml < env vars."""
    # 1) defaults (safe baseline)
    merged = asdict(AppSettings())

    # 2) base.toml (shared defaults)
    merged = _merge_dicts(merged, _load_toml("base.toml"))

    # 3) {ENV}.toml (environment-specific overrides)
    env_name = os.getenv("ENV", merged.get("env", "dev"))
    merged = _merge_dicts(merged, _load_toml(f"{env_name}.toml"))

    # 4) environment variables (highest priority)
    merged = _apply_env_overrides(merged)

    # Return frozen dataclass instance
    return replace(AppSettings(), **merged)


# Eager global instance
settings = load_settings()
