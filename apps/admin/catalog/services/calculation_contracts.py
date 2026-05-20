from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class CalculationRequest:
    source: str
    brand_code: str = ""
    customer_ref: str = ""
    external_order_id: str | None = None
    external_customer_id: str | None = None
    idempotency_key: str | None = None

    product_template_code: str = ""
    material_code: str = ""
    quantity: int = 1
    selected_operation_codes: tuple[str, ...] = ()

    locale: str = "en"
    currency: str = "USD"

    input_payload_json: dict = field(default_factory=dict)

    def to_normalized_payload(self) -> dict:
        return {
            "source": self.source,
            "brand_code": self.brand_code,
            "customer_ref": self.customer_ref,
            "external_order_id": self.external_order_id,
            "external_customer_id": self.external_customer_id,
            "idempotency_key": self.idempotency_key,
            "product_template_code": self.product_template_code,
            "material_code": self.material_code,
            "quantity": self.quantity,
            "selected_operation_codes": list(self.selected_operation_codes),
            "locale": self.locale,
            "currency": self.currency,
        }


@dataclass(frozen=True, slots=True)
class CalculationResult:
    calculation_id: str | None
    source: str

    template_code: str
    material_code: str
    quantity: int
    selected_operation_codes: tuple[str, ...]

    locale: str
    currency: str

    route: list
    lines: list
    subtotal: Decimal
    total: Decimal

    human_report_json: dict
    external_report_json: dict