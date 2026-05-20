from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from calculator_engine.adapters.alerts.telegram import (
    build_intake_alert_message,
    send_telegram_alert,
)


def notify_intake_alert(
    *,
    event_type: str,
    detail: str,
    payload: Mapping[str, Any] | None = None,
) -> bool:
    """Send best-effort intake alert to Telegram."""
    message = build_intake_alert_message(
        event_type=event_type,
        detail=detail,
        payload=dict(payload or {}),
    )
    return send_telegram_alert(message)

#== End of file: app/apps/api/backend/calculator_engine/app/services/intake_alerts.py

