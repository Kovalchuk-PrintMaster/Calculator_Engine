from django.contrib import admin

from ..models import MaterialPrice, OperationPrice


@admin.register(MaterialPrice)
class MaterialPriceAdmin(admin.ModelAdmin):
    list_display = ("id", "material", "price", "unit", "waste_percent", "active")
    list_filter = ("unit", "active")
    search_fields = ("material__code", "material__name_uk")
    autocomplete_fields = ("material",)
    ordering = ("material__name_uk",)


@admin.register(OperationPrice)
class OperationPriceAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "operation_type",
        "setup_price",
        "unit_price",
        "unit",
        "active",
    )
    list_filter = ("unit", "active", "operation_type__group")
    search_fields = ("operation_type__code", "operation_type__name_uk")
    autocomplete_fields = ("operation_type",)
    ordering = ("operation_type__group", "operation_type__sort_order", "operation_type__name_uk")