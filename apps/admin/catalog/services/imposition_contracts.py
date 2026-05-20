from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True, slots=True)
class ImpositionRequest:
    product_template_code: str
    material_code: str
    quantity: int
    layout_mode: str
    finished_width_mm: float | None = None
    finished_height_mm: float | None = None
    bleed_mm: float | None = None
    input_file_path: str | None = None


@dataclass(frozen=True, slots=True)
class ImpositionResult:
    status: Literal["completed", "failed", "manual_required"]
    engine_code: str
    layout_mode: str
    imposed_sheet_count: int | None
    items_per_sheet: int | None
    waste_percent: float | None
    output_file_path: str | None
    message: str = ""


class ImpositionProvider(Protocol):
    def build_layout(self, request: ImpositionRequest) -> ImpositionResult:
        ...