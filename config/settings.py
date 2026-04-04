import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR / 'legacy.db'}")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY", "legacy-dev-secret-key")
    UI_USERNAME = os.getenv("UI_USERNAME", "servicing")
    UI_PASSWORD = os.getenv("UI_PASSWORD", "servicing123")
    API_TOKEN = os.getenv("API_TOKEN", "dev-integration-token")
    BATCH_EXPORT_DIR = os.getenv("BATCH_EXPORT_DIR", str(BASE_DIR / "run" / "exports"))
