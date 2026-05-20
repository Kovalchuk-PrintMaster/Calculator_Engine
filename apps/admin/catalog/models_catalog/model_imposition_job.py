from __future__ import annotations

import uuid

from django.db import models


class ImpositionJob(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"
        MANUAL_REQUIRED = "manual_required", "Manual Required"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )

    engine_code = models.CharField(max_length=64, blank=True, default="mock")
    layout_mode = models.CharField(max_length=32, blank=True, default="none")

    product_template_code = models.CharField(max_length=128, blank=True, default="")
    material_code = models.CharField(max_length=128, blank=True, default="")
    quantity = models.PositiveIntegerField(default=0)

    request_json = models.JSONField(default=dict, blank=True)
    result_json = models.JSONField(default=dict, blank=True)

    input_file_path = models.TextField(blank=True, default="")
    output_file_path = models.TextField(blank=True, default="")
    message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "imposition_jobs"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.public_id} ({self.status})"