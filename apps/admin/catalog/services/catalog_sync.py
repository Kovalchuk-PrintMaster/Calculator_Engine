from __future__ import annotations

from dataclasses import dataclass
from pdb import run
from django.utils import timezone
from datetime import datetime

from catalog.models import (
    CatalogSyncIssue,
    CatalogSyncRun,
    Material,
    MaterialCategory,
    OperationType,
    ProductTemplate,
    ProductType,
    UiBrand,
    UiSkin,
)
from catalog.models_catalog.model_sync_metadata import SyncSourceSystem


@dataclass(frozen=True, slots=True)
class CatalogSyncStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: int = 0


def _merge_name_uk(name_i18n: dict, fallback: str) -> str:
    return name_i18n.get("uk") or name_i18n.get("en") or fallback


def sync_material_categories(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_material_categories(since=since):
        try:
            obj = MaterialCategory.objects.filter(code=item.code).first()
            defaults = {
                "name_uk": _merge_name_uk(item.name_i18n, item.code),
                "name_i18n": item.name_i18n,
                "description_i18n": item.description_i18n,
                "form_factor": item.form_factor,
                "active": item.active,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                MaterialCategory.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="material_category",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={"code": item.code},
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)


def sync_operation_types(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_operation_types():
        try:
            obj = OperationType.objects.filter(code=item.code).first()
            defaults = {
                "name_uk": _merge_name_uk(item.name_i18n, item.code),
                "name_i18n": item.name_i18n,
                "description_i18n": item.description_i18n,
                "group": item.group,
                "handler_code": item.handler_code,
                "requires_setup": item.requires_setup,
                "active": item.active,
                "sort_order": item.sort_order,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                OperationType.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="operation_type",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={"code": item.code},
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)


def sync_materials(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_materials(since=since):
        try:
            category = MaterialCategory.objects.get(code=item.category_code)

            obj = Material.objects.filter(code=item.code).first()
            defaults = {
                "name_uk": _merge_name_uk(item.name_i18n, item.code),
                "name_i18n": item.name_i18n,
                "category": category,
                "form_factor": item.form_factor,
                "density_gsm": item.density_gsm,
                "is_printable": item.is_printable,
                "active": item.active,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                Material.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="material",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={"code": item.code, "category_code": item.category_code},
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)


def run_catalog_sync(
    *,
    client,
    sync_mode: str = "full",
    since: datetime | None = None,
    ) -> CatalogSyncRun:

    run = CatalogSyncRun.objects.create(
        source_system="library",
        sync_mode=sync_mode,
        status=CatalogSyncRun.Status.STARTED,
        meta_json={
            "since": since.isoformat() if since else None,
        },
    )

    total_created = total_updated = total_skipped = total_errors = 0

    for func in (
        sync_material_categories,
        sync_operation_types,
        sync_materials,
        sync_ui_brands,
        sync_product_types,
        sync_product_templates,
        ):
        stats = func(run=run, client=client, since=since)
        
    
        
        stats = func(run=run, client=client, since=since)
        total_created += stats.created
        total_updated += stats.updated
        total_skipped += stats.skipped
        total_errors += stats.errors

    

    run.created_count = total_created
    run.updated_count = total_updated
    run.skipped_count = total_skipped
    run.error_count = total_errors
    run.finished_at = timezone.now()
    run.status = (
        CatalogSyncRun.Status.PARTIAL if total_errors else CatalogSyncRun.Status.SUCCESS
    )
    run.save(
    update_fields=[
        "created_count",
        "updated_count",
        "skipped_count",
        "error_count",
        "finished_at",
        "status",
        ]
    )

    
    return run

def sync_ui_brands(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_ui_brands(since=since):
        try:
            default_skin = UiSkin.objects.get(code=item.default_skin_code)

            obj = UiBrand.objects.filter(code=item.code).first()
            defaults = {
                "name": item.name,
                "region_code": item.region_code,
                "default_locale": item.default_locale,
                "default_currency": item.default_currency,
                "default_skin": default_skin,
                "active": item.active,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                UiBrand.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="ui_brand",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={"code": item.code},
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)


def sync_product_types(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_product_types():
        try:
            obj = ProductType.objects.filter(code=item.code).first()
            defaults = {
                "name_uk": _merge_name_uk(item.name_i18n, item.code),
                "name_i18n": item.name_i18n,
                "description_i18n": item.description_i18n,
                "active": item.active,
                "sort_order": item.sort_order,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                ProductType.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="product_type",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={"code": item.code},
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)


def sync_product_templates(*, run: CatalogSyncRun, client, since: datetime | None = None) -> CatalogSyncStats:
    created = updated = skipped = errors = 0

    for item in client.fetch_product_templates(since=since):
        try:
            product_type = ProductType.objects.get(code=item.product_type_code)

            obj = ProductTemplate.objects.filter(code=item.code).first()
            defaults = {
                "name_uk": _merge_name_uk(item.name_i18n, item.code),
                "name_i18n": item.name_i18n,
                "description_i18n": item.description_i18n,
                "product_type": product_type,
                "active": item.active,
                "sort_order": item.sort_order,
                "allowed_material_categories_json": item.allowed_material_categories_json,
                "parameter_schema_json": item.parameter_schema_json,
                "ui_schema_json": item.ui_schema_json,
                "route_profile": item.route_profile,
                "pricing_profile": item.pricing_profile,
                "external_id": item.external_id,
                "source_system": SyncSourceSystem.LIBRARY,
                "source_updated_at": item.updated_at,
            }

            if obj is None:
                ProductTemplate.objects.create(code=item.code, **defaults)
                created += 1
            else:
                changed = False
                for field, value in defaults.items():
                    if getattr(obj, field) != value:
                        setattr(obj, field, value)
                        changed = True
                if changed:
                    obj.save()
                    updated += 1
                else:
                    skipped += 1
        except Exception as exc:
            CatalogSyncIssue.objects.create(
                run=run,
                entity_type="product_template",
                external_id=item.external_id,
                code="sync_error",
                message=str(exc),
                payload_json={
                    "code": item.code,
                    "product_type_code": item.product_type_code,
                },
            )
            errors += 1

    return CatalogSyncStats(created, updated, skipped, errors)    