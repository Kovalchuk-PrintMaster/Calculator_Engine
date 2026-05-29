from __future__ import annotations

from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.services import (
    ProjectionBoundaryError,
    assert_projection_usage,
    build_projection_boundary_descriptor,
)


def test_library_material_is_projection_only() -> None:
    descriptor = build_projection_boundary_descriptor(
        entity_type="material",
        code="tintoretto_neve_300",
        source_system="library",
    )

    assert descriptor.is_projection is True
    assert descriptor.is_canonical is False
    assert descriptor.projection_kind == "library_import_projection"


def test_library_material_allows_calculation_input_usage() -> None:
    descriptor = assert_projection_usage(
        entity_type="material",
        code="tintoretto_neve_300",
        source_system="library",
        intended_usage="calculation_input",
    )

    assert descriptor.is_projection is True
    assert descriptor.is_canonical is False


def test_library_material_rejects_canonical_truth_usage() -> None:
    try:
        assert_projection_usage(
            entity_type="material",
            code="tintoretto_neve_300",
            source_system="library",
            intended_usage="canonical_truth",
        )
    except ProjectionBoundaryError as exc:
        assert "non-canonical" in str(exc)
        assert "canonical_truth" in str(exc)
    else:
        raise AssertionError("Expected ProjectionBoundaryError")


def test_ui_brand_rejects_global_registry_usage() -> None:
    try:
        assert_projection_usage(
            entity_type="ui_brand",
            code="printmaster_pl",
            source_system="library",
            intended_usage="global_registry",
        )
    except ProjectionBoundaryError as exc:
        assert "global_registry" in str(exc)
    else:
        raise AssertionError("Expected ProjectionBoundaryError")


def test_local_product_template_is_still_non_canonical_projection() -> None:
    descriptor = build_projection_boundary_descriptor(
        entity_type="product_template",
        code="business_card_standard",
        source_system="local",
    )

    assert descriptor.is_projection is True
    assert descriptor.is_canonical is False
    assert descriptor.projection_kind == "local_projection"