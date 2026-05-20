from __future__ import annotations

import html
import logging
import os
from typing import Any
from urllib import parse, request

logger = logging.getLogger(__name__)


def _truncate(value: Any, limit: int = 200) -> str:
    text = "" if value is None else str(value)
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def build_intake_alert_message(
    *,
    event_type: str,
    detail: str,
    payload: dict[str, Any] | None = None,
) -> str:
    payload = payload or {}

    lines = [
        "⚠️ <b>Calculator intake alert</b>",
        f"<b>event:</b> {html.escape(_truncate(event_type, 64))}",
        f"<b>detail:</b> {html.escape(_truncate(detail, 300))}",
        f"<b>brand:</b> {html.escape(_truncate(payload.get('brand_code') or '-', 64))}",
        f"<b>external_order_id:</b> {html.escape(_truncate(payload.get('external_order_id') or '-', 128))}",
        f"<b>external_customer_id:</b> {html.escape(_truncate(payload.get('external_customer_id') or '-', 128))}",
        f"<b>idempotency_key:</b> {html.escape(_truncate(payload.get('idempotency_key') or '-', 128))}",
        f"<b>template:</b> {html.escape(_truncate(payload.get('product_template_code') or '-', 64))}",
        f"<b>material:</b> {html.escape(_truncate(payload.get('material_code') or '-', 64))}",
        f"<b>quantity:</b> {html.escape(_truncate(payload.get('quantity') or '-', 32))}",
    ]
    return "\n".join(lines)


def send_telegram_alert(message: str) -> bool:
    """Send best-effort Telegram alert. Returns False if disabled or failed."""
    bot_token = os.getenv("CALC_TELEGRAM_ALERT_BOT_TOKEN", "").strip()
    chat_id = os.getenv("CALC_TELEGRAM_ALERT_CHAT_ID", "").strip()

    if not bot_token or not chat_id:
        return False

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=5) as response:
            response.read()
        return True
    except Exception:
        logger.exception("Failed to send Telegram alert.")
        return False