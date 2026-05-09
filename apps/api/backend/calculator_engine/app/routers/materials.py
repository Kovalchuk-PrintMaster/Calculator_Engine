"""Роутер для роботи з каталогом матеріалів (/materials).

Поточна мета (мінімальний крок):
    - Повернути порожній список з БД (якщо таблиця порожня).
    - Переконатися, що таблиця існує (після міграцій).
    - Дати людинозрозумілу помилку, якщо міграції не виконані.

Нотатка:
    Тут свідомо не визначаємо ORM-модель і не серіалізуємо рядки з таблиці —
    ми лише "пінгуємо" наявність таблиці й повертаємо []. Наступним кроком
    додамо Pydantic-схеми й ORM-модель під реальні колонки.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from calculator_engine.adapters.db.engine import get_engine

router = APIRouter(prefix="/materials", tags=["materials"])


@router.get("", summary="Список матеріалів (мінімальний скелет)")
def list_materials() -> list[dict]:
    """Повертає список матеріалів.

    Поточна реалізація:
        - Перевіряє, що таблиця `materials` існує і до неї можна звернутися.
        - НЕ читає реальні рядки, а повертає порожній список.
        - Якщо міграцію ще не прогнали — віддає 503 з підказкою.
    """
    eng = get_engine()
    try:
        with eng.connect() as conn:
            # Легка перевірка: якщо таблиця є — SELECT 1 LIMIT 1 відпрацює.
            conn.exec_driver_sql("SELECT 1 FROM materials LIMIT 1")
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Таблиця 'materials' недоступна. Переконайтесь, що виконано міграції "
                f"(make alembic-up). Помилка: {exc}"
            ),
        ) from exc
    # На цьому кроці навмисно повертаємо порожній список — API вже стабільне.
    return []
