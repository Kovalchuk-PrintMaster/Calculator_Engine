from django.contrib import admin

from ..models import MaterialOperationCapability, ProductTemplateOperation


@admin.register(MaterialOperationCapability)
class MaterialOperationCapabilityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "material",
        "operation_type",
        "is_allowed",
        "priority",
        "active",
    )
    list_filter = ("is_allowed", "active", "operation_type")
    search_fields = ("material__code", "material__name_uk", "operation_type__code", "operation_type__name_uk")
    autocomplete_fields = ("material", "operation_type")
    ordering = ("material", "priority", "operation_type")


@admin.register(ProductTemplateOperation)
class ProductTemplateOperationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product_template",
        "operation_type",
        "is_required",
        "is_optional",
        "default_enabled",
        "sequence_order",
        "active",
    )
    list_filter = ("is_required", "is_optional", "default_enabled", "active")
    search_fields = (
        "product_template__code",
        "product_template__name_uk",
        "operation_type__code",
        "operation_type__name_uk",
    )
    autocomplete_fields = ("product_template", "operation_type")
    ordering = ("product_template", "sequence_order", "operation_type")