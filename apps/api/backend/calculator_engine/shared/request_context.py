"""
Контекстні змінні запиту.

Завдання:
    - Зберігати request_id впродовж обробки одного запиту (ASGI).
    - Дати доступ логуванню для додавання request_id у кожен запис.

Чому ContextVar:
    - Безпечний для async/await.
    - Не потребує прокидання параметрів через усі функції вручну.
"""

from __future__ import annotations
import contextvars
from typing import Optional

# Головна контекстна змінна для ідентифікатора запиту
REQUEST_ID_VAR: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
