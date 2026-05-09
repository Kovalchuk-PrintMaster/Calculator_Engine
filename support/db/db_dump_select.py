# python app/support/db/db_dump_select.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📄 Назва: db_dump_select.py

🧠 Призначення:
    Інтерактивно створює селективний PostgreSQL dump для вибраних таблиць public
    через Docker Compose і одразу перевіряє, що TABLE DATA реально потрапили в dump.

🔗 Залежності:
    Потрібні:
    - Docker / Docker Compose
    - контейнер postgres із compose-файла infra/docker/docker-compose.yml
    - файл конфігурації ../config/.env
    - PostgreSQL утиліти всередині контейнера: psql, pg_dump, pg_restore

    Результат використовують:
    - support/db/db_restore.py
    - ручне резервне копіювання довідників

🗂 Шляхи/налаштування:
    - APP_DIR            = .../calculator_engine/app
    - PROJECT_ROOT       = .../calculator_engine
    - COMPOSE_FILE       = APP_DIR/infra/docker/docker-compose.yml
    - ENV_FILE           = PROJECT_ROOT/config/.env
    - BACKUP_DIR         = PROJECT_ROOT/data/backups

🔍 Аудит і рекомендації:
    - Скрипт не залежить від поточної робочої директорії.
    - Усі дампи складаються в єдину теку ../data/backups.
    - Якщо DEBUG=1, друкує всі docker/psql/pg_dump команди.

✅ Актуальність:
    Працює з Python 3.11+.

📦 Пропозиція:
    Наступним кроком можна винести ці самі шляхи в єдиний config paths-модуль,
    але для поточного етапу самодостатній варіант надійніший.

▶️ Приклади запуску:
    - python app/support/db/db_dump_select.py
    - DEBUG=1 python app/support/db/db_dump_select.py
"""

from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# ============================================================================
# Базові шляхи проєкту
# ============================================================================

SCRIPT_FILE = Path(__file__).resolve()
APP_DIR = SCRIPT_FILE.parents[2]          # .../calculator_engine/app
PROJECT_ROOT = APP_DIR.parent             # .../calculator_engine
COMPOSE_FILE = APP_DIR / "infra" / "docker" / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / "config" / ".env"
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"

PG_SERVICE = "postgres"
PG_SHELL = ["sh", "-lc"]
DEBUG = os.environ.get("DEBUG") == "1"


# ============================================================================
# Допоміжні функції
# ============================================================================

def validate_paths() -> None:
    """Перевіряє наявність ключових файлів і каталогів."""
    if not COMPOSE_FILE.is_file():
        print(f"❌ Не знайдено compose-файл: {COMPOSE_FILE}")
        sys.exit(1)

    if not ENV_FILE.is_file():
        print(f"❌ Не знайдено env-файл: {ENV_FILE}")
        sys.exit(1)

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def build_dc() -> list[str]:
    """Повертає базову docker compose команду."""
    return [
        "docker",
        "compose",
        "-f",
        str(COMPOSE_FILE),
        "--env-file",
        str(ENV_FILE),
    ]


def run(
    cmd: list[str],
    *,
    stdin: bytes | None = None,
    capture: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess:
    """Виконує shell-команду.

    Args:
        cmd: Команда як список аргументів.
        stdin: Вхідні байти для процесу.
        capture: Чи збирати stdout/stderr.
        check: Чи кидати виняток при ненульовому коді завершення.

    Returns:
        subprocess.CompletedProcess

    Raises:
        subprocess.CalledProcessError: Якщо check=True і код завершення не 0.
    """
    if DEBUG:
        print("+ " + " ".join(shlex.quote(x) for x in cmd), file=sys.stderr)

    cp = subprocess.run(
        cmd,
        input=stdin,
        capture_output=capture,
        text=False,
    )

    if check and cp.returncode != 0:
        raise subprocess.CalledProcessError(
            cp.returncode,
            cmd,
            output=cp.stdout if capture else None,
            stderr=cp.stderr if capture else None,
        )
    return cp


def dc_exec_sh(
    script: str,
    *,
    capture: bool = False,
    check: bool = True,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess:
    """Виконує shell-команду всередині postgres-контейнера."""
    args = build_dc() + ["exec", "-T", PG_SERVICE] + PG_SHELL + [script]
    return run(args, stdin=stdin, capture=capture, check=check)


def dc_exec_cat_from_container(path_inside: str, host_path: Path) -> None:
    """Копіює файл з контейнера на хост через stdout."""
    cp = dc_exec_sh(f'cat "{path_inside}"', capture=True, check=True)
    host_path.write_bytes(cp.stdout)


def psql_at(query: str) -> str:
    """Виконує SQL і повертає plain-text результат без форматування."""
    cp = dc_exec_sh(
        (
            'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" '
            '-d "$POSTGRES_DB" -Atc '
            + shlex.quote(query)
        ),
        capture=True,
        check=True,
    )
    return (cp.stdout or b"").decode("utf-8", "replace").strip()


def list_public_tables() -> list[str]:
    """Повертає список таблиць зі schema public."""
    rows = psql_at(
        "SELECT tablename FROM pg_catalog.pg_tables "
        "WHERE schemaname='public' ORDER BY 1"
    )
    if not rows:
        return []
    return [row for row in rows.splitlines() if row.strip()]


def count_rows(table: str) -> int:
    """Рахує кількість рядків у таблиці public.<table>."""
    out = psql_at(f"SELECT count(*) FROM public.{table}")
    try:
        return int(out)
    except Exception:
        return -1


def ensure_tmp_path() -> str:
    """Генерує унікальний шлях tmp dump всередині контейнера."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"/tmp/sel_{ts}.dump"


