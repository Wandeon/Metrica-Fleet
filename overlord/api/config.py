"""Configuration settings for Fleet Management API"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""

    # Application
    VERSION: str = "1.0.0"
    LOG_LEVEL: str = "info"

    # Database
    POSTGRES_USER: str = "fleet"
    POSTGRES_PASSWORD: str = "changeme"
    POSTGRES_DB: str = "fleet"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components"""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

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
