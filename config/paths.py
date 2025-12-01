"""Централізовані шляхи проєкту.

Призначення:
    - Мати одне місце, де оголошені всі ключові директорії (config/data/logs/tmp).
    - Не розкидати "магічні" шляхи по коду — імпортуємо константи звідси.
    - Гарантувати існування службових тек (створюємо їх під час імпорту).

Зверніть увагу:
    - Назви піддиректорій логів узгоджені з очікуваннями команди:
      * logs/autentification  — логи автентифікації (так, саме з одним "h", як ви просили)
      * logs/data_base        — логи бази даних
"""

from pathlib import Path

# Базові опорні шляхи (визначаються відносно цього файлу)
HERE = Path(__file__).resolve()
APP_ROOT = HERE.parents[1]     # .../src/calculator_engine
SRC_ROOT = HERE.parents[2]     # .../src
PROJECT_ROOT = HERE.parents[3] # .../

# Публічні директорії верхнього рівня
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR   = PROJECT_ROOT / "data"
LOGS_DIR   = PROJECT_ROOT / "logs"
TMP_DIR    = PROJECT_ROOT / "tmp"

# Спеціалізовані піддиректорії логів (як просили)
AUTH_LOGS_DIR = LOGS_DIR / "autentification"
DB_LOGS_DIR   = LOGS_DIR / "data_base"

# Гарантуємо наявність службових тек
for p in (CONFIG_DIR, DATA_DIR, LOGS_DIR, TMP_DIR, AUTH_LOGS_DIR, DB_LOGS_DIR):
    p.mkdir(parents=True, exist_ok=True)
