from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_brand_templates_global_uses_brand_defaults() -> None:
    response = client.get("/catalog/brands/printmaster_global/templates")
    assert response.status_code == 200

    payload = response.json()
    assert payload["brand_code"] == "printmaster_global"
    assert payload["context"]["locale"] == "en"
    assert payload["context"]["currency"] == "USD"
    assert payload["context"]["source_locale"] == "brand-default"
    assert payload["context"]["source_currency"] == "brand-default"
    assert [item["code"] for item in payload["templates"]] == [
        "business_card_standard",
        "flyer_standard",
        "poster_standard",
    ]


def test_brand_templates_poland_returns_polish_names() -> None:
    response = client.get("/catalog/brands/printmaster_pl/templates")
    assert response.status_code == 200

    payload = response.json()
    assert payload["brand_code"] == "printmaster_pl"
    assert payload["context"]["locale"] == "pl"
    assert payload["context"]["currency"] == "EUR"
    assert payload["templates"][0]["name"] == "Wizytówka standard"


def test_brand_templates_explicit_locale_overrides_brand_default() -> None:
    response = client.get(
        "/catalog/brands/printmaster_pl/templates",
        params={"locale": "en"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["context"]["locale"] == "en"
    assert payload["context"]["source_locale"] == "explicit"
    assert payload["templates"][0]["name"] == "Business Card Standard"