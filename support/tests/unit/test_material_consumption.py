from __future__ import annotations

from decimal import Decimal

from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.services import build_material_consumption_estimate
from calculator_engine.app.services.material_consumption_projection import (
    build_calculation_job_material_consumption_estimate,
    build_draft_material_consumption_estimate,
)

from calculator_engine.app.services.configurator_drafts import (
    create_configurator_draft,
    update_configurator_draft,
)

def test_build_material_consumption_estimate_standalone() -> None:
    estimate = build_material_consumption_estimate(
        context_type="standalone",
        source_ref="example:standalone",
        material_ref="tintoretto_neve_300",
        material_name_snapshot="Tintoretto Neve 300",
        requested_quantity=100,
        actual_material_quantity=105,
        unit="sheet",
        calculation_basis="example_fixture",
    )

    assert estimate.context_type == "standalone"
    assert estimate.requested_quantity == 100
    assert estimate.actual_material_quantity == 105
    assert estimate.waste_quantity == 5
    assert estimate.waste_percent == Decimal("5.00")
    assert estimate.unit == "sheet"


def test_draft_material_consumption_estimate() -> None:
    
    created = create_configurator_draft(
        brand_code="printmaster_pl",
        locale=None,
        currency=None,
        request_context_locale="en",
        request_context_currency="USD",
        client_meta={},
        state={},
    )

    update_configurator_draft(
        draft_id=created.draft_id,
        product_template_code="business_card_standard",
        material_code="tintoretto_neve_300",
        quantity=100,
        selected_operation_codes=["foil"],
        state={},
    )

    estimate = build_draft_material_consumption_estimate(draft_id=created.draft_id)

    assert estimate.context_type == "draft"
    assert estimate.draft_ref == created.draft_id
    assert estimate.material_ref == "tintoretto_neve_300"
    assert estimate.requested_quantity == 100
    assert estimate.actual_material_quantity == 105
    assert estimate.waste_quantity == 5
    assert estimate.waste_percent == Decimal("5.00")


def test_calculation_job_material_consumption_estimate() -> None:
    from catalog.models import Material, ProductTemplate
    from catalog.services import process_calculation_request
    from catalog.services.calculation_contracts import CalculationRequest

    material = Material.objects.get(code="tintoretto_neve_300")
    template = ProductTemplate.objects.get(code="business_card_standard")

    request = CalculationRequest(
        source="manual",
        brand_code="printmaster_pl",
        customer_ref="",
        external_order_id=None,
        external_customer_id=None,
        idempotency_key=None,
        product_template_code=template.code,
        material_code=material.code,
        quantity=100,
        selected_operation_codes=("foil",),
        locale="pl",
        currency="EUR",
        input_payload_json={},
    )

    job, result, reused = process_calculation_request(request)
    assert reused is False

    estimate = build_calculation_job_material_consumption_estimate(
        job_public_id=str(job.public_id)
    )

    assert estimate.context_type == "calculation_job"
    assert estimate.calculation_job_ref == str(job.public_id)
    assert estimate.requested_quantity == 100
    assert estimate.actual_material_quantity == 105
    assert estimate.waste_quantity == 5
    assert estimate.waste_percent == Decimal("5.00")


def test_material_consumption_estimate_is_not_reservation() -> None:
    estimate = build_material_consumption_estimate(
        context_type="standalone",
        source_ref="example:standalone",
        material_ref="tintoretto_neve_300",
        material_name_snapshot="Tintoretto Neve 300",
        requested_quantity=100,
        actual_material_quantity=105,
        unit="sheet",
        calculation_basis="example_fixture",
    )

    assert estimate.context_type in {"draft", "quote", "calculation_job", "standalone"}
    assert "reservation" not in estimate.calculation_basis.lower()