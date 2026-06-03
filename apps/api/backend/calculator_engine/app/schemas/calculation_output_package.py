from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from calculator_engine.app.schemas.material_consumption import (
    MaterialConsumptionEstimateSchema,
)
from calculator_engine.app.schemas.reports import (
    QuoteLineSchema,
    QuoteRouteStepSchema,
)


class ValidationWarningSchema(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"
    field: str | None = None


class ManualCustomOperationDraftSchema(BaseModel):
    operation_code: str
    display_name: str
    reason: str
    price_impact: Decimal | str
    currency: str
    notes: str | None = None


class PriceBreakdownSchema(BaseModel):
    currency: str
    subtotal: Decimal | str
    total: Decimal | str
    route: list[QuoteRouteStepSchema]
    lines: list[QuoteLineSchema]


class QuoteDraftSchema(BaseModel):
    quote_id: str
    calculation_id: str
    source: str
    brand_code: str
    product_template_code: str
    material_code: str
    quantity: int
    currency: str
    subtotal: Decimal | str
    total: Decimal | str
    selected_operation_codes: list[str]
    route_codes: list[str]
    summary_lines: list[str] = Field(default_factory=list)


class OrderDraftSchema(BaseModel):
    order_draft_id: str
    calculation_id: str
    source: str
    brand_code: str
    customer_ref: str | None = None
    external_order_ref: str | None = None
    external_customer_ref: str | None = None
    product_template_code: str
    material_code: str
    quantity: int
    currency: str
    estimated_total: Decimal | str
    selected_operation_codes: list[str]
    downstream_refs: dict[str, str | None] = Field(default_factory=dict)


class ProductionMethodPlanSchema(BaseModel):
    method_code: str
    method_name: str
    route_codes: list[str]
    assumptions: list[str] = Field(default_factory=list)


class OperationSequenceSchema(BaseModel):
    route_codes: list[str]
    steps: list[QuoteRouteStepSchema]


class AccountingLineDraftSchema(BaseModel):
    code: str
    name: str
    category: str
    amount: Decimal | str
    currency: str
    quantity: int
    unit: str


class PrepressRequirementDraftSchema(BaseModel):
    requirement_code: str
    title: str
    description: str
    required: bool
    source: str


class SourceContextSchema(BaseModel):
    origin: str
    source: str
    brand_code: str
    used_catalog_source: str
    calculation_mode: str
    source_locale: str | None = None
    source_currency: str | None = None


class CalculationOutputPackageSchema(BaseModel):
    package_id: str
    calculation_id: str
    quote_draft: QuoteDraftSchema
    order_draft: OrderDraftSchema
    price_breakdown: PriceBreakdownSchema
    material_consumption_estimate: MaterialConsumptionEstimateSchema
    production_method_plan: ProductionMethodPlanSchema
    operation_sequence: OperationSequenceSchema
    accounting_line_drafts: list[AccountingLineDraftSchema]
    prepress_requirement_drafts: list[PrepressRequirementDraftSchema]
    validation_warnings: list[ValidationWarningSchema] = Field(default_factory=list)
    manual_custom_operation_drafts: list[ManualCustomOperationDraftSchema] = Field(
        default_factory=list
    )
    source_context: SourceContextSchema
    created_at: str