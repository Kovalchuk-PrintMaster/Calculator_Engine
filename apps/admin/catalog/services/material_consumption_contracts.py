from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Literal


MaterialConsumptionContextType = Literal["draft", "quote", "calculation_job", "standalone"]


@dataclass(frozen=True, slots=True)
class MaterialConsumptionEstimate:
    estimate_id: str
    context_type: MaterialConsumptionContextType
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

    warnings: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    created_at: str = ""