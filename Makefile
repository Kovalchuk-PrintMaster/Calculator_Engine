# ============================================================
# Project: calculator_engine — Makefile
# Works with: Docker Desktop + WSL, .venv_calculator (Python)
# ============================================================

SHELL       := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.ONESHELL:

# --- Paths / tools -----------------------------------------------------------
VENV            := .venv_calculator
PY              := $(CURDIR)/$(VENV)/bin/python
UVICORN         := $(CURDIR)/$(VENV)/bin/uvicorn

API_DIR   		:= apps/api

ALEMBIC         := $(CURDIR)/$(VENV)/bin/alembic

ADMIN_DIR       := apps/admin/
MANAGE          := $(CURDIR)/$(ADMIN_DIR)/manage.py

DC              := docker compose -f docker/docker-compose.yml --env-file .env
DOCKER          := infra/docker

BACKUP_DIR     := data/backups
TIMESTAMP       := $(shell date +%Y%m%d_%H%M%S)

PGUSER := $(shell awk -F= '/^POSTGRES_USER=/{print $$2}' .env)
PGPASS := $(shell awk -F= '/^POSTGRES_PASSWORD=/{print $$2}' .env)
PGDB   := $(shell awk -F= '/^POSTGRES_DB=/{print $$2}' .env)
PGPORT := $(shell awk -F= '/^POSTGRES_PORT=/{print $$2}' .env)

ifdef DEBUG
BASH_X := set -x;
endif

# --- Silent targets ----------------------------------------------------------
.SILENT: db-restore-all db-restore-schema-only db-restore-data-only db-dump-select

.DELETE_ON_ERROR:

# --- Phony targets -----------------------------------------------------------
.PHONY: help \
		infra-up infra-down infra-logs infra-status \
		db-wait psql-docker psql-file db-ping db-ping-strict \
		redis-cli-docker redis-ping redis-cli-run \
		alembic-up run \
		admin-migrate admin-superuser admin-run admin-shell admin-reset-password \
		db-list-tables db-dump-select db-restore-all db-restore-schema-only db-restore-data-only  \
		

# --- Help --------------------------------------------------------------------
help: ## Показати довідку по цілям
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS":.*##"; printf("")} /^[a-zA-Z0-9_-]+:.*?##/ {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)
	@echo ""

# --- Guard: docker present ---------------------------------------------------
ensure-docker:
ifeq ($(DOCKER),)
	@echo "⚠️  Docker не знайдено у цьому WSL-дистрибутиві."
	@echo "   Відкрий Docker Desktop → Settings → Resources → WSL Integration та увімкни для цього дистро."
	@exit 1
endif

# --- Infra (Docker) ----------------------------------------------------------
infra-up: ensure-docker ## Підняти інфраструктуру (Postgres, Redis)
	$(DC) up -d

infra-down: ensure-docker ## Зупинити контейнери/томи
	$(DC) down

infra-down-destroy: ensure-docker ## Зупинити та видалити контейнери/томи
	$(DC) down -v

infra-logs: ensure-docker ## Логи всіх сервісів
	$(DC) logs -f

infra-status: ensure-docker ## Стан контейнерів
	$(DC) ps

# --- Database Postgres quick checks ---------------------------------------------------

db-wait: ensure-docker ## Очікувати готовність Postgres
	$(DC) exec -T postgres sh -lc 'pg_isready -U "$$POSTGRES_USER" -h 127.0.0.1 -p "$$POSTGRES_PORT"'

# Зайти в psql усередині контейнера
psql-docker: ensure-docker ## Запустити psql в контейнері
	$(DC) exec -it postgres sh -lc '\
		psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" "$$POSTGRES_DB" \
	'

psql-file: ensure-docker ## Виконати SQL-файл у Postgres (використання: make psql-file FILE=seed.sql)
	@[ -n "$(FILE)" ] || (echo "Usage: make psql-file FILE=path.sql"; exit 1)
	$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" "$$POSTGRES_DB"' < $(FILE)

db-ping: ## Перевірити підключення до БД (ліберально)
	$(PY) -m calculator_engine.scripts.db_ping || true

db-ping-strict: ## Перевірити підключення до БД (строго, з кодом помилки)
	$(PY) -m calculator_engine.scripts.db_ping

