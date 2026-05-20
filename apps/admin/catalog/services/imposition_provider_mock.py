from __future__ import annotations

from .imposition_contracts import ImpositionRequest, ImpositionResult


class MockImpositionProvider:
    def build_layout(self, request: ImpositionRequest) -> ImpositionResult:
        if request.layout_mode == "manual":
            return ImpositionResult(
                status="manual_required",
                engine_code="mock",
                layout_mode=request.layout_mode,
                imposed_sheet_count=None,
                items_per_sheet=None,
                waste_percent=None,
                output_file_path=None,
                message="Manual imposition required.",
            )

        if request.layout_mode == "n_up":
            return ImpositionResult(
                status="completed",
                engine_code="mock",
                layout_mode="n_up",
                imposed_sheet_count=max(1, request.quantity // 8 + (1 if request.quantity % 8 else 0)),
                items_per_sheet=8,
                waste_percent=3.0,
                output_file_path="",
                message="Mock N-up layout prepared.",
            )

        if request.layout_mode == "step_repeat":
            return ImpositionResult(
                status="completed",
                engine_code="mock",
                layout_mode="step_repeat",
                imposed_sheet_count=max(1, request.quantity // 24 + (1 if request.quantity % 24 else 0)),
                items_per_sheet=24,
                waste_percent=2.5,
                output_file_path="",
                message="Mock Step&Repeat layout prepared.",
            )

        return ImpositionResult(
            status="completed",
            engine_code="mock",
            layout_mode="none",
            imposed_sheet_count=None,
            items_per_sheet=None,
            waste_percent=None,
            output_file_path="",
            message="No imposition required.",
        )