from django.db import models

# managed = False, бо схему мігрує Alembic

class ProductKind(models.Model):
    id = models.AutoField(primary_key=True)  # integer serial
    code = models.CharField(max_length=32, unique=True)
    name_uk = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    name_en = models.CharField(max_length=255, null=True, blank=True)
    group_code = models.TextField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "product_kinds"

    def __str__(self):
        return f"{self.code} — {self.name_uk}"


class ProductKindName(models.Model):
    id = models.BigAutoField(primary_key=True)
    product_kind = models.ForeignKey(ProductKind, on_delete=models.CASCADE, db_column="product_kind_id")
    lang = models.CharField(max_length=8)
    name = models.TextField()

    class Meta:
        managed = False
        db_table = "product_kind_names"
        unique_together = (("product_kind", "lang"),)


class Material(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "materials"

    def __str__(self):
        return f"{self.code} — {self.name}"


class MaterialAlias(models.Model):
    id = models.AutoField(primary_key=True)
    material = models.ForeignKey(Material, on_delete=models.CASCADE, db_column="material_id")
    alias = models.TextField()

    class Meta:
        managed = False
        db_table = "material_aliases"
        unique_together = (("material", "alias"),)


class Size(models.Model):
    id = models.AutoField(primary_key=True)  # integer serial
    code = models.TextField(null=True, blank=True, unique=True)
    name_uk = models.TextField(null=True, blank=True)
    name_ru = models.TextField(null=True, blank=True)
    name_en = models.TextField(null=True, blank=True)
    label_uk = models.CharField(max_length=255)
    label_ru = models.CharField(max_length=255, null=True, blank=True)
    label_en = models.CharField(max_length=255, null=True, blank=True)
    width_mm = models.IntegerField()
    height_mm = models.IntegerField()
    is_vertical = models.BooleanField(null=True, blank=True)
    kind = models.ForeignKey(ProductKind, on_delete=models.SET_NULL, null=True, blank=True, db_column="kind_id")

    class Meta:
        managed = False
        db_table = "sizes"


class FinishingKind(models.Model):
    id = models.AutoField(primary_key=True)
    code = models.CharField(max_length=64, unique=True)
    name_uk = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    name_en = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "finishing_kinds"


class FinishingOption(models.Model):
    id = models.AutoField(primary_key=True)
    kind = models.ForeignKey(FinishingKind, on_delete=models.SET_NULL, null=True, db_column="kind_id")
    code = models.CharField(max_length=64)
    name_uk = models.CharField(max_length=255)
    name_ru = models.CharField(max_length=255, null=True, blank=True)
    name_en = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "finishing_options"
        unique_together = (("kind", "code"),)


class PrintColorScheme(models.Model):
    id = models.BigAutoField(primary_key=True)
    code = models.TextField(unique=True)
    name_uk = models.TextField()
    name_ru = models.TextField()
    name_en = models.TextField()
    colors_front = models.IntegerField()
    colors_back = models.IntegerField()
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "print_color_schemes"

    def __str__(self):
        return f"{self.code} — {self.name_uk}"


class ProductKindPrintColor(models.Model):
    # після 0004 у нас буде surrogate PK + required
    id = models.BigAutoField(primary_key=True)
    product_kind = models.ForeignKey(ProductKind, on_delete=models.CASCADE, db_column="product_kind_id")
    color_scheme = models.ForeignKey(PrintColorScheme, on_delete=models.CASCADE, db_column="color_scheme_id")
    required = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = "product_kind_print_colors"
        unique_together = (("product_kind", "color_scheme"),)
