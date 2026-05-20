from django.contrib import admin

from ..models import CalculationJob


@admin.register(CalculationJob)
class CalculationJobAdmin(admin.ModelAdmin):
    list_display = (
        "public_id",
        "source",
        "status",
        "brand_code",
        "external_order_id",
        "product_template_code",
        "material_code",
        "quantity",
        "currency",
        "total",
        "created_at",
        "finished_at",
    )
    list_filter = ("source", "status", "brand_code", "currency", "locale")
    search_fields = (
        "public_id",
        "external_order_id",
        "external_customer_id",
        "customer_ref",
        "product_template_code",
        "material_code",
        "idempotency_key",
    )
    ordering = ("-created_at",)
    readonly_fields = (
        "public_id",
        "created_at",
        "finished_at",
        "request_payload_json",
        "normalized_request_json",
        "human_report_json",
        "external_report_json",
        "error_message",
    )