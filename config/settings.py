import os
from pathlib import Path
from urllib.parse import quote

from dotenv import load_dotenv
from sqlalchemy.engine.url import make_url


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _normalize_database_url(raw: str) -> str:
    """Strip EB/console paste issues and use psycopg3 dialect (requirements use psycopg only)."""
    url = raw.strip()
    if len(url) >= 2 and url[0] == url[-1] and url[0] in "'\"":
        url = url[1:-1].strip()
    if not url or url.startswith("sqlite:"):
        return url
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://") :]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://") :]
    return url


def _url_from_elastic_beanstalk_rds() -> str | None:
    """Build URI from standard EB/RDS environment properties (password safely encoded)."""
    host = os.getenv("RDS_HOSTNAME", "").strip()
    user = os.getenv("RDS_USERNAME", "").strip()
    password = os.getenv("RDS_PASSWORD", "").strip()
    port = (os.getenv("RDS_PORT") or "5432").strip()
    db = os.getenv("RDS_DB_NAME", "").strip()
    if not all([host, user, password, db]):
        return None
    u = quote(user, safe="")
    p = quote(password, safe="")
    return f"postgresql+psycopg://{u}:{p}@{host}:{port}/{db}?sslmode=require"


def _database_url() -> str:
    sqlite_default = f"sqlite:///{BASE_DIR / 'legacy.db'}"
    rds_composed = _url_from_elastic_beanstalk_rds()
    raw = os.getenv("DATABASE_URL")
    if raw is None or not raw.strip():
        if rds_composed:
            return rds_composed
        return sqlite_default

    raw_stripped = raw.strip()
    # Full SQLAlchemy URL (postgresql://..., sqlite://..., etc.)
    if "://" in raw_stripped:
        normalized = _normalize_database_url(raw_stripped)
        if not normalized:
            return sqlite_default
        try:
            make_url(normalized)
        except Exception as exc:
            raise ValueError(
                "DATABASE_URL could not be parsed as a SQLAlchemy URL. "
                "Use a single string like postgresql+psycopg://USER:PASSWORD@HOST:5432/DBNAME "
                "with no spaces around '=' in the EB console; percent-encode special characters "
                "in USER or PASSWORD (for example @ as %40, # as %23). See README Database Notes."
            ) from exc
        return normalized

    # Common mistake: only the hostname was pasted into DATABASE_URL. Prefer EB RDS_* vars.
    if rds_composed:
        return rds_composed

    normalized = _normalize_database_url(raw_stripped)
    try:
        make_url(normalized)
    except Exception as exc:
        raise ValueError(
            "DATABASE_URL must be a full URL (e.g. postgresql+psycopg://USER:PASS@HOST:5432/DBNAME), "
            "not just a hostname. On Elastic Beanstalk you can clear DATABASE_URL and rely on "
            "RDS_HOSTNAME, RDS_USERNAME, RDS_PASSWORD, RDS_PORT, and RDS_DB_NAME instead."
        ) from exc
    return normalized


def _sqlalchemy_engine_options(database_url: str) -> dict:
    """RDS often drops non-SSL clients with 'server closed the connection unexpectedly'."""
    opts: dict = {"pool_pre_ping": True}
    if not database_url.startswith("postgresql"):
        return opts
    explicit = os.getenv("DATABASE_SSLMODE", "").strip().lower()
    if explicit in {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}:
        mode = explicit
    elif "rds.amazonaws.com" in database_url:
        mode = "require"
    else:
        mode = "prefer"
    opts["connect_args"] = {"sslmode": mode}
    return opts


class Config:
    DATABASE_URL = _database_url()
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = _sqlalchemy_engine_options(DATABASE_URL)

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
