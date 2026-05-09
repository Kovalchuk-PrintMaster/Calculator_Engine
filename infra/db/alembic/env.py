"""Alembic environment: підключаємо metadata з нашого Base і DSN із settings."""

from __future__ import annotations

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 1) Конфіг Alembic з ini
config = context.config
fileConfig(config.config_file_name)

# 2) Підтягуємо metadata з нашого проекту
from calculator_engine.django_infra.db.base import Base
from settings.app_settings import settings

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Offline режим: генерувати SQL без реального конекту."""
    url = settings.postgres_dsn
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Online режим: реальний конект і виконання міграцій."""
    cfg = config.get_section(config.config_ini_section) or {}
    # Перекриваємо DSN з settings (щоб не плодити місця правди):
    cfg["sqlalchemy.url"] = settings.postgres_dsn

    connectable = engine_from_config(
        cfg, prefix="sqlalchemy.", poolclass=pool.NullPool, future=True
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
