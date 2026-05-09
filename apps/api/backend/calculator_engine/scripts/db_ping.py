"""Перевірка доступності БД (ping) з виводом людиночитного статусу.

Виклик:
    python -m calculator_engine.scripts.db_ping
"""

from __future__ import annotations

from calculator_engine.adapters.db.engine import ping_db
from calculator_engine.shared.config import app_config


def main() -> int:
    dsn = app_config.postgres_dsn
    try:
        ping_db(dsn=dsn)
        print(f"DB OK -> {dsn}")
        return 0
    except Exception as exc:
        print(f"DB DOWN: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
