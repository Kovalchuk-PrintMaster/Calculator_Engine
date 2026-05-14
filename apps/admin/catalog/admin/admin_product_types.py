from django.contrib import admin

from ..models import ProductType


@admin.register(ProductType)
class ProductTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name_uk", "active", "sort_order")
    list_filter = ("active",)
    search_fields = ("code", "name_uk")
    ordering = ("sort_order", "name_uk")