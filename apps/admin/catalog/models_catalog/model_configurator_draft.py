from __future__ import annotations

import uuid

from django.db import models


class ConfiguratorDraft(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        QUOTED = "quoted", "Quoted"
        SUBMITTED = "submitted", "Submitted"

    public_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True,
    )

    status = models.CharField(
        max_length=32,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )

    brand_code = models.CharField(max_length=64, blank=True, default="")
    product_template_code = models.CharField(max_length=128, blank=True, default="")
    material_code = models.CharField(max_length=128, blank=True, default="")

    quantity = models.PositiveIntegerField(null=True, blank=True)

    selected_operation_codes_json = models.JSONField(default=list, blank=True)

    locale = models.CharField(max_length=16, blank=True, default="")
    currency = models.CharField(max_length=8, blank=True, default="")

    client_meta_json = models.JSONField(default=dict, blank=True)
    state_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "configurator_drafts"
        ordering = ("-updated_at",)

    def __str__(self) -> str:
        return f"{self.public_id} ({self.status})"