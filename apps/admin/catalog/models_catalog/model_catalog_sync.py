from __future__ import annotations

import uuid

from django.db import models


class CatalogSyncRun(models.Model):
    class Status(models.TextChoices):
        STARTED = "started", "Started"
        SUCCESS = "success", "Success"
        PARTIAL = "partial", "Partial"
        FAILED = "failed", "Failed"

    public_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    source_system = models.CharField(max_length=32, default="library", db_index=True)
    sync_mode = models.CharField(max_length=32, default="full")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.STARTED,
        db_index=True,
    )

    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    meta_json = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "catalog_sync_runs"
        ordering = ("-started_at",)

    def __str__(self) -> str:
        return f"{self.public_id} ({self.status})"


class CatalogSyncIssue(models.Model):
    run = models.ForeignKey(
        CatalogSyncRun,
        on_delete=models.CASCADE,
        related_name="issues",
    )

    entity_type = models.CharField(max_length=64, db_index=True)
    external_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    code = models.CharField(max_length=64, db_index=True)
    message = models.TextField()
    payload_json = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "catalog_sync_issues"
        ordering = ("-created_at",)

    def __str__(self) -> str:
        return f"{self.entity_type}:{self.external_id} [{self.code}]"