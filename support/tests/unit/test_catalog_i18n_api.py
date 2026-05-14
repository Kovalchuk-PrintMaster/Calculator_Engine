from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_preview_returns_english_labels() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/preview",
        params={
            "material_code": "tintoretto_neve_300",
            "locale": "en",
        },
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["product_template_name"] == "Business Card Standard"
    assert payload["material_options"][0]["category_name"] == "Designer Cardstock"
    assert payload["context"]["locale"] == "en"


def test_quote_returns_polish_route_names() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params=[
            ("material_code", "tintoretto_neve_300"),
            ("quantity", 100),
            ("selected_operation_codes", "foil"),
            ("locale", "pl"),
        ],
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["currency"] == "USD"
    assert [step["operation_name"] for step in payload["route"]] == [
        "Cięcie gilotynowe",
        "Druk cyfrowy",
        "Złocenie folią",
    ]
    assert payload["context"]["locale"] == "pl"