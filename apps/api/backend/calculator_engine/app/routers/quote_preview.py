"""Quote preview router."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from calculator_engine.app.dependencies.context import get_request_context
from calculator_engine.shared.request_context import ResolvedRequestContext

from calculator_engine.adapters.django_bootstrap import setup_django


router = APIRouter(
    prefix="/catalog/templates",
    tags=["catalog"],
    responses={404: {"description": "Not found"}},
)


class QuoteRouteStepResponse(BaseModel):
    operation_code: str
    operation_name: str
    operation_group: str
    handler_code: str
    sequence_order: int
    source: str


class QuoteLineResponse(BaseModel):
    code: str
    name: str
    category: str
    quantity: int
    unit: str
    unit_price: Decimal
    total: Decimal
    meta: dict


class QuotePreviewResponse(BaseModel):
    template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str]
    route: list[QuoteRouteStepResponse]
    lines: list[QuoteLineResponse]
    subtotal: Decimal
    total: Decimal
    currency: str
    context: ResolvedContextResponse
    
class ResolvedContextResponse(BaseModel):
    locale: str
    currency: str
    country_code: str | None
    source_locale: str
    source_currency: str


@router.get(
    "/{template_code}/quote-preview",
    summary="Get quote preview for selected configuration",
    response_model=QuotePreviewResponse,
)
def get_quote_preview(
    template_code: str,
    material_code: str = Query(...),
    quantity: int = Query(..., ge=1),
    selected_operation_codes: list[str] = Query(default_factory=list),
    context: ResolvedRequestContext = Depends(get_request_context),
) -> QuotePreviewResponse:
    """Return route and price breakdown for selected configuration."""
    setup_django()

    from catalog.models import Material, ProductTemplate
    from catalog.services import PricingDataError, RouteValidationError, build_price_quote

    try:
        template = ProductTemplate.objects.get(code=template_code, active=True)
    except ProductTemplate.DoesNotExist as exc:
        raise HTTPException(
            status_code=404,
            detail=f"ProductTemplate not found: {template_code}",
        ) from exc

    try:
        material = Material.objects.get(code=material_code, active=True)
    except Material.DoesNotExist as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {material_code}",
        ) from exc

    try:
        quote = build_price_quote(
            product_template=template,
            material=material,
            quantity=quantity,
            selected_operation_codes=selected_operation_codes,
            strict=True,
            locale=context.locale,
        )
    except RouteValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PricingDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QuotePreviewResponse(
        template_code=template.code,
        material_code=material.code,
        quantity=quantity,
        selected_operation_codes=selected_operation_codes,
        route=[
            QuoteRouteStepResponse(
                operation_code=step.operation_code,
                operation_name=step.operation_name,
                operation_group=step.operation_group,
                handler_code=step.handler_code,
                sequence_order=step.sequence_order,
                source=step.source,
            )
            for step in quote.route
        ],
        lines=[
            QuoteLineResponse(
                code=line.code,
                name=line.name,
                category=line.category,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                total=line.total,
                meta=line.meta,
            )
            for line in quote.lines
        ],
        subtotal=quote.subtotal,
        total=quote.total,
        currency=context.currency,
        context=ResolvedContextResponse(
            locale=context.locale,
            currency=context.currency,
            country_code=context.country_code,
            source_locale=context.source_locale,
            source_currency=context.source_currency,
        ),
    )
    
def get_quote_preview(
    template_code: str,
    material_code: str = Query(...),
    quantity: int = Query(..., ge=1),
    selected_operation_codes: list[str] = Query(default_factory=list),
) -> QuotePreviewResponse:
    """Return route and price breakdown for selected configuration."""
    setup_django()

    from catalog.models import Material, ProductTemplate
    from catalog.services import PricingDataError, RouteValidationError, build_price_quote

    try:
        template = ProductTemplate.objects.get(code=template_code, active=True)
    except ProductTemplate.DoesNotExist as exc:
        raise HTTPException(
            status_code=404,
            detail=f"ProductTemplate not found: {template_code}",
        ) from exc

    try:
        material = Material.objects.get(code=material_code, active=True)
    except Material.DoesNotExist as exc:
        raise HTTPException(
            status_code=404,
            detail=f"Material not found: {material_code}",
        ) from exc

    try:
        quote = build_price_quote(
            product_template=template,
            material=material,
            quantity=quantity,
            selected_operation_codes=selected_operation_codes,
            strict=True,
        )
    except RouteValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PricingDataError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return QuotePreviewResponse(
        template_code=template.code,
        material_code=material.code,
        quantity=quantity,
        selected_operation_codes=selected_operation_codes,
        route=[
            QuoteRouteStepResponse(
                operation_code=step.operation_code,
                operation_name=step.operation_name,
                operation_group=step.operation_group,
                handler_code=step.handler_code,
                sequence_order=step.sequence_order,
                source=step.source,
            )
            for step in quote.route
        ],
        lines=[
            QuoteLineResponse(
                code=line.code,
                name=line.name,
                category=line.category,
                quantity=line.quantity,
                unit=line.unit,
                unit_price=line.unit_price,
                total=line.total,
                meta=line.meta,
            )
            for line in quote.lines
        ],
        subtotal=quote.subtotal,
        total=quote.total,
        currency=context.currency,
        context=ResolvedContextResponse(
            locale=context.locale,
            currency=context.currency,
            country_code=context.country_code,
            source_locale=context.source_locale,
            source_currency=context.source_currency,
        ),
    )