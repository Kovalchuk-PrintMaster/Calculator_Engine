from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app

client = TestClient(app)


def test_preview_uses_explicit_locale() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/preview",
        params={"material_code": "tintoretto_neve_300", "locale": "en"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["context"]["locale"] == "en"
    assert payload["context"]["source_locale"] == "explicit"


def test_preview_uses_accept_language_fallback() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/preview",
        params={"material_code": "tintoretto_neve_300"},
        headers={"Accept-Language": "pl-PL,pl;q=0.9"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["context"]["locale"] == "pl"
    assert payload["context"]["source_locale"] == "accept-language"


def test_quote_uses_geo_defaults_for_europe() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params={
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
        },
        headers={"CF-IPCountry": "DE"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["currency"] == "EUR"
    assert payload["context"]["locale"] == "de"
    assert payload["context"]["country_code"] == "DE"
    assert payload["context"]["source_currency"] == "geoip-default"


def test_quote_uses_geo_defaults_for_non_europe() -> None:
    response = client.get(
        "/catalog/templates/business_card_standard/quote-preview",
        params={
            "material_code": "tintoretto_neve_300",
            "quantity": 100,
        },
        headers={"CF-IPCountry": "BR"},
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["currency"] == "USD"
    assert payload["context"]["locale"] == "en"
    assert payload["context"]["country_code"] == "BR"