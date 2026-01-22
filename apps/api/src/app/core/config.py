"""
Application Configuration

Loads and validates environment variables using Pydantic Settings.
Fails fast if required variables are missing.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    Pydantic automatically reads from environment variables
    and validates types.
    """

    model_config = SettingsConfigDict(
        # Order matters: later files override earlier ones
        # .env.local should have highest priority for local development
        env_file=(".env", "../../.env", ".env.local", "../../.env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================
    # Environment
    # ==========================================
    python_env: Literal["development", "staging", "production"] = "development"
    api_debug: bool = True

    # ==========================================
    # API Server
    # ==========================================
    api_host: str = "0.0.0.0"
    # Pydantic will automatically check for an env var named PORT or API_PORT
    api_port: int = Field(default=8002, alias="PORT")
    api_secret_key: str = Field(min_length=32)

    # ==========================================
    # Database
    # ==========================================
    postgres_host: str = "localhost"
    postgres_port: int = 5440
    postgres_user: str = "eksms"
    postgres_password: str = "eksms_dev_password"
    postgres_db: str = "eksms_dev"

    @computed_field
    @property
    def database_url(self) -> str:
        """Construct async database URL."""
        # Check if DATABASE_URL is provided directly (Railway/production)
        import os

        direct_url = os.getenv("DATABASE_URL")
        if direct_url:
            # Convert postgres:// to postgresql+asyncpg://
            if direct_url.startswith("postgres://"):
                return direct_url.replace("postgres://", "postgresql+asyncpg://", 1)
            if direct_url.startswith("postgresql://"):
                return direct_url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return direct_url

        # Construct from components (local development)
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @computed_field
    @property
    def database_url_sync(self) -> str:
        """Construct sync database URL (for Alembic migrations)."""
        import os

        direct_url = os.getenv("DATABASE_URL")
        if direct_url:
            # Force +psycopg2 for Alembic to avoid "ModuleNotFoundError: psycopg2"
            if direct_url.startswith("postgres://"):
                return direct_url.replace("postgres://", "postgresql+psycopg2://", 1)
            if direct_url.startswith("postgresql://") and "+psycopg2" not in direct_url:
                return direct_url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return direct_url

        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ==========================================
    # Redis
    # ==========================================
    redis_url: str = "redis://localhost:6380/0"

    # ==========================================
    # JWT Authentication
    # ==========================================
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ==========================================
    # Email (SMTP)
    # ==========================================
    smtp_host: str = "localhost"
    smtp_port: int = 1025
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "noreply@eksms.local"
    smtp_from_name: str = "EK-SMS"

    # ==========================================
    # Two-Factor Authentication
    # ==========================================
    totp_issuer_name: str = "EK-SMS"

    # ==========================================
    # Security
    # ==========================================
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:3003,http://localhost:3004,https://ek-sms-web.vercel.app"
    )
    allowed_hosts: str = Field(default="localhost,127.0.0.1")

    @computed_field
    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins into a list."""
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @computed_field
    @property
    def allowed_hosts_list(self) -> list[str]:
        """Parse allowed hosts into a list."""
        return [host.strip() for host in self.allowed_hosts.split(",")]

    # ==========================================
    # Logging
    # ==========================================
    log_level: str = "DEBUG"

    # ==========================================
    # Computed Properties
    # ==========================================
    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.python_env == "development"

    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.python_env == "production"


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Using lru_cache ensures settings are only loaded once,
    and the same instance is reused throughout the application.
    """
    return Settings()


# Export a default settings instance for convenience
settings = get_settings()
