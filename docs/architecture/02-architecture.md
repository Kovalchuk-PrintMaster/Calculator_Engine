# 02. Архітектура проєкту «Calculator Engine»

> Версія: 0.0.1 · Останнє оновлення: 2025‑11‑09 · Статус: **draft**
> Власник: Core Platform Team

## 1) Мета документа

Цей документ описує загальну архітектуру сервісу **Calculator Engine** — модульного цінового рушія для поліграфії. Документ покликаний допомогти новому учаснику команди швидко розібратись із шаровою структурою, залежностями, потоками даних, принципами та дорожньою мапою розвитку.

## 2) Принципи проєктування

* **Проста шаровість**: `app → domain → infra`, плюс системні шари `config` і `shared`.
* **Чіткі межі**: роутери не знають про БД напряму — вони звертаються до доменних сервісів.
* **Контракти стабільні**: API-респонси та вхідні payload-и описані моделями (Pydantic), логіка — в домені.
* **Тестованість**: модульні тести для кожного шару, ізоляція домену від інфраструктури.
* **Спостережуваність**: єдиний стек логування (root-logger + `RequestIdFilter`), окремі каталоги логів.
* **Конфігурація через файли та env**: `settings` з пріоритетами та константами.
* **Еволюційність**: кожен шар може замінюватись (напр., синхронна/асинхронна БД) без масових змін API.

## 3) Огляд шарів та модулів

```
src/calculator_engine/
├─ app/              # ASGI-вхід, FastAPI, middleware, маршрути
│  ├─ main.py        # створює FastAPI app, підключає routers + middleware, /health
│  ├─ middleware.py  # Request-ID middleware (генерація/прокидання в заголовки)
│  └─ routers/
│     ├─ meta.py     # /meta/ping, /meta/info
│     ├─ price.py    # /price/quote (каркас розрахунку)
│     └─ doctor.py   # /doctor/status (системні перевірки)
│
├─ domain/           # бізнес-логіка (чиста, без залежності від FastAPI/SQLAlchemy)
│  ├─ pricing/       # ядро розрахунку: моделі, правила, обчислення
│  │  └─ core.py
│  └─ doctor/
│     └─ checks.py   # перевірки здоров'я сервісу (конфіг, залежності, тощо)
│
├─ infra/            # адаптери до зовнішніх систем
│  ├─ logging/
│  │  ├─ setup.py    # root-logger, Plain/Csv форматери, RequestIdFilter
│  │  └─ request_id.py
│  ├─ db/            # (майбутнє) SQLAlchemy engine/session/migrations
│  │  ├─ base.py
│  │  ├─ engine.py
│  │  └─ session.py
│  └─ storage/       # (майбутнє) інтеграція з S3, локальне сховище
│
├─ config/
│  ├─ paths.py       # єдине джерело шляхів (logs/, data/, config/ ...)
│  └─ settings.py    # AppSettings + пріоритети: defaults < base.toml < env.toml < ENV
│
└─ shared/
   ├─ constants.py   # крос‑шарові константи
   └─ request_context.py # ContextVar для request_id
```

### 3.1) Шар `app`

* **Відповідальність**: HTTP/ASGI, валідація вхідних даних, серіалізація відповіді, підключення middleware/routers.
* **Точки входу**: `app/main.py` (експорт `app` для Uvicorn/ASGI).
* **Маршрутизатори**:

  * `/health` — простий liveness.
  * `/meta/*` — службові метадані сервісу.
  * `/price/*` — API для розрахунку цін (каркас готовий; розширюватимемо).
  * `/doctor/*` — перевірки стану (конфіг, БД, залежності) для CI/ops.
* **Middleware**: `request_id` — генерує/прокидує `X-Request-ID` та заносить у контекст логування.

### 3.2) Шар `domain`

* **Відповідальність**: бізнес‑правила, розрахункові алгоритми, чисті функції/класи.
* **Без залежностей** від FastAPI/SQLAlchemy/Redis — лише стандартна бібліотека та Pydantic (за потреби DTO).
* **Приклад**: `pricing/core.py` — прототип розрахунку (qty, коефіцієнти, аудиторія).

### 3.3) Шар `infra`