# --- Redis -------------------------------------------------------------------
redis-cli-docker: ensure-docker ## Відкрити redis-cli у контейнері
	$(DC) exec -it redis sh -lc 'redis-cli -h 127.0.0.1 -p "$$REDIS_PORT"'

redis-ping: ensure-docker ## Перевірити Redis (PING)
	$(DC) exec -T redis sh -lc 'redis-cli -h 127.0.0.1 -p "$$REDIS_PORT" PING'

redis-cli-run: ensure-docker ## Тимчасовий redis-cli у мережі docker_default
	docker run --rm -it --network docker_default redis:7-alpine redis-cli -h redis -p 6379

# --- Alembic (DB migrations for API) ----------------------------------------

# --- Застосувати міграції Alembic (до head)
db-upgrade:
	$(ALEMBIC) upgrade head

db-downgrade:
	@read -p "Downgrade to revision (e.g. -1 or <rev>): " REV; \
	$(ALEMBIC) downgrade $$REV

db-history:
	$(ALEMBIC) history

db-current:
	$(ALEMBIC) current -v

# db-seed FILE?=data/seeds/01_print_colors_and_finishing.sql
db-seed: ## Виконати SQL seed: make db-seed FILE=data/seeds/xxx.sql
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres \
	psql -U $$POSTGRES_USER -d $$POSTGRES_DB -v "ON_ERROR_STOP=1" -f "$(FILE)"
	@echo "Seed OK -> $(FILE)"


#--- Seed базових довідників ---------------------------------------------------
db-seed-basics: ## seed базових довідників (кольорові схеми, finishing)
	$(PYTHON) - <<'PY'
	from sqlalchemy import text
	from calculator_engine.db import engine
	sql = """
	-- (тут той самий SQL блок що вище)
	"""
	with engine.begin() as conn:
	conn.execute(text(sql))
	print("Seed OK")
	PY


# --- FastAPI app -------------------------------------------------------------
run: ## Запустити FastAPI (локально, dev)
	$(UVICORN) calculator_engine.app.main:app --reload --host 127.0.0.1 --port 8001


#--- Finish work with Django ------------------------------------------------

# --- Django Admin ------------------------------------------------------------

admin-run: ## Django: запустити адмінку на 8001
	@set -euo pipefail; { \
	if PIDS="$$(lsof -t -i:8001 -sTCP:LISTEN 2>/dev/null)"; then \
		echo "🔒 Порт 8001 зайнятий, зупиняю PID(s): $$PIDS"; kill -9 $$PIDS || true; \
	else echo "✅ Порт 8001 вільний"; fi; \
	docker compose -f $(DOCKER_DIR)/docker-compose.yml --env-file .env up -d; \
	./.venv_calculator/bin/python $(ADMIN_DIR)/manage.py runserver 127.0.0.1:8001; \
	}


db-show-config: ## Показати налаштування підключення до БД (Django)	
	@cd $(ADMIN_DIR) && \
	python manage.py shell -c "from django.conf import settings; print(settings.DATABASES['default'])" && \
	cd ..

admin-migrate: ## Django: застосувати базові міграції (auth, admin, sessions)
	$(PY) $(MANAGE) migrate

admin-superuser: ## Django: створити суперкористувача
	$(PY) $(MANAGE) createsuperuser

admin-kill: ## Django: вбити процес на 8001
	lsof -ti :8001 | xargs -r kill -9

admin-shell: ## Django: відкрити shell
	$(PY) $(MANAGE) shell

#--- Django Admin: User management ------------------------------------------------


admin-list-users: ## Django: показати список користувачів
	@cd $(ADMIN_DIR) && \
	python manage.py shell -c 'from django.contrib.auth import get_user_model as g; U=g(); print(list(U.objects.values_list("id","username","email")))' && \
	cd ..

# Django Admin: перевірка підключення до БД та моделей каталогу
admin-check:
	$(PY) -	<<'PY'
	from django.conf import settings
	from django.apps import apps
	print("DB:", settings.DATABASES['default'])
	print("Installed catalog:", apps.is_installed('catalog'))
	for m in ['ProductKind','ProductKindName','Material','MaterialAlias','Size','FinishingKind','FinishingOption','PrintColorScheme','ProductKindPrintColor']:
	try:
		apps.get_model('catalog', m)
		print("OK model:", m)
	except Exception as e:
		print("ERR model:", m, e)
	PY


