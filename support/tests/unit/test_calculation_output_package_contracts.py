from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from calculator_engine.app.main import app
from calculator_engine.app.schemas.calculation_output_package import (
    CalculationOutputPackageSchema,
)

client = TestClient(app)

FIXTURES = Path("support/fixtures/calculator")


def _load_json(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _create_job() -> str:
    response = client.post(
        "/intake/orders/quote",
        json={
            "source": "external",
            "brand_code": "printmaster_pl",
            "external_order_id": "SITE-ORDER-CONTRACT-001",
            "external_customer_id": "SITE-CUSTOMER-CONTRACT-001",
            "product_template_code": "business_card_standard",
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
            "selected_operation_codes": ["foil"],
            "locale": "pl",
        },
    )
    assert response.status_code == 200
    return response.json()["data"]["job_public_id"]


def test_output_package_response_fixture_validates() -> None:
    payload = _load_json("calculation_output_package_response_example.json")
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    package = CalculationOutputPackageSchema.model_validate(payload["data"])
    assert package.quote_draft.product_template_code == "business_card_standard"


def test_output_package_warning_response_fixture_validates() -> None:
    payload = _load_json("calculation_output_package_with_warning_response_example.json")
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    package = CalculationOutputPackageSchema.model_validate(payload["data"])
    warning_codes = [item.code for item in package.validation_warnings]

    assert "manual_price_confirmation_recommended" in warning_codes
    assert "waste_assumption_applied" in warning_codes


def test_output_package_endpoint_contract_shape() -> None:
    job_public_id = _create_job()

    response = client.get(f"/reports/jobs/{job_public_id}/output-package")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert "data" in payload
    assert "meta" in payload
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    required_keys = {
        "package_id",
        "calculation_id",
        "quote_draft",
        "order_draft",
        "price_breakdown",
        "material_consumption_estimate",
        "production_method_plan",
        "operation_sequence",
        "accounting_line_drafts",
        "prepress_requirement_drafts",
        "validation_warnings",
        "manual_custom_operation_drafts",
        "source_context",
        "created_at",
    }
    assert required_keys.issubset(data.keys())


def test_output_package_endpoint_preserves_warning_contract_shape() -> None:
    job_public_id = _create_job()

    response = client.get(f"/reports/jobs/{job_public_id}/output-package")
    assert response.status_code == 200

    data = response.json()["data"]
    warnings = data["validation_warnings"]

    assert isinstance(warnings, list)
    assert warnings

    first = warnings[0]
    assert "code" in first
    assert "message" in first
    assert "severity" in first