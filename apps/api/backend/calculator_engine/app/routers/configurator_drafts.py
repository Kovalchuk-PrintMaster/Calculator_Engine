from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Body, Depends
from pydantic import BaseModel, Field
from decimal import Decimal

from calculator_engine.app.api_errors import (
    ApiMeta,
    build_api_error_response,
    build_api_meta,
)
from calculator_engine.app.dependencies.context import get_request_context
from calculator_engine.app.services.configurator_drafts import (
    ConfiguratorDraftBrandError,
    ConfiguratorDraftNotFoundError,
    ConfiguratorDraftValidationError,
    create_configurator_draft,
    get_configurator_draft,
    update_configurator_draft,
)
from calculator_engine.shared.request_context import ResolvedRequestContext

from calculator_engine.app.services.configurator_context import (
    ConfiguratorContextNotFoundError,
    ConfiguratorContextValidationError,
    build_configurator_draft_context,
    build_configurator_draft_quote_preview,
)

from calculator_engine.app.schemas.reports import (
    ExternalQuoteReportSchema,
    HumanQuoteReportSchema,
)
from calculator_engine.app.services.configurator_submit import (
    ConfiguratorSubmitNotFoundError,
    ConfiguratorSubmitValidationError,
    submit_configurator_draft,
)

from calculator_engine.app.schemas.material_consumption import MaterialConsumptionEstimateSchema
from calculator_engine.app.services.material_consumption_projection import (
    MaterialConsumptionProjectionNotFoundError,
    MaterialConsumptionProjectionValidationError,
    build_draft_material_consumption_estimate,
)

router = APIRouter(
    prefix="/configurator/drafts",
    tags=["configurator"],
)

class ConfiguratorMaterialOptionSchema(BaseModel):
    code: str
    name: str
    category_code: str
    category_name: str
    form_factor: str
    density_gsm: int | None
    is_printable: bool


class ConfiguratorDraftContextData(BaseModel):
    draft_id: str
    step: str
    brand_code: str
    locale: str
    currency: str
    product_template_code: str | None
    material_code: str | None
    quantity: int | None
    selected_operation_codes: list[str]
    available_operation_codes: list[str]
    default_route_codes: list[str]
    material_options: list[ConfiguratorMaterialOptionSchema]
    missing_fields: list[str]
    can_select_material: bool
    can_quote: bool


class ConfiguratorDraftContextEnvelope(BaseModel):
    status: Literal["ok"]
    data: ConfiguratorDraftContextData
    meta: ApiMeta


class ConfiguratorDraftQuoteRouteStepSchema(BaseModel):
    operation_code: str
    operation_name: str
    operation_group: str
    handler_code: str
    sequence_order: int
    source: str


class ConfiguratorDraftQuoteLineSchema(BaseModel):
    code: str
    name: str
    category: str
    quantity: int
    unit: str
    unit_price: str
    total: str
    meta: dict[str, Any]


class ConfiguratorDraftQuotePreviewData(BaseModel):
    draft_id: str
    step: str
    locale: str
    currency: str
    product_template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: list[str]
    route: list[ConfiguratorDraftQuoteRouteStepSchema]
    lines: list[ConfiguratorDraftQuoteLineSchema]
    subtotal: Decimal
    total: Decimal


class ConfiguratorDraftQuotePreviewEnvelope(BaseModel):
    status: Literal["ok"]
    data: ConfiguratorDraftQuotePreviewData
    meta: ApiMeta

class ConfiguratorDraftSubmitRequest(BaseModel):
    source: str = "manual"
    customer_ref: str = ""


class ConfiguratorDraftSubmitContextSchema(BaseModel):
    locale: str
    currency: str
    source_locale: str
    source_currency: str
    brand_code: str


class ConfiguratorDraftSubmitData(BaseModel):
    draft_id: str
    job_public_id: str
    status: str
    source: str
    reused: bool
    locale: str
    currency: str
    subtotal: Decimal
    total: Decimal
    context: ConfiguratorDraftSubmitContextSchema
    human_report: HumanQuoteReportSchema
    external_report: ExternalQuoteReportSchema


class ConfiguratorDraftSubmitEnvelope(BaseModel):
    status: Literal["ok"]
    data: ConfiguratorDraftSubmitData
    meta: ApiMeta    

class ConfiguratorDraftSubmitRequest(BaseModel):
    source: str = "manual"
    customer_ref: str = ""


class ConfiguratorDraftSubmitContextSchema(BaseModel):
    locale: str
    currency: str
    source_locale: str
    source_currency: str
    brand_code: str


class ConfiguratorDraftSubmitData(BaseModel):
    draft_id: str
    job_public_id: str
    status: str
    source: str
    reused: bool
    locale: str
    currency: str
    subtotal: Decimal
    total: Decimal
    context: ConfiguratorDraftSubmitContextSchema
    human_report: HumanQuoteReportSchema
    external_report: ExternalQuoteReportSchema


