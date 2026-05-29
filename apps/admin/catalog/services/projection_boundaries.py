from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


ProjectionUsage = Literal[
    "calculation_input",
    "projection_cache",
    "snapshot",
    "canonical_truth",
    "global_registry",
    "library_replacement",
]

ProjectionKind = Literal[
    "library_import_projection",
    "local_projection",
    "calculation_snapshot",
]


NON_CANONICAL_PROJECTION_ENTITIES = frozenset(
    {
        "material_category",
        "material",
        "operation_type",
        "product_type",
        "product_template",
        "ui_brand",
        "ui_skin",
        "template_visibility",
        "imported_catalog_structure",
    }
)

ALLOWED_PROJECTION_USAGES = frozenset(
    {
        "calculation_input",
        "projection_cache",
        "snapshot",
    }
)

FORBIDDEN_PROJECTION_USAGES = frozenset(
    {
        "canonical_truth",
        "global_registry",
        "library_replacement",
    }
)


class ProjectionBoundaryError(ValueError):
    """Raised when non-canonical projection is treated as canonical data."""


@dataclass(frozen=True, slots=True)
class ProjectionBoundaryDescriptor:
    entity_type: str
    code: str
    source_system: str
    is_projection: bool
    is_canonical: bool
    projection_kind: ProjectionKind
    allowed_usages: tuple[str, ...]
    forbidden_usages: tuple[str, ...]


def _normalize(value: str | None) -> str:
    return str(value or "").strip().lower()


def build_projection_boundary_descriptor(
    *,
    entity_type: str,
    code: str,
    source_system: str | None,
) -> ProjectionBoundaryDescriptor:
    normalized_entity_type = _normalize(entity_type)
    normalized_code = str(code or "").strip()
    normalized_source_system = _normalize(source_system)

    if normalized_entity_type not in NON_CANONICAL_PROJECTION_ENTITIES:
        raise ProjectionBoundaryError(
            f"Unsupported non-canonical projection entity type: {entity_type}"
        )

    projection_kind: ProjectionKind
    if normalized_source_system == "library":
        projection_kind = "library_import_projection"
    elif normalized_source_system in {"snapshot", "imported_snapshot"}:
        projection_kind = "calculation_snapshot"
    else:
        projection_kind = "local_projection"

    return ProjectionBoundaryDescriptor(
        entity_type=normalized_entity_type,
        code=normalized_code,
        source_system=normalized_source_system,
        is_projection=True,
        is_canonical=False,
        projection_kind=projection_kind,
        allowed_usages=tuple(sorted(ALLOWED_PROJECTION_USAGES)),
        forbidden_usages=tuple(sorted(FORBIDDEN_PROJECTION_USAGES)),
    )


def assert_projection_usage(
    *,
    entity_type: str,
    code: str,
    source_system: str | None,
    intended_usage: ProjectionUsage,
) -> ProjectionBoundaryDescriptor:
    descriptor = build_projection_boundary_descriptor(
        entity_type=entity_type,
        code=code,
        source_system=source_system,
    )

    if intended_usage in FORBIDDEN_PROJECTION_USAGES:
        raise ProjectionBoundaryError(
            f"{descriptor.entity_type}:{descriptor.code} is a non-canonical "
            f"{descriptor.projection_kind} and cannot be used as {intended_usage}."
        )

    if intended_usage not in ALLOWED_PROJECTION_USAGES:
        raise ProjectionBoundaryError(
            f"Unsupported projection usage: {intended_usage}"
        )

    return descriptor