from __future__ import annotations

from django.db import models


class SyncSourceSystem(models.TextChoices):
    LOCAL = "local", "Local"
    LIBRARY = "library", "Library"


class SyncMetadataMixin(models.Model):
    external_id = models.CharField(max_length=128, blank=True, default="", db_index=True)
    source_system = models.CharField(
        max_length=16,
        choices=SyncSourceSystem.choices,
        default=SyncSourceSystem.LOCAL,
        db_index=True,
    )
    source_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True