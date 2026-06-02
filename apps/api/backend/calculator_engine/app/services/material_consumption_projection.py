from __future__ import annotations

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.services.configurator_flow import (
    resolve_configurator_draft_flow_state,
)


class MaterialConsumptionProjectionError(ValueError):
    """Base material consumption projection error."""


class MaterialConsumptionProjectionNotFoundError(MaterialConsumptionProjectionError):
    """Raised when source object is not found."""


class MaterialConsumptionProjectionValidationError(MaterialConsumptionProjectionError):
    """Raised when estimate cannot be built."""


def _extract_material_line(lines: list) -> object:
    for line in lines:
        if str(line.code).startswith("material:"):
            return line
    raise MaterialConsumptionProjectionValidationError("Material line not found.")


def build_draft_material_consumption_estimate(*, draft_id: str):
    setup_django()

    from catalog.models import ConfiguratorDraft, Material, ProductTemplate
    from catalog.services import (
        assert_projection_usage,
        build_material_consumption_estimate,
        build_price_quote,
    )

    try:
        draft = ConfiguratorDraft.objects.get(public_id=draft_id)
    except ConfiguratorDraft.DoesNotExist as exc:
        raise MaterialConsumptionProjectionNotFoundError(
            f"ConfiguratorDraft not found: {draft_id}"
        ) from exc

    flow = resolve_configurator_draft_flow_state(
        current_status=draft.status,
        product_template_code=draft.product_template_code,
        material_code=draft.material_code,
        quantity=draft.quantity,
    )

    if not flow.can_estimate_material_consumption:
        raise MaterialConsumptionProjectionValidationError(
            "Draft is not ready for material consumption estimate."
        )

    template = ProductTemplate.objects.filter(
        code=draft.product_template_code,
        active=True,
    ).first()
    if template is None:
        raise MaterialConsumptionProjectionValidationError(
            f"ProductTemplate not found: {draft.product_template_code}"
        )

    material = Material.objects.filter(
        code=draft.material_code,
        active=True,
    ).first()
    if material is None:
        raise MaterialConsumptionProjectionValidationError(
            f"Material not found: {draft.material_code}"
        )

    assert_projection_usage(
        entity_type="product_template",
        code=template.code,
        source_system=template.source_system,
        intended_usage="calculation_input",
    )
    assert_projection_usage(
        entity_type="material",
        code=material.code,
        source_system=material.source_system,
        intended_usage="calculation_input",
    )

    quote = build_price_quote(
        template,
        material,
        quantity=draft.quantity,
        selected_operation_codes=list(draft.selected_operation_codes_json or []),
        locale=draft.locale,
    )
    material_line = _extract_material_line(list(quote.lines))

    requested_quantity = int(
        material_line.meta.get("requested_quantity", draft.quantity)
    )

    return build_material_consumption_estimate(
        context_type="draft",
        source_ref=str(draft.public_id),
        draft_ref=str(draft.public_id),
        material_ref=material.code,
        material_name_snapshot=material_line.name,
        requested_quantity=requested_quantity,
        actual_material_quantity=material_line.quantity,
        unit=material_line.unit,
        calculation_basis="quote_material_line",
        warnings=[],
        metadata=dict(material_line.meta or {}),
    )


def build_calculation_job_material_consumption_estimate(*, job_public_id: str):
    setup_django()

    from catalog.models import CalculationJob
    from catalog.services import (
        assert_projection_usage,
        build_material_consumption_estimate,
    )

    job = CalculationJob.objects.filter(public_id=job_public_id).first()
    if job is None:
        raise MaterialConsumptionProjectionNotFoundError(
            f"CalculationJob not found: {job_public_id}"
        )

    report = dict(job.external_report_json or {})
    lines = list(report.get("lines") or [])

    material_line = None
    for line in lines:
        if str(line.get("code", "")).startswith("material:"):
            material_line = line
            break

    if material_line is None:
        raise MaterialConsumptionProjectionValidationError(
            "Material line not found in calculation job."
        )

    requested_quantity = int(
        material_line.get("meta", {}).get("requested_quantity", job.quantity)
    )
    material_ref = str(job.material_code)

    assert_projection_usage(
        entity_type="material",
        code=material_ref,
        source_system="library",
        intended_usage="calculation_input",
    )

    return build_material_consumption_estimate(
        context_type="calculation_job",
        source_ref=str(job.public_id),
        quote_ref=str(job.public_id),
        calculation_job_ref=str(job.public_id),
        material_ref=material_ref,
        material_name_snapshot=str(material_line["name"]),
        requested_quantity=requested_quantity,
        actual_material_quantity=int(material_line["quantity"]),
        unit=str(material_line["unit"]),
        calculation_basis="calculation_job_external_report",
        warnings=[],
        metadata=dict(material_line.get("meta") or {}),
    )