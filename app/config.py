"""Configuration via variables d'environnement."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Paramètres de l'application chargés depuis .env."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/french_voice"

    # GROQ
    GROQ_API_KEY: str = ""
    GROQ_API_URL: str = "https://api.groq.com/openai/v1/chat/completions"
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_WHISPER_MODEL: str = "whisper-large-v3-turbo"

    # App
    APP_NAME: str = "French Voice Learning API"
    DEBUG: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Retourne les settings (cached)."""
    return Settings()
