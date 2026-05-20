from __future__ import annotations

from typing import Any


def build_catalog_sync_alert_message(run: Any, *, issues_limit: int = 3) -> str:
    """Build short Telegram alert for failed/partial catalog sync."""
    issue_lines: list[str] = []

    issues = list(run.issues.all().order_by("-created_at")[:issues_limit])
    for issue in issues:
        external = f" ({issue.external_id})" if issue.external_id else ""
        issue_lines.append(f"- {issue.entity_type}{external}: {issue.code} | {issue.message}")

    issues_block = "\n".join(issue_lines) if issue_lines else "- no issue details"

    return (
        "⚠️ Catalog sync issues detected\n"
        f"run_id={run.public_id}\n"
        f"status={run.status}\n"
        f"created={run.created_count} updated={run.updated_count} "
        f"skipped={run.skipped_count} errors={run.error_count}\n"
        f"source={run.source_system} mode={run.sync_mode}\n"
        "issues:\n"
        f"{issues_block}"
    )


def notify_catalog_sync_issues(run: Any) -> bool:
    if run is None:
        return False
    if run.error_count <= 0:
        return False

    from calculator_engine.adapters.alerts.telegram import send_telegram_alert

    message = build_catalog_sync_alert_message(run)
    return send_telegram_alert(message)