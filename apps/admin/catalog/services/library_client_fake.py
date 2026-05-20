from __future__ import annotations

from datetime import datetime, timezone

from .library_client import (
    LibraryCatalogClient,
    LibraryMaterialCategoryDTO,
    LibraryMaterialDTO,
    LibraryOperationTypeDTO,
    LibraryProductTemplateDTO,
    LibraryProductTypeDTO,
    LibraryUiBrandDTO,
)


class FakeLibraryCatalogClient(LibraryCatalogClient):
    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    def fetch_material_categories(self, since=None) -> list[LibraryMaterialCategoryDTO]:
        now = self._now()
        return [
            LibraryMaterialCategoryDTO(
                external_id="lib-mcat-designer-cardstock",
                code="designer_cardstock",
                name_i18n={
                    "uk": "Дизайнерський картон",
                    "en": "Designer Cardstock",
                    "pl": "Karton designerski",
                },
                description_i18n={},
                form_factor="sheet",
                active=True,
                updated_at=now,
            )
        ]

    def fetch_operation_types(self, since=None) -> list[LibraryOperationTypeDTO]:
        now = self._now()
        return [
            LibraryOperationTypeDTO(
                external_id="lib-op-digital-print",
                code="digital_print",
                name_i18n={
                    "uk": "Цифровий друк",
                    "en": "Digital Print",
                    "pl": "Druk cyfrowy",
                },
                description_i18n={},
                group="print",
                handler_code="digital_print",
                requires_setup=False,
                active=True,
                sort_order=20,
                updated_at=now,
            )
        ]

    def fetch_materials(self, since=None) -> list[LibraryMaterialDTO]:
        now = self._now()
        return [
            LibraryMaterialDTO(
                external_id="lib-mat-tintoretto-neve-300",
                code="tintoretto_neve_300",
                name_i18n={
                    "uk": "Tintoretto Neve 300",
                    "en": "Tintoretto Neve 300",
                    "pl": "Tintoretto Neve 300",
                },
                category_code="designer_cardstock",
                form_factor="sheet",
                density_gsm=300,
                is_printable=True,
                active=True,
                updated_at=now,
            )
        ]
    
    def fetch_ui_brands(self, since=None) -> list[LibraryUiBrandDTO]:
        now = self._now()
        return [
            LibraryUiBrandDTO(
                external_id="lib-brand-printmaster-pl",
                code="printmaster_pl",
                name="PrintMaster Poland",
                region_code="PL",
                default_locale="pl",
                default_currency="EUR",
                default_skin_code="light_poland",
                active=True,
                updated_at=now,
            ),
            LibraryUiBrandDTO(
                external_id="lib-brand-printmaster-global",
                code="printmaster_global",
                name="PrintMaster Global",
                region_code="GLOBAL",
                default_locale="en",
                default_currency="USD",
                default_skin_code="light_default",
                active=True,
                updated_at=now,
            ),
        ]

    def fetch_product_types(self, since=None) -> list[LibraryProductTypeDTO]:
        now = self._now()
        return [
            LibraryProductTypeDTO(
                external_id="lib-ptype-business-card",
                code="business_card",
                name_i18n={
                    "uk": "Візитка",
                    "en": "Business Card",
                    "pl": "Wizytówka",
                },
                description_i18n={},
                active=True,
                sort_order=10,
                updated_at=now,
            ),
            LibraryProductTypeDTO(
                external_id="lib-ptype-flyer",
                code="flyer",
                name_i18n={
                    "uk": "Флаєр",
                    "en": "Flyer",
                    "pl": "Ulotka",
                },
                description_i18n={},
                active=True,
                sort_order=20,
                updated_at=now,
            ),
        ]

    def fetch_product_templates(self, since=None) -> list[LibraryProductTemplateDTO]:
        now = self._now()
        return [
            LibraryProductTemplateDTO(
                external_id="lib-ptmpl-business-card-standard",
                code="business_card_standard",
                name_i18n={
                    "uk": "Візитка стандарт",
                    "en": "Business Card Standard",
                    "pl": "Wizytówka standard",
                },
                description_i18n={},
                product_type_code="business_card",
                active=True,
                sort_order=10,
                allowed_material_categories_json=["designer_cardstock"],
                parameter_schema_json={},
                ui_schema_json={},
                route_profile="default",
                pricing_profile="default",
                updated_at=now,
            ),
            LibraryProductTemplateDTO(
                external_id="lib-ptmpl-flyer-standard",
                code="flyer_standard",
                name_i18n={
                    "uk": "Флаєр стандарт",
                    "en": "Flyer Standard",
                    "pl": "Ulotka standard",
                },
                description_i18n={},
                product_type_code="flyer",
                active=True,
                sort_order=20,
                allowed_material_categories_json=["designer_cardstock"],
                parameter_schema_json={},
                ui_schema_json={},
                route_profile="default",
                pricing_profile="default",
                updated_at=now,
            ),
        ]
