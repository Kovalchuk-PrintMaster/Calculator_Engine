
Налаштування (settings)
Пріоритет

defaults (код) < config/base.toml < config/{ENV}.toml < env

Ключі (поточні)

env — "dev" | "prod" | "test"

debug — bool

app_name — назва сервісу

postgres_dsn — DSN для SQLAlchemy

redis_url — URL Redis

s3_endpoint — S3-сумісна кінцева точка

s3_bucket_backups — бакет для бекапів

Додаєш новий ключ — онови і .env.example, і цей файл.
