# =============================================================================
# Calculator Engine — Makefile
# Уніфіковані корисні задачі для локальної розробки.
#
# Використання:
#   make help
#   make venv deps
#   make up | make down | make ps | make logs
#   make admin-run | make admin-migrate | make admin-superuser
#   make db-dump-select | make db-restore | make db-shell
# =============================================================================

SHELL       := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

# --- Базові шляхи ------------------------------------------------------------
APP_DIR       := $(CURDIR)
PROJECT_ROOT  := $(abspath ..)

VENV          := .venv_calculator
PY            := $(APP_DIR)/$(VENV)/bin/python
PIP           := $(APP_DIR)/$(VENV)/bin/pip

CONFIG_DIR    := $(PROJECT_ROOT)/config
ENV_FILE      := $(CONFIG_DIR)/.env

DATA_DIR      := $(PROJECT_ROOT)/data
BACKUP_DIR    := $(DATA_DIR)/backups
TIMESTAMP     := $(shell date +%Y%m%d_%H%M%S)

# --- Docker Compose ----------------------------------------------------------
DC            := docker compose -f infra/docker/docker-compose.yml --env-file "$(ENV_FILE)"

# --- Django admin ------------------------------------------------------------
ADMIN_DIR     := apps/admin
MANAGE        := $(APP_DIR)/$(ADMIN_DIR)/manage.py

# --- Support / service tools -------------------------------------------------

SUPPORT_DIR    := $(APP_DIR)/support
TOOLS_DB_DIR   := $(SUPPORT_DIR)/db
TESTS_DIR      := $(SUPPORT_DIR)/tests
API_BACKEND_DIR := $(APP_DIR)/apps/api/backend

DB_DUMP_SEL    := $(TOOLS_DB_DIR)/db_dump_select.py
DB_RESTORE     := $(TOOLS_DB_DIR)/db_restore.py

# --- Змінні з config/.env ----------------------------------------------------
PGUSER := $(shell awk -F= '/^POSTGRES_USER=/{print $$2}' "$(ENV_FILE)" 2>/dev/null)
PGDB   := $(shell awk -F= '/^POSTGRES_DB=/{print $$2}' "$(ENV_FILE)" 2>/dev/null)
PGPORT := $(shell awk -F= '/^POSTGRES_PORT=/{print $$2}' "$(ENV_FILE)" 2>/dev/null)

.DEFAULT_GOAL := help

.PHONY: help
help: ## Показати доступні команди
	@grep -E '^[a-zA-Z0-9\-\_]+:.*?## ' $(MAKEFILE_LIST) | \
		sed -E 's/:.*##/: /' | sort | awk 'BEGIN {FS=": "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

# --- Перевірка наявності .env та ключових змінних ------------------------------------------------------------
.PHONY: ensure-env
ensure-env:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		echo "❌ Не знайдено $(ENV_FILE)"; \
		exit 1; \
	fi

ENV_REQUIRED_TARGETS := up down down-reset ps logs admin-run admin-migrate admin-superuser \
						db-dump-select db-dump-select-debug db-restore db-shell check-env

$(ENV_REQUIRED_TARGETS): ensure-env

# --- Зберегти структуру проекту у tree.txt --------------------------------------------------------------------
.PHONY: tree 
tree: 
	tree -L 10 -I 'venv|.venv|__pycache__|.git|.vscode|.idea|.pytest_cache|.mypy_cache' > tree.txt

# =============================================================================
# Python/venv
# =============================================================================

.PHONY: venv
venv: ## Створити virtualenv (.venv_calculator)
	@test -d $(VENV) || python3 -m venv $(VENV)
	@echo "✅ venv готовий: $(VENV)"

