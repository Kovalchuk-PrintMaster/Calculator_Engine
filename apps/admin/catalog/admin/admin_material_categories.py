from django.contrib import admin

from ..models import MaterialCategory


@admin.register(MaterialCategory)
class MaterialCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name_uk", "form_factor", "active", "sort_order")
    list_filter = ("form_factor", "active")
    search_fields = ("code", "name_uk")
    ordering = ("sort_order", "name_uk")