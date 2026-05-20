from __future__ import annotations

from uuid import uuid4

from django.db import models


class CalculationSource(models.TextChoices):
    MANUAL = "manual", "Manual"
    EXTERNAL = "external", "External"


class CalculationStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class CalculationJob(models.Model):
    public_id = models.UUIDField(default=uuid4, unique=True, editable=False, db_index=True)

    source = models.CharField(
        max_length=16,
        choices=CalculationSource.choices,
        default=CalculationSource.MANUAL,
        db_index=True,
    )
    status = models.CharField(
        max_length=16,
        choices=CalculationStatus.choices,
        default=CalculationStatus.PENDING,
        db_index=True,
    )

    brand_code = models.CharField(max_length=64, blank=True, default="", db_index=True)
    customer_ref = models.CharField(max_length=128, blank=True, default="", db_index=True)

    external_order_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    external_customer_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    idempotency_key = models.CharField(
        max_length=128,
        null=True,
        blank=True,
        unique=True,
        db_index=True,
    )

    product_template_code = models.CharField(max_length=64, db_index=True)
    material_code = models.CharField(max_length=64, db_index=True)
    quantity = models.PositiveIntegerField()

    selected_operation_codes_json = models.JSONField(default=list, blank=True)

    locale = models.CharField(max_length=16, default="en")
    currency = models.CharField(max_length=8, default="USD")

    request_payload_json = models.JSONField(default=dict, blank=True)
    normalized_request_json = models.JSONField(default=dict, blank=True)

    human_report_json = models.JSONField(default=dict, blank=True)
    external_report_json = models.JSONField(default=dict, blank=True)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    finished_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        db_table = "calculation_jobs"
        verbose_name = "Calculation job"
        verbose_name_plural = "Calculation jobs"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "status", "created_at"]),
            models.Index(fields=["external_order_id", "created_at"]),
            models.Index(fields=["brand_code", "created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.public_id} [{self.source}:{self.status}]"