class ConfiguratorDraftSubmitEnvelope(BaseModel):
    status: Literal["ok"]
    data: ConfiguratorDraftSubmitData
    meta: ApiMeta


class ConfiguratorClientSchema(BaseModel):
    channel: str = "web"
    device: str = "unknown"
    app_version: str | None = None
    platform: str | None = None


class ConfiguratorDraftCreateRequest(BaseModel):
    brand_code: str = ""
    locale: str | None = None
    currency: str | None = None
    client: ConfiguratorClientSchema = Field(default_factory=ConfiguratorClientSchema)
    state: dict[str, Any] = Field(default_factory=dict)


class ConfiguratorDraftPatchRequest(BaseModel):
    product_template_code: str | None = None
    material_code: str | None = None
    quantity: int | None = None
    selected_operation_codes: list[str] | None = None
    state: dict[str, Any] | None = None


class ConfiguratorDraftData(BaseModel):
    draft_id: str
    status: str
    step: str
    brand_code: str
    product_template_code: str | None
    material_code: str | None
    quantity: int | None
    selected_operation_codes: list[str]
    locale: str
    currency: str
    client: dict[str, Any]
    state: dict[str, Any]
    created_at: str
    updated_at: str


class ConfiguratorDraftEnvelope(BaseModel):
    status: Literal["ok"]
    data: ConfiguratorDraftData
    meta: ApiMeta

class MaterialConsumptionEstimateEnvelope(BaseModel):
    status: Literal["ok"]
    data: MaterialConsumptionEstimateSchema
    meta: ApiMeta


def _to_envelope(result: Any) -> ConfiguratorDraftEnvelope:
    return ConfiguratorDraftEnvelope(
        status="ok",
        data=ConfiguratorDraftData(
            draft_id=result.draft_id,
            status=result.status,
            step=result.step,
            brand_code=result.brand_code,
            product_template_code=result.product_template_code,
            material_code=result.material_code,
            quantity=result.quantity,
            selected_operation_codes=result.selected_operation_codes,
            locale=result.locale,
            currency=result.currency,
            client=result.client,
            state=result.state,
            created_at=result.created_at,
            updated_at=result.updated_at,
        ),
        meta=build_api_meta(),
    )


@router.post("", response_model=ConfiguratorDraftEnvelope, summary="Create configurator draft")
def create_draft(
    payload: ConfiguratorDraftCreateRequest = Body(...),
    context: ResolvedRequestContext = Depends(get_request_context),
):
    try:
        result = create_configurator_draft(
            brand_code=payload.brand_code,
            locale=payload.locale,
            currency=payload.currency,
            request_context_locale=context.locale,
            request_context_currency=context.currency,
            client_meta=payload.client.model_dump(mode="python"),
            state=payload.state,
        )
    except ConfiguratorDraftBrandError as exc:
        return build_api_error_response(
            status_code=400,
            code="brand_not_found",
            message="Brand not found.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorDraftValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="invalid_draft_payload",
            message="Draft payload is invalid.",
            detail=str(exc),
            retryable=False,
        )

    return _to_envelope(result)

@router.get(
    "/{draft_id}",
    response_model=ConfiguratorDraftEnvelope,
    summary="Get configurator draft",
)
def get_draft(draft_id: str):
    try:
        result = get_configurator_draft(draft_id=draft_id)
    except ConfiguratorDraftValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="invalid_draft_id",
            message="Draft id is invalid.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorDraftNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return _to_envelope(result)


@router.get(
    "/{draft_id}/context",
    response_model=ConfiguratorDraftContextEnvelope,
    summary="Get configurator draft context",
)
def get_draft_context(draft_id: str):
    try:
        result = build_configurator_draft_context(draft_id=draft_id)
    except ConfiguratorContextValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="invalid_draft_context",
            message="Draft context is invalid.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorContextNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return ConfiguratorDraftContextEnvelope(
        status="ok",
        data=ConfiguratorDraftContextData(
            draft_id=result.draft_id,
            step=result.step,
            brand_code=result.brand_code,
            locale=result.locale,
            currency=result.currency,
            product_template_code=result.product_template_code,
            material_code=result.material_code,
            quantity=result.quantity,
            selected_operation_codes=result.selected_operation_codes,
            available_operation_codes=result.available_operation_codes,
            default_route_codes=result.default_route_codes,
            material_options=[
                ConfiguratorMaterialOptionSchema(
                    code=item.code,
                    name=item.name,
                    category_code=item.category_code,
                    category_name=item.category_name,
                    form_factor=item.form_factor,
                    density_gsm=item.density_gsm,
                    is_printable=item.is_printable,
                )
                for item in result.material_options
            ],
            missing_fields=result.missing_fields,
            can_select_material=result.can_select_material,
            can_quote=result.can_quote,
        ),
        meta=build_api_meta(),
    )