# Django: створити суперкористувача з параметрами (make admin-create-superuser USER=printmaster EMAIL=kovalchuk.printmaster@gmail.com PASS=kardan0303	
admin-create-superuser:
	@cd $(ADMIN_DIR) && \
	python manage.py createsuperuser --username printmaster --email kovalchuk.printmaster@gmail.com && \
	cd ..

admin-reset-password: ## Django: скинути пароль (make admin-reset-password USER=printmaster PASS='NewPass123!')
	@[ -n "$(USER)" ] || (echo "Usage: make admin-reset-password USER=username PASS='NewPass123!'"; exit 1)
	@[ -n "$(PASS)" ] || (echo "Usage: make admin-reset-password USER=username PASS='NewPass123!'"; exit 1)
	$(PY) $(MANAGE) shell -c "from django.contrib.auth import get_user_model; U=get_user_model(); u=U.objects.get(username='$(USER)'); u.set_password('$(PASS)'); u.save(); print('OK')"

# Команди Django Import/Export

# експорт
	python manage.py export_app_data app.Size --format=xlsx --output data/exports/sizes.xlsx

# імпорт (dry-run)
	python manage.py import_app_data app.Size --format=xlsx --input data/exports/sizes.xlsx --dry-run

# імпорт (застосувати)
	python manage.py import_app_data app.Size --format=xlsx --input data/exports/sizes.xlsx

#--- Finish work with Django ------------------------------------------------

#--- Backup Data Base ------------------------------------------------

# Список публічних таблиць (службова, для внутрішнього використання)
db-tables-list: ## Вивести список таблиць у public
	$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" -c "\dt public.*"'


db-dump: ensure-docker ## Зробити dump БД у data/backups/db_YYYYmmdd_HHMMSS.dump
	@mkdir -p $(BACKUP_DIR)
	@ts=$$(date +%Y%m%d_%H%M%S); \
	$(DC) exec -T postgres sh -lc '\
		pg_dump \
			-U "$$POSTGRES_USER" \
			-h localhost -p "$$POSTGRES_PORT" \
			-d "$$POSTGRES_DB" \
			-F c -Z 6 \
	' > $(BACKUP_DIR)/db_$${ts}.dump
	@echo "OK -> $(BACKUP_DIR)/db_$${ts}.dump"

db-dump-select: ## Інтерактивний вибір таблиць та створення .dump (через Python)
	@./.venv_calculator/bin/python $(DB_TOOLS)/db_dump_select.py

db-dump-select-debug: ## Те саме, але з детальним виводом (DEBUG=1)
	@DEBUG=1 python3 source/utils/db/db_dump_select.py

# Плейн SQL (структура+дані у тексті .sql)
db-dump-plain: ## Повний dump як plain SQL (.sql)
	set -euo pipefail
	mkdir -p data/backups
	ts="$$(date +%Y%m%d_%H%M%S)"
	file="data/backups/db_FULL_$${ts}.sql"
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc \
	'pg_dump -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB"' \
	> "$$file"
	echo "✅ OK -> $$file"

# Лише схема (без даних)
db-dump-schema: ## Тільки схема (DDL) як plain SQL (.sql)
	set -euo pipefail
	mkdir -p data/backups
	ts="$$(date +%Y%m%d_%H%M%S)"
	file="data/backups/db_SCHEMA_$${ts}.sql"
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc \
	'pg_dump -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" --schema-only' \
	> "$$file"
	echo "✅ OK -> $$file"

# Лише дані (без CREATE TABLE)
db-dump-data: ## Тільки дані як plain SQL (.sql)
	set -euo pipefail
	mkdir -p data/backups
	ts="$$(date +%Y%m%d_%H%M%S)"
	file="data/backups/db_DATA_$${ts}.sql"
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc \
	'pg_dump -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" --data-only' \
	> "$$file"
	echo "✅ OK -> $$file"

# Відновлення з конкретного файлу: make db-restore FILE=data/backups/db_xxx.dump

# ========== ВНУТРІШНІ ХЕЛПЕРИ ==========

