from django.contrib import admin

from ..models import ProductTemplate, ProductTemplateOperation


class ProductTemplateOperationInline(admin.TabularInline):
    model = ProductTemplateOperation
    extra = 1
    autocomplete_fields = ("operation_type",)
    fields = (
        "operation_type",
        "is_required",
        "is_optional",
        "default_enabled",
        "sequence_order",
        "active",
        "constraints_json",
    )


@admin.register(ProductTemplate)
class ProductTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name_uk",
        "product_type",
        "active",
        "sort_order",
        "route_profile",
        "pricing_profile",
    )
    list_filter = ("product_type", "active")
    search_fields = ("code", "name_uk")
    ordering = ("sort_order", "name_uk")
    autocomplete_fields = ("product_type",)
    inlines = [ProductTemplateOperationInline]