@router.get(
    "/{draft_id}/quote-preview",
    response_model=ConfiguratorDraftQuotePreviewEnvelope,
    summary="Get configurator draft quote preview",
)
def get_draft_quote_preview(draft_id: str):
    try:
        result = build_configurator_draft_quote_preview(draft_id=draft_id)
    except ConfiguratorContextValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="draft_not_ready_for_quote",
            message="Draft is not ready for quote preview.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorContextNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return ConfiguratorDraftQuotePreviewEnvelope(
        status="ok",
        data=ConfiguratorDraftQuotePreviewData(
            draft_id=result.draft_id,
            step=result.step,
            locale=result.locale,
            currency=result.currency,
            product_template_code=result.product_template_code,
            material_code=result.material_code,
            quantity=result.quantity,
            selected_operation_codes=result.selected_operation_codes,
            route=[
                ConfiguratorDraftQuoteRouteStepSchema(
                    operation_code=item.operation_code,
                    operation_name=item.operation_name,
                    operation_group=item.operation_group,
                    handler_code=item.handler_code,
                    sequence_order=item.sequence_order,
                    source=item.source,
                )
                for item in result.route
            ],
            lines=[
                ConfiguratorDraftQuoteLineSchema(
                    code=item.code,
                    name=item.name,
                    category=item.category,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    total=item.total,
                    meta=item.meta,
                )
                for item in result.lines
            ],
            subtotal=result.subtotal,
            total=result.total,
        ),
        meta=build_api_meta(),
    )

@router.get(
    "/{draft_id}/material-consumption-estimate",
    response_model=MaterialConsumptionEstimateEnvelope,
    summary="Get configurator draft material consumption estimate",
)
def get_draft_material_consumption_estimate(draft_id: str):
    try:
        result = build_draft_material_consumption_estimate(draft_id=draft_id)
    except MaterialConsumptionProjectionValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="draft_not_ready_for_material_consumption_estimate",
            message="Draft is not ready for material consumption estimate.",
            detail=str(exc),
            retryable=False,
        )
    except MaterialConsumptionProjectionNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return MaterialConsumptionEstimateEnvelope(
        status="ok",
        data=MaterialConsumptionEstimateSchema.model_validate(result.__dict__),
        meta=build_api_meta(),
    )

@router.post(
    "/{draft_id}/submit",
    response_model=ConfiguratorDraftSubmitEnvelope,
    summary="Submit configurator draft",
)
def submit_draft(
    draft_id: str,
    payload: ConfiguratorDraftSubmitRequest = Body(default_factory=ConfiguratorDraftSubmitRequest),
    context: ResolvedRequestContext = Depends(get_request_context),
):
    try:
        result = submit_configurator_draft(
            draft_id=draft_id,
            source=payload.source,
            customer_ref=payload.customer_ref,
            request_context_locale=context.locale,
            request_context_currency=context.currency,
        )
    except ConfiguratorSubmitValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="draft_not_ready_for_submit",
            message="Draft is not ready for submit.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorSubmitNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return ConfiguratorDraftSubmitEnvelope(
        status="ok",
        data=ConfiguratorDraftSubmitData(
            draft_id=result.draft_id,
            job_public_id=result.job_public_id,
            status=result.status,
            source=result.source,
            reused=result.reused,
            locale=result.locale,
            currency=result.currency,
            subtotal=result.subtotal,
            total=result.total,
            context=ConfiguratorDraftSubmitContextSchema(
                locale=result.context.locale,
                currency=result.context.currency,
                source_locale=result.context.source_locale,
                source_currency=result.context.source_currency,
                brand_code=result.context.brand_code,
            ),
            human_report=result.human_report,
            external_report=result.external_report,
        ),
        meta=build_api_meta(),
    )

@router.patch(
    "/{draft_id}",
    response_model=ConfiguratorDraftEnvelope,
    summary="Update configurator draft",
)
def patch_draft(
    draft_id: str,
    payload: ConfiguratorDraftPatchRequest = Body(...),
):
    try:
        result = update_configurator_draft(
            draft_id=draft_id,
            product_template_code=payload.product_template_code,
            material_code=payload.material_code,
            quantity=payload.quantity,
            selected_operation_codes=payload.selected_operation_codes,
            state=payload.state,
        )
    except ConfiguratorDraftValidationError as exc:
        return build_api_error_response(
            status_code=400,
            code="invalid_draft_payload",
            message="Draft payload is invalid.",
            detail=str(exc),
            retryable=False,
        )
    except ConfiguratorDraftNotFoundError as exc:
        return build_api_error_response(
            status_code=404,
            code="draft_not_found",
            message="Draft not found.",
            detail=str(exc),
            retryable=False,
        )

    return _to_envelope(result)