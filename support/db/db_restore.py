# python app/support/db/db_restore.py
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
📄 Назва: db_restore.py

🧠 Призначення:
    Інтерактивне відновлення PostgreSQL з custom dump через Docker Compose.

🔗 Залежності:
    - Docker / Docker Compose
    - контейнер postgres із compose-файла infra/docker/docker-compose.yml
    - файл конфігурації ../config/.env
    - дампи у ../data/backups або в іншій директорії, яку користувач вкаже вручну

🗂 Шляхи/налаштування:
    - APP_DIR            = .../calculator_engine/app
    - PROJECT_ROOT       = .../calculator_engine
    - COMPOSE_FILE       = APP_DIR/infra/docker/docker-compose.yml
    - ENV_FILE           = PROJECT_ROOT/config/.env
    - DEFAULT_BACKUP_DIR = PROJECT_ROOT/data/backups

🔍 Аудит і рекомендації:
    - Скрипт не залежить від cwd.
    - Працює однаково і з повними, і з селективними dump.
    - Для повного відновлення попереджає, які таблиці в БД зникнуть після DROP SCHEMA.

✅ Актуальність:
    Працює з Python 3.11+.

📦 Пропозиція:
    Далі можна винести спільні docker/path helper-и в окремий модуль support/db/common.py

▶️ Приклади запуску:
    - python app/support/db/db_restore.py
    - DEBUG=1 python app/support/db/db_restore.py
