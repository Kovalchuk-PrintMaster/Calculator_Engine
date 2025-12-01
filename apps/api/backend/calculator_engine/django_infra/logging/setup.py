"""Єдине місце ініціалізації логування.

Що робить:
    - Конфігурує root-логер так, щоб pytest caplog бачив записи.
    - Інжектить request_id у КОЖЕН LogRecord через LogRecordFactory (працює з caplog).
    - Додає зручний консольний форматер і (опційно) CSV-хендлер.

Політика:
    - НЕ видаляємо сторонні хендлери (наприклад, caplog).
    - Наші хендлери позначаємо атрибутом `_ce_managed = True` і лише їх прибираємо при повторній ініціалізації.
    - Рівень root: DEBUG якщо debug=True, інакше INFO.
    - Уже створеним логерам виставляємо NOTSET, аби вони успадковували рівень root.
"""

from __future__ import annotations

import logging
from logging import Handler, LogRecord

from calculator_engine.config.paths import LOGS_DIR
# ЄДИНЕ джерело request_id
from calculator_engine.shared.request_context import REQUEST_ID_VAR


# ---------- Форматери ----------

class PlainFormatter(logging.Formatter):
    """Людяний формат для консолі: `[ LEVEL] logger request_id: message`."""

    def format(self, record: LogRecord) -> str:
        level = f"{record.levelname:>5}"
        logger_name = record.name
        request_id = getattr(record, "request_id", None) or "None"
        msg = record.getMessage()
        return f"[ {level}] {logger_name} {request_id}: {msg}"


class CsvFormatter(logging.Formatter):
    """Спрощений CSV: час;рівень;логер;request_id;повідомлення."""

    def format(self, record: LogRecord) -> str:
        ts = self.formatTime(record, datefmt="%Y-%m-%d %H:%M:%S")
        level = record.levelname
        logger_name = record.name
        request_id = getattr(record, "request_id", "") or ""
        msg = record.getMessage().replace("\n", "\\n")
        return f"{ts};{level};{logger_name};{request_id};{msg}"


# ---------- Сервісні утиліти ----------

def _attach_request_id_to_all_records() -> None:
    """Інжектити request_id у КОЖЕН LogRecord через LogRecordFactory.

    Це надійніше за фільтри на логерах/хендлерах, бо працює навіть із pytest caplog.
    """
    orig_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        rec = orig_factory(*args, **kwargs)
        try:
            rid = REQUEST_ID_VAR.get()
        except Exception:
            rid = None
        # Інжектимо атрибут незалежно від того, який хендлер/логер спрацював
        if not hasattr(rec, "request_id"):
            setattr(rec, "request_id", rid)
        return rec

    logging.setLogRecordFactory(record_factory)


def _mark_and_add(handler: Handler, root: logging.Logger) -> None:
    """Позначити наш handler і додати до root."""
    setattr(handler, "_ce_managed", True)
    root.addHandler(handler)


def _remove_our_handlers(root: logging.Logger) -> None:
    """Прибрати лише хендлери, які ми додавали раніше."""
    for h in list(root.handlers):
        if getattr(h, "_ce_managed", False):
            root.removeHandler(h)


def _make_existing_loggers_inherit_root() -> None:
    """Скинути рівень уже створених логерів до NOTSET (успадковують root)."""
    mgr = logging.root.manager
    for _name, lg in list(mgr.loggerDict.items()):
        if isinstance(lg, logging.Logger):
            lg.setLevel(logging.NOTSET)


# ---------- Публічна точка входу ----------

def setup_logging(*, debug: bool = False, enable_csv: bool = True) -> None:
    """Ініціалізувати логування проєкту.

    Параметри:
        debug: якщо True — root рівень DEBUG, інакше INFO.
        enable_csv: якщо True — додати CSV-файл із агрегованими логами.
    """
    # 0) Глобально інжектимо request_id у LogRecord
    _attach_request_id_to_all_records()

    root = logging.getLogger()

    # 1) Прибрати лише наші попередні хендлери
    _remove_our_handlers(root)

    # 2) Рівень root
    root.setLevel(logging.DEBUG if debug else logging.INFO)

    # 3) Усі вже існуючі логери -> NOTSET (успадковують root)
    _make_existing_loggers_inherit_root()

    # 4) Консольний handler (видимий у caplog)
    console = logging.StreamHandler()
    console.setFormatter(PlainFormatter())
    _mark_and_add(console, root)

    # 5) За потреби — CSV handler
    if enable_csv:
        csv_path = LOGS_DIR / "app.csv"
        csv_file = logging.FileHandler(csv_path, encoding="utf-8")
        csv_file.setFormatter(CsvFormatter())
        _mark_and_add(csv_file, root)