* **Відповідальність**: інтеграції з зовнішнім світом (БД, кеш, S3, черги, логування).
* **Логування**: `infra/logging/setup.py` — root-logger + фільтр `RequestIdFilter`, форматери `PlainFormatter`/`CsvFormatter`. Логи в `logs/`.
* **База даних**: заготовки для SQLAlchemy 2.0 (`engine.py`, `session.py`, `base.py`). Деталі — у `04-db.md`.

### 3.4) Системні шари `config` і `shared`

* **`config.paths`** — єдине місце для шляхів (гарантує існування `logs/`, `data/`, `tmp/`).
* **`config.settings`** — завантаження налаштувань із TOML + ENV, повертає `AppSettings` (immutabledataclass).
* **`shared.request_context`** — `ContextVar` для `request_id`.
* **`shared.constants`** — загальні сталі.

## 4) Потік обробки HTTP‑запиту (high‑level)

1. **Uvicorn → FastAPI**: запит потрапляє в ASGI‑app `app`.
2. **Middleware (request_id)**: читає `X-Request-ID` або генерує новий, кладе в `ContextVar`, додає заголовок до відповіді.
3. **Router/Endpoint**: Pydantic валідація вхідних даних → виклик доменної логіки.
4. **Domain**: обчислення/перевірки/агрегації; звернення до `infra` через абстракції.
5. **Infra**: взаємодія з БД/кешем/S3 (асинхронно/синхронно, залежно від обраного стеку).
6. **Відповідь**: серіалізація і повернення даних; `request_id` вже в заголовках.

## 5) Контракти та моделі (DTO)

* Вхід/вихід HTTP‑ендпоінтів описуються **Pydantic** моделями.
* У домені DTO є простими типами/`BaseModel` без залежності від FastAPI.
* Контракти стабілізуються і покриваються тестами на backward‑compat.

## 6) Обробка помилок

* Помилки в домені — власні винятки з чіткими кодами/контекстом.
* У `app` рівні — перетворення на HTTP‑відповіді (400/404/409/422/500), логування через root‑logger.
* У майбутньому — централізований exception handler і мапінг у Problem Details (RFC 7807).

## 7) Логування та request_id

* Детально описано в `03-logging.md`.
* Коротко: root‑logger + `RequestIdFilter` (додає `record.request_id`), `PlainFormatter` для консолі і опційний `CsvFormatter` у `logs/app.csv`.

## 8) Конфігурація та середовища

* `settings` з пріоритетами: **defaults < config/base.toml < config/{ENV}.toml < ENV**.
* Стандартні ключі: `env`, `debug`, `app_name`, `postgres_dsn`, `redis_url`, `s3_*`.
* Для секретів/креденшалів — `.env` + GitHub Actions secrets.

## 9) Тестування

* **Pytest** + `pytest-randomly`, `pytest-xdist`, `pytest-cov`.
* Типи тестів: `unit` (домен, роутери, middleware, логування), згодом `integration` (БД, Redis), `e2e` (smoke через HTTP).
* Команди: `make test`, `make testv`, `make test-cov`, `make test-fast`.

## 10) CI/CD (коротко)

* GitHub Actions: ruff, black (—check), mypy, pytest (—q / —vv залежно від job), кешування .venv/pip.
* Далі: інтеграційні тести з Postgres (services), збірка container image, деплой на staging/production.

## 11) Безпека та відповідність

* Мінімальні скоупи для ключів БД/S3.
* Ліміти розміру запитів/таймаути в Uvicorn/Reverse‑proxy.
* Логи без секретів (редакція чутливих полів у майбутньому).

## 12) Дорожня карта (high‑level)

1. **Базова БД** (схема `pricing`, `quote`, `materials`; Alembic; docker-compose для dev) — див. `04-db.md`.
2. **Повний розрахунок** (правила ціноутворення, калькуляція багатошарових виробів).
3. **Кешування** (Redis для довідників/формул/проміжних результатів).
4. **Черги/події** (webhooks, нотифікації, async jobs).
5. **Спостережуваність** (метрики, трасування, алерти).

---

**Повʼязані документи**:

* `01-handbook/README.md` — як читати документацію, прийняті стандарти.
* `03-logging.md` — деталі логування.
* `04-db.md` — схема БД, міграції та робота з даними.
