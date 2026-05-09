# apps/admin/catalog/admin.py

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin

from . import models_catalog
from .models import (
    FinishingKind,
    FinishingOption,
    Material,
    MaterialAlias,
    PrintColorScheme,
    ProductKind,
    ProductKindName,
    ProductKindPrintColor,
    Size,
)

# === Ручні, «красиві» адмін-класи для основних таблиць ===


@admin.register(ProductKind)
class ProductKindAdmin(ImportExportModelAdmin):
    list_display = ("id", "code", "name_uk", "group_code")
    search_fields = ("code", "name_uk", "group_code")
    list_per_page = 50
    readonly_fields = ("id",)


@admin.register(ProductKindName)
class ProductKindNameAdmin(ImportExportModelAdmin):
    list_display = ("id", "product_kind", "lang", "name")
    list_filter = ("lang",)
    search_fields = ("name", "product_kind__code", "product_kind__name_uk")
    readonly_fields = ("id",)


@admin.register(Material)
class MaterialAdmin(ImportExportModelAdmin):
    list_display = ("id", "code", "name", "price_per_unit")
    search_fields = ("code", "name")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(MaterialAlias)
class MaterialAliasAdmin(ImportExportModelAdmin):
    list_display = ("id", "material", "alias")
    search_fields = ("alias", "material__code", "material__name")
    readonly_fields = ("id",)


@admin.register(Size)
class SizeAdmin(ImportExportModelAdmin):
    list_display = ("id", "code", "label_uk", "width_mm", "height_mm", "is_vertical", "kind")
    list_filter = ("is_vertical", "kind")
    search_fields = ("code", "label_uk", "name_uk")
    readonly_fields = ("id",)


@admin.register(FinishingKind)
class FinishingKindAdmin(ImportExportModelAdmin):
    list_display = ("id", "code", "name_uk", "created_at", "updated_at")
    search_fields = ("code", "name_uk")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(FinishingOption)
class FinishingOptionAdmin(ImportExportModelAdmin):
    list_display = ("id", "kind", "code", "name_uk")
    list_filter = ("kind",)
    search_fields = ("code", "name_uk", "kind__code")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(PrintColorScheme)
class PrintColorSchemeAdmin(ImportExportModelAdmin):
    list_display = ("id", "code", "name_uk", "colors_front", "colors_back")
    search_fields = ("code", "name_uk")
    readonly_fields = ("id", "created_at", "updated_at")


@admin.register(ProductKindPrintColor)
class ProductKindPrintColorAdmin(ImportExportModelAdmin):
    list_display = ("id", "product_kind", "color_scheme", "required")
    list_filter = ("required", "product_kind")
    search_fields = ("product_kind__code", "color_scheme__code")
    readonly_fields = ("id",)


# === Додатково: «страховка» — автоматична реєстрація всіх моделей,
#     які не були зареєстровані вручну вище. Корисно, щоб не забути.
for name in dir(models_catalog):
    obj = getattr(models_catalog, name)
    if isinstance(obj, type) and hasattr(obj, "_meta") and getattr(obj._meta, "db_table", None):
        try:
            admin.site.register(obj)
        except admin.sites.AlreadyRegistered:
            pass
