from pathlib import Path
import os

# --- База
BASE_DIR = Path(__file__).resolve().parent.parent

# --- Env
try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR.parent / ".env")
except Exception:
    pass

# --- Безпека / дебаг
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key-change-me")
DEBUG = True
ALLOWED_HOSTS = ["*"]

# --- Додатки
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "import_export",
    "admin_app.catalog.apps.CatalogConfig",

]
IMPORT_EXPORT_USE_TRANSACTIONS = True   # щоб імпорт був атомарним

# --- Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "calc_admin.urls"

# --- Шаблони
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "calc_admin.wsgi.application"

# --- Postgres з .env
DB_NAME = os.getenv("POSTGRES_DB", "calculator")
DB_USER = os.getenv("POSTGRES_USER", "calc_user")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "calc_pass")
DB_HOST = os.getenv("POSTGRES_HOST", "127.0.0.1")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASS,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}

# --- Інше
AUTH_PASSWORD_VALIDATORS = []  # у деві спростимо

LANGUAGE_CODE = "uk"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django не має створювати міграції для віддзеркалення таблиць
MIGRATION_MODULES = {
    "catalog": None,
}
