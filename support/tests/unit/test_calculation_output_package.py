from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from calculator_engine.app.main import app
from calculator_engine.app.schemas.calculation_output_package import (
    CalculationOutputPackageSchema,
    ManualCustomOperationDraftSchema,
)
from calculator_engine.app.services.calculation_output_package import (
    build_calculation_output_package_from_submit_payload,
    calculation_output_package_to_dict,
)

client = TestClient(app)

FIXTURES = Path("support/fixtures/calculator")


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _build_submit_payload() -> dict:
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
            "selected_operation_codes": ["foil"],
        },
    )
    assert patched.status_code == 200
    assert patched.json()["data"]["status"] == "quote_ready"

    submitted = client.post(
        f"/configurator/drafts/{draft_id}/submit",
        json={},
    )
    assert submitted.status_code == 200
    return submitted.json()["data"]


def test_calculation_output_package_can_be_created() -> None:
    submit_payload = _build_submit_payload()

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload
    )

    assert package.calculation_id == submit_payload["job_public_id"]
    assert package.quote_draft.product_template_code == "business_card_standard"
    assert package.order_draft.product_template_code == "business_card_standard"
    assert package.price_breakdown.total == "1100.00"
    assert package.material_consumption_estimate.actual_material_quantity == 105


def test_quote_draft_and_order_draft_are_generated_from_submit_payload() -> None:
    submit_payload = _build_submit_payload()

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload
    )

    assert package.quote_draft.total == "1100.00"
    assert package.order_draft.estimated_total == "1100.00"
    assert package.quote_draft.route_codes == [
        "guillotine_cut",
        "digital_print",
        "foil",
    ]
    assert package.order_draft.selected_operation_codes == ["foil"]


def test_warnings_and_manual_custom_operations_are_preserved() -> None:
    submit_payload = _build_submit_payload()

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload,
        validation_warnings=[
            {
                "code": "manual_review",
                "message": "Manual review recommended.",
                "severity": "warning",
                "field": "selected_operation_codes",
            }
        ],
        manual_custom_operation_drafts=[
            {
                "operation_code": "custom_corner_rounding",
                "display_name": "Custom corner rounding",
                "reason": "Manager requested non-standard finishing.",
                "price_impact": "120.00",
                "currency": "EUR",
                "notes": "Manual custom operation kept as draft only.",
            }
        ],
    )

    warning_codes = [item.code for item in package.validation_warnings]

    assert "manual_review" in warning_codes
    assert "manual_price_confirmation_recommended" in warning_codes
    assert "waste_assumption_applied" in warning_codes

    assert package.manual_custom_operation_drafts[0].operation_code == (
        "custom_corner_rounding"
    )

def test_output_package_is_json_serializable() -> None:
    submit_payload = _build_submit_payload()

    package = build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload
    )
    payload = calculation_output_package_to_dict(package)

    json.dumps(payload)

    assert payload["quote_draft"]["total"] == "1100.00"
    assert payload["order_draft"]["estimated_total"] == "1100.00"
    assert payload["price_breakdown"]["total"] == "1100.00"
    assert payload["material_consumption_estimate"]["actual_material_quantity"] == 105


def test_output_package_fixtures_validate_successfully() -> None:
    fixture_names = [
        "business_card_quote_package_example.json",
        "flyer_quote_package_example.json",
        "calculation_with_warning_example.json",
        "order_draft_package_example.json",
    ]

    for name in fixture_names:
        payload = _load_json(name)
        package = CalculationOutputPackageSchema.model_validate(payload)
        assert package.package_id

    manual_operation = _load_json("manual_custom_operation_example.json")
    draft = ManualCustomOperationDraftSchema.model_validate(manual_operation)
    assert draft.operation_code == "custom_corner_rounding"