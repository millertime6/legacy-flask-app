import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'legacy.db'}")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    APP_ENV = os.getenv("APP_ENV", "development")
    DEBUG = _env_bool("DEBUG", APP_ENV != "production")
    APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT = int(os.getenv("PORT", "5001"))

    SECRET_KEY = os.getenv("SECRET_KEY", "legacy-dev-secret-key")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", APP_ENV == "production")
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")

    UI_USERNAME = os.getenv("UI_USERNAME", "servicing")
    UI_PASSWORD = os.getenv("UI_PASSWORD", "servicing123")
    API_TOKEN = os.getenv("API_TOKEN", "dev-integration-token")
    BATCH_EXPORT_DIR = os.getenv("BATCH_EXPORT_DIR", str(BASE_DIR / "run" / "exports"))
