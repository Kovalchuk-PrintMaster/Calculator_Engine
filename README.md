# Calculator Engine

Движок калькуляції цін для друкарні: бекенд на **Python 3.12** (FastAPI), з чіткою структурою, централізованими конфігами та фокусом на зрозумілості коду навіть через роки.

> Мета документа — щоб нова людина змогла легко увійти в проєкт, зрозуміти архітектуру та процеси.

---

## 1) Принципи проєкту

- **Чистий корінь репозиторію.** У корені лише найнеобхідніше; службові речі у піддиректоріях (`src/`, `config/`, `requirements/`, тощо).
- **Докстрінги й коментарі.** Кожен публічний модуль/клас/функція мають докстрінг (Google style), у коментарях пояснюємо **чому**, а не лише **що**.
- **Централізовані конфіги та шляхи.** Жодних “магічних” шляхів у коді — лише через `config/settings.py` та `config/paths.py`.
- **Тести з першого дня.** Unit тести для бізнес-логіки, окремо integration/e2e — поступово.

---

## 2) Структура репозиторію (src-layout)

.
├─ src/
│ └─ calculator_engine/
│ ├─ app/ # FastAPI-програма (роутинг, точки входу)
│ ├─ config/ # централізовані конфіги/шляхи (settings/paths)
│ ├─ domain/ # бізнес-логіка (pricing, rules, entities)
│ ├─ infra/ # інфраструктура (db, cache, s3, email, pdf)
│ └─ shared/ # утиліти, типи, НЕ секретні константи
├─ tests/ # unit / integration / e2e тести
├─ config/ # TOML-конфіги середовищ (base/dev/prod) — пізніше
├─ requirements/ # списки залежностей (app.txt, dev.txt)
├─ data/ logs/ tmp/ # службові теки (локальні дані/логи/тимчасове)
├─ .env.example # приклад змінних середовища (без секретів)
├─ .env # локальні змінні (не комітити)
├─ pyproject.toml # інструменти (pytest/ruff/black) і метадані
└─ README.md

yaml
Copy code

**Чому так:** увесь код у `src/…` — імпорти з пакета `calculator_engine`, що зменшує конфлікти та робить проєкт переносимим.

---

## 3) Швидкий старт (WSL/Ubuntu)

```bash
cd ~/calculator_engine
python3 -m venv .venv_calculator
source .venv_calculator/bin/activate

# для src-layout
echo 'PYTHONPATH=src' >> .env

# залежності для розробки (runtime + інструменти)
pip install -r requirements/dev.txt

# перевірка
pytest -q
Опційно для VS Code (.vscode/settings.json):

json
Copy code
{
  "python.defaultInterpreterPath": ".venv_calculator/bin/python",
  "python.envFile": "${workspaceFolder}/.env",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "python.testing.pytestArgs": ["-q"],
  "editor.formatOnSave": true
}
4) Конфігурація, секрети та шляхи
Секрети не зберігаємо в коді. Локально — через .env; продакшн — менеджер секретів.

Централізовані шляхи: src/calculator_engine/config/paths.py.

Налаштування: src/calculator_engine/config/settings.py (зараз — os.getenv; пізніше — мердж .env + config/*.toml).

При додаванні нового параметра — онови .env.example.

Приклад .env.example:

dotenv
Copy code
ENV=dev
DEBUG=true
POSTGRES_DSN=postgresql+psycopg://user:pass@localhost:5432/app
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=https://s3.example.com
S3_BUCKET_BACKUPS=calc-backups
5) Залежності
Файли у requirements/:

app.txt — runtime (бекенд).

dev.txt — містить -r app.txt + інструменти розробки.

Встановлення:

bash
Copy code
# розробка
pip install -r requirements/dev.txt
# прод/CI
pip install -r requirements/app.txt
Поточний намір залежностей runtime (мінімальний скелет):

css
Copy code
fastapi, uvicorn, SQLAlchemy, pydantic, pydantic-settings,
psycopg[binary], redis, python-dotenv
Фактична установка крок за кроком, коли дійдемо до відповідних модулів.

6) Тести
Unit (tests/unit) — чиста логіка без зовнішніх сервісів.

Integration (tests/integration) — з Postgres/Redis/S3 (пізніше).

E2E (tests/e2e) — сценарії “як користувач” (пізніше).

Запуск:

bash
Copy code
pytest -q
7) Якість коду (ruff + black)
Налаштування у pyproject.toml:

ruff: лінтинг (E/F/I/B/UP), auto-fix імпортів.

black: форматування, 100 символів у рядку.

Ручний запуск:

bash
Copy code
ruff check . && ruff check . --fix
black .
8) Коментарі та докстрінги
Вимоги:

Докстрінг у кожному публічному модулі, класі, функції (Google style) + type hints.

Коментарі відповідають на питання “чому так”.

Теги:

# NOTE: важливі зауваження;

# TODO: запланована робота (посилання/таска);

# FIXME: відомі проблемні місця.

Шаблон функції:

python
Copy code
def compute_price(qty: int, *, base: float, discount: float = 0.0) -> float:
    """Calculate final unit price with discount.

    Args:
        qty: Ordered quantity (>= 1).
        base: Base unit price before discounts/taxes.
        discount: Relative discount in [0.0, 1.0].

    Returns:
        Final unit price (rounded according to rules).

    Raises:
        ValueError: On invalid args.
    """
    ...
9) Git-процес (коротко)
Гілки: feat/..., fix/..., chore/..., docs/....

Коміти: Conventional Commits (напр., feat(pricing): add audience discount).

PR: коротко пояснюємо що/навіщо/як перевірити.

10) Дорожня карта (ближчі кроки)
Підключити мердж конфігів .env + config/base.toml/dev.toml у settings.py.

Додати FastAPI-залежності й базовий /health ендпоїнт (вже є заглушка).

Скелет domain/pricing з юніт-тестами (pure functions).

Локальні Docker-сервіси для integration-тестів (Postgres/Redis).

11) Ліцензія / авторство
TBD — визначимо разом (MIT/Apache-2.0/…). Авторські права й контактні дані додамо на етапі підготовки публічної документації.

markdown
Copy code
