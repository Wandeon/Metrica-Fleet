"""Configuration settings for Fleet Management API"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "info"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fleet:changeme@postgres:5432/fleet"

    # API
    API_PORT: int = 8080
    API_SECRET_KEY: str = "changeme-generate-random-secret-key-here"
    API_KEY_HEADER: str = "X-API-Key"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]

    # GitHub
    GITHUB_TOKEN: str = ""

    # Tailscale
    TAILSCALE_AUTH_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
