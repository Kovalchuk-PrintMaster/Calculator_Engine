#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import shlex
import subprocess
from datetime import datetime
from pathlib import Path

# ---------------------------
# конфіг
# ---------------------------
DC = ["docker", "compose", "-f", "docker/docker-compose.yml", "--env-file", ".env"]
PG_SHELL = ["sh", "-lc"]
BACKUP_DIR = Path("data/backups")
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
DEBUG = os.environ.get("DEBUG") == "1"

def run(cmd: list[str], *, stdin: bytes | None = None, capture: bool = False, check: bool = True):
    if DEBUG:
        # друкуємо “плаский” варіант команди
        print("+ " + " ".join(shlex.quote(x) for x in cmd), file=sys.stderr)
    cp = subprocess.run(cmd, input=stdin, capture_output=capture, text=False)
    if check and cp.returncode != 0:
        raise subprocess.CalledProcessError(cp.returncode, cmd, output=cp.stdout if capture else None, stderr=cp.stderr if capture else None)
    return cp

def dc_exec_sh(script: str, *, capture: bool = False, check: bool = True, stdin: bytes | None = None):
    args = DC + ["exec", "-T", "postgres"] + PG_SHELL + [script]
    return run(args, stdin=stdin, capture=capture, check=check)

def dc_exec_cat_from_container(path_inside: str, host_path: Path):
    # копіюємо файл з контейнера на хост через stdout
    cp = dc_exec_sh(f'cat "{path_inside}"', capture=True)
    host_path.write_bytes(cp.stdout)

def psql_at(query: str) -> str:
    cp = dc_exec_sh(
        f'psql -U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -Atc {shlex.quote(query)}',
        capture=True
    )
    return (cp.stdout or b"").decode("utf-8", "replace").strip()

def list_public_tables() -> list[str]:
    rows = psql_at("SELECT tablename FROM pg_catalog.pg_tables WHERE schemaname='public' ORDER BY 1")
    if not rows:
        return []
    return [r for r in rows.splitlines() if r.strip()]

def count_rows(table: str) -> int:
    out = psql_at(f"SELECT count(*) FROM public.{table}")
    try:
        return int(out)
    except Exception:
        return -1

def ensure_tmp_path() -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"/tmp/sel_{ts}.dump"

def copy_dump_to_container(tmp_inside: str, tables: list[str]) -> None:
    # формуємо -t для кожної таблиці
    tflags = " ".join(f"-t public.{t}" for t in tables)
    script = (
        'set -e; '
        f'pg_dump --enable-row-security '
        '-U "$POSTGRES_USER" -h localhost -p "$POSTGRES_PORT" -d "$POSTGRES_DB" '
        f'-F c -Z 6 {tflags} -f "{tmp_inside}"'
    )
    dc_exec_sh(script)

def extract_toc_lines(tmp_inside: str) -> str:
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True)
    return (cp.stdout or b"").decode("utf-8", "replace")

def table_has_data_in_dump(toc_text: str, table: str) -> tuple[bool, int | None]:
    """
    Повертає (has_data, toc_id) для TABLE DATA public <table>.
    toc_id — ціле число з початку рядка ("3492; ...").
    """
    has = False
    toc_id = None
    pat = re.compile(rf"^(\d+);.*TABLE DATA\s+public\s+{re.escape(table)}\b", re.M)
    m = pat.search(toc_text)
    if m:
        has = True
        toc_id = int(m.group(1))
    return has, toc_id

def count_rows_via_tocL(tmp_inside: str, toc_id: int) -> int:
    
    # Точно витягуємо конкретний TABLE DATA entry через -L і рахуємо рядки між COPY ... FROM stdin; та '\.'.

    # 1) Зняти повний TOC
    cp = dc_exec_sh(f'pg_restore -l "{tmp_inside}"', capture=True)
    toc = (cp.stdout or b"").decode("utf-8", "replace").splitlines()
    # 2) Витягнути рядок з потрібним id (починається з "3492;")
    selected = "\n".join([line for line in toc if line.startswith(f"{toc_id};")])
    if not selected:
        return 0
    # 3) Запишемо listfile у контейнер
    dc_exec_sh(f'cat > "/tmp/_list_{toc_id}.txt"', stdin=selected.encode("utf-8"))
    # 4) Зробимо екстракт тільки цього entry
    cp2 = dc_exec_sh(f'pg_restore -a -L "/tmp/_list_{toc_id}.txt" -f - "{tmp_inside}"', capture=True)
    text = (cp2.stdout or b"").decode("utf-8", "replace")
    # 5) Рахуємо рядки даних у COPY
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

