"""Приклад простої доменної таблиці `materials`.

Призначення:
    - Демонстраційна модель для подальших прикладів (репозиторії, міграції).
    - Зберігання номенклатури матеріалів (код, назва, ціна за одиницю).

Зверніть увагу:
    - Numeric(10, 2) підходить для валют (зберігається як Decimal).
    - Для індексу на code використано index=True.
"""

from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from calculator_engine.adapters.db.base import Base, TimestampMixin


class Material(TimestampMixin, Base):
    """ORM-модель матеріалу (спрощена)."""

    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    price_per_unit: Mapped[Decimal] = mapped_column(Numeric(10, 2))
