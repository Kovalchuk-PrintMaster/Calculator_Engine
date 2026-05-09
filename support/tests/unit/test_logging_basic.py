# support/tests/unit/test_logging_basic.py
import logging
from calculator_engine.adapters.logging.setup import setup_logging

def test_logging_writes_without_errors(caplog):
    setup_logging(debug=True)
    logger = logging.getLogger("price")
    with caplog.at_level(logging.INFO):
        logger.info("test-log", extra={"context": {"k": "v"}})
    assert any("test-log" in rec.message for rec in caplog.records)