def main():
    tables = list_public_tables()
    print("Зчитую список таблиць з public...")
    if not tables:
        print("  (нема таблиць у public — можливо, ви відновили тільки селективний дамп).")
        return 1
    for i, t in enumerate(tables, 1):
        print(f" {i:2d}. {t}")
    print()
    sel = input("Введи номери таблиць (напр. 1 3 5 або 1,3,5; або * / all для всіх): ").strip()
    if sel.lower() in ("*", "all"):
        chosen = tables[:]
    else:
        sel = sel.replace(",", " ")
        nums = [s for s in sel.split() if s.isdigit()]
        idxs = [int(n) for n in nums if 1 <= int(n) <= len(tables)]
        if not idxs:
            print("❌ Нічого не вибрано — перервано")
            return 1
        chosen = [tables[i - 1] for i in idxs]

    # підрахунок перед дампом
    print("\n📊 Попередній стан (у БД перед дампом):")
    before_counts = {}
    for t in chosen:
        c = count_rows(t)
        before_counts[t] = c
        c_txt = c if c >= 0 else "ERR"
        print(f"  - public.{t} : {c_txt} рядків")

    # дампимо в контейнер, копіюємо на хост
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    tmp_inside = ensure_tmp_path()
    short = "+".join(chosen)
    if len(short) > 60:
        short = short[:60]
    host_file = BACKUP_DIR / f"db_SEL_{short}_{ts}.dump"
    print(f"\n➡️  Дампую: {' '.join(chosen)} -> {host_file}")
    try:
        copy_dump_to_container(tmp_inside, chosen)
    except subprocess.CalledProcessError as e:
        print("❌ Помилка під час pg_dump. Перевірте лог/права.")
        if DEBUG and e.stderr:
            sys.stderr.write(e.stderr.decode("utf-8", "replace"))
        return 2

    # копія на хост
    dc_exec_cat_from_container(tmp_inside, host_file)
    print(f"✅ Створено: {host_file}")

    # перевіряємо TOC і рахуємо рядки для кожної обраної таблиці
    print("\n🔎 Перевіряю вміст дампа…")
    toc_text = extract_toc_lines(tmp_inside)

    print("\n{:<30} | {:>12} | {:>10} | {:>14}".format("Таблиця", "Було(БД)", "DATA в dump", "Рядків у dump*"))
    print("{:<30}-+-{:>12}-+-{:>10}-+-{:>14}".format("-"*28, "-"*12, "-"*10, "-"*14))

    suspect = False
    total_before = 0
    total_dump = 0
    for t in chosen:
        before = before_counts.get(t, -1)
        total_before += (before if before > 0 else 0)
        has_data, toc_id = table_has_data_in_dump(toc_text, t)
        dump_rows = 0
        if has_data and toc_id:
            try:
                dump_rows = count_rows_via_tocL(tmp_inside, toc_id)
            except subprocess.CalledProcessError:
                dump_rows = 0
        total_dump += dump_rows
        print("{:<30} | {:>12} | {:>10} | {:>14}".format(f"public.{t}", before if before>=0 else "ERR", "yes" if has_data else "no", dump_rows))

    if total_before > 0 and total_dump == 0:
        suspect = True
        print("  \x1b[31m⚠️  ПОПЕРЕДЖЕННЯ: у БД були рядки, а в дампі пораховано 0. Перевірте RLS/права.\x1b[0m")
    print("* Рядки у dump — за селективним екстрагуванням конкретних TABLE DATA (TOC -L).")

    # якщо “підозрілий” — зробимо копію з суфіксом
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
