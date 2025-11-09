# 03. Логування в Calculator Engine

> **Мета**: описати, як у проєкті організовано логування, як додається `request_id`, які є форматери (людяний та CSV), де зберігаються журнали, як їх читати, та як це все тестується через `pytest`/`caplog`.

## 1) Огляд стека логування

У проєкті використовується стандартний модуль Python `logging` з централізованою ініціалізацією у файлі:

* `src/calculator_engine/infra/logging/setup.py` — єдине місце, де ми конфігуруємо root-логер, хендлери, форматери та фільтри (див. функцію `setup_logging`).
* `src/calculator_engine/infra/logging/request_id.py` — оголошено `REQUEST_ID_VAR` (контекстна змінна), яка зберігає `request_id` для поточного запиту/контексту.
* `src/calculator_engine/app/middleware.py` — ASGI-middleware, яке читає/генерує `X-Request-ID` та прокидує його в `REQUEST_ID_VAR`, а також додає заголовок у відповідь.

### Компоненти

* **Root-логер** — єдине джерело правди для конфігурації рівня логування та хендлерів. Рівень: `DEBUG` (при `debug=True`) або `INFO`.
* **RequestIdFilter** — додає поле `request_id` до кожного запису `LogRecord` на базі `REQUEST_ID_VAR`. Це дає можливість:

  * бачити `request_id` у консолі та CSV;
  * перевіряти його наявність у тестах через `caplog`.
* **PlainFormatter** — компактний «людяний» формат для консолі:

  ```
  [  INFO] price req-123: message
  ```
* **CsvFormatter** — машинозчитуваний формат `;`-роздільником:

  ```
  YYYY-MM-DD HH:MM:SS;LEVEL;LOGGER;REQUEST_ID;MESSAGE
  ```

## 2) Де ініціалізується логування

### 2.1. Точка входу застосунку

* `src/calculator_engine/app/main.py`

  * Викликає `setup_logging(debug=...)` на старті застосунку, **до** підняття ASGI-роутерів.
  * Підключає `setup_middleware(app)` з `src/calculator_engine/app/middleware.py`.

### 2.2. Чому один «setup» для всього проєкту

* Уникаємо локальних конфігурацій логерів «по місцях» — це спрощує підтримку та роботу `caplog` у тестах.
* Всі дочірні логери (наприклад, `logging.getLogger("price")`) успадковують рівень та хендлери від root.

## 3) `request_id` та кореляція подій

### 3.1. Як це працює

* У middleware перевіряємо заголовок `X-Request-ID`. Якщо його немає — генеруємо новий UUID4.
* Значення записується у `REQUEST_ID_VAR` (контекстна змінна), а також додається в заголовок відповіді.
* `RequestIdFilter` зчитує `REQUEST_ID_VAR` й інжектить поле `record.request_id` для кожного лог-запису.

### 3.2. Навіщо це

* `request_id` дозволяє зв’язати всі логи одного HTTP-запиту та спростити аналіз ланцюжків подій.
* Можна прокидати `request_id` далі у звернення до БД, черг, зовнішніх сервісів (майбутній етап).

### 3.3. Мінімальний приклад

```python
import logging
from calculator_engine.infra.logging.setup import setup_logging
from calculator_engine.infra.logging.request_id import REQUEST_ID_VAR

setup_logging(debug=True, enable_csv=False)

# імітуємо, ніби ми в контексті одного запиту
REQUEST_ID_VAR.set("req-42")

logger = logging.getLogger("price")
logger.info("price calculated", extra={"context": {"job_id": 123}})
```

Консольний вивід відповідатиме шаблону `PlainFormatter`:

```
[  INFO] price req-42: price calculated
```

## 4) Де лежать журнали і як їх читати

Шляхи централізовано оголошені у `src/calculator_engine/config/paths.py`:

* **Загальний каталог логів**: `logs/`
* **Логи автентифікації**: `logs/autentification/` *(написання узгоджене)*
* **Логи бази даних**: `logs/data_base/`

