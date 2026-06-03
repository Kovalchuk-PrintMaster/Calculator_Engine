from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4
from uuid import UUID
from calculator_engine.adapters.django_bootstrap import setup_django

from calculator_engine.app.schemas.calculation_output_package import (
    AccountingLineDraftSchema,
    CalculationOutputPackageSchema,
    ManualCustomOperationDraftSchema,
    OperationSequenceSchema,
    OrderDraftSchema,
    PrepressRequirementDraftSchema,
    PriceBreakdownSchema,
    ProductionMethodPlanSchema,
    QuoteDraftSchema,
    SourceContextSchema,
    ValidationWarningSchema,
)

class CalculationOutputPackageError(ValueError):
    """Base calculation output package error."""


class CalculationOutputPackageNotFoundError(CalculationOutputPackageError):
    """Raised when source calculation job does not exist."""

def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _route_codes_from_human_report(human_report: dict[str, Any]) -> list[str]:
    return [
        str(item.get("operation_code", ""))
        for item in _as_list(human_report.get("route"))
        if str(item.get("operation_code", "")).strip()
    ]


def _summary_lines_from_human_report(
    human_report: dict[str, Any],
    *,
    currency: str,
) -> list[str]:
    summary: list[str] = []
    for line in _as_list(human_report.get("lines"))[:3]:
        name = str(line.get("name", "")).strip()
        total = str(line.get("total", "")).strip()
        if not name:
            continue
        summary.append(f"{name}: {total} {currency}".strip())
    return summary


def _find_material_line(human_report: dict[str, Any]) -> dict[str, Any]:
    for line in _as_list(human_report.get("lines")):
        if str(line.get("code", "")).startswith("material:"):
            return _as_dict(line)
    raise ValueError("Material line not found in human_report.")


def build_price_breakdown_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> PriceBreakdownSchema:
    human_report = _as_dict(submit_payload.get("human_report"))

    return PriceBreakdownSchema.model_validate(
        {
            "currency": str(submit_payload.get("currency", "")),
            "subtotal": str(submit_payload.get("subtotal", "")),
            "total": str(submit_payload.get("total", "")),
            "route": _as_list(human_report.get("route")),
            "lines": _as_list(human_report.get("lines")),
        }
    )


def build_quote_draft_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> QuoteDraftSchema:
    human_report = _as_dict(submit_payload.get("human_report"))
    route_codes = _route_codes_from_human_report(human_report)
    currency = str(submit_payload.get("currency", ""))

    return QuoteDraftSchema.model_validate(
        {
            "quote_id": str(uuid4()),
            "calculation_id": str(submit_payload.get("job_public_id", "")),
            "source": str(submit_payload.get("source", "")),
            "brand_code": str(human_report.get("brand_code", "")),
            "product_template_code": str(human_report.get("product_template_code", "")),
            "material_code": str(human_report.get("material_code", "")),
            "quantity": int(human_report.get("quantity", 0)),
            "currency": currency,
            "subtotal": str(submit_payload.get("subtotal", "")),
            "total": str(submit_payload.get("total", "")),
            "selected_operation_codes": list(
                human_report.get("selected_operation_codes") or []
            ),
            "route_codes": route_codes,
            "summary_lines": _summary_lines_from_human_report(
                human_report,
                currency=currency,
            ),
        }
    )


def build_order_draft_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> OrderDraftSchema:
    human_report = _as_dict(submit_payload.get("human_report"))
    external_report = _as_dict(submit_payload.get("external_report"))

    return OrderDraftSchema.model_validate(
        {
            "order_draft_id": str(uuid4()),
            "calculation_id": str(submit_payload.get("job_public_id", "")),
            "source": str(submit_payload.get("source", "")),
            "brand_code": str(human_report.get("brand_code", "")),
            "customer_ref": str(human_report.get("customer_ref", "")) or None,
            "external_order_ref": str(external_report.get("external_order_id", "")) or None,
            "external_customer_ref": str(
                external_report.get("external_customer_id", "")
            )
            or None,
            "product_template_code": str(human_report.get("product_template_code", "")),
            "material_code": str(human_report.get("material_code", "")),
            "quantity": int(human_report.get("quantity", 0)),
            "currency": str(submit_payload.get("currency", "")),
            "estimated_total": str(submit_payload.get("total", "")),
            "selected_operation_codes": list(
                human_report.get("selected_operation_codes") or []
            ),
            "downstream_refs": {
                "operational_registry_order_ref": None,
                "accounting_package_ref": None,
                "prepress_package_ref": None,
            },
        }
    )


