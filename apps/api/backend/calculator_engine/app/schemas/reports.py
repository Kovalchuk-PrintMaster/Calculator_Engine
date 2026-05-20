from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class QuoteRouteStepSchema(BaseModel):
    operation_code: str
    operation_name: str
    operation_group: str
    handler_code: str
    sequence_order: int
    source: str


class QuoteLineSchema(BaseModel):
    code: str
    name: str
    category: str
    quantity: int
    unit: str
    unit_price: Decimal | str
    total: Decimal | str
    meta: dict


class HumanQuoteReportSchema(BaseModel):
    report_type: str
    schema_version: str
    calculation_id: str | None
    source: str
    brand_code: str
    customer_ref: str
    external_order_id: str | None
    product_template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str]
    locale: str
    currency: str
    route: list[QuoteRouteStepSchema]
    lines: list[QuoteLineSchema]
    subtotal: Decimal | str
    total: Decimal | str


class ExternalQuoteReportSchema(BaseModel):
    report_type: str
    schema_version: str
    status: str
    calculation_id: str | None
    source: str
    brand_code: str
    external_order_id: str | None
    external_customer_id: str | None
    product_template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str]
    route_codes: list[str]
    lines: list[QuoteLineSchema]
    subtotal: Decimal | str
    total: Decimal | str
    currency: str