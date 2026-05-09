"""Базові класи для ORM (SQLAlchemy 2.0).

Призначення:
    - Єдиний Declarative Base для всіх моделей.
    - Універсальні міксини (напр., мітки часу).

Чому так:
    - Окремий модуль полегшує імпорти (щоб уникати циклів).
    - Можна централізовано додавати загальні поля/поведінку.
"""

from __future__ import annotations

from datetime import datetime
from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Спільний базовий клас для всіх ORM-моделей."""


class TimestampMixin:
    """Міксин для автоматичних часових міток.

    Поля:
        created_at: коли запис створено (за замовчуванням now()).
        updated_at: коли запис востаннє змінено (оновлюється автоматично).
    """

    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )
