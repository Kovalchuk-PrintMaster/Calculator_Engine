# python -m settings.paths
"""
📄 Назва: paths.py – централізовані шляхи проєкту.

🧠 Призначення:
  Єдине джерело істини для всіх директорій і службових файлів:
  - кореневі теки (config/data/logs/tmp/docs/tests/tools/apps/infra/…)
  - модулі: Docker, Django Admin, API backend, DB, Backups, Logs
  - формування службових URL/DSN із .env (де доречно)

🔗 Залежності:
  - .env у корені репозиторію (необов’язково; якщо нема – працюємо з дефолтами)
  - фактична структура тек (див. docs/architecture/* і tree.txt)

🗂 Шляхи/налаштування:
  У всьому коді імпортуємо так: `from config import paths as PATH`.

🔍 Аудит і рекомендації:
  - Нову службову теку спершу додай сюди, потім використовуй у скриптах.
  - Уникай “жорстких” шляхів у Make/скриптах — читай їх із PATH.

✅ Актуальність: вирівняно під дерево з support/db (міграція з support/db).

📦 Приклади:
  from settings import paths as PATH
  print(PATH.DATA_BACKUPS_DIR)
  print(PATH.PG_DSN)
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# -----------------------------------------------------------------------------
# ROOTS
# -----------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
CONFIG_DIR = THIS_FILE.parent
PROJECT_ROOT = CONFIG_DIR.parent  # ~/calculator_engine

# Публічні кореневі теки
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TMP_DIR = PROJECT_ROOT / "tmp"
DOCS_DIR = PROJECT_ROOT / "docs"
TOOLS_DIR = PROJECT_ROOT / "tools"
TESTS_DIR = PROJECT_ROOT / "tests"
INFRA_DIR = PROJECT_ROOT / "infra"
APPS_DIR = PROJECT_ROOT / "apps"

# Гарантуємо службові теки
for p in (DATA_DIR, LOGS_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# LOGS
# -----------------------------------------------------------------------------
AUTH_LOGS_DIR = LOGS_DIR / "autentification"  # так, як узгоджено
DB_LOGS_DIR = LOGS_DIR / "data_base"
for p in (AUTH_LOGS_DIR, DB_LOGS_DIR):
    p.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# DATA
# -----------------------------------------------------------------------------
DATA_BACKUPS_DIR = DATA_DIR / "backups"
DATA_SEEDS_DIR = DATA_DIR / "seeds"
DATA_RAW_DIR = DATA_DIR / "data_base"  # сирі xlsx/csv тощо
for p in (DATA_BACKUPS_DIR, DATA_SEEDS_DIR, DATA_RAW_DIR):
    p.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------------------------------
# DOCS
# -----------------------------------------------------------------------------
DOCS_DB_DIR = DOCS_DIR / "db"
DOCS_ARCH_DIR = DOCS_DIR / "architecture"
DOCS_MODULES_DIR = DOCS_DIR / "modules"
DOCS_OPS_DIR = DOCS_DIR / "ops"
DOCS_REFERENCE_DIR = DOCS_DIR / "reference"
DOCS_PROJECT_CFG = DOCS_DIR / "project_config"

# -----------------------------------------------------------------------------
# DOCKER / DB-INFRA
# -----------------------------------------------------------------------------
# Повернули compose до ./docker, бо так у твоєму Makefile
DOCKER_DIR = PROJECT_ROOT / "docker"
DOCKER_COMPOSE = DOCKER_DIR / "docker-compose.yml"

DB_INFRA_DIR = INFRA_DIR / "db"
ALEMBIC_DIR = DB_INFRA_DIR / "alembic"
ALEMBIC_INI = DB_INFRA_DIR / "alembic.ini"
ALEMBIC_VERSIONS = ALEMBIC_DIR / "versions"
DB_SEEDS_INFRA = DB_INFRA_DIR / "seeds"

# -----------------------------------------------------------------------------
# APPS: Django Admin + API backend
# -----------------------------------------------------------------------------
# Django admin
ADMIN_ROOT = APPS_DIR / "admin"
ADMIN_DJANGO_DIR = ADMIN_ROOT / "calc_admin"
ADMIN_MANAGE_PY = ADMIN_ROOT / "manage.py"
ADMIN_CATALOG_APP = ADMIN_ROOT / "catalog"
ADMIN_REQUIREMENTS = PROJECT_ROOT / "requirements" / "admin.txt"

# API backend (пакет calculator_engine)
API_BACKEND_ROOT = APPS_DIR / "api" / "backend"
API_PKG_ROOT = API_BACKEND_ROOT / "calculator_engine"
API_APP_DIR = API_PKG_ROOT / "app"
API_ROUTERS_DIR = API_APP_DIR / "routers"
API_DJANGO_INFRA = API_PKG_ROOT / "django_infra"  # локальна інфра API
API_DOMAIN_DIR = API_PKG_ROOT / "domain"
API_SHARED_DIR = API_PKG_ROOT / "shared"
API_SCRIPTS_DIR = API_PKG_ROOT / "scripts"
API_REQUIREMENTS = PROJECT_ROOT / "requirements" / "app.txt"

# -----------------------------------------------------------------------------
# TOOLS (утиліти роботи з БД) – МІГРУВАЛИ ДО support/db
# -----------------------------------------------------------------------------
TOOLS_DB_DIR = TOOLS_DIR / "db"
TOOL_DB_DUMP_SELECT = TOOLS_DB_DIR / "db-dump-select.py"  # з гіфеном
TOOL_DB_RESTORE = TOOLS_DB_DIR / "db-restore.py"  # з гіфеном

# -----------------------------------------------------------------------------
# ENV / DSN / SERVICE URLS (дефолти дружні для локалки)
# -----------------------------------------------------------------------------
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
PG_DB = os.getenv("POSTGRES_DB", "calculator")
PG_USER = os.getenv("POSTGRES_USER", "calc_user")
PG_PASS = os.getenv("POSTGRES_PASSWORD", "")

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

PG_DSN = f"postgresql://{PG_USER}:{PG_PASS}@{PG_HOST}:{PG_PORT}/{PG_DB}"
REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# Зручний docker compose командний префікс як список (для subprocess.run)
DC_PREFIX = [
    "docker",
    "compose",
    "-f",
    str(DOCKER_COMPOSE),
    "--env-file",
    str(PROJECT_ROOT / ".env"),
]


# -----------------------------------------------------------------------------
# Короткий підсумковий об’єкт (для REPL/діагностики)
# -----------------------------------------------------------------------------
@dataclass(frozen=True)
class Summary:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = DATA_DIR
    backups: Path = DATA_BACKUPS_DIR
    logs: Path = LOGS_DIR
    tmp: Path = TMP_DIR
    docker_compose: Path = DOCKER_COMPOSE
    admin_manage: Path = ADMIN_MANAGE_PY
    api_pkg: Path = API_PKG_ROOT
    pg_dsn: str = PG_DSN
    redis_url: str = REDIS_URL


PATH = Summary()


# --- compatibility aliases for tests / legacy imports ------------------------

_SETTINGS_DIR = Path(__file__).resolve().parent

APP_ROOT = _SETTINGS_DIR.parent
PROJECT_ROOT = APP_ROOT.parent
SRC_ROOT = APP_ROOT / "apps" / "api" / "backend"
