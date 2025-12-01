from django.contrib import admin
from .models import (
    ProductKind, ProductKindName, Material, MaterialAlias, Size,
    FinishingKind, FinishingOption, PrintColorScheme, ProductKindPrintColor
)

@admin.register(ProductKind)
class ProductKindAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name_uk", "group_code")
    search_fields = ("code", "name_uk", "name_ru", "name_en")
    list_filter = ("group_code",)

@admin.register(ProductKindName)
class ProductKindNameAdmin(admin.ModelAdmin):
    list_display = ("id", "product_kind", "lang", "name")
    search_fields = ("name",)
    list_filter = ("lang",)

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "price_per_unit")
    search_fields = ("code", "name")
    ordering = ("code",)

@admin.register(MaterialAlias)
class MaterialAliasAdmin(admin.ModelAdmin):
    list_display = ("id", "material", "alias")
    search_fields = ("alias", "material__code", "material__name")

@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "label_uk", "width_mm", "height_mm", "is_vertical")
    search_fields = ("code", "label_uk", "name_uk", "name_ru", "name_en")
    list_filter = ("is_vertical",)
    ordering = ("code",)
    list_per_page = 50

@admin.register(FinishingKind)
class FinishingKindAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name_uk")
    search_fields = ("code", "name_uk", "name_ru", "name_en")

@admin.register(FinishingOption)
class FinishingOptionAdmin(admin.ModelAdmin):
    list_display = ("id", "kind", "code", "name_uk")
    search_fields = ("code", "name_uk", "name_ru", "name_en")
    list_filter = ("kind",)

@admin.register(PrintColorScheme)
class PrintColorSchemeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name_uk", "colors_front", "colors_back")
    search_fields = ("code", "name_uk", "name_ru", "name_en")
    list_filter = ("colors_front", "colors_back")
    ordering = ("code",)

@admin.register(ProductKindPrintColor)
class ProductKindPrintColorAdmin(admin.ModelAdmin):
    list_display = ("id", "product_kind", "color_scheme", "required")
    list_filter = ("required", "product_kind")
    search_fields = ("product_kind__code", "product_kind__name_uk",
                     "color_scheme__code", "color_scheme__name_uk")
    ordering = ("product_kind__code", "color_scheme__code")
    list_per_page = 50
