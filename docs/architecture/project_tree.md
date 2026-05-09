# Project tree

## Top level


calculator_engine/
├── app/            # код, тести, службові інструменти, внутрішня документація
├── config/         # зовнішній env/config
├── data/           # backups, source files, seeds
├── logs/           # runtime logs
├── state/          # postgres, redis
└── _quarantine/    # тимчасово винесені legacy-файли

app/
├── apps/           # Django admin + API backend
│   ├── admin/
│   └── api/
├── docs/           # внутрішня документація проєкту
│   ├── architecture/
│   ├── db/
│   ├── modules/
│   ├── ops/
│   ├── project_config/
│   ├── reference/
│   └── style/
├── infra/          # docker, alembic, db infra
│   ├── db/
│   └── docker/
├── requirements/   # requirements/*.txt
├── settings/       # canonical app settings / paths
│   ├── app_settings.py
│   ├── paths.py
│   ├── base.toml
│   ├── dev.toml
│   └── __init__.py
├── source/         # runtime/shared application code
├── support/        # службові інструменти і тести
│   ├── common/
│   ├── db/
│   │   ├── db_dump_select.py
│   │   └── db_restore.py
│   └── tests/
│       └── unit/
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

Notes
app/ містить тільки код, тести, tooling і docs.
config/ містить зовнішню конфігурацію середовища.
data/ містить файли, бекапи та seed-артефакти.
logs/ і state/ винесені з app/, щоб не змішувати runtime із кодом.
support/ — єдиний корінь для службових DB-утиліт і тестів.