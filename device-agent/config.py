"""Configuration for Metrica Fleet Device Agent"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class AgentConfig:
    """Device agent configuration"""

    # Device Identity
    DEVICE_ID: str = os.getenv("DEVICE_ID", "")
    DEVICE_ROLE: str = os.getenv("DEVICE_ROLE", "unknown")
    DEVICE_BRANCH: str = os.getenv("DEVICE_BRANCH", "main")

    # API Configuration
    API_URL: str = os.getenv("API_URL", "http://localhost:8080")
    API_KEY: str = os.getenv("API_KEY", "")

    # Agent Behavior
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "60"))  # seconds
    HEARTBEAT_INTERVAL: int = int(os.getenv("HEARTBEAT_INTERVAL", "30"))  # seconds

    # Paths
    REPO_PATH: Path = Path(os.getenv("REPO_PATH", "/opt/metrica-fleet"))
    COMPOSE_FILE: Path = Path(os.getenv("COMPOSE_FILE", "docker-compose.yml"))
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/var/lib/metrica-fleet"))

    # Safe Mode
    SAFE_MODE_ENABLED: bool = os.getenv("SAFE_MODE_ENABLED", "true").lower() == "true"
    SAFE_MODE_PORT: int = int(os.getenv("SAFE_MODE_PORT", "8888"))

    @classmethod
    def validate(cls) -> list[str]:
        """Validate required configuration"""
        errors = []

        if not cls.DEVICE_ID:
            errors.append("DEVICE_ID is required")

        if not cls.API_URL:
            errors.append("API_URL is required")

        if not cls.REPO_PATH.exists():
            errors.append(f"REPO_PATH does not exist: {cls.REPO_PATH}")

        return errors


config = AgentConfig()