def build_material_consumption_estimate_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> dict[str, Any]:
    human_report = _as_dict(submit_payload.get("human_report"))
    material_line = _find_material_line(human_report)
    meta = _as_dict(material_line.get("meta"))

    calculation_id = str(submit_payload.get("job_public_id", ""))
    requested_quantity = int(
        meta.get("requested_quantity", human_report.get("quantity", 0))
    )
    actual_material_quantity = int(material_line.get("quantity", 0))
    waste_quantity = max(actual_material_quantity - requested_quantity, 0)

    return {
        "estimate_id": str(uuid4()),
        "context_type": "calculation_job",
        "source_ref": calculation_id,
        "draft_ref": None,
        "quote_ref": calculation_id,
        "calculation_job_ref": calculation_id,
        "material_ref": str(human_report.get("material_code", "")),
        "material_name_snapshot": str(material_line.get("name", "")),
        "requested_quantity": requested_quantity,
        "actual_material_quantity": actual_material_quantity,
        "waste_quantity": waste_quantity,
        "unit": str(material_line.get("unit", "")),
        "waste_percent": str(meta.get("waste_percent", "0.00")),
        "confidence_level": "high",
        "calculation_basis": "submit_human_report",
        "warnings": [],
        "metadata": meta,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def build_production_method_plan_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> ProductionMethodPlanSchema:
    human_report = _as_dict(submit_payload.get("human_report"))
    route_codes = _route_codes_from_human_report(human_report)
    selected_ops = list(human_report.get("selected_operation_codes") or [])

    assumptions = [
        "route_based_production_plan",
        f"selected_operations={','.join(selected_ops) if selected_ops else 'none'}",
        "catalog_source=local_projection",
    ]

    return ProductionMethodPlanSchema(
        method_code="route_based_production_plan",
        method_name="Route-based production plan",
        route_codes=route_codes,
        assumptions=assumptions,
    )


def build_operation_sequence_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> OperationSequenceSchema:
    human_report = _as_dict(submit_payload.get("human_report"))
    route = _as_list(human_report.get("route"))
    route_codes = _route_codes_from_human_report(human_report)

    return OperationSequenceSchema.model_validate(
        {
            "route_codes": route_codes,
            "steps": route,
        }
    )


def build_accounting_line_drafts_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> list[AccountingLineDraftSchema]:
    human_report = _as_dict(submit_payload.get("human_report"))
    currency = str(submit_payload.get("currency", ""))

    drafts: list[AccountingLineDraftSchema] = []
    for line in _as_list(human_report.get("lines")):
        drafts.append(
            AccountingLineDraftSchema.model_validate(
                {
                    "code": str(line.get("code", "")),
                    "name": str(line.get("name", "")),
                    "category": str(line.get("category", "")),
                    "amount": str(line.get("total", "")),
                    "currency": currency,
                    "quantity": int(line.get("quantity", 0)),
                    "unit": str(line.get("unit", "")),
                }
            )
        )
    return drafts


def build_prepress_requirement_drafts_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> list[PrepressRequirementDraftSchema]:
    human_report = _as_dict(submit_payload.get("human_report"))
    selected_ops = list(human_report.get("selected_operation_codes") or [])

    items = [
        {
            "requirement_code": "print_ready_pdf",
            "title": "Print-ready PDF",
            "description": "Provide final print-ready PDF export for production.",
            "required": True,
            "source": "calculator_default",
        }
    ]

    if "foil" in selected_ops:
        items.append(
            {
                "requirement_code": "foil_layer_required",
                "title": "Foil layer file",
                "description": "Provide separate foil mask/layer for foil finishing.",
                "required": True,
                "source": "calculator_selected_operation",
            }
        )

    return [
        PrepressRequirementDraftSchema.model_validate(item)
        for item in items
    ]


def build_source_context_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
) -> SourceContextSchema:
    context = _as_dict(submit_payload.get("context"))
    human_report = _as_dict(submit_payload.get("human_report"))

    return SourceContextSchema.model_validate(
        {
            "origin": "configurator_submit",
            "source": str(submit_payload.get("source", "")),
            "brand_code": str(
                context.get("brand_code", "") or human_report.get("brand_code", "")
            ),
            "used_catalog_source": "local_projection",
            "calculation_mode": "sandbox",
            "source_locale": str(context.get("source_locale", "")) or None,
            "source_currency": str(context.get("source_currency", "")) or None,
        }
    )


