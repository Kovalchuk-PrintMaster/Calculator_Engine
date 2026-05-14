from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_configuration_preview_without_material() -> None:
    response = client.get("/catalog/templates/business_card_standard/preview")
    assert response.status_code == 200

    payload = response.json()
    assert payload["product_template_code"] == "business_card_standard"
    assert isinstance(payload["material_options"], list)
    assert payload["selected_material_code"] is None
    assert payload["available_operation_codes"] == []
    assert payload["default_route_codes"] == []


def test_configuration_preview_with_material() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/preview",
        params={"material_code": "tintoretto_neve_300"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["product_template_code"] == "business_card_standard"
    assert payload["selected_material_code"] == "tintoretto_neve_300"
    assert payload["available_operation_codes"] == [
        "guillotine_cut",
        "digital_print",
        "uv_print",
        "foil",
        "emboss",
    ]
    assert payload["default_route_codes"] == [
        "guillotine_cut",
        "digital_print",
    ]


def test_quote_preview_default_route() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params={
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["template_code"] == "business_card_standard"
    assert payload["material_code"] == "tintoretto_neve_300"
    assert payload["quantity"] == 100
    assert [step["operation_code"] for step in payload["route"]] == [
        "guillotine_cut",
        "digital_print",
    ]
    assert payload["total"] == "800.00"


def test_quote_preview_with_optional_operation() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params=[
            ("material_code", "tintoretto_neve_300"),
            ("quantity", 100),
            ("selected_operation_codes", "foil"),
        ],
    )
    assert response.status_code == 200

    payload = response.json()
    assert [step["operation_code"] for step in payload["route"]] == [
        "guillotine_cut",
        "digital_print",
        "foil",
    ]
    assert payload["total"] == "1100.00"


def test_quote_preview_rejects_invalid_operation() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params=[
            ("material_code", "tintoretto_neve_300"),
            ("quantity", 100),
            ("selected_operation_codes", "eco_solvent_print"),
        ],
    )
    assert response.status_code == 400

    payload = response.json()
    assert "Invalid selected operations" in payload["detail"]