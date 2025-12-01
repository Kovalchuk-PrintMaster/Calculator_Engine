#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
db-restore.py — інтерактивне відновлення PostgreSQL з .dump у Docker Compose.

Фішки:
- вибір дампа з data/backups/ (або іншої директорії, якщо порожньо);
- попередній перегляд TOC і перелік таблиць у дампі з ознакою наявності DATA;
- два обсяги: 1) Повний (увесь дамп), 2) Лише таблиці з дампа (інші не чіпаємо);
- режими: 1) pre-data + TRUNCATE + data-only, 2) schema-only (pre-data), 3) data-only;
- ЗВІТ: по кожній таблиці “було / у dump≈ / стало”;
- Без конфлікту --single-transaction і -j;
- У селективному data-only використовуємо точний TOC (-L) для TABLE DATA.

Змінні середовища:
- DEBUG=1 — детальні команди.
"""

import os
import sys
import glob
import shlex
import subprocess
from datetime import datetime
from typing import List, Tuple, Dict, Optional

DC = ["docker", "compose", "-f", "docker/docker-compose.yml", "--env-file", ".env"]
PG_CONT = "postgres"


# ============== низькорівневі утиліти ==============

def dbg(msg: str) -> None:
    if os.getenv("DEBUG"):
        print(f"[DEBUG] {msg}")

def run(cmd: List[str], *, capture: bool=False, check: bool=True, stdin: bytes|None=None) -> subprocess.CompletedProcess:
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

def dc_exec_sh(shell_cmd: str, *, capture: bool=False, check: bool=True, stdin: bytes|None=None) -> subprocess.CompletedProcess:
    args = DC + ["exec", "-T", PG_CONT, "sh", "-lc", shell_cmd]
    return run(args, capture=capture, check=check, stdin=stdin)

def ask(prompt: str, valid: List[str]) -> str:
    valid_set = {v.lower() for v in valid}
    while True:
        val = input(prompt).strip().lower()
        if val in valid_set:
            return val
        print(f"Введи одне з: {', '.join(valid)}")

def ask_num(prompt: str, lo: int, hi: int) -> int:
    while True:
        s = input(prompt).strip()
        if s.isdigit():
            n = int(s)
            if lo <= n <= hi:
                return n
        print(f"Введи число у діапазоні [{lo}..{hi}]")

def human_size(n: int) -> str:
    for unit in ["B","KB","MB","GB","TB"]:
        if n < 1024 or unit == "TB":
            return f"{n}{unit}"
        n //= 1024
    return f"{n}B"


# ============== пошук дампів ==============

def list_dumps(search_dir: str) -> List[str]:
    paths = glob.glob(os.path.join(search_dir, "*.dump"))
    paths.sort(key=lambda p: os.path.getmtime(p), reverse=True)
    return paths

def pick_dump_interactive() -> str:
    search_dir = os.path.join(os.getcwd(), "data", "backups")
    while True:
        dumps = list_dumps(search_dir)
        if not dumps:
            print(f"❌ У {search_dir} не знайдено *.dump.")
            alt = input("Вкажи іншу директорію або Enter, щоб вийти: ").strip()
            if not alt:
                sys.exit(1)
            search_dir = alt
            continue
        print("Доступні дампи:")
        for i, p in enumerate(dumps, 1):
            ts = datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M:%S")
            size = human_size(os.path.getsize(p))
            print(f"  {i:2d}. {p}  ({ts}, {size})")
        idx = ask_num("\nВибери номер дампа: ", 1, len(dumps))
        return dumps[idx-1]


# ============== інспекція дампа ==============

def show_toc_first_lines(tmp_inside: str, lines: int = 25) -> None:
    print("\n—— Інфо про дамп (TOC, перші 25 рядків) ——")
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    text = cp.stdout.decode("utf-8", "replace").splitlines()
    for ln in text[:lines]:
        print(ln)

def parse_tables_and_data_flags(tmp_inside: str) -> Dict[str, bool]:
    """
    Повертає { 'public.table': has_data_bool } за TOC.
    """
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    res: Dict[str, bool] = {}
    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if "; " not in line:
            continue
        parts = line.split("; ", 1)[1]
        # TABLE (schema, name)
        if " TABLE " in parts and " public " in parts:
            toks = parts.split()
            try:
                i_tbl = toks.index("TABLE")
            except ValueError:
                continue
            if i_tbl + 2 < len(toks) and toks[i_tbl+1] == "public":
                tbl = toks[i_tbl+1] + "." + toks[i_tbl+2]
                res.setdefault(tbl, False)
        # TABLE DATA (schema, name)
        if " TABLE DATA " in parts and " public " in parts:
            toks = parts.split()
            try:
                i_td = toks.index("TABLE")
            except ValueError:
                continue
            if i_td + 3 < len(toks) and toks[i_td+2] == "public":
                tbl = toks[i_td+2] + "." + toks[i_td+3]
                res[tbl] = True
    # лише public.*
    return {k: v for k, v in res.items() if k.startswith("public.")}

def list_dump_tables_print(d_tables: Dict[str,bool]) -> None:
    print("\n📦 У дампі знайдені таблиці (будуть враховані під час відновлення):")
    print("  {:<30} {:>12}".format("Таблиця","DATA в dump"))
    print("  " + "-"*45)
    for t in sorted(d_tables.keys()):
        print("  {:<30} {:>12}".format(t, "yes" if d_tables[t] else "no"))

def copy_dump_into_container(host_path: str) -> str:
    tmp_inside = f'/tmp/restore_{datetime.now().strftime("%Y%m%d_%H%M%S")}.dump'
    print("▶️  Копіюю дамп у контейнер …")
    with open(host_path, "rb") as f:
        data = f.read()
    dc_exec_sh(f'cat > "{tmp_inside}"', check=True, stdin=data)
    return tmp_inside


# ============== підрахунок рядків ==============

def count_rows_in_db(table: str) -> int:
    cp = dc_exec_sh(
        f'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM {table}"',
        capture=True, check=False
    )
    out = cp.stdout.decode().strip()
    return int(out) if out.isdigit() else 0

def find_table_data_toc_id(tmp_inside: str, table: str) -> Optional[str]:
    """
    Знаходимо TOC id для конкретного TABLE DATA public.<name>.
    """
    tbl_name = table.split(".", 1)[1]
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    for line in cp.stdout.decode("utf-8", "replace").splitlines():
        if " TABLE DATA " in line and f" public {tbl_name} " in line:
            head = line.split(";", 1)[0].strip()
            if head.isdigit():
                return head
    return None

def count_rows_in_dump(tmp_inside: str, table: str) -> int:
    """
    Витягуємо TABLE DATA запис (-L) і рахуємо рядки між "COPY ... FROM stdin;" та "\.".
    Це працює і для селективних дампів.
    """
    toc_id = find_table_data_toc_id(tmp_inside, table)
    if not toc_id:
        return 0

    list_path = f"/tmp/_list_{toc_id}.txt"
    # сформуємо список з ЄДИНИМ потрібним TOC entry
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    wanted = None
    for ln in cp.stdout.decode("utf-8","replace").splitlines():
        if ln.startswith(toc_id + ";"):
            wanted = ln
            break
    if not wanted:
        return 0

    dc_exec_sh(f'cat > "{list_path}"', stdin=(wanted+"\n").encode("utf-8"), check=True)
    cp2 = dc_exec_sh(f'pg_restore -a -L "{list_path}" -f - "{tmp_inside}"', capture=True, check=True)
    data = cp2.stdout.decode("utf-8", "replace").splitlines()

    in_copy = False
    cnt = 0
    for ln in data:
        if not in_copy:
            if ln.startswith("COPY ") and ln.endswith(" FROM stdin;"):
                in_copy = True
            continue
        if ln == "\\.":
            break
        if ln.strip() != "":
            cnt += 1
    return cnt


# ============== допоміжне: формування -t та -L ==============

def build_target_args(tables: List[str]) -> str:
    """Повертає рядок виду: '-t public.a -t public.b'."""
    return " ".join(f"-t {shlex.quote(t)}" for t in tables)

def build_listfile_for_table_data(tmp_inside: str, tables: List[str]) -> str:
    """
    Створює listfile у контейнері з точними TABLE DATA entries для вказаних таблиць.
    Повертає шлях до listfile.
    """
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True, check=True)
    lines = cp.stdout.decode("utf-8", "replace").splitlines()
    tbl_set = {t.split(".", 1)[1] for t in tables}  # тільки імена без 'public.'
    picked: List[str] = []
    for ln in lines:
        if " TABLE DATA " in ln and " public " in ln:
            # формат: "<id>; ... TABLE DATA public <name> ..."
            parts = ln.split("; ", 1)
            if len(parts) != 2:
                continue
            body = parts[1]
            toks = body.split()
            try:
                i_tbl = toks.index("public")
            except ValueError:
                continue
            if i_tbl + 1 < len(toks):
                name = toks[i_tbl+1]
                if name in tbl_set:
                    picked.append(ln)

    list_path = f'/tmp/_data_list_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
    dc_exec_sh(f'cat > "{list_path}"', stdin=("\n".join(picked) + "\n").encode("utf-8"), check=True)
    dbg(f"Listfile for data-only: {list_path} with {len(picked)} entries")
    return list_path


# ============== дії відновлення ==============

def restore_full_drop_schema(tmp_inside: str) -> None:
    print("▶️  Drop & recreate schema public ...")
    dc_exec_sh(
        'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 '
        '-c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public;"',
        check=True
    )
    print("▶️  Відновлюю (повністю, схема+дані, -j 4) ...")
    # жодного --single-transaction разом з -j
    dc_exec_sh(
        f'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--clean --if-exists --no-owner --no-privileges -j 4 "{tmp_inside}"',
        check=True
    )

def restore_predata_selected(tmp_inside: str, tables: List[str]) -> None:
    if not tables:
        return
    targets = build_target_args(tables)
    print("▶️  Відновлюю pre-data для вибраних таблиць …")
    # pre-data + schema-only очищає/створює самі таблиці/сиквенси без FK/індексів
    dc_exec_sh(
        f'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--section=pre-data --schema-only --clean --if-exists {targets} "{tmp_inside}"',
        check=True
    )

def truncate_selected(tables: List[str]) -> None:
    if not tables:
        return
    print("▶️  TRUNCATE (RESTART IDENTITY CASCADE) вибраних таблиць …")
    joined = ", ".join(tables)
    dc_exec_sh(
        f'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -v ON_ERROR_STOP=1 '
        f'-c "TRUNCATE TABLE {joined} RESTART IDENTITY CASCADE;"',
        check=True
    )

def restore_data_selected(tmp_inside: str, tables: List[str]) -> None:
    if not tables:
        return
    print("▶️  Заливаю data-only для вибраних таблиць …")
    # Критично: будуємо -L зі СПИСКОМ САМЕ TABLE DATA entries для кожної таблиці.
    listfile = build_listfile_for_table_data(tmp_inside, tables)
    # --disable-triggers захищає від FK/тригерів; --no-owner/--no-privileges щоб не чіпати власників
    dc_exec_sh(
        f'pg_restore -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'--data-only --disable-triggers --no-owner --no-privileges -L "{listfile}" "{tmp_inside}"',
        check=True
    )


# ============== головна логіка ==============

def main() -> int:
    host_dump = pick_dump_interactive()
    tmp_inside = copy_dump_into_container(host_dump)
    show_toc_first_lines(tmp_inside, lines=25)

    d_tables = parse_tables_and_data_flags(tmp_inside)
    list_dump_tables_print(d_tables)
    print("\nℹ️  Буде відновлено ТІЛЬКИ перелічені вище таблиці.")

    print("\nОбсяг відновлення:")
    print("  1) Повний — використовувати весь дамп (може торкнутися всієї БД)")
    print("  2) Лише таблиці з дампа — інші таблиці не чіпаємо")
    scope = ask_num("Вибір [1/2]: ", 1, 2)

    # поточні таблиці у БД
    cp = dc_exec_sh(
        'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        "-Atc \"SELECT 'public.' || tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY 1\"",
        capture=True, check=True
    )
    db_tables_now = [ln.strip() for ln in cp.stdout.decode().splitlines() if ln.strip()]

    selected_tables = sorted(d_tables.keys())

    # попередження для повного дропа
    if scope == 1:
        missing = sorted(set(db_tables_now) - set(selected_tables))
        if missing:
            print("\n⚠️  УВАГА: у БД є таблиці, яких немає в дампі — після DROP SCHEMA вони зникнуть:")
            for t in missing:
                print(f"   • {t}")
            conf = ask("Дійсно виконати ПОВНИЙ відкат (ці таблиці буде втрачено)? [y/N]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)

    # вибір режиму
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

    # підрахунки до/≈dump/після
    before = {t: count_rows_in_db(t) for t in selected_tables}
    approx = {t: count_rows_in_dump(tmp_inside, t) for t in selected_tables}

    print(f"\nФайл: {host_dump}")

    if scope == 1:
        if mode == 1:
            conf = ask("Підтвердити: ПОВНЕ відновлення (DROP SCHEMA public + схема+дані)? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_full_drop_schema(tmp_inside)
        elif mode == 2:
            conf = ask("Підтвердити: відновлення ЛИШЕ СХЕМИ (pre-data) для таблиць із дампа? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)
        else:
            print("\n⚠️  Попередження: якщо у поточній БД існують FK/тригери, вставка data-only може падати для окремих таблиць.")
            conf = ask("Підтвердити: відновлення ЛИШЕ ДАНИХ для таблиць із дампа? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_data_selected(tmp_inside, selected_tables)
    else:
        if mode == 1:
            conf = ask("Підтвердити: pre-data для вибраних таблиць + TRUNCATE + їхні дані? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)
            truncate_selected(selected_tables)
            restore_data_selected(tmp_inside, selected_tables)
        elif mode == 2:
            conf = ask("Підтвердити: відновлення ЛИШЕ СХЕМИ (pre-data) — селективний? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_predata_selected(tmp_inside, selected_tables)
        else:
            print("\n⚠️  Попередження: якщо у поточній БД існують FK/тригери, вставка data-only може падати для окремих таблиць.")
            conf = ask("Підтвердити: відновлення ЛИШЕ ДАНИХ — селективний? [Y/n]: ", ["y","n",""])
            if conf != "y":
                print("Перервано користувачем.")
                sys.exit(1)
            restore_data_selected(tmp_inside, selected_tables)

    after = {t: count_rows_in_db(t) for t in selected_tables}

    # --------- звіт ---------
    print("\n📑 ЗВІТ")
    print("{:<34} {:>6} {:>8} {:>6}".format("Таблиця", "Було", "У dump", "Стало"))
    print("-"*60)
    changed = 0
    sum_before = 0
    sum_dump = 0
    sum_after = 0
    for t in sorted(selected_tables):
        b = before.get(t, 0)
        d = approx.get(t, 0)
        a = after.get(t, 0)
        if a != b:
            changed += 1
        sum_before += b
        sum_dump += d
        sum_after += a
        print("{:<34} {:>6} {:>8} {:>6}".format(t, b, d, a))
    print("-"*60)
    print(f"Таблиць опрацьовано: {len(selected_tables)}, змінених: {changed}")
    print(f"Рядків: було={sum_before}, у dump≈{sum_dump}, стало={sum_after}")
    print("✅ Restore done.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except subprocess.CalledProcessError as e:
        if e.stderr:
            sys.stderr.write(e.stderr.decode("utf-8", "replace"))
        print("❌ Помилка виконання команди. Відновлення перервано.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nПерервано користувачем.")
        sys.exit(130)