def build_calculation_output_package_from_submit_payload(
    *,
    submit_payload: dict[str, Any],
    validation_warnings: list[dict[str, Any]] | None = None,
    manual_custom_operation_drafts: list[dict[str, Any]] | None = None,
) -> CalculationOutputPackageSchema:
    price_breakdown = build_price_breakdown_from_submit_payload(
        submit_payload=submit_payload
    )
    quote_draft = build_quote_draft_from_submit_payload(
        submit_payload=submit_payload
    )
    order_draft = build_order_draft_from_submit_payload(
        submit_payload=submit_payload
    )
    material_consumption_estimate = (
        build_material_consumption_estimate_from_submit_payload(
            submit_payload=submit_payload
        )
    )
    production_method_plan = build_production_method_plan_from_submit_payload(
        submit_payload=submit_payload
    )
    operation_sequence = build_operation_sequence_from_submit_payload(
        submit_payload=submit_payload
    )
    accounting_line_drafts = build_accounting_line_drafts_from_submit_payload(
        submit_payload=submit_payload
    )
    prepress_requirement_drafts = build_prepress_requirement_drafts_from_submit_payload(
        submit_payload=submit_payload
    )
    source_context = build_source_context_from_submit_payload(
        submit_payload=submit_payload
    )

    warnings_models = [
        ValidationWarningSchema.model_validate(item)
        for item in (validation_warnings or [])
    ]
    manual_ops_models = [
        ManualCustomOperationDraftSchema.model_validate(item)
        for item in (manual_custom_operation_drafts or [])
    ]

    payload = {
        "package_id": str(uuid4()),
        "calculation_id": str(submit_payload.get("job_public_id", "")),
        "quote_draft": price_breakdown_to_quote_draft_dict(quote_draft),
        "order_draft": order_draft.model_dump(mode="python"),
        "price_breakdown": price_breakdown.model_dump(mode="python"),
        "material_consumption_estimate": material_consumption_estimate,
        "production_method_plan": production_method_plan.model_dump(mode="python"),
        "operation_sequence": operation_sequence.model_dump(mode="python"),
        "accounting_line_drafts": [
            item.model_dump(mode="python") for item in accounting_line_drafts
        ],
        "prepress_requirement_drafts": [
            item.model_dump(mode="python") for item in prepress_requirement_drafts
        ],
        "validation_warnings": [
            item.model_dump(mode="python") for item in warnings_models
        ],
        "manual_custom_operation_drafts": [
            item.model_dump(mode="python") for item in manual_ops_models
        ],
        "source_context": source_context.model_dump(mode="python"),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    return CalculationOutputPackageSchema.model_validate(payload)


def price_breakdown_to_quote_draft_dict(
    quote_draft: QuoteDraftSchema,
) -> dict[str, Any]:
    return quote_draft.model_dump(mode="python")


def calculation_output_package_to_dict(
    package: CalculationOutputPackageSchema,
) -> dict[str, Any]:
    return json.loads(package.model_dump_json())

def _build_submit_payload_like_from_job(job) -> dict[str, Any]:
    human_report = _as_dict(job.human_report_json)
    external_report = _as_dict(job.external_report_json)

    return {
        "job_public_id": str(job.public_id),
        "status": job.status,
        "source": job.source,
        "reused": False,
        "locale": str(job.locale),
        "currency": str(job.currency),
        "subtotal": str(job.subtotal or ""),
        "total": str(job.total or ""),
        "context": {
            "locale": str(job.locale),
            "currency": str(job.currency),
            "source_locale": str(job.locale),
            "source_currency": str(job.currency),
            "brand_code": str(job.brand_code),
        },
        "human_report": human_report,
        "external_report": external_report,
    }


def build_calculation_output_package_for_job(
    *,
    job_public_id: str,
    validation_warnings: list[dict[str, Any]] | None = None,
    manual_custom_operation_drafts: list[dict[str, Any]] | None = None,
) -> CalculationOutputPackageSchema:
    setup_django()

    from catalog.models import CalculationJob

    try:
        UUID(str(job_public_id))
    except ValueError as exc:
        raise CalculationOutputPackageNotFoundError(
            f"Invalid calculation job id: {job_public_id}"
        ) from exc

    job = CalculationJob.objects.filter(public_id=job_public_id).first()
    if job is None:
        raise CalculationOutputPackageNotFoundError(
            f"CalculationJob not found: {job_public_id}"
        )

    submit_payload = _build_submit_payload_like_from_job(job)

    return build_calculation_output_package_from_submit_payload(
        submit_payload=submit_payload,
        validation_warnings=validation_warnings,
        manual_custom_operation_drafts=manual_custom_operation_drafts,
    )