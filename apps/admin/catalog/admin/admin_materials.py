from django.contrib import admin

from ..models import Material, MaterialOperationCapability


class MaterialOperationCapabilityInline(admin.TabularInline):
    model = MaterialOperationCapability
    extra = 1
    autocomplete_fields = ("operation_type",)
    fields = (
        "operation_type",
        "is_allowed",
        "priority",
        "active",
        "constraints_json",
        "notes",
    )


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name_uk",
        "category",
        "form_factor",
        "density_gsm",
        "is_printable",
        "active",
    )
    list_filter = ("category", "form_factor", "is_printable", "active")
    search_fields = ("code", "name_uk", "vendor_name")
    ordering = ("name_uk",)
    autocomplete_fields = ("category",)
    inlines = [MaterialOperationCapabilityInline]