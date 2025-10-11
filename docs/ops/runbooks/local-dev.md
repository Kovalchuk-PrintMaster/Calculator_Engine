
Локальний запуск (WSL + VS Code)
Налаштування
python3 -m venv .venv_calculator
source .venv_calculator/bin/activate
echo 'PYTHONPATH=src' >> .env
pip install -r requirements/dev.txt
pytest -q

Перевірки якості
ruff check . && black --check . && mypy && pytest -q

Запуск API
uvicorn calculator_engine.app.main:app --reload --port 8000
# http://localhost:8000/docs


