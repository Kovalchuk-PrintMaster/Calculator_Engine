from __future__ import annotations

from typing import Any

from calculator_engine.shared.request_context import normalize_locale


class IntakeNormalizationError(ValueError):
    """Raised when intake payload cannot be normalized safely."""


def _clean_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _clean_nullable_text(value: Any) -> str | None:
    cleaned = _clean_text(value)
    return cleaned or None


def _clean_operation_code(value: Any) -> str | None:
    cleaned = _clean_text(value).lower().replace(" ", "_")
    return cleaned or None


def normalize_quote_intake_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize external intake payload into stable internal form."""
    if not isinstance(payload, dict):
        raise IntakeNormalizationError("Intake payload must be an object.")

    normalized = dict(payload)

    normalized["source"] = _clean_text(payload.get("source") or "external").lower() or "external"
    normalized["brand_code"] = _clean_text(payload.get("brand_code")).lower()
    normalized["customer_ref"] = _clean_text(payload.get("customer_ref"))
    normalized["external_order_id"] = _clean_nullable_text(payload.get("external_order_id"))
    normalized["external_customer_id"] = _clean_nullable_text(payload.get("external_customer_id"))
    normalized["idempotency_key"] = _clean_nullable_text(payload.get("idempotency_key"))

    normalized["product_template_code"] = _clean_text(
        payload.get("product_template_code")
    ).lower()
    normalized["material_code"] = _clean_text(payload.get("material_code")).lower()

    locale = normalize_locale(payload.get("locale"))
    normalized["locale"] = locale

    currency = _clean_text(payload.get("currency")).upper()
    normalized["currency"] = currency or None

    raw_quantity = payload.get("quantity")
    if raw_quantity in (None, ""):
        raise IntakeNormalizationError("Quantity is required.")
    try:
        normalized["quantity"] = int(raw_quantity)
    except (TypeError, ValueError) as exc:
        raise IntakeNormalizationError("Quantity must be an integer.") from exc

    raw_operations = payload.get("selected_operation_codes") or []
    if not isinstance(raw_operations, list):
        raise IntakeNormalizationError("selected_operation_codes must be a list.")

    cleaned_operations: list[str] = []
    seen: set[str] = set()
    for item in raw_operations:
        code = _clean_operation_code(item)
        if not code or code in seen:
            continue
        cleaned_operations.append(code)
        seen.add(code)

    normalized["selected_operation_codes"] = cleaned_operations

    input_payload_json = payload.get("input_payload_json")
    normalized["input_payload_json"] = input_payload_json if isinstance(input_payload_json, dict) else {}

    return normalized