.PHONY: deps
deps: venv ## Встановити залежності (якщо є requirements/*.txt)
	@if [ -f requirements/dev.txt ]; then \
		$(PIP) install -r requirements/dev.txt; \
	elif [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	else \
		echo "ℹ️ requirements* не знайдено — пропускаю"; \
	fi

# =============================================================================
# Docker
# =============================================================================

.PHONY: up
up: ## Підняти локальні сервіси
	$(DC) up -d

.PHONY: down
down: ## Зупинити локальні сервіси
	$(DC) down

.PHONY: down-reset
down-reset: ## Зупинити сервіси і ВИДАЛИТИ volumes
	$(DC) down -v

.PHONY: ps
ps: ## Переглянути список контейнерів
	$(DC) ps

.PHONY: logs
logs: ## Стрім логів docker-compose
	$(DC) logs -f --tail=150

# =============================================================================
# Django admin (локальна адмінка для наповнення даних)
# =============================================================================

.PHONY: admin-run
admin-run: ## Запустити Django-адмінку на 127.0.0.1:8001
	@set -euo pipefail; { \
		if PIDS="$$(lsof -t -i:8001 -sTCP:LISTEN 2>/dev/null)"; then \
			echo "🔒 Порт 8001 зайнятий, зупиняю PID(s): $$PIDS"; \
			kill -9 $$PIDS || true; \
		else \
			echo "✅ Порт 8001 вільний"; \
		fi; \
		$(DC) up -d; \
		$(PY) $(MANAGE) runserver 127.0.0.1:8001; \
	}

.PHONY: admin-migrate
admin-migrate: ## Застосувати міграції Django
	$(PY) $(MANAGE) migrate

.PHONY: admin-superuser
admin-superuser: ## Створити суперкористувача Django (інтерактивно)
	$(PY) $(MANAGE) createsuperuser

# =============================================================================
# База даних: дамп/відновлення/консоль
# =============================================================================

.PHONY: db-dump-select
db-dump-select: ## Створити селективний дамп
	@mkdir -p "$(BACKUP_DIR)"
	$(PY) $(DB_DUMP_SEL)

.PHONY: db-dump-select-debug
db-dump-select-debug: ## Те саме з DEBUG
	@mkdir -p "$(BACKUP_DIR)"
	DEBUG=1 $(PY) $(DB_DUMP_SEL)

.PHONY: db-restore
db-restore: ## Відновлення з дампа
	$(PY) $(DB_RESTORE)

.PHONY: db-shell
db-shell: ## Відкрити psql у контейнері postgres
	$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB"'
	
# =============================================================================
# Перевірки/утиліти
# =============================================================================

.PHONY: check-env
check-env: ## Показати ключові змінні з .env (без секретів)
	@echo "POSTGRES_USER=$(PGUSER)"
	@echo "POSTGRES_DB=$(PGDB)"
	@echo "POSTGRES_PORT=$(PGPORT)"

# ------------------- Запустити тести --------------------------------------------------------------

.PHONY: test
test: ## Запустити тести
	PYTHONPATH="$(API_BACKEND_DIR):$(APP_DIR):$${PYTHONPATH:-}" \
	$(PY) -m pytest "$(TESTS_DIR)" -q

.PHONY: test-v
test-v: ## Запустити тести з детальним виводом
	PYTHONPATH="$(API_BACKEND_DIR):$(APP_DIR):$${PYTHONPATH:-}" \
	$(PY) -m pytest "$(TESTS_DIR)" -v

.PHONY: test-one
test-one: ## Запустити один тест: make test-one T=support/tests/unit/test_sanity.py
	@test -n "$(T)" || (echo '❌ Вкажи T=шлях_до_тесту'; exit 1)
	PYTHONPATH="$(API_BACKEND_DIR):$(APP_DIR):$${PYTHONPATH:-}" \
	$(PY) -m pytest "$(T)" -v

# ------------------- Створити теку для бекапів, якщо відсутня --------------------------------------
.PHONY: ensure-backup-dir
ensure-backup-dir: ## Створити теку для бекапів, якщо відсутня
	@mkdir -p "$(BACKUP_DIR)"; echo "📦 $(BACKUP_DIR) готова"

# ------------------- Базова перевірка проєкту -------------------------------------------------------	
.PHONY: check
check: ## Базова перевірка проєкту
	$(PY) apps/admin/manage.py check
	$(MAKE) test

.PHONY: install-editable
install-editable: ## Встановити пакет у editable mode
	$(PIP) install -e .

.PHONY: tree-app
tree-app: ## Показати коротке дерево app
	tree -L 2 $(APP_DIR)

