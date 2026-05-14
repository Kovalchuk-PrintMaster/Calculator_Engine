from __future__ import annotations

from dataclasses import dataclass

from catalog.models import (
    Material,
    MaterialOperationCapability,
    OperationType,
    ProductTemplate,
    ProductTemplateOperation,
)


@dataclass(frozen=True, slots=True)
class AvailableOperation:
    operation_type: OperationType
    is_required: bool
    is_optional: bool
    default_enabled: bool
    sequence_order: int
    material_priority: int
    material_constraints: dict
    template_constraints: dict


def is_material_allowed_for_template(
    product_template: ProductTemplate,
    material: Material,
) -> bool:
    """Check whether material category is allowed by template."""

    allowed_categories = product_template.allowed_material_categories_json or []
    if not allowed_categories:
        return True

    if material.category_id is None:
        return False

    return material.category.code in allowed_categories


def get_available_operations(
    product_template: ProductTemplate,
    material: Material,
) -> list[AvailableOperation]:
    """Return operations allowed both by template and by material."""

    if not product_template.active or not material.active:
        return []

    if not is_material_allowed_for_template(product_template, material):
        return []

    material_capabilities = (
        MaterialOperationCapability.objects.select_related("operation_type")
        .filter(
            material=material,
            active=True,
            is_allowed=True,
            operation_type__active=True,
        )
        .order_by("priority", "operation_type__sort_order", "operation_type__name_uk")
    )

    template_operations = (
        ProductTemplateOperation.objects.select_related("operation_type")
        .filter(
            product_template=product_template,
            active=True,
            operation_type__active=True,
        )
        .order_by("sequence_order", "operation_type__sort_order", "operation_type__name_uk")
    )

    material_by_operation_id = {
        cap.operation_type_id: cap
        for cap in material_capabilities
    }

    result: list[AvailableOperation] = []
    for template_op in template_operations:
        material_cap = material_by_operation_id.get(template_op.operation_type_id)
        if material_cap is None:
            continue

        result.append(
            AvailableOperation(
                operation_type=template_op.operation_type,
                is_required=template_op.is_required,
                is_optional=template_op.is_optional,
                default_enabled=template_op.default_enabled,
                sequence_order=template_op.sequence_order,
                material_priority=material_cap.priority,
                material_constraints=material_cap.constraints_json or {},
                template_constraints=template_op.constraints_json or {},
            )
        )

    return result