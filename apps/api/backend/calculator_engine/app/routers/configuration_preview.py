"""Configuration preview router."""

from __future__ import annotations

from pydantic import BaseModel

from calculator_engine.adapters.django_bootstrap import setup_django
from fastapi import APIRouter, Depends, HTTPException, Query
from calculator_engine.app.dependencies.context import get_request_context
from calculator_engine.shared.request_context import ResolvedRequestContext


router = APIRouter(
    prefix="/catalog/templates",
    tags=["catalog"],
    responses={404: {"description": "Not found"}},
)


class MaterialOptionResponse(BaseModel):
    code: str
    name: str
    category_code: str | None
    category_name: str | None
    form_factor: str
    density_gsm: int | None
    is_printable: bool


class ProductConfigurationPreviewResponse(BaseModel):
    product_template_code: str
    product_template_name: str
    material_options: list[MaterialOptionResponse]
    selected_material_code: str | None
    available_operation_codes: list[str]
    default_route_codes: list[str]
    context: ResolvedContextResponse
    
class ResolvedContextResponse(BaseModel):
    locale: str
    currency: str
    country_code: str | None
    source_locale: str
    source_currency: str

@router.get(
    "/{template_code}/preview",
    summary="Get product configuration preview",
    response_model=ProductConfigurationPreviewResponse,
)
def get_configuration_preview(
    template_code: str,
    material_code: str | None = Query(default=None),
    context: ResolvedRequestContext = Depends(get_request_context),
) -> ProductConfigurationPreviewResponse:
    """Return allowed materials and operation preview for a template."""
    setup_django()

    from catalog.models import Material, ProductTemplate
    from catalog.services import build_product_configuration_preview

    try:
        template = ProductTemplate.objects.get(code=template_code, active=True)
    except ProductTemplate.DoesNotExist as exc:
        raise HTTPException(
            status_code=404,
            detail=f"ProductTemplate not found: {template_code}",
        ) from exc

    material = None
    if material_code:
        try:
            material = Material.objects.select_related("category").get(
                code=material_code,
                active=True,
            )
        except Material.DoesNotExist as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Material not found: {material_code}",
            ) from exc

    preview = build_product_configuration_preview(
        product_template=template,
        material=material,
        locale=context.locale,
    )

    return ProductConfigurationPreviewResponse(
        product_template_code=preview.product_template_code,
        product_template_name=preview.product_template_name,
        material_options=[
            MaterialOptionResponse(
                code=item.code,
                name=item.name,
                category_code=item.category_code,
                category_name=item.category_name,
                form_factor=item.form_factor,
                density_gsm=item.density_gsm,
                is_printable=item.is_printable,
            )
            for item in preview.material_options
        ],
        selected_material_code=preview.selected_material_code,
        available_operation_codes=preview.available_operation_codes,
        default_route_codes=preview.default_route_codes,
        context=ResolvedContextResponse(
            locale=context.locale,
            currency=context.currency,
            country_code=context.country_code,
            source_locale=context.source_locale,
            source_currency=context.source_currency,
        ),
    )
