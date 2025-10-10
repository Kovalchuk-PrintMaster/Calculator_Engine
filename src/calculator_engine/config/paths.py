from pathlib import Path

# Фізичні шляхи проєкту (без жодних секретів)
# .../src/calculator_engine/config/paths.py
HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]  # .../src/calculator_engine
SRC_ROOT = HERE.parents[2]  # .../src
PROJECT_ROOT = HERE.parents[3]  # .../

CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
LOGS_DIR = PROJECT_ROOT / "logs"
TMP_DIR = PROJECT_ROOT / "tmp"

# Гарантуємо наявність службових тек
for p in (CONFIG_DIR, DATA_DIR, LOGS_DIR, TMP_DIR):
    p.mkdir(parents=True, exist_ok=True)
