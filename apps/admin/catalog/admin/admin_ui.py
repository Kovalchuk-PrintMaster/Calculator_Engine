from django.contrib import admin

from ..models import UiBrand, UiBrandProductTemplateVisibility, UiSkin


class UiBrandProductTemplateVisibilityInline(admin.TabularInline):
    model = UiBrandProductTemplateVisibility
    extra = 1
    autocomplete_fields = ("product_template",)
    fields = (
        "product_template",
        "is_visible",
        "default_enabled",
        "active",
        "sort_order",
    )


@admin.register(UiSkin)
class UiSkinAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "active", "sort_order")
    list_filter = ("active",)
    search_fields = ("code", "name")
    ordering = ("sort_order", "name")


@admin.register(UiBrand)
class UiBrandAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "region_code",
        "default_locale",
        "default_currency",
        "default_skin",
        "active",
        "sort_order",
    )
    list_filter = ("active", "region_code", "default_locale", "default_currency")
    search_fields = ("code", "name", "region_code")
    autocomplete_fields = ("default_skin",)
    ordering = ("sort_order", "name")
    inlines = [UiBrandProductTemplateVisibilityInline]


@admin.register(UiBrandProductTemplateVisibility)
class UiBrandProductTemplateVisibilityAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "brand",
        "product_template",
        "is_visible",
        "default_enabled",
        "active",
        "sort_order",
    )
    list_filter = ("brand", "is_visible", "default_enabled", "active")
    search_fields = (
        "brand__code",
        "brand__name",
        "product_template__code",
        "product_template__name_uk",
    )
    autocomplete_fields = ("brand", "product_template")
    ordering = ("brand", "sort_order", "product_template")