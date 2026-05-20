from __future__ import annotations

from datetime import datetime, timezone

from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.models import (
    CatalogSyncIssue,
    Material,
    MaterialCategory,
    OperationType,
    ProductTemplate,
    ProductType,
    UiBrand,
)

from catalog.services.catalog_sync import run_catalog_sync
from catalog.services.library_client import (
    LibraryMaterialCategoryDTO,
    LibraryMaterialDTO,
    LibraryOperationTypeDTO,
)
from catalog.services.library_client_fake import FakeLibraryCatalogClient
from catalog.services.library_client import LibraryProductTemplateDTO


class FixedFakeLibraryCatalogClient(FakeLibraryCatalogClient):
    def _now(self) -> datetime:
        return datetime(2026, 1, 1, tzinfo=timezone.utc)


class BrokenLibraryCatalogClient(FixedFakeLibraryCatalogClient):
    def fetch_materials(self):
        return [
            LibraryMaterialDTO(
                external_id="broken-mat-1",
                code="broken_material_sync",
                name_i18n={"uk": "Broken Material"},
                category_code="missing_category_code",
                form_factor="sheet",
                density_gsm=100,
                is_printable=True,
                active=True,
                updated_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            )
        ]

class BrokenTemplateLibraryCatalogClient(FixedFakeLibraryCatalogClient):
    def fetch_product_templates(self, since=None):
        now = self._now()
        return [
            LibraryProductTemplateDTO(
                external_id="broken-template-1",
                code="broken_template_sync",
                name_i18n={"uk": "Broken Template"},
                description_i18n={},
                product_type_code="missing_product_type",
                active=True,
                sort_order=999,
                allowed_material_categories_json=[],
                parameter_schema_json={},
                ui_schema_json={},
                route_profile="default",
                pricing_profile="default",
                updated_at=now,
            )
        ]


def test_run_catalog_sync_becomes_partial_on_missing_product_type_for_template() -> None:
    run = run_catalog_sync(client=BrokenTemplateLibraryCatalogClient(), sync_mode="full")

    assert run.status == "partial"
    assert run.error_count >= 1

    issue = CatalogSyncIssue.objects.filter(run=run, entity_type="product_template").first()
    assert issue is not None
    assert issue.code == "sync_error" 