# Calculator Engine

Локальний движок калькуляції для друкарні з:

- Django admin для ведення довідників
- FastAPI backend для API
- PostgreSQL + Redis у Docker
- утилітами для дампів і відновлення БД
- чистою структурою, де код, конфіги, дані, логи та runtime-state не змішані між собою

---

## 1. Поточна структура проєкту


calculator_engine/
├── app/            # код, тести, службові інструменти, docs
├── config/         # зовнішній env/config
├── data/           # backups, source files, seeds
├── logs/           # runtime logs
├── state/          # postgres, redis
└── _quarantine/    # тимчасово винесені legacy-файли

app/
├── apps/           # Django admin + API backend
│   ├── admin/
│   └── api/
├── docs/           # внутрішня документація
├── infra/          # docker, alembic, db infra
├── requirements/   # requirements/*.txt
├── settings/       # canonical app settings / paths
├── source/         # runtime/shared application code
├── support/        # службові інструменти і тести
│   ├── common/
│   ├── db/
│   └── tests/
├── Makefile
├── pyproject.toml
└── README.md

data/
├── backups/                # дампи БД
├── seeds/
│   └── sql/                # SQL seed-файли
└── source_files/
    └── catalog/            # Excel / вхідні файли каталогу

runtime
env file: config/.env
postgres state: state/postgres
redis state: state/redis
runtime logs: logs/

2. Де що лежить
Конфіг

Основний env-файл:

config/.env
Дані

Бекапи БД:
data/backups

Вхідні Excel/каталожні файли:
data/source_files/catalog

SQL seed-файли:
data/seeds/sql

Налаштування застосунку

Canonical app settings живуть тут:
app/settings/app_settings.py
app/settings/paths.py
app/settings/base.toml
app/settings/dev.toml

Службові інструменти
DB dump / restore:
app/support/db

Тести:
app/support/tests

3. Швидкий старт
cd /srv/software_development/forprint-project/calculator_engine/app

python3 -m venv .venv_calculator
source .venv_calculator/bin/activate

pip install -r requirements/dev.txt
pip install -e .

Підняти локальну інфраструктуру:

make up
make ps
4. Django admin
Застосувати міграції:

make admin-migrate

Створити суперкористувача:

make admin-superuser

Запустити адмінку:

make admin-run

Локальна адреса:

http://127.0.0.1:8001/admin

5. Основні команди Makefile
Інфраструктура
make up
make down
make ps
make logs
Django admin
make admin-migrate
make admin-superuser
make admin-run
База даних
make db-shell
make db-dump-select
make db-restore
Тести
make test
make test-v
make test-one T=support/tests/unit/test_sanity.py
make check
Python package
make install-editable

6. Робота з дампами
Селективний дамп
make db-dump-select

Скрипт:

читає список таблиць із public
дозволяє вибрати потрібні таблиці
створює dump у data/backups
показує коротку звірку:
було в БД
чи є DATA в dump
скільки рядків реально потрапило в dump
Restore
make db-restore

Підтримуються режими:

повний restore
лише таблиці з дампа
schema-only
data-only
pre-data + TRUNCATE + data

Для сценаріїв із data-only скрипт синхронізує sequence там, де це потрібно.

7. Тести
Тести лежать у:

app/support/tests

Запуск:

make test

Verbose:

make test-v

Один файл:

make test-one T=support/tests/unit/test_sanity.py

8. Правила структури
Не змішуємо відповідальності
app/ — тільки код, тести, tooling і docs
config/ — зовнішня конфігурація середовища
data/ — файли, бекапи та seed-артефакти
logs/ — runtime logs
state/ — bind-mounted state контейнерів
Нові шляхи

У коді не додаємо “магічні” абсолютні або відносні шляхи.
Використовуємо тільки:
app/settings/paths.py
Нові службові скрипти

Кладемо в:
app/support/db
app/support/common
Нові тести

Кладемо в:
app/support/tests

9. Поточний технічний статус

На поточному етапі перевірено:

python apps/admin/manage.py check
make test
pip install -e .

Тобто структура проєкту вже узгоджена з:

Django admin
pytest
Makefile
editable install
DB dump / restore tooling

10. Legacy / quarantine
Старі файли та попередні варіанти структури не видаляються одразу.
Вони тимчасово складаються в:
_quarantine/
і лежать там, поки нова схема достатньо довго не відпрацює стабільно.