def copy_dump_to_container(tmp_inside: str, tables: list[str]) -> None:
    """Створює custom dump у контейнері для вказаних таблиць."""
    tflags = " ".join(f"-t public.{table}" for table in tables)
    script = (
        'set -e; '
        'pg_dump --enable-row-security '
        '-U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'-F c -Z 6 {tflags} -f "{tmp_inside}"'
    )
    dc_exec_sh(script, check=True)


def extract_toc_lines(tmp_inside: str) -> str:
    """Повертає TOC custom dump як текст."""
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    return (cp.stdout or b"").decode("utf-8", "replace")


def table_has_data_in_dump(toc_text: str, table: str) -> tuple[bool, int | None]:
    """Шукає TABLE DATA entry для public.<table> у TOC.

    Returns:
        (has_data, toc_id)
    """
    pattern = re.compile(
        rf"^(\d+);.*TABLE DATA\s+public\s+{re.escape(table)}\b",
        re.M,
    )
    match = pattern.search(toc_text)
    if not match:
        return False, None
    return True, int(match.group(1))


def count_rows_via_toc_listfile(tmp_inside: str, toc_id: int) -> int:
    """Рахує рядки в конкретному TABLE DATA через pg_restore -L."""
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    toc_lines = (cp.stdout or b"").decode("utf-8", "replace").splitlines()

    selected = "\n".join(line for line in toc_lines if line.startswith(f"{toc_id};"))
    if not selected:
        return 0

    listfile = f"/tmp/_list_{toc_id}.txt"
    dc_exec_sh(f'cat > "{listfile}"', stdin=selected.encode("utf-8"), check=True)

    cp2 = dc_exec_sh(
        f'pg_restore -a -L "{listfile}" -f - "{tmp_inside}"',
        capture=True,
        check=True,
    )
    text = (cp2.stdout or b"").decode("utf-8", "replace")

    in_copy = False
    rows = 0
    for line in text.splitlines():
        if not in_copy and line.startswith("COPY ") and " FROM stdin;" in line:
            in_copy = True
            continue
        if in_copy:
            if line == r"\.":
                break
            if line != "":
                rows += 1
    return rows


# ============================================================================
# Основна логіка
# ============================================================================

