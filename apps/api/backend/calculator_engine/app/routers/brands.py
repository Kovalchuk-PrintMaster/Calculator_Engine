from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from calculator_engine.adapters.django_bootstrap import setup_django
from calculator_engine.app.dependencies.context import get_request_context
from calculator_engine.shared.request_context import ResolvedRequestContext


router = APIRouter(
    prefix="/catalog/brands",
    tags=["catalog"],
    responses={404: {"description": "Not found"}},
)


class BrandTemplateOptionResponse(BaseModel):
    code: str
    name: str
    product_type_code: str
    product_type_name: str
    default_enabled: bool
    sort_order: int


class BrandResolvedContextResponse(BaseModel):
    locale: str
    currency: str
    country_code: str | None
    source_locale: str
    source_currency: str
    skin_code: str | None


class BrandCatalogResponse(BaseModel):
    brand_code: str
    brand_name: str
    region_code: str
    default_locale: str
    default_currency: str
    default_skin_code: str | None
    templates: list[BrandTemplateOptionResponse]
    context: BrandResolvedContextResponse


@router.get(
    "/{brand_code}/templates",
    summary="Get visible templates for brand",
    response_model=BrandCatalogResponse,
)
def get_brand_templates(
    brand_code: str,
    context: ResolvedRequestContext = Depends(get_request_context),
) -> BrandCatalogResponse:
    setup_django()

    from catalog.models import UiBrand
    from catalog.services import build_brand_catalog_projection

    try:
        brand = UiBrand.objects.select_related("default_skin").get(code=brand_code, active=True)
    except UiBrand.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail=f"UiBrand not found: {brand_code}") from exc

    if context.source_locale == "explicit":
        effective_locale = context.locale
        locale_source = context.source_locale
    else:
        effective_locale = brand.default_locale or context.locale
        locale_source = "brand-default" if brand.default_locale else context.source_locale

    if context.source_currency == "explicit":
        effective_currency = context.currency
        currency_source = context.source_currency
    else:
        effective_currency = brand.default_currency or context.currency
        currency_source = "brand-default" if brand.default_currency else context.source_currency

    projection = build_brand_catalog_projection(
        brand=brand,
        locale=effective_locale,
    )

    return BrandCatalogResponse(
        brand_code=projection.brand_code,
        brand_name=projection.brand_name,
        region_code=projection.region_code,
        default_locale=projection.default_locale,
        default_currency=projection.default_currency,
        default_skin_code=projection.default_skin_code,
        templates=[
            BrandTemplateOptionResponse(
                code=item.code,
                name=item.name,
                product_type_code=item.product_type_code,
                product_type_name=item.product_type_name,
                default_enabled=item.default_enabled,
                sort_order=item.sort_order,
            )
            for item in projection.templates
        ],
        context=BrandResolvedContextResponse(
            locale=effective_locale,
            currency=effective_currency,
            country_code=context.country_code,
            source_locale=locale_source,
            source_currency=currency_source,
            skin_code=projection.default_skin_code,
        ),
    )