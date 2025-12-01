"""
HTTP-роутер для запуску «доктора» (перевірок стану системи).
"""

from __future__ import annotations

from fastapi import APIRouter

from calculator_engine.domain.doctor.checks import run_all_checks

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/doctor", summary="Запустити перевірки стану («доктор»)")
def doctor():
    """
    Повертає загальний статус системи та деталізований список перевірок.
    overall: ok | degraded | down
    checks: [{name, status, detail}]
    """
    return run_all_checks()
