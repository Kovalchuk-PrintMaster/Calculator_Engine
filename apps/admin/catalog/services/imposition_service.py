from __future__ import annotations

from django.utils import timezone

from catalog.models import ImpositionJob, ProductTemplate
from .imposition_contracts import ImpositionRequest
from .imposition_provider_mock import MockImpositionProvider


class ImpositionServiceError(ValueError):
    """Raised when imposition request cannot be processed."""


def build_imposition_job(
    *,
    product_template_code: str,
    material_code: str,
    quantity: int,
    input_file_path: str | None = None,
) -> ImpositionJob:
    template = ProductTemplate.objects.filter(code=product_template_code, active=True).first()
    if template is None:
        raise ImpositionServiceError(f"ProductTemplate not found: {product_template_code}")

    layout_mode = template.layout_profile or "none"

    provider = MockImpositionProvider()
    request = ImpositionRequest(
        product_template_code=product_template_code,
        material_code=material_code,
        quantity=quantity,
        layout_mode=layout_mode,
        input_file_path=input_file_path,
    )
    result = provider.build_layout(request)

    job = ImpositionJob.objects.create(
        status=result.status,
        engine_code=result.engine_code,
        layout_mode=result.layout_mode,
        product_template_code=product_template_code,
        material_code=material_code,
        quantity=quantity,
        request_json={
            "product_template_code": product_template_code,
            "material_code": material_code,
            "quantity": quantity,
            "input_file_path": input_file_path or "",
        },
        result_json={
            "imposed_sheet_count": result.imposed_sheet_count,
            "items_per_sheet": result.items_per_sheet,
            "waste_percent": result.waste_percent,
            "output_file_path": result.output_file_path,
        },
        input_file_path=input_file_path or "",
        output_file_path=result.output_file_path or "",
        message=result.message,
        finished_at=timezone.now(),
    )
    return job