"""

from __future__ import annotations

import glob
import os
import shlex
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ============================================================================
# Базові шляхи проєкту
# ============================================================================

SCRIPT_FILE = Path(__file__).resolve()
APP_DIR = SCRIPT_FILE.parents[2]  # .../calculator_engine/app
PROJECT_ROOT = APP_DIR.parent  # .../calculator_engine
COMPOSE_FILE = APP_DIR / "infra" / "docker" / "docker-compose.yml"
ENV_FILE = PROJECT_ROOT / "config" / ".env"
DEFAULT_BACKUP_DIR = PROJECT_ROOT / "data" / "backups"

PG_SERVICE = "postgres"


# ============================================================================
# Низькорівневі утиліти
# ============================================================================


def dbg(message: str) -> None:
    """Друкує DEBUG-повідомлення."""
    if os.getenv("DEBUG"):
        print(f"[DEBUG] {message}")


def validate_paths() -> None:
    """Перевіряє наявність ключових файлів."""
    if not COMPOSE_FILE.is_file():
        print(f"❌ Не знайдено compose-файл: {COMPOSE_FILE}")
        sys.exit(1)

    if not ENV_FILE.is_file():
        print(f"❌ Не знайдено env-файл: {ENV_FILE}")
        sys.exit(1)

    DEFAULT_BACKUP_DIR.mkdir(parents=True, exist_ok=True)


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
    capture: bool = False,
    check: bool = True,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess:
    """Виконує системну команду."""
    if os.getenv("DEBUG"):
        printable = " ".join(shlex.quote(x) for x in cmd)
        print(f"+ {printable}")

    return subprocess.run(
        cmd,
        input=stdin,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=check,
    )


def dc_exec_sh(
    shell_cmd: str,
    *,
    capture: bool = False,
    check: bool = True,
    stdin: bytes | None = None,
) -> subprocess.CompletedProcess:
    """Виконує shell-команду всередині postgres-контейнера."""
    args = build_dc() + ["exec", "-T", PG_SERVICE, "sh", "-lc", shell_cmd]
    return run(args, capture=capture, check=check, stdin=stdin)


def ask(prompt: str, valid: list[str]) -> str:
    """Інтерактивно читає відповідь із обмеженим набором значень."""
    valid_set = {value.lower() for value in valid}
    while True:
        value = input(prompt).strip().lower()
        if value in valid_set:
            return value
        print(f"Введи одне з: {', '.join(valid)}")


def ask_num(prompt: str, lo: int, hi: int) -> int:
    """Інтерактивно читає число в діапазоні."""
    while True:
        value = input(prompt).strip()
        if value.isdigit():
            number = int(value)
            if lo <= number <= hi:
                return number
        print(f"Введи число у діапазоні [{lo}..{hi}]")


def ask_yes_no(prompt: str, default_yes: bool = True) -> bool:
    """Повертає True/False для yes/no з коректною обробкою Enter."""
    suffix = "[Y/n]" if default_yes else "[y/N]"

    while True:
        value = input(f"{prompt} {suffix}: ").strip().lower()

        if value == "":
            return default_yes

        if value in {"y", "yes"}:
            return True

        if value in {"n", "no"}:
            return False

        print("Введи y або n")


def human_size(size_bytes: int) -> str:
    """Повертає людинозрозумілий розмір."""
    size = size_bytes
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024 or unit == "TB":
            return f"{size}{unit}"
        size //= 1024
    return f"{size_bytes}B"


# ============================================================================
# Пошук дампів
# ============================================================================


def list_dumps(search_dir: Path) -> list[Path]:
    """Повертає список *.dump, відсортований за новизною."""
    paths = [Path(p) for p in glob.glob(str(search_dir / "*.dump"))]
    paths.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return paths


def pick_dump_interactive() -> Path:
    """Інтерактивно пропонує вибрати dump-файл."""
    search_dir = DEFAULT_BACKUP_DIR

    while True:
        dumps = list_dumps(search_dir)

        if not dumps:
            print(f"❌ У {search_dir} не знайдено *.dump.")
            alt = input("Вкажи іншу директорію або Enter, щоб вийти: ").strip()
            if not alt:
                sys.exit(1)
            search_dir = Path(alt).expanduser().resolve()
            continue

        print("Доступні дампи:")
        for index, path in enumerate(dumps, 1):
            timestamp = datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            size = human_size(path.stat().st_size)
            print(f"  {index:2d}. {path}  ({timestamp}, {size})")

        chosen = ask_num("\nВибери номер дампа: ", 1, len(dumps))
        return dumps[chosen - 1]


# ============================================================================
# Інспекція дампа
# ============================================================================


def show_toc_first_lines(tmp_inside: str, lines: int = 25) -> None:
    """Показує перші рядки TOC custom dump."""
    print("\n—— Інфо про дамп (TOC, перші 25 рядків) ——")
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    text = cp.stdout.decode("utf-8", "replace").splitlines()
    for line in text[:lines]:
        print(line)


def parse_tables_and_data_flags(tmp_inside: str) -> dict[str, bool]:
    """Повертає словник {'public.table': has_data_bool} за TOC."""
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    result: dict[str, bool] = {}

    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if "; " not in line:
            continue

        body = line.split("; ", 1)[1]

        if " TABLE " in body and " public " in body:
            tokens = body.split()
            try:
                index = tokens.index("TABLE")
            except ValueError:
                index = -1

            if index >= 0 and index + 2 < len(tokens) and tokens[index + 1] == "public":
                table = tokens[index + 1] + "." + tokens[index + 2]
                result.setdefault(table, False)

        if " TABLE DATA " in body and " public " in body:
            tokens = body.split()
            try:
                index = tokens.index("TABLE")
            except ValueError:
                index = -1

            if index >= 0 and index + 3 < len(tokens) and tokens[index + 2] == "public":
                table = tokens[index + 2] + "." + tokens[index + 3]
                result[table] = True

    return {key: value for key, value in result.items() if key.startswith("public.")}


def list_dump_tables_print(dump_tables: dict[str, bool]) -> None:
    """Друкує список таблиць, знайдених у dump."""
    print("\n📦 У дампі знайдені таблиці (будуть враховані під час відновлення):")
    print("  {:<34} {:>10}".format("Таблиця", "DATA в dump"))
    print("  " + "-" * 48)
    for table in sorted(dump_tables.keys()):
        print("  {:<34} {:>10}".format(table, "yes" if dump_tables[table] else "no"))


def copy_dump_into_container(host_path: Path) -> str:
    """Копіює dump-файл у контейнер postgres."""
    tmp_inside = f'/tmp/restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.dump'
    print("▶️  Копіюю дамп у контейнер …")

    data = host_path.read_bytes()
    dc_exec_sh(f'cat > "{tmp_inside}"', check=True, stdin=data)
    return tmp_inside


# ============================================================================
# Підрахунок рядків
# ============================================================================


def count_rows_in_db(table: str) -> int:
    """Рахує кількість рядків у таблиці БД."""
    cp = dc_exec_sh(
        (
            'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" '
            '-d "$POSTGRES_DB" -Atc ' + shlex.quote(f"SELECT count(*) FROM {table}")
        ),
        capture=True,
        check=False,
    )
    output = cp.stdout.decode().strip()
    return int(output) if output.isdigit() else 0


def find_table_data_toc_id(tmp_inside: str, table: str) -> str | None:
    """Повертає TOC id для TABLE DATA public.<table>."""
    table_name = table.split(".", 1)[1]
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)

    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if " TABLE DATA " in line and f" public {table_name} " in line:
            head = line.split(";", 1)[0].strip()
            if head.isdigit():
                return head
    return None


def count_rows_in_dump(tmp_inside: str, table: str) -> int:
    """Рахує рядки для конкретної таблиці з dump через listfile (-L)."""
    toc_id = find_table_data_toc_id(tmp_inside, table)
    if not toc_id:
        return 0

    list_path = f"/tmp/_list_{toc_id}.txt"
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)

    wanted = None
    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if line.startswith(toc_id + ";"):
            wanted = line
            break

    if not wanted:
        return 0

    dc_exec_sh(
        f'cat > "{list_path}"',
        stdin=(wanted + "\n").encode("utf-8"),
        check=True,
    )

    cp2 = dc_exec_sh(
        f'pg_restore -a -L "{list_path}" -f - "{tmp_inside}"',
        capture=True,
        check=True,
    )
    data = cp2.stdout.decode("utf-8", "replace").splitlines()

    in_copy = False
    count = 0
    for line in data:
        if not in_copy:
            if line.startswith("COPY ") and line.endswith(" FROM stdin;"):
                in_copy = True
            continue

        if line == "\\.":
            break

        if line.strip() != "":
            count += 1

    return count


# ============================================================================
# Допоміжне: формування target args і listfile
# ============================================================================


def build_target_args(tables: list[str]) -> str:
    """Повертає рядок виду '-t public.a -t public.b'."""
    return " ".join(f"-t {shlex.quote(table)}" for table in tables)


def build_listfile_for_table_data(tmp_inside: str, tables: list[str]) -> str:
    """Створює listfile тільки з TABLE DATA entries для вказаних таблиць."""
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    lines = cp.stdout.decode("utf-8", "replace").splitlines()

    table_names = {table.split(".", 1)[1] for table in tables}
    picked: list[str] = []

    for line in lines:
        if " TABLE DATA " not in line or " public " not in line:
            continue

        parts = line.split("; ", 1)
        if len(parts) != 2:
            continue

        body = parts[1]
        tokens = body.split()
        try:
            public_index = tokens.index("public")
        except ValueError:
            continue

        if public_index + 1 < len(tokens):
            name = tokens[public_index + 1]
            if name in table_names:
                picked.append(line)

    list_path = f'/tmp/_data_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    dc_exec_sh(
        f'cat > "{list_path}"',
        stdin=("\n".join(picked) + "\n").encode("utf-8"),
        check=True,
    )
    dbg(f"Listfile for data-only: {list_path} with {len(picked)} entries")
    return list_path


# ============================================================================
# Дії відновлення
# ============================================================================


def restore_full_drop_schema(tmp_inside: str) -> None:
    """DROP SCHEMA public і повне відновлення всього dump."""
    print("▶️  Drop & recreate schema public ...")
    dc_exec_sh(
        'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        '-v ON_ERROR_STOP=1 -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"',
        check=True,
    )

    print("▶️  Відновлюю (повністю, схема+дані, -j 4) ...")
    dc_exec_sh(
        'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--clean --if-exists --no-owner --no-privileges -j 4 "{tmp_inside}"',
        check=True,
    )


def restore_predata_selected(tmp_inside: str, tables: list[str]) -> None:
    """Відновлює тільки pre-data для вказаних таблиць."""
    if not tables:
        return

    targets = build_target_args(tables)
    print("▶️  Відновлюю pre-data для вибраних таблиць …")
    dc_exec_sh(
        'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--section=pre-data --schema-only --clean --if-exists {targets} "{tmp_inside}"',
        check=True,
    )


def truncate_selected(tables: list[str]) -> None:
    """TRUNCATE вибраних таблиць."""
    if not tables:
        return

    print("▶️  TRUNCATE (RESTART IDENTITY CASCADE) вибраних таблиць …")
    joined = ", ".join(tables)
    dc_exec_sh(
        'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'-v ON_ERROR_STOP=1 -c "TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE;"',
        check=True,
    )


def restore_data_selected(tmp_inside: str, tables: list[str]) -> None:
    """Відновлює data-only для вказаних таблиць."""
    if not tables:
        return

    print("▶️  Заливаю data-only для вибраних таблиць …")
    listfile = build_listfile_for_table_data(tmp_inside, tables)
    dc_exec_sh(
        'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--data-only --disable-triggers --no-owner --no-privileges -L "{listfile}" "{tmp_inside}"',
        check=True,
    )


def sync_sequences_for_tables(tables: list[str]) -> None:
    """Синхронізує sequence лише для таблиць, де є колонка id і прив'язана sequence."""
    if not tables:
        return

    print("▶️  Синхронізую sequence для вибраних таблиць …")

    for table in tables:
        schema, name = table.split(".", 1)

        # 1) Перевіряємо, чи є колонка id
        has_id_sql = f"""
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = '{schema}'
          AND table_name = '{name}'
          AND column_name = 'id'
        LIMIT 1;
        """
        cp_has_id = dc_exec_sh(
            'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
            "-Atc " + shlex.quote(has_id_sql),
            capture=True,
            check=False,
        )
        has_id = (cp_has_id.stdout or b"").decode("utf-8", "replace").strip() == "1"
        if not has_id:
            dbg(f"Skip sequence sync for {table}: no id column")
            continue

        # 2) Шукаємо sequence для id
        seq_sql = f"SELECT pg_get_serial_sequence('{schema}.{name}', 'id');"
        cp_seq = dc_exec_sh(
            'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
            "-Atc " + shlex.quote(seq_sql),
            capture=True,
            check=False,
        )
        seq_name = (cp_seq.stdout or b"").decode("utf-8", "replace").strip()
        if not seq_name:
            dbg(f"Skip sequence sync for {table}: no serial/identity sequence")
            continue

        # 3) Ставимо sequence на MAX(id)
        sync_sql = f"""
        SELECT setval(
            '{seq_name}',
            COALESCE((SELECT MAX(id) FROM {schema}.{name}), 1),
            true
        );
        """
        dc_exec_sh(
            'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
            "-v ON_ERROR_STOP=1 -q -c " + shlex.quote(sync_sql),
            capture=True,
            check=True,
        )


