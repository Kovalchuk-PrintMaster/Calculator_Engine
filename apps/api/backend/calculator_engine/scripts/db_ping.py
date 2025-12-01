"""Перевірка доступності БД (ping) з виводом людиночитного статусу.

Виклик:
    python -m calculator_engine.scripts.db_ping
"""

from __future__ import annotations

import sys

from calculator_engine.config.settings import settings
from calculator_engine.django_infra.db.engine import ping_db


def main() -> int:
    dsn = settings.postgres_dsn
    try:
        ping_db(dsn=dsn)
        print(f"DB OK -> {dsn}")
        return 0
    except Exception as exc:
        print(f"DB DOWN: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