# Обрати дамп зі списку -> змінна DUMP у підшеллі
define __pick_dump
	@shopt -s nullglob; \
	FILES=(data/backups/*.dump); \
	if (( $${#FILES[@]} == 0 )); then echo "❌ Немає файлів у data/backups/*.dump"; exit 1; fi; \
	echo "Доступні дампи:"; i=1; \
	for f in "$${FILES[@]}"; do printf "%2d. %s  (%s)\n" $$i "$$f" "$$(stat -c %y "$$f")"; ((i++)); done; \
	echo; printf "Вибери номер дампа: "; read -r idx; \
	if ! [[ "$$idx" =~ ^[0-9]+$$ ]] || (( idx<1 || idx> $${#FILES[@]} )); then echo "❌ Некоректний номер"; exit 1; fi; \
	echo "$${FILES[$$((idx-1))]}"
endef

# Внутрішня функція: визначити тип дампа (custom vs plain)
define __dump_kind
	@DUMP="$(1)"; \
	magic="$$(head -c 5 "$$DUMP" 2>/dev/null || true)"; \
	if [ "$$magic" = "PGDMP" ]; then \
		echo custom; \
	else \
		echo plain; \
	fi
endef

# Копіювати дамп у контейнер і відновлювати по файловому шляху (а не через stdin)
# 1) docker compose cp <host_file> postgres:/tmp/restore.dump
# 2) pg_restore ... /tmp/restore.dump
define _restore_from_file
set -euo pipefail; \
DUMP_FILE="$1"; \
echo "▶️  Копіюю дамп у контейнер: $$DUMP_FILE -> postgres:/tmp/restore.dump"; \
docker compose -f docker/docker-compose.yml --env-file .env cp "$$DUMP_FILE" postgres:/tmp/restore.dump; \
docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc \
	'pg_restore $(RESTORE_ARGS) -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" /tmp/restore.dump'; \
echo "🧹 Прибираю тимчасовий файл..."; \
docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc 'rm -f /tmp/restore.dump'
endef

# ========== ПУБЛІЧНІ ЦІЛІ ==========

# 1) Готовий restore з явним файлом:
#    make db-restore FILE=data/backups/xxx.dump
db-restore: # Відновити (DROP/CREATE + дані) з вказаного файлу FILE=...
	@./.venv_calculator/bin/python $(DB_TOOLS)/db_restore.py

db-restore-debug: # DEBUG Відновити (DROP/CREATE + дані) з вказаного файлу FILE=...
	DEBUG=1 @./.venv_calculator/bin/python $(DB_TOOLS)/db_restore.py

db-restore-path: # або вказати інший каталог пошуку дампів
	python3 source/utils/db/db_restore.py --dir /path/to/dumps

# 2) Повне відновлення (з вибору файлу)
db-restore-all: ## Повне відновлення (DROP/CREATE всього, що є у дампі)
	FILES="$$(ls -1t $(BACKUP_DIR)/*.dump 2>/dev/null || true)"; \
	if [ -z "$$FILES" ]; then echo "❌ Немає дампів у $(BACKUP_DIR)"; exit 1; fi; \
	echo "Доступні дампи:"; \
	n=1; for f in $$FILES; do ts="$$(stat -c %y "$$f")"; printf " %d. %s  (%s)\n" $$n "$$f" "$$ts"; n=$$((n+1)); done; \
	echo; printf "Вибери номер дампа: "; read -r idx; \
	cnt=$$(printf "%s\n" $$FILES | wc -l); \
	if ! printf "%s" "$$idx" | grep -Eq '^[0-9]+$$' || [ "$$idx" -lt 1 ] || [ "$$idx" -gt "$$cnt" ]; then echo "❌ Хибний номер"; exit 1; fi; \
	FILE="$$(printf "%s\n" $$FILES | sed -n "$${idx}p")"; \
	echo "Файл: $$FILE"; printf "Підтвердити відновлення? [yes/NO]: "; read -r ok; \
	if [ "$$ok" != "yes" ]; then echo "Перервано"; exit 1; fi; \
	# повне відновлення: дропаємо й створюємо схему public, потім pg_restore
	echo "Dropping and recreating schema public..."; \
	$(DC) exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"'; \
	echo "Restoring..."; \
	$(DC) exec -T postgres sh -lc 'pg_restore -l' < "$$FILE"\
		-U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
		--no-owner --role="$$POSTGRES_USER" -F c -v' < "$$FILE"; \
	echo "✅ Done."

# 3) Тільки схема
db-restore-schema-only: ## Відновити тільки схему з обраного .dump (DROP/CREATE, без даних)
	FILES="$$(ls -1t $(BACKUP_DIR)/*.dump 2>/dev/null || true)"; \
	if [ -z "$$FILES" ]; then echo "❌ Немає дампів у $(BACKUP_DIR)"; exit 1; fi; \
	echo "Доступні дампи:"; n=1; \
	for f in $$FILES; do ts="$$(stat -c %y "$$f")"; printf " %d. %s  (%s)\n" $$n "$$f" "$$ts"; n=$$((n+1)); done; \
	echo; printf "Вибери номер дампа: "; read -r idx; \
	cnt=$$(printf "%s\n" $$FILES | wc -l); \
	if ! printf "%s" "$$idx" | grep -Eq '^[0-9]+$$' || [ "$$idx" -lt 1 ] || [ "$$idx" -gt "$$cnt" ]; then echo "❌ Хибний номер"; exit 1; fi; \
	FILE="$$(printf "%s\n" $$FILES | sed -n "$${idx}p")"; \
	printf "Відновити ТІЛЬКИ СХЕМУ з $$FILE? [yes/NO]: "; read -r ok; \
	if [ "$$ok" != "yes" ]; then echo "Перервано"; exit 1; fi; \
	$(DC) exec -i postgres sh -lc 'pg_restore \
		-U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
		--schema-only --no-owner --role="$$POSTGRES_USER" -F c -v' < "$$FILE"; \
	echo "✅ Done."

# 4) Тільки дані
db-restore-data-only: ## Відновити тільки дані з обраного .dump (без схеми)
	FILES="$$(ls -1t $(BACKUP_DIR)/*.dump 2>/dev/null || true)"; \
	if [ -z "$$FILES" ]; then echo "❌ Немає дампів у $(BACKUP_DIR)"; exit 1; fi; \
	echo "Доступні дампи:"; n=1; \
	for f in $$FILES; do ts="$$(stat -c %y "$$f")"; printf " %d. %s  (%s)\n" $$n "$$f" "$$ts"; n=$$((n+1)); done; \
	echo; printf "Вибери номер дампа: "; read -r idx; \
	cnt=$$(printf "%s\n" $$FILES | wc -l); \
	if ! printf "%s" "$$idx" | grep -Eq '^[0-9]+$$' || [ "$$idx" -lt 1 ] || [ "$$idx" -gt "$$cnt" ]; then echo "❌ Хибний номер"; exit 1; fi; \
	FILE="$$(printf "%s\n" $$FILES | sed -n "$${idx}p")"; \
	printf "Відновити ТІЛЬКИ ДАНІ з $$FILE? [yes/NO]: "; read -r ok; \
	if [ "$$ok" != "yes" ]; then echo "Перервано"; exit 1; fi; \
	$(DC) exec -i postgres sh -lc 'pg_restore \
		-U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
		--data-only --disable-triggers --no-owner --role="$$POSTGRES_USER" -F c -v' < "$$FILE"; \
	echo "✅ Done."

# 5) Вибіркове відновлення таблиць
db-restore-select: ## Інтерактивне відновлення вибраних таблиць з .dump (DROP/CREATE + DATA)
	@set -euo pipefail; { \
		FILES="$$(ls -1t $(BACKUP_DIR)/*.dump 2>/dev/null || true)"; \
		if [ -z "$$FILES" ]; then echo "❌ Немає дампів у $(BACKUP_DIR)"; exit 1; fi; \
		echo "Доступні дампи:"; n=1; \
		for f in $$FILES; do ts="$$(stat -c %y "$$f")"; printf " %d. %s  (%s)\n" $$n "$$f" "$$ts"; n=$$((n+1)); done; \
		echo; printf "Вибери номер дампа: "; read -r idx; \
		cnt=$$(printf "%s\n" $$FILES | wc -l); \
		if ! printf "%s" "$$idx" | grep -Eq '^[0-9]+$$' || [ "$$idx" -lt 1 ] || [ "$$idx" -gt "$$cnt" ]; then \
			echo "❌ Хибний номер"; exit 1; \
		fi; \
		FILE="$$(printf "%s\n" $$FILES | sed -n "$${idx}p")"; \
		echo "Читаю список таблиць у дампі..."; \
		TABS="$$( \
			$(DC) exec -T postgres sh -lc 'pg_restore -l' < "$$FILE" \
			| awk '/^[0-9]+;.*TABLE[[:space:]]/ { \
				if (match($$0,/TABLE[[:space:]]+([A-Za-z0-9_]+)[[:space:]]+([A-Za-z0-9_]+)/,m)) { print m[1]"."m[2]; next } \
				if (match($$0,/TABLE[[:space:]]+([A-Za-z0-9_]+\.[A-Za-z0-9_]+)/,m2))       { print m2[1] } \
			}' | grep -E "^public\\." | sort -u \
		)"; \
		if [ -z "$$TABS" ]; then echo "❌ У дампі не знайдено таблиць public.*"; exit 1; fi; \
		echo "Таблиці у дампі:"; printf "%s\n" "$$TABS" | nl -w2 -s'. '; \
		echo; printf "Введи номери таблиць для відновлення (напр. 1 3 5 або 1,3,5): "; read -r sel; \
		sel="$${sel//,/ }"; CHOSEN=""; \
		for n in $$sel; do \
			if printf "%s" "$$n" | grep -Eq '^[0-9]+$$' && [ "$$n" -ge 1 ] && [ "$$n" -le $$(printf "%s\n" "$$TABS" | wc -l) ]; then \
				t="$$(printf "%s\n" "$$TABS" | sed -n "$${n}p")"; CHOSEN="$$CHOSEN $$t"; \
			else echo "⚠️  Ігнорую: $$n"; fi; \
		done; \
		if [ -z "$$CHOSEN" ]; then echo "❌ Нічого не вибрано — перервано"; exit 1; fi; \
		echo; echo "Буде виконано відновлення таблиць (із DROP/CREATE):"; \
		for t in $$CHOSEN; do echo "  $$t"; done; \
		printf "Підтвердити? [yes/NO]: "; read -r ok; [ "$$ok" = "yes" ] || { echo "Перервано"; exit 1; }; \
		echo "▶️  Готую дамп у контейнері..."; \
		# 1) Кладемо дамп у контейнер (без TTY, з stdin)
		$(DC) exec -T postgres sh -lc 'cat > /tmp/restore.dump' < "$$FILE"; \
		echo "▶️  Відновлюю..."; \
		# 2) Схема + 3) Дані для кожної вибраної таблиці
		for t in $$CHOSEN; do \
			base="$$t"; base="$${base#public.}"; \
			# СХЕМА (DROP/CREATE)
			$(DC) exec -T postgres sh -lc 'pg_restore -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
				--clean --if-exists -F c -v -s -t public.'"$$base"' /tmp/restore.dump'; \
			# ДАНІ
			$(DC) exec -T postgres sh -lc 'pg_restore -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
				-F c -v -a -t public.'"$$base"' /tmp/restore.dump'; \
		done; \
		# 4) Прибирання тимчасового файлу
		$(DC) exec -T postgres sh -lc 'rm -f /tmp/restore.dump'; \
		echo "✅ Готово."; \
	}


# docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc 'pg_restore -l' < data/backups/db_SEL_sizes_20251114_112327.dump \
# | grep -E 'TABLE DATA[[:space:]]+public[[:space:]]+sizes' || echo "⛔ Немає DATA для sizes"

# docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc 'psql -U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" -c "SELECT count(*) AS rows_in_sizes FROM public.sizes;"'



## Приклад неінтерактивного відновлення
db-restore-select-nonint: 
#   make db-restore-select-nonint FILE=data/backups/db_20251112_173126.dump \
#   TABLES="public.product_kinds public.sizes public.print_color_schemes"
	@set -euo pipefail
	:test -n "$(FILE)" || { echo "Need FILE=path/to.dump"; exit 1; }
	:test -n "$(TABLES)" || { echo 'Need TABLES="public.t1 public.t2"'; exit 1; }
	docker compose -f docker/docker-compose.yml --env-file .env cp "$(FILE)" postgres:/tmp/restore.dump
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc \
		'pg_restore --clean --if-exists --no-owner --no-privileges \
		$$(for t in $(TABLES); do printf " -t %s" "$$t"; done) \
		-U "$$POSTGRES_USER" -h localhost -p "$$POSTGRES_PORT" -d "$$POSTGRES_DB" \
		/tmp/restore.dump'
	docker compose -f docker/docker-compose.yml --env-file .env exec -T postgres sh -lc 'rm -f /tmp/restore.dump'


