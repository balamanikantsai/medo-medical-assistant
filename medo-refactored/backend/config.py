"""
Centralized Configuration for Medo Medical Assistant Backend.

All credentials, file paths, API keys, and tunable settings live here.
Update THIS file when changing any service credential or model parameter.
"""

import os
import warnings
from dotenv import load_dotenv

load_dotenv()


def _get_secret_key():
    """Get secret key with validation for production."""
    key = os.getenv("FLASK_SECRET_KEY", "")
    env = os.getenv("FLASK_ENV", "development")

    if not key or key == "change-me-in-production":
        if env == "production":
            raise ValueError(
                "FLASK_SECRET_KEY must be set to a secure value in production! "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        warnings.warn(
            "Using default secret key. Set FLASK_SECRET_KEY in .env for security.",
            UserWarning,
        )
        return "dev-secret-key-do-not-use-in-production"
    return key


class Config:
    """Base configuration — shared across all environments."""

    # ── Flask ─────────────────────────────────────────────
    SECRET_KEY = _get_secret_key()
    DEBUG = False

    # ── CORS (React frontend origin) ─────────────────────
    FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:3000")

    # ── Google Cloud Credentials ─────────────────────────
    #    Point each variable to the JSON key-file on disk.
    GOOGLE_TRANSLATE_CREDENTIALS = os.getenv(
        "GOOGLE_TRANSLATE_CREDENTIALS", "credentials/translate.json"
    )
    GOOGLE_SPEECH_CREDENTIALS = os.getenv(
        "GOOGLE_SPEECH_CREDENTIALS", "credentials/speech-credentials.json"
    )
    GOOGLE_CALENDAR_CREDENTIALS = os.getenv(
        "GOOGLE_CALENDAR_CREDENTIALS", "credentials/tempCredentials.json"
    )
    GOOGLE_CALENDAR_TOKEN = os.getenv(
        "GOOGLE_CALENDAR_TOKEN", "credentials/token.json"
    )
    GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
    GOOGLE_CALENDAR_ID = "primary"

    # ── Firecrawl (Web Search) ───────────────────────────
    FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY", "")
    FIRECRAWL_SEARCH_LIMIT = 10

    # ── OpenRouter API Configuration ──────────────────────
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
    OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "nvidia/llama-3.3-nemotron-super-49b-v1:free")
    OPENROUTER_MAX_TOKENS = int(os.getenv("OPENROUTER_MAX_TOKENS", "4096"))
    OPENROUTER_TEMPERATURE = float(os.getenv("OPENROUTER_TEMPERATURE", "0.7"))

    # ── LLM Temperature Settings ──────────────────────────
    LLM_DECISION_TEMPERATURE = 0.1
    LLM_ANSWER_TEMPERATURE = 0.5
    LLM_PARSE_TEMPERATURE = 0.1

    # ── Database ─────────────────────────────────────────
    DATABASE_PATH = os.getenv("DATABASE_PATH", "medo.db")
    EXCEL_FILE = os.getenv("EXCEL_FILE", "users.xlsx")

    # ── File Uploads ─────────────────────────────────────
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", "uploads")
    ALLOWED_EXTENSIONS = {"txt"}

    # ── Supported Languages ──────────────────────────────
    SUPPORTED_LANGUAGES = {
        "en": "English",
        "hi": "Hindi",
        "es": "Spanish",
        "fr": "French",
        "te": "Telugu",
        "ko": "Korean",
    }

    # BCP-47 codes used by Google Speech / TTS
    BCP47_MAP = {
        "en": "en-US",
        "hi": "hi-IN",
        "es": "es-ES",
        "fr": "fr-FR",
        "te": "te-IN",
        "ko": "ko-KR",
    }


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Quick selector — set FLASK_ENV in .env to switch
config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}


def get_config():
    """Get configuration class based on FLASK_ENV."""
    env = os.getenv("FLASK_ENV", "development")
    return config_by_name.get(env, DevelopmentConfig)
