from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from catalog.models import Material, ProductTemplate

from .availability import get_available_operations


class RouteValidationError(ValueError):
    """Raised when selected operations are invalid for current route context."""


@dataclass(frozen=True, slots=True)
class RouteStep:
    operation_code: str
    operation_name: str
    operation_group: str
    handler_code: str
    sequence_order: int
    source: str  # required | default | selected


def validate_selected_operation_codes(
    product_template: ProductTemplate,
    material: Material,
    *,
    selected_operation_codes: Iterable[str] | None = None,
) -> tuple[set[str], list[str]]:
    """Validate selected operation codes against available operations."""
    selected_codes = set(selected_operation_codes or [])
    available_operations = get_available_operations(
        product_template=product_template,
        material=material,
    )
    available_codes = {item.operation_type.code for item in available_operations}

    invalid_codes = sorted(selected_codes - available_codes)
    return selected_codes, invalid_codes


def build_route(
    product_template: ProductTemplate,
    material: Material,
    *,
    selected_operation_codes: Iterable[str] | None = None,
    strict: bool = False,
    locale: str = "uk",
) -> list[RouteStep]:
    """Build a simple production route for given template and material."""
    selected_codes, invalid_codes = validate_selected_operation_codes(
        product_template=product_template,
        material=material,
        selected_operation_codes=selected_operation_codes,
    )

    if strict and invalid_codes:
        raise RouteValidationError(
            "Invalid selected operations for current template/material: "
            + ", ".join(invalid_codes)
        )

    available_operations = get_available_operations(
        product_template=product_template,
        material=material,
    )

    route: list[RouteStep] = []

    for item in available_operations:
        source: str | None = None

        if item.is_required:
            source = "required"
        elif item.default_enabled:
            source = "default"
        elif item.operation_type.code in selected_codes:
            source = "selected"

        if source is None:
            continue

        route.append(
            RouteStep(
                operation_code=item.operation_type.code,
                operation_name=item.operation_type.get_name(locale),
                operation_group=item.operation_type.group,
                handler_code=item.operation_type.handler_code,
                sequence_order=item.sequence_order,
                source=source,
            )
        )

    route.sort(key=lambda step: (step.sequence_order, step.operation_code))
    return route