За замовчуванням `setup_logging(enable_csv=True)` створює файл:

* `logs/app.csv` — агрегований CSV-журнал для всього застосунку.

Приклад рядка у `app.csv`:

```
2025-10-09 12:34:56;INFO;price;req-42;price calculated
```

### Читання логів

* Останні 50 рядків: `make logs-tail`
* Пошук за `request_id`:

  ```bash
  grep 'req-42' logs/app.csv
  ```
* Імпорт у табличний інструмент (LibreOffice / Excel): роздільник `;`.

## 5) Використання в тестах (pytest + caplog)

* Тести ініціалізують логування через `setup_logging(debug=True, enable_csv=False)`,
  щоб:

  * мати консольний хендлер і бачити записи в `caplog`;
  * не створювати зайвих файлів під час юніт-тестів.

### Приклади асерцій

* Перевірити, що повідомлення з’явилось у логах:

  ```python
  def test_logging_writes_without_errors(caplog):
      setup_logging(debug=True)
      logger = logging.getLogger("price")
      with caplog.at_level(logging.INFO):
          logger.info("test-log", extra={"context": {"k": "v"}})
      assert any("test-log" in rec.message for rec in caplog.records)
  ```

* Перевірити наявність `request_id` у записі:

  ```python
  from calculator_engine.infra.logging.request_id import REQUEST_ID_VAR

  def test_request_id_appears_in_log_records(caplog):
      setup_logging(debug=True, enable_csv=False)
      rid = "req-123"
      token = REQUEST_ID_VAR.set(rid)
      try:
          logger = logging.getLogger("price")
          with caplog.at_level(logging.INFO):
              logger.info("log-with-request-id")
          assert any(getattr(rec, "request_id", None) == rid for rec in caplog.records)
      finally:
          REQUEST_ID_VAR.reset(token)
  ```

## 6) Як підняти сервіс та подивитись логи

* Запуск у dev-режимі (блокує термінал, авто‑reload):

  ```bash
  make run
  ```
* Перевірка доступності:

  ```bash
  make health   # GET /health
  ```
* Запуск у фоні:

  ```bash
  make run-bg
  make ps       # показати PID
  make stop     # зупинити
  make logs-tail
  ```

## 7) Розширення (roadmap)

* **Прив’язка до структурованого логування**:

  * опційний JSON-форматер для інтеграції з ELK/OpenSearch/GCP Logging.
* **Збагачення контексту**:

  * користувач / роль / IP / user-agent / версія клієнта;
  * кореляція з транзакціями БД, чергами, HTTP-клієнтами (`httpx` middleware).
* **Ротація логів**:

  * додати `TimedRotatingFileHandler` для `app.csv` (щоб не ріс нескінченно).
* **Захист чутливих даних**:

  * фільтрація PII/секретів через кастомні фільтри.

## 8) Короткий чекліст для внесення змін

1. Додаєте новий модуль — **не створюйте власні root-конфігурації**. Беріть `logging.getLogger("<namespace>")`.
2. Логування у функціях: додавайте мінімум корисного контексту через `extra={"context": {...}}`.
3. Якщо потрібен `request_id` поза HTTP-мідлварою — встановіть його вручну через `REQUEST_ID_VAR.set(...)` у відповідному контексті (фонова задача тощо).
4. Для інтеграційних змін — оновіть цей документ (розділ 7) і, за потреби, `docs/ops/01-logging.md`.

---

**Де шукати код**

* Ініціалізація: `src/calculator_engine/infra/logging/setup.py`
* Request ID var: `src/calculator_engine/infra/logging/request_id.py`
* Middleware: `src/calculator_engine/app/middleware.py`
* Шляхи логів: `src/calculator_engine/config/paths.py`
* Makefile команди: `Makefile` (`logs-tail`, `run[-bg]`, `stop`, `ps`)

**Питання/пропозиції** — додавайте issues у репозиторії або доповнюйте цей файл PR-ом.