def warn_data_only_mode(before: dict[str, int]) -> None:
    """Показує розширене попередження перед data-only restore."""
    populated_tables = [table for table, rows in sorted(before.items()) if rows > 0]

    print("\n⚠️  Попередження: режим data-only НЕ очищає таблиці перед вставкою.")

    if populated_tables:
        print("🔴 У поточній БД вже є дані в таких таблицях:")
        for table in populated_tables[:10]:
            print(f"   • {table} ({before[table]} рядків)")
        if len(populated_tables) > 10:
            print(f"   • ... і ще {len(populated_tables) - 10} таблиць")

        print("🔴 Можливі duplicate key / unique constraint errors.")
        print("💡 Для перезаливки існуючих таблиць використовуйте режим 1:")
        print("   pre-data для вибраних таблиць + TRUNCATE + їхні дані")
    else:
        print("ℹ️  У вибраних таблицях зараз немає рядків — режим data-only безпечніший.")


# ============================================================================
# Головна логіка
# ============================================================================


def main() -> int:
    """Головна точка входу."""
    validate_paths()

    host_dump = pick_dump_interactive()
    tmp_inside = copy_dump_into_container(host_dump)
    show_toc_first_lines(tmp_inside, lines=25)

    dump_tables = parse_tables_and_data_flags(tmp_inside)
    list_dump_tables_print(dump_tables)
    print("\nℹ️  Буде відновлено ТІЛЬКИ перелічені вище таблиці.")

    print("\nОбсяг відновлення:")
    print("  1) Повний — використовувати весь дамп (може торкнутися всієї БД)")
    print("  2) Лише таблиці з дампа — інші таблиці не чіпаємо")
    scope = ask_num("Вибір [1/2]: ", 1, 2)

    cp = dc_exec_sh(
        'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        "-Atc \"SELECT 'public.' || tablename FROM pg_catalog.pg_tables "
        "WHERE schemaname='public' ORDER BY 1\"",
        capture=True,
        check=True,
    )
    db_tables_now = [line.strip() for line in cp.stdout.decode().splitlines() if line.strip()]

    selected_tables = sorted(dump_tables.keys())

    if scope == 1:
        missing = sorted(set(db_tables_now) - set(selected_tables))
        if missing:
            print(
                "\n⚠️  УВАГА: у БД є таблиці, яких немає в дампі — після DROP SCHEMA вони зникнуть:"
            )
            for table in missing:
                print(f"   • {table}")
            if not ask_yes_no(
                "Дійсно виконати ПОВНИЙ відкат (ці таблиці буде втрачено)?", default_yes=False
            ):
                print("Перервано користувачем.")
                sys.exit(1)

    if scope == 1:
        print("\nРежим відновлення:")
        print("  1) DROP SCHEMA public + повне відновлення (схема+дані, -j 4)")
        print("  2) Лише схема (schema-only, ТІЛЬКИ pre-data — без пост-об’єктів)")
        print("  3) Лише дані (data-only)")
        mode = ask_num("Вибір [1/2/3]: ", 1, 3)
    else:
        print("\nРежим відновлення:")
        print("  1) pre-data для вибраних таблиць + TRUNCATE + їхні дані")
        print("  2) Лише схема (schema-only, ТІЛЬКИ pre-data — без пост-об’єктів)")
        print("  3) Лише дані (data-only)")
        mode = ask_num("Вибір [1/2/3]: ", 1, 3)

    before = {table: count_rows_in_db(table) for table in selected_tables}
    approx = {table: count_rows_in_dump(tmp_inside, table) for table in selected_tables}

    print(f"\nФайл: {host_dump}")

    if scope == 1:
        if mode == 1:
            if not ask_yes_no(
                "Підтвердити: ПОВНЕ відновлення (DROP SCHEMA public + схема+дані)?",
                default_yes=False,
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_full_drop_schema(tmp_inside)

        elif mode == 2:
            if not ask_yes_no(
                "Підтвердити: відновлення ЛИШЕ СХЕМИ (pre-data) для таблиць із дампа?",
                default_yes=False,
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)

        else:
            warn_data_only_mode(before)
            if not ask_yes_no(
                "Підтвердити: відновлення ЛИШЕ ДАНИХ — селективний?", default_yes=False
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_data_selected(tmp_inside, selected_tables)
            sync_sequences_for_tables(selected_tables)

    else:
        if mode == 1:
            if not ask_yes_no(
                "Підтвердити: pre-data для вибраних таблиць + TRUNCATE + їхні дані?",
                default_yes=False,
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)
            truncate_selected(selected_tables)
            restore_data_selected(tmp_inside, selected_tables)
            sync_sequences_for_tables(selected_tables)

        elif mode == 2:
            if not ask_yes_no(
                "Підтвердити: відновлення ЛИШЕ СХЕМИ (pre-data) — селективний?", default_yes=False
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)

        else:
            warn_data_only_mode(before)
            if not ask_yes_no(
                "Підтвердити: відновлення ЛИШЕ ДАНИХ для таблиць із дампа?", default_yes=False
            ):
                print("Перервано користувачем.")
                sys.exit(1)
            restore_data_selected(tmp_inside, selected_tables)
            sync_sequences_for_tables(selected_tables)

    after = {table: count_rows_in_db(table) for table in selected_tables}

    print("\n📑 ЗВІТ")
    print("{:<34} {:>6} {:>8} {:>6}".format("Таблиця", "Було", "У dump", "Стало"))
    print("-" * 60)

    changed = 0
    sum_before = 0
    sum_dump = 0
    sum_after = 0

    for table in sorted(selected_tables):
        before_rows = before.get(table, 0)
        dump_rows = approx.get(table, 0)
        after_rows = after.get(table, 0)

        if after_rows != before_rows:
            changed += 1

        sum_before += before_rows
        sum_dump += dump_rows
        sum_after += after_rows

        print(f"{table:<34} {before_rows:>6} {dump_rows:>8} {after_rows:>6}")

    print("-" * 60)
    print(f"Таблиць опрацьовано: {len(selected_tables)}, змінених: {changed}")
    print(f"Рядків: було={sum_before}, у dump≈{sum_dump}, стало={sum_after}")
    print("✅ Restore done.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as exc:
        if exc.stderr:
            sys.stderr.write(exc.stderr.decode("utf-8", "replace"))
        print("❌ Помилка виконання команди. Відновлення перервано.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПерервано користувачем.")
        sys.exit(130)
