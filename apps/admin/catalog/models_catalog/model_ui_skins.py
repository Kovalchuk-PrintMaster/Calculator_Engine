from django.db import models


class UiSkin(models.Model):
    code = models.CharField(max_length=64, unique=True, db_index=True)
    name = models.CharField(max_length=255)
    theme_json = models.JSONField(default=dict, blank=True)
    active = models.BooleanField(default=True, db_index=True)
    sort_order = models.PositiveIntegerField(default=100, db_index=True)

    class Meta:
        db_table = "ui_skins"
        verbose_name = "UI skin"
        verbose_name_plural = "UI skins"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name