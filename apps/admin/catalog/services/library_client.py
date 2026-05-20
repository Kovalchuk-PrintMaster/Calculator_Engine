from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class LibraryMaterialCategoryDTO:
    external_id: str
    code: str
    name_i18n: dict
    description_i18n: dict
    form_factor: str
    active: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LibraryOperationTypeDTO:
    external_id: str
    code: str
    name_i18n: dict
    description_i18n: dict
    group: str
    handler_code: str
    requires_setup: bool
    active: bool
    sort_order: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LibraryMaterialDTO:
    external_id: str
    code: str
    name_i18n: dict
    category_code: str
    form_factor: str
    density_gsm: int | None
    is_printable: bool
    active: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LibraryUiBrandDTO:
    external_id: str
    code: str
    name: str
    region_code: str
    default_locale: str
    default_currency: str
    default_skin_code: str
    active: bool
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LibraryProductTypeDTO:
    external_id: str
    code: str
    name_i18n: dict
    description_i18n: dict
    active: bool
    sort_order: int
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LibraryProductTemplateDTO:
    external_id: str
    code: str
    name_i18n: dict
    description_i18n: dict
    product_type_code: str
    active: bool
    sort_order: int
    allowed_material_categories_json: list[str]
    parameter_schema_json: dict
    ui_schema_json: dict
    route_profile: str
    pricing_profile: str
    updated_at: datetime

@dataclass(frozen=True, slots=True)
class LibraryCatalogClient(Protocol):
    def fetch_material_categories(
        self,
        since: datetime | None = None,
    ) -> list[LibraryMaterialCategoryDTO]: ...

    def fetch_operation_types(
        self,
        since: datetime | None = None,
    ) -> list[LibraryOperationTypeDTO]: ...

    def fetch_materials(
        self,
        since: datetime | None = None,
    ) -> list[LibraryMaterialDTO]: ...

    def fetch_ui_brands(
        self,
        since: datetime | None = None,
    ) -> list[LibraryUiBrandDTO]: ...

    def fetch_product_types(
        self,
        since: datetime | None = None,
    ) -> list[LibraryProductTypeDTO]: ...

    def fetch_product_templates(
        self,
        since: datetime | None = None,
    ) -> list[LibraryProductTemplateDTO]: ...    