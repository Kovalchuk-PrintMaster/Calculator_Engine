from __future__ import annotations

import logging

from calculator_engine.adapters.logging.setup import setup_logging
from calculator_engine.shared.request_context import REQUEST_ID_VAR


def test_request_id_appears_in_log_records(caplog) -> None:
    setup_logging(debug=True, enable_csv=False)  # ініт логування один раз

    rid = "req-123"
    token = REQUEST_ID_VAR.set(rid)
    try:
        logger = logging.getLogger("price")
        with caplog.at_level(logging.INFO):
            logger.info("log-with-request-id", extra={"context": {"k": "v"}})
        # Переконуємось, що хоча б один запис має request_id у рекорді
        assert any(getattr(rec, "request_id", None) == rid for rec in caplog.records)
    finally:
        REQUEST_ID_VAR.reset(token)
