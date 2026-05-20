from __future__ import annotations

from typing import Literal

from fastapi.responses import JSONResponse
from pydantic import BaseModel

from calculator_engine.shared.request_context import REQUEST_ID_VAR


class ApiMeta(BaseModel):
    schema_version: str
    request_id: str


class ApiErrorBody(BaseModel):
    code: str
    message: str
    detail: str
    request_id: str
    retryable: bool


class ApiErrorEnvelope(BaseModel):
    status: Literal["error"]
    error: ApiErrorBody
    meta: ApiMeta


def build_api_meta() -> ApiMeta:
    request_id = REQUEST_ID_VAR.get("-")
    return ApiMeta(
        schema_version="v1",
        request_id=request_id,
    )


def build_api_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    detail: str,
    retryable: bool = False,
) -> JSONResponse:
    request_id = REQUEST_ID_VAR.get("-")
    payload = ApiErrorEnvelope(
        status="error",
        error=ApiErrorBody(
            code=code,
            message=message,
            detail=detail,
            request_id=request_id,
            retryable=retryable,
        ),
        meta=build_api_meta(),
    )
    return JSONResponse(
        status_code=status_code,
        content=payload.model_dump(mode="json"),
    )


def build_intake_processing_error_response(detail: str) -> JSONResponse:
    if detail.startswith("UiBrand not found:"):
        return build_api_error_response(
            status_code=400,
            code="brand_not_found",
            message="Brand not found.",
            detail=detail,
            retryable=False,
        )

    if detail.startswith("Material not found:"):
        return build_api_error_response(
            status_code=400,
            code="material_not_found",
            message="Material not found.",
            detail=detail,
            retryable=False,
        )

    if detail.startswith("ProductTemplate not found:"):
        return build_api_error_response(
            status_code=400,
            code="product_template_not_found",
            message="Product template not found.",
            detail=detail,
            retryable=False,
        )

    if detail.startswith("Invalid selected operations"):
        return build_api_error_response(
            status_code=400,
            code="invalid_selected_operations",
            message="Selected operations are invalid for current configuration.",
            detail=detail,
            retryable=False,
        )

    if detail.startswith("Quantity is required.") or detail.startswith("Quantity must"):
        return build_api_error_response(
            status_code=400,
            code="invalid_quantity",
            message="Quantity is invalid.",
            detail=detail,
            retryable=False,
        )

    if detail.startswith("selected_operation_codes must be a list."):
        return build_api_error_response(
            status_code=400,
            code="invalid_selected_operation_codes",
            message="selected_operation_codes must be a list.",
            detail=detail,
            retryable=False,
        )

    return build_api_error_response(
        status_code=400,
        code="intake_processing_error",
        message="Intake request cannot be processed.",
        detail=detail,
        retryable=False,
    )