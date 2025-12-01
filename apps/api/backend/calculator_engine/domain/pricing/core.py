"""
Pricing domain core (stub).

Purpose:
    Provide a pure function to compute a quote for a given product configuration.
    This is a TEMPORARY stub: no DB access, no Redis, only deterministic math,
    so unit tests can rely on a stable contract while we develop the engine.

Why pure:
    Pure functions are easier to test and reason about. I/O (DB/cache) will be
    introduced via infra layer later, while keeping this callable as thin as possible.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class QuoteInput:
    """Normalized quote input used by the domain layer."""

    product_id: str
    qty: int
    audience: str  # "b2c" | "b2b" | "partner"
    attributes: Mapping[str, Any] | None = None
    options: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class QuoteOutput:
    """Quote output produced by the domain layer (money in base currency)."""

    unit_price: float
    subtotal: float
    vat: float
    total: float
    lead_time_days: int


def compute_quote(inp: QuoteInput) -> QuoteOutput:
    """Compute a quote (temporary stub with deterministic numbers).

    Design (stub):
        - unit_price is fixed 10.0 for any product.
        - subtotal = unit_price * qty
        - vat = 0.0 (no tax yet; VAT rules will be added later)
        - total = subtotal + vat
        - lead_time_days = 2 (placeholder)

    Args:
        inp: Normalized input (product/qty/audience/...).

    Returns:
        QuoteOutput: monetary breakdown with a placeholder lead time.

    Raises:
        ValueError: if qty < 1 (contract enforcement).
    """
    if inp.qty < 1:
        raise ValueError("qty must be >= 1")

    unit_price = 10.0
    subtotal = unit_price * inp.qty
    vat = 0.0
    total = subtotal + vat
    lead_time_days = 2

    return QuoteOutput(
        unit_price=unit_price,
        subtotal=subtotal,
        vat=vat,
        total=total,
        lead_time_days=lead_time_days,
    )
