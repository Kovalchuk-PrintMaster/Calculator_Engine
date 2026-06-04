from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app
from calculator_engine.app.services.calculation_output_package import (
    build_calculation_output_package_from_submit_payload,
)

client = TestClient(app)


def _build_submit_payload(selected_operation_codes: list[str]) -> dict:
    created = client.post(
        "/configurator/drafts",
        json={"brand_code": "printmaster_pl"},
    )
    assert created.status_code == 200
    draft_id = created.json()["data"]["draft_id"]

    patched = client.patch(
        f"/configurator/drafts/{draft_id}",
        json={
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": selected_operation_codes,
        },
    )
    assert patched.status_code == 200

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200
    return submitted.json()["data"]


def test_output_package_generates_default_warnings_for_foil_and_waste() -> None:
    submit_payload = _build_submit_payload(["foil"])

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload
    )

    warning_codes = [item.code for item in package.validation_warnings]

    assert "manual_price_confirmation_recommended" in warning_codes
    assert "waste_assumption_applied" in warning_codes


def test_output_package_generates_waste_warning_without_foil() -> None:
    submit_payload = _build_submit_payload([])

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload
    )

    warning_codes = [item.code for item in package.validation_warnings]

    assert "manual_price_confirmation_recommended" not in warning_codes
    assert "waste_assumption_applied" in warning_codes


def test_explicit_warning_is_merged_without_duplicates() -> None:
    submit_payload = _build_submit_payload(["foil"])

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload,
        validation_warnings=[
            {
                "code": "manual_price_confirmation_recommended",
                "message": "Recommended manual review for foil finishing before final order creation.",
                "severity": "warning",
                "field": "selected_operation_codes",
            },
            {
                "code": "custom_warning",
                "message": "Custom downstream notice.",
                "severity": "info",
                "field": "order_draft",
            },
        ],
    )

    warning_codes = [item.code for item in package.validation_warnings]

    assert warning_codes.count("manual_price_confirmation_recommended") == 1
    assert "custom_warning" in warning_codes