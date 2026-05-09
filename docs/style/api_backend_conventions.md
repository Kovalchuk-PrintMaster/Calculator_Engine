# API backend conventions

## Призначення

Цей документ фіксує правила структури та імпортів для пакета:

```text
apps/api/backend/calculator_engine

Мета:

уникати плутанини між шарами;
не змішувати HTTP, domain і infrastructure;
тримати код передбачуваним і однаково оформленим.
1. Структура пакета
calculator_engine/
├── app/          # HTTP-рівень: FastAPI app, routers, middleware
├── domain/       # бізнес-логіка без FastAPI/HTTP
├── adapters/     # DB, logging, cache, storage adapters
├── shared/       # спільні константи, request context, config adapters
└── scripts/      # службові скрипти пакета
2. Правило імпортів

Усередині calculator_engine використовуємо тільки absolute imports.

Правильно
from calculator_engine.app.routers.meta import router as meta_router
from calculator_engine.domain.pricing.core import QuoteInput, compute_quote
from calculator_engine.adapters.db.engine import get_engine
from calculator_engine.shared.config import app_config
Неправильно
from .routers.meta import router as meta_router
from ...domain.pricing.core import QuoteInput, compute_quote
from .engine import get_engine
3. Межі шарів
app/

Тут живе тільки HTTP-рівень:

FastAPI app
routers
middleware
request/response schemas

app/ не повинен містити бізнес-розрахунки.

domain/

Тут живе бізнес-логіка:

чисті функції
dataclass/value objects
правила розрахунку
lightweight checks

domain/ не повинен знати про:

FastAPI
APIRouter
HTTPException
Docker
SQLAlchemy engine
зовнішні settings напряму
adapters/

Тут живе інтеграція із зовнішнім світом:

DB engine/session/models
logging setup
cache/storage adapters
shared/

Тут живуть:

константи
request context
маленькі adapter-фасади над зовнішніми settings/paths
4. Доступ до settings і paths

Всередині пакета calculator_engine не імпортуємо top-level settings.* напряму, крім спеціальних adapter-файлів.

Канонічно:
calculator_engine.shared.config
calculator_engine.shared.paths
Не канонічно:
from settings.app_settings import settings
from settings.paths import LOGS_DIR

Такі імпорти дозволені тільки всередині adapter-рівня shared/config.py та shared/paths.py.

5. Правило для API-схем

Усі HTTP request/response schema у FastAPI-шарі робимо через pydantic.BaseModel.

Правильно
from pydantic import BaseModel

class InfoResponse(BaseModel):
    service: str
    version: str
    env: str
    docs: str
Не бажано
from typing_extensions import TypedDict

TypedDict допустимий лише у внутрішніх технічних місцях, але не як основний стиль HTTP-контрактів.

6. Router → Domain → Adapters

Типовий напрямок залежностей:

app -> domain
app -> adapters
domain -> shared
adapters -> shared

Небажані залежності:

domain -> app
domain -> FastAPI
domain -> external settings
7. Doctor endpoint

Канонічна схема:

router: app/routers/doctor.py
логіка: domain/doctor/checks.py

meta.py не повинен містити doctor-бізнес-логіку.

8. Materials endpoint

Поточний materials router — мінімальний skeleton.
Коли буде доробка:

Pydantic response schemas
читання реальних рядків із БД
явний service/repository flow
9. Перед merge / commit перевіряємо
python apps/admin/manage.py check
make test

Для перевірки стилю імпортів у API-пакеті:

grep -RinE \
  --include='*.py' \
  '^[[:space:]]*from[[:space:]]+\.+|^[[:space:]]*import[[:space:]]+\.' \
  apps/api/backend/calculator_engine

Результат має бути порожній.

10. Коротке правило

Якщо сумніваєшся, куди класти код:

HTTP/роут/response model → app/
бізнес-правило → domain/
БД/логування/інтеграція → adapters/
спільний фасад або константа → shared/

## 2. Додай короткий блок у
```text
app/docs/modules/api.md

Можеш вставити такий розділ ближче до початку:

## Поточні правила для API backend

Канонічний пакет API:

```text
apps/api/backend/calculator_engine

Прийняті правила:

тільки absolute imports усередині пакета;
HTTP-схеми через pydantic.BaseModel;
бізнес-логіка не живе в router'ах;
доступ до зовнішніх settings/paths тільки через:
calculator_engine.shared.config
calculator_engine.shared.paths

Структура:

app/ — FastAPI layer
domain/ — business logic
adapters/ — DB/logging/infrastructure adapters
shared/ — shared constants/context/adapters
scripts/ — service scripts

## 3. І ще корисна дрібниця
У `app/docs/architecture/project_tree.md` варто замінити згадку `django_infra` на `adapters`, якщо вона ще десь лишилась.

Для швидкої перевірки:
grep -Rin "django_infra\|TypedDict\|from settings\.app_settings import settings\|from settings\.paths import" app/docs apps/api/backend/calculator_engine --include='*.md' --include='*.py'