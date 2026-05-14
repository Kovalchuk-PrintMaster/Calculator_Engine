from django.contrib import admin

from ..models import OperationType


@admin.register(OperationType)
class OperationTypeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name_uk",
        "group",
        "handler_code",
        "requires_setup",
        "active",
        "sort_order",
    )
    list_filter = ("group", "requires_setup", "active")
    search_fields = ("code", "name_uk", "handler_code")
    ordering = ("group", "sort_order", "name_uk")