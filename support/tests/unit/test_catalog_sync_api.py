from __future__ import annotations

from fastapi.testclient import TestClient

from calculator_engine.app.main import app
from calculator_engine.adapters.django_bootstrap import setup_django

setup_django()

from catalog.services.catalog_sync import run_catalog_sync
from catalog.services.library_client_fake import FakeLibraryCatalogClient

client = TestClient(app)


def test_get_latest_catalog_sync_run() -> None:
    run = run_catalog_sync(client=FakeLibraryCatalogClient(), sync_mode="full")

    response = client.get("/catalog-sync/runs/latest")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["meta"]["schema_version"] == "v1"

    data = payload["data"]
    assert data["run_public_id"] == str(run.public_id)
    assert data["source_system"] == "library"
    assert data["sync_mode"] == "full"
    assert data["status"] in {"success", "partial"}