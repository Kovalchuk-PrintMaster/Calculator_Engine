from django.db import models

from catalog.utils import get_i18n_value
from .model_sync_metadata import SyncMetadataMixin


class OperationGroup(models.TextChoices):
    PRINT = "print", "Print"
    FINISHING = "finishing", "Finishing"
    CUTTING = "cutting", "Cutting"
    ASSEMBLY = "assembly", "Assembly"
    SERVICE = "service", "Service"


class OperationType(SyncMetadataMixin, models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name_uk = models.CharField(max_length=255)
    name_i18n = models.JSONField(default=dict, blank=True)

    group = models.CharField(
        max_length=32,
        choices=OperationGroup.choices,
        db_index=True,
    )
    handler_code = models.CharField(max_length=64, unique=True)

    description = models.TextField(blank=True, default="")
    description_i18n = models.JSONField(default=dict, blank=True)

    requires_setup = models.BooleanField(default=False)
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "operation_types"
        verbose_name = "Operation type"
        verbose_name_plural = "Operation types"
        ordering = ["group", "sort_order", "name_uk"]

    def get_name(self, locale: str = "uk") -> str:
        return get_i18n_value(self.name_i18n, locale) or self.name_uk

    def get_description(self, locale: str = "uk") -> str:
        return get_i18n_value(self.description_i18n, locale) or self.description

    def __str__(self) -> str:
        return self.get_name("uk")