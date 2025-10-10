"""
Price router.

Purpose:
    Expose HTTP endpoints to calculate quotes for product configurations.
    This module handles request/response schemas and delegates math to domain.

Contract (MVP):
    POST /price/quote
        - Request: product_id, qty, audience, optional attributes/options.
        - Response: unit_price, subtotal, vat, total, lead_time_days, breakdown?

Notes:
    - Pydantic v2 models are used for input/output validation.
    - Domain is responsible for pure calculation; router must stay I/O-free.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ...domain.pricing.core import QuoteInput, compute_quote
from ...shared.constants import SUPPORTED_AUDIENCES

router = APIRouter(
    prefix="/price",
    tags=["price"],
    responses={404: {"description": "Not found"}},
)


# ------------------------- Schemas (Pydantic v2) -------------------------------


class QuoteRequest(BaseModel):
    """Input schema for POST /price/quote."""

    product_id: str = Field(..., description="Product identifier (SKU/code).")
    qty: int = Field(..., ge=1, description="Ordered quantity (>= 1).")
    audience: str = Field("b2c", description="Audience segment affects modifiers/output")

    attributes: dict[str, Any] | None = Field(
        default=None, description="Variant attributes (color/size/material/...)"
    )
    options: dict[str, Any] | None = Field(
        default=None, description="Extra options (rush/delivery/finishes/...)"
    )


class QuoteResponse(BaseModel):
    """Output schema for POST /price/quote (stable minimal contract)."""

    unit_price: float
    subtotal: float
    vat: float
    total: float
    lead_time_days: int


# ----------------------------- Endpoints --------------------------------------


@router.post("/quote", summary="Compute a price quote", response_model=QuoteResponse)
def post_quote(req: QuoteRequest) -> QuoteResponse:
    """Compute a quote for the given configuration (temporary stub).

    Validation:
        - Ensures audience is supported.
        - qty validated by Pydantic (>= 1).

    Raises:
        HTTPException(400): if audience is unsupported (defensive).
    """
    if req.audience not in SUPPORTED_AUDIENCES:
        raise HTTPException(status_code=400, detail="Unsupported audience")

    out = compute_quote(
        QuoteInput(
            product_id=req.product_id,
            qty=req.qty,
            audience=req.audience,
            attributes=req.attributes or {},
            options=req.options or {},
        )
    )

    # NOTE: Router does not return domain dataclass directly to keep HTTP schema explicit.
    return QuoteResponse(
        unit_price=out.unit_price,
        subtotal=out.subtotal,
        vat=out.vat,
        total=out.total,
        lead_time_days=out.lead_time_days,
    )
