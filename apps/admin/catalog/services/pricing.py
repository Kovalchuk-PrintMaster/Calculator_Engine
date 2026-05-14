from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_UP

from catalog.models import Material, MaterialPrice, OperationPrice, ProductTemplate

from .route_builder import RouteStep, build_route


class PricingDataError(ValueError):
    """Raised when pricing data is missing or unsupported."""


@dataclass(frozen=True, slots=True)
class QuoteLine:
    code: str
    name: str
    category: str
    quantity: int
    unit: str
    unit_price: Decimal
    total: Decimal
    meta: dict


@dataclass(frozen=True, slots=True)
class QuoteResult:
    quantity: int
    route: list[RouteStep]
    lines: list[QuoteLine]
    subtotal: Decimal
    total: Decimal


def _round_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal("0.01"))


def _apply_waste(quantity: int, waste_percent: Decimal) -> int:
    multiplier = Decimal("1.00") + (waste_percent / Decimal("100.00"))
    return int((Decimal(quantity) * multiplier).quantize(Decimal("1"), rounding=ROUND_UP))


def build_price_quote(
    product_template: ProductTemplate,
    material: Material,
    *,
    quantity: int,
    selected_operation_codes: list[str] | None = None,
    strict: bool = True,
    locale: str = "uk",
) -> QuoteResult:
    """Build a simple demo price quote based on route and base prices."""
    if quantity <= 0:
        raise PricingDataError("Quantity must be greater than zero.")

    route = build_route(
        product_template=product_template,
        material=material,
        selected_operation_codes=selected_operation_codes,
        strict=strict,
        locale=locale,
    )

    try:
        material_price = MaterialPrice.objects.get(material=material, active=True)
    except MaterialPrice.DoesNotExist as exc:
        raise PricingDataError(
            f"Missing active material price for material: {material.code}"
        ) from exc

    if material_price.unit not in {"sheet", "item"}:
        raise PricingDataError(
            f"Unsupported material price unit for v1: {material_price.unit}"
        )

    effective_material_quantity = _apply_waste(quantity, material_price.waste_percent)
    material_total = _round_money(material_price.price * Decimal(effective_material_quantity))

    lines: list[QuoteLine] = [
        QuoteLine(
            code=f"material:{material.code}",
            name=material.get_name(locale),
            category="material",
            quantity=effective_material_quantity,
            unit=material_price.unit,
            unit_price=material_price.price,
            total=material_total,
            meta={
                "requested_quantity": quantity,
                "waste_percent": str(material_price.waste_percent),
            },
        )
    ]

    subtotal = material_total

    for step in route:
        try:
            operation_price = OperationPrice.objects.get(
                operation_type__code=step.operation_code,
                active=True,
            )
        except OperationPrice.DoesNotExist as exc:
            raise PricingDataError(
                f"Missing active operation price for operation: {step.operation_code}"
            ) from exc

        if operation_price.unit == "order":
            billed_quantity = 1
        elif operation_price.unit in {"item", "sheet"}:
            billed_quantity = quantity
        else:
            raise PricingDataError(
                f"Unsupported operation price unit for v1: {operation_price.unit}"
            )

        total = _round_money(
            operation_price.setup_price
            + (operation_price.unit_price * Decimal(billed_quantity))
        )

        lines.append(
            QuoteLine(
                code=f"operation:{step.operation_code}",
                name=step.operation_name,
                category="operation",
                quantity=billed_quantity,
                unit=operation_price.unit,
                unit_price=operation_price.unit_price,
                total=total,
                meta={
                    "setup_price": str(operation_price.setup_price),
                    "group": step.operation_group,
                    "handler_code": step.handler_code,
                    "source": step.source,
                },
            )
        )
        subtotal += total

    subtotal = _round_money(subtotal)

    return QuoteResult(
        quantity=quantity,
        route=route,
        lines=lines,
        subtotal=subtotal,
        total=subtotal,
    )