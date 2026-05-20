from __future__ import annotations

from calculator_engine.app.intake_normalization import normalize_quote_intake_payload


def test_normalize_quote_intake_payload_trims_and_deduplicates() -> None:
    payload = normalize_quote_intake_payload(
        {
            "source": " EXTERNAL ",
            "brand_code": " PrintMaster_PL ",
            "external_order_id": "  ORDER-1  ",
            "external_customer_id": "  CUSTOMER-1  ",
            "product_template_code": " Business_Card_Standard ",
            "material_code": " Tintoretto_Neve_300 ",
            "quantity": "100",
            "locale": "pl-PL",
            "currency": " eur ",
            "selected_operation_codes": [" foil ", "FOIL", " digital_print ", "", None],
        }
    )

    assert payload["source"] == "external"
    assert payload["brand_code"] == "printmaster_pl"
    assert payload["external_order_id"] == "ORDER-1"
    assert payload["external_customer_id"] == "CUSTOMER-1"
    assert payload["product_template_code"] == "business_card_standard"
    assert payload["material_code"] == "tintoretto_neve_300"
    assert payload["quantity"] == 100
    assert payload["locale"] == "pl"
    assert payload["currency"] == "EUR"
    assert payload["selected_operation_codes"] == ["foil", "digital_print"]