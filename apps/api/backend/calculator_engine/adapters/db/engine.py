"""Фабрика підключення до БД (SQLAlchemy Engine) + утиліта ping_db.

Призначення:
    - Ліниво (on-demand) створювати Engine за DSN із settings.postgres_dsn.
    - Єдине місце налаштувань пулу з'єднань.
    - Перевірити доступність БД через простий ping (SELECT 1).

Чому так:
    - Не створюємо Engine на імпорті (щоб тести без БД не падали).
    - ping_db() можна викликати як із переданим Engine, так і з DSN/дефолтним Engine.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

from calculator_engine.shared.config import app_config

_engine: Optional[Engine] = None


def make_engine(dsn: Optional[str] = None) -> Engine:
    """Створити новий Engine.

    Параметри:
        dsn: рядок з'єднання, за замовчуванням беремо з settings.postgres_dsn.

    Налаштування:
        - QueuePool з невеликими лімітами (стартово).
        - pool_pre_ping=True — автоматично перевіряє "живість" конекшенів.
        - future=True — сучасний API SQLAlchemy 2.0.
        - echo=settings.debug — вивід SQL при DEBUG-режимі.
    """
    url = dsn or app_config.postgres_dsn
    engine = create_engine(
        url,
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
        future=True,
        echo=app_config.debug
    )
    return engine


def get_engine() -> Engine:
    """Повернути (або створити) singleton Engine для процесу."""
    global _engine
    if _engine is None:
        _engine = make_engine()
    return _engine


def ping_db(
    engine: Optional[Engine] = None,
    *,
    dsn: Optional[str] = None,
) -> bool:
    """Перевірити доступність БД простою командою SELECT 1.

    Використання:
        - ping_db()                  -> використовує get_engine()
        - ping_db(dsn="...")         -> створює temp Engine і пінгує
        - ping_db(engine=some_engine)-> використовує переданий Engine

    Повертає:
        True, якщо запит виконано успішно.
    Підіймає:
        Будь-який виняток SQLAlchemy/драйвера — якщо БД недоступна.
    """
    eng = engine or (make_engine(dsn) if dsn else get_engine())
    # exec_driver_sql("SELECT 1") — прямий виклик драйвера, без текстових компіляцій.
    with eng.connect() as conn:
        conn.exec_driver_sql("SELECT 1")
    return True
