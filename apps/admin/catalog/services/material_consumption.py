from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from .material_consumption_contracts import MaterialConsumptionEstimate


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_material_consumption_estimate(
    *,
    context_type: str,
    source_ref: str,
    material_ref: str,
    material_name_snapshot: str,
    requested_quantity: int,
    actual_material_quantity: int,
    unit: str,
    calculation_basis: str,
    quote_ref: str | None = None,
    draft_ref: str | None = None,
    calculation_job_ref: str | None = None,
    confidence_level: str = "high",
    warnings: list[str] | None = None,
    metadata: dict | None = None,
) -> MaterialConsumptionEstimate:
    actual_qty = int(actual_material_quantity)
    requested_qty = int(requested_quantity)
    waste_qty = max(actual_qty - requested_qty, 0)

    waste_percent = Decimal("0.00")
    if requested_qty > 0:
        waste_percent = (Decimal(waste_qty) / Decimal(requested_qty) * Decimal("100")).quantize(
            Decimal("0.01")
        )

    return MaterialConsumptionEstimate(
        estimate_id=str(uuid4()),
        context_type=context_type,
        source_ref=source_ref,
        quote_ref=quote_ref,
        draft_ref=draft_ref,
        calculation_job_ref=calculation_job_ref,
        material_ref=material_ref,
        material_name_snapshot=material_name_snapshot,
        requested_quantity=requested_qty,
        actual_material_quantity=actual_qty,
        waste_quantity=waste_qty,
        waste_percent=waste_percent,
        unit=unit,
        calculation_basis=calculation_basis,
        confidence_level=confidence_level,
        warnings=list(warnings or []),
        metadata=dict(metadata or {}),
        created_at=_utc_now_iso(),
    )


def material_consumption_estimate_to_dict(
    estimate: MaterialConsumptionEstimate,
) -> dict:
    result = asdict(estimate)
    result["waste_percent"] = str(estimate.waste_percent)
    return result