"""
«Доктор» — прості перевірки стану системи.

Поточна версія:
    - Перевірка наявності базових конфігів.
    - Перевірка валідності DSN Postgres (поверхнево).
Наступні кроки:
    - Реальні ping-и до Postgres/Redis/S3.
    - Стан міграцій БД.
"""

from __future__ import annotations

from typing import Dict, List
import logging

from calculator_engine.config.settings import settings

logger = logging.getLogger("doctor")


def check_config() -> Dict:
    ok = bool(settings.app_name and settings.postgres_dsn and settings.redis_url)
    return {
        "name": "config",
        "status": "ok" if ok else "fail",
        "detail": "Основні налаштування присутні" if ok else "Відсутні ключові параметри",
    }


def check_postgres_configured() -> Dict:
    ok = settings.postgres_dsn.startswith("postgresql")
    return {
        "name": "postgres-config",
        "status": "ok" if ok else "warn",
        "detail": f"DSN: {settings.postgres_dsn}",
    }


def run_all_checks() -> Dict:
    checks: List[Dict] = [
        check_config(),
        check_postgres_configured(),
    ]
    if any(c["status"] == "fail" for c in checks):
        overall = "down"
    elif any(c["status"] == "warn" for c in checks):
        overall = "degraded"
    else:
        overall = "ok"

    logger.info("Doctor run result", extra={"context": {"overall": overall, "checks": checks}})
    return {"overall": overall, "checks": checks}
