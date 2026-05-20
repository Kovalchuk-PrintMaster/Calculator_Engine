from __future__ import annotations

from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.models import ImpositionJob
from catalog.services import build_imposition_job


def test_build_imposition_job_for_business_card() -> None:
    job = build_imposition_job(
        product_template_code="business_card_standard",
        material_code="tintoretto_neve_300",
        quantity=100,
    )

    assert job.status == "completed"
    assert job.layout_mode in {"step_repeat", "n_up", "none", "manual"}
    assert job.product_template_code == "business_card_standard"


def test_build_imposition_job_rejects_unknown_template() -> None:
    try:
        build_imposition_job(
            product_template_code="missing_template",
            material_code="tintoretto_neve_300",
            quantity=100,
        )
    except Exception as exc:
        assert "ProductTemplate not found" in str(exc)
    else:
        raise AssertionError("Expected ProductTemplate not found error")