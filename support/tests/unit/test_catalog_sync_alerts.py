from __future__ import annotations

from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.models import CatalogSyncIssue, CatalogSyncRun
from catalog.services.catalog_sync_alerts import (
    build_catalog_sync_alert_message,
    notify_catalog_sync_issues,
)


def test_build_catalog_sync_alert_message_contains_summary() -> None:
    run = CatalogSyncRun.objects.create(
        source_system="library",
        sync_mode="full",
        status="partial",
        created_count=1,
        updated_count=2,
        skipped_count=3,
        error_count=1,
    )
    CatalogSyncIssue.objects.create(
        run=run,
        entity_type="material",
        external_id="ext-1",
        code="sync_error",
        message="Missing category",
        payload_json={"code": "broken_material"},
    )

    message = build_catalog_sync_alert_message(run)

    assert "Catalog sync issues detected" in message
    assert "status=partial" in message
    assert "errors=1" in message
    assert "material (ext-1): sync_error" in message


def test_notify_catalog_sync_issues_skips_when_no_errors(monkeypatch) -> None:
    run = CatalogSyncRun.objects.create(
        source_system="library",
        sync_mode="full",
        status="success",
        error_count=0,
    )

    called = {"sent": False}

    def fake_send(_message: str) -> bool:
        called["sent"] = True
        return True

    monkeypatch.setattr(
        "calculator_engine.adapters.alerts.telegram.send_telegram_alert",
        fake_send,
    )

    sent = notify_catalog_sync_issues(run)

    assert sent is False
    assert called["sent"] is False


def test_notify_catalog_sync_issues_sends_when_errors_exist(monkeypatch) -> None:
    run = CatalogSyncRun.objects.create(
        source_system="library",
        sync_mode="full",
        status="partial",
        error_count=1,
    )
    CatalogSyncIssue.objects.create(
        run=run,
        entity_type="material",
        external_id="ext-2",
        code="sync_error",
        message="Broken payload",
        payload_json={},
    )

    captured = {"message": None}

    def fake_send(message: str) -> bool:
        captured["message"] = message
        return True

    monkeypatch.setattr(
        "calculator_engine.adapters.alerts.telegram.send_telegram_alert",
        fake_send,
    )

    sent = notify_catalog_sync_issues(run)

    assert sent is True
    assert captured["message"] is not None
    assert "errors=1" in captured["message"]