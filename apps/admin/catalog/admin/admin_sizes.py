# apps/admin/catalog/admin/admin_sizes.py
from django.contrib import admin
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin
from ..models import Size, ProductKind

class SizeResource(resources.ModelResource):
    # простий lookup по коду виду (замість FK id) — зручно для XLSX
    kind_code = fields.Field(column_name="kind_code")

    class Meta:
        model = Size
        import_id_fields = ("code",)   # upsert по code
        fields = (
            "code",
            "kind_code",
            "width_mm", "height_mm",
            "label_uk", "label_ru", "label_en",
            "name_uk", "name_ru", "name_en",
            "is_vertical",
        )
        skip_unchanged = True
        report_skipped = True
        use_bulk = True

    def dehydrate_kind_code(self, obj):
        return obj.kind.code if obj.kind else ""

    def before_import_row(self, row, **kwargs):
        # мапимо kind_code → FK
        k = row.get("kind_code")
        if k:
            try:
                row["kind"] = ProductKind.objects.get(code=k).pk
            except ProductKind.DoesNotExist:
                raise ValueError(f"ProductKind with code '{k}' not found")

class SizeAdmin(ImportExportModelAdmin):
    resource_class = SizeResource
    list_display = ("id", "code", "label_uk", "width_mm", "height_mm", "is_vertical")
    search_fields = ("code", "label_uk", "name_uk", "name_en", "name_ru")
    list_filter = ("is_vertical", "kind")

admin.site.register(Size, SizeAdmin)
