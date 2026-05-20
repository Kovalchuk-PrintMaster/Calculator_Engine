from __future__ import annotations

from calculator_engine.adapters.alerts.telegram import build_intake_alert_message


def test_build_intake_alert_message_contains_key_fields() -> None:
    message = build_intake_alert_message(
        event_type="intake_idempotency_conflict",
        detail="Idempotency key already exists for different request payload.",
        payload={
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-5001",
            "external_customer_id": "SITE-CUSTOMER-5001",
            "idempotency_key": "idem-manual-5001",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
        },
    )

    assert "intake_idempotency_conflict" in message
    assert "printmaster_pl" in message
    assert "SITE-ORDER-5001" in message
    assert "idem-manual-5001" in message