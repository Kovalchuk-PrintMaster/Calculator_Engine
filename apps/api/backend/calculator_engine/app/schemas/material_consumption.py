from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class MaterialConsumptionEstimateSchema(BaseModel):
    estimate_id: str
    context_type: Literal["draft", "quote", "calculation_job", "standalone"]
    source_ref: str
    quote_ref: str | None
    draft_ref: str | None
    calculation_job_ref: str | None
    material_ref: str
    material_name_snapshot: str
    requested_quantity: int
    actual_material_quantity: int
    waste_quantity: int
    waste_percent: Decimal
    unit: str
    calculation_basis: str
    confidence_level: str
    warnings: list[str]
    metadata: dict
    created_at: str