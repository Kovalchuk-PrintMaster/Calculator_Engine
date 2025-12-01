calculator_engine/
├─ apps/                      # великі застосунки (чітко відокремлені)
│  ├─ admin/                  # Django-адмінка (повністю ізольована)
│  │  ├─ manage.py
│  │  └─ calc_admin/          # settings/urls/wsgi/asgi
│  │     ├─ __init__.py
│  │     ├─ settings.py
│  │     ├─ urls.py
│  │     └─ wsgi.py
│  │  └─ catalog/             # наші Django-моделі та адмін-реєстрації
│  │     ├─ apps.py
│  │     ├─ models/
│  │     │  ├─ model_sizes.py
│  │     │  ├─ model_materials.py
│  │     │  ├─ model_material_aliases.py
│  │     │  └─ model_product_kinds.py
│  │     ├─ admin/
│  │     │  └─ admin_sizes.py
│  │     └─ migrations/
│  └─ api/                    # FastAPI/сервісна частина (теперішній пакет)
│     └─ calculator_engine/   # залишається як Python-пакет
│        ├─ app/
│        ├─ infra/
│        ├─ domain/
│        ├─ shared/
│        └─ scripts/
│
├─ infra/                     # інфраструктура (Docker, Alembic, CI)
│  ├─ docker/
│  │  └─ docker-compose.yml
│  └─ db/
│     ├─ alembic.ini
│     ├─ alembic/
│     │  ├─ env.py
│     │  └─ versions/
│     └─ seeds/               # SQL-сіди
│
├─ tools/                     # консольні утиліти / сервісні скрипти
│  └─ db/
│     ├─ db-dump-select.py
│     └─ db-restore.py
│
├─ config/                    # загальні конфіги (томли, шляхи, .env.example)
│  ├─ base.toml
│  ├─ dev.toml
│  └─ paths.py
│
├─ data/                      # дані проєкту (бекупи, імпортні xlsx)
│  ├─ backups/
│  ├─ data_base/
│  └─ seeds/                  # (можна тримати й тут копію, якщо зручно)
│
├─ docs/                      # документація (перенесено з source/docs)
│  ├─ README.md
│  ├─ architecture/
│  ├─ modules/
│  ├─ db/
│  ├─ ops/
│  └─ reference/
│
├─ logs/                      # логи
│  ├─ app.jsonl
│  ├─ autentification/
│  └─ data_base/
│
├─ requirements/
│  ├─ admin.txt
│  ├─ app.txt
│  └─ dev.txt
│
├─ tests/                     # тести (як і було)
├─ Makefile                   # один у корені (чистий, з варіабельними шляхами)
├─ pyproject.toml
└─ README.md
