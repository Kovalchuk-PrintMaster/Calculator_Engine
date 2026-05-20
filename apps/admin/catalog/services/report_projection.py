from __future__ import annotations

from catalog.services.calculation_contracts import CalculationRequest
from catalog.services.pricing import QuoteResult


def _serialize_route_step(step) -> dict:
    return {
        "operation_code": step.operation_code,
        "operation_name": step.operation_name,
        "operation_group": step.operation_group,
        "handler_code": step.handler_code,
        "sequence_order": step.sequence_order,
        "source": step.source,
    }


def _serialize_quote_line(line) -> dict:
    return {
        "code": line.code,
        "name": line.name,
        "category": line.category,
        "quantity": line.quantity,
        "unit": line.unit,
        "unit_price": str(line.unit_price),
        "total": str(line.total),
        "meta": line.meta,
    }


def build_human_quote_report(
    request: CalculationRequest,
    quote: QuoteResult,
    *,
    calculation_id: str | None = None,
) -> dict:
    return {
        "report_type": "human_quote",
        "schema_version": "v1",
        "calculation_id": calculation_id,
        "source": request.source,
        "brand_code": request.brand_code,
        "customer_ref": request.customer_ref,
        "external_order_id": request.external_order_id,
        "product_template_code": request.product_template_code,
        "material_code": request.material_code,
        "quantity": request.quantity,
        "selected_operation_codes": list(request.selected_operation_codes),
        "locale": request.locale,
        "currency": request.currency,
        "route": [_serialize_route_step(step) for step in quote.route],
        "lines": [_serialize_quote_line(line) for line in quote.lines],
        "subtotal": str(quote.subtotal),
        "total": str(quote.total),
    }


def build_external_quote_response(
    request: CalculationRequest,
    quote: QuoteResult,
    *,
    calculation_id: str | None = None,
) -> dict:
    return {
        "report_type": "external_quote",
        "schema_version": "v1",
        "status": "ok",
        "calculation_id": calculation_id,
        "source": request.source,
        "brand_code": request.brand_code,
        "external_order_id": request.external_order_id,
        "external_customer_id": request.external_customer_id,
        "product_template_code": request.product_template_code,
        "material_code": request.material_code,
        "quantity": request.quantity,
        "selected_operation_codes": list(request.selected_operation_codes),
        "route_codes": [step.operation_code for step in quote.route],
        "lines": [_serialize_quote_line(line) for line in quote.lines],
        "subtotal": str(quote.subtotal),
        "total": str(quote.total),
        "currency": request.currency,

    }