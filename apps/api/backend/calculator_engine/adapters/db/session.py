"""Сесії SQLAlchemy та залежність FastAPI get_db().

Призначення:
    - Надати SessionLocal (sessionmaker) для транзакційної роботи.
    - Зручний context manager і залежність FastAPI для роутерів.

Правила:
    - expire_on_commit=False — об'єкти після commit не "протухають".
    - Весь контроль транзакції в одному місці: commit/rollback/close.
"""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from calculator_engine.adapters.db.engine import get_engine

# Створюємо фабрику сесій поверх загального Engine.
SessionLocal = sessionmaker(
    bind=get_engine(), autoflush=False, autocommit=False, expire_on_commit=False
)


@contextmanager
def db_session() -> Generator[Session, None, None]:
    """Контекстний менеджер для ручного користування поза FastAPI.

    Приклад:
        with db_session() as s:
            s.add(obj)
            ...
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """Залежність FastAPI: віддає сесію на запит і коректно її закриває."""
    with db_session() as s:
        yield s
