"""Контекстний request_id для кореляції логів.

Призначення:
    - Єдине джерело правди для request_id.
    - Доступний і з middleware, і з логера, і з тестів.

Використання:
    REQUEST_ID_VAR.set("abc-123")
    ...
    rid = REQUEST_ID_VAR.get()
"""

from __future__ import annotations

from contextvars import ContextVar

# Контекстна змінна: в межах одного запиту (асинхронного контексту)
# тримає ідентифікатор request_id.
REQUEST_ID_VAR: ContextVar[str | None] = ContextVar("request_id", default=None)
