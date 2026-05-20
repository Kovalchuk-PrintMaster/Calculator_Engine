from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand

from catalog.services.catalog_sync import run_catalog_sync
from catalog.services.catalog_sync_alerts import notify_catalog_sync_issues
from catalog.services.library_client_fake import FakeLibraryCatalogClient
from catalog.services.library_client_http import LibraryHttpClient


class Command(BaseCommand):
    help = "Sync catalog reference data from Library service"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default="fake",
            choices=["fake", "http"],
            help="Library source adapter",
        )
        parser.add_argument(
            "--mode",
            default="full",
            choices=["full", "incremental"],
            help="Sync mode",
        )
        parser.add_argument(
            "--since",
            default="",
            help="ISO datetime for incremental sync, e.g. 2026-05-19T10:00:00+00:00",
        )

    def handle(self, *args, **options):
        source = options["source"]
        mode = options["mode"]
        since_raw = options["since"].strip()

        since = datetime.fromisoformat(since_raw) if since_raw else None

        if source == "fake":
            client = FakeLibraryCatalogClient()
        elif source == "http":
            client = LibraryHttpClient()
        else:
            raise ValueError(f"Unsupported source: {source}")

        run = run_catalog_sync(client=client, sync_mode=mode, since=since)
        notify_catalog_sync_issues(run)

        self.stdout.write(self.style.SUCCESS("✅ Catalog sync completed"))
        self.stdout.write(
            f"Run: {run.public_id} | status={run.status} | "
            f"created={run.created_count} updated={run.updated_count} "
            f"skipped={run.skipped_count} errors={run.error_count}"
        )