def main() -> int:
    """Головна точка входу скрипта."""
    validate_paths()

    tables = list_public_tables()
    print("Зчитую список таблиць з public...")

    if not tables:
        print("  (нема таблиць у public — можливо, БД порожня або ви відновили тільки частину стану).")
        return 1

    for index, table in enumerate(tables, 1):
        print(f" {index:2d}. {table}")
    print()

    selection = input(
        "Введи номери таблиць (напр. 1 3 5 або 1,3,5; або * / all для всіх): "
    ).strip()

    if selection.lower() in ("*", "all"):
        chosen = tables[:]
    else:
        selection = selection.replace(",", " ")
        numbers = [item for item in selection.split() if item.isdigit()]
        indexes = [int(item) for item in numbers if 1 <= int(item) <= len(tables)]
        if not indexes:
            print("❌ Нічого не вибрано — перервано.")
            return 1
        chosen = [tables[i - 1] for i in indexes]

    print("\n📊 Попередній стан (у БД перед дампом):")
    before_counts: dict[str, int] = {}
    for table in chosen:
        count = count_rows(table)
        before_counts[table] = count
        count_text = count if count >= 0 else "ERR"
        print(f"  - public.{table} : {count_text} рядків")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_inside = ensure_tmp_path()

    short_name = "+".join(chosen)
    if len(short_name) > 60:
        short_name = short_name[:60]

    host_file = BACKUP_DIR / f"db_SEL_{short_name}_{timestamp}.dump"

    print(f"\n➡️  Дампую: {' '.join(chosen)} -> {host_file}")
    try:
        copy_dump_to_container(tmp_inside, chosen)
    except subprocess.CalledProcessError as exc:
        print("❌ Помилка під час pg_dump. Перевірте лог/права.")
        if DEBUG and exc.stderr:
            sys.stderr.write(exc.stderr.decode("utf-8", "replace"))
        return 2

    dc_exec_cat_from_container(tmp_inside, host_file)
    print(f"✅ Створено: {host_file}")

    print("\n🔎 Перевіряю вміст дампа…")
    toc_text = extract_toc_lines(tmp_inside)

    print(
        "\n{:<30} | {:>12} | {:>10} | {:>14}".format(
            "Таблиця",
            "Було(БД)",
            "DATA в dump",
            "Рядків у dump*",
        )
    )
    print("{:<30}-+-{:>12}-+-{:>10}-+-{:>14}".format("-" * 28, "-" * 12, "-" * 10, "-" * 14))

    suspect = False
    total_before = 0
    total_dump = 0

    for table in chosen:
        before = before_counts.get(table, -1)
        if before > 0:
            total_before += before

        has_data, toc_id = table_has_data_in_dump(toc_text, table)

        dump_rows = 0
        if has_data and toc_id:
            try:
                dump_rows = count_rows_via_toc_listfile(tmp_inside, toc_id)
            except subprocess.CalledProcessError:
                dump_rows = 0

        total_dump += dump_rows

        print(
            "{:<30} | {:>12} | {:>10} | {:>14}".format(
                f"public.{table}",
                before if before >= 0 else "ERR",
                "yes" if has_data else "no",
                dump_rows,
            )
        )

    if total_before > 0 and total_dump == 0:
        suspect = True
        print("  \x1b[31m⚠️  ПОПЕРЕДЖЕННЯ: у БД були рядки, а в дампі пораховано 0. Перевірте RLS/права.\x1b[0m")

    print("* Рядки у dump — за селективним екстрагуванням конкретних TABLE DATA (TOC -L).")

    if suspect:
        suspect_path = host_file.with_name(host_file.stem + "_SUSPECT" + host_file.suffix)
        try:
            host_file.rename(suspect_path)
            print(f"\n🏁 Готово: {suspect_path}")
        except Exception:
            print(f"\n🏁 Готово: {host_file} (не вдалося перейменувати у *_SUSPECT)")
    else:
        print(f"\n🏁 Готово: {host_file}")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nПерервано користувачем.")
        sys.exit(130)