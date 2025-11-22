"""
Core configuration using Pydantic Settings
"""
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings"""

    # Application
    APP_NAME: str = "FastAPI Middleware"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32))

    # Server
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # Database
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/middleware_db",
        env="DATABASE_URL"
    )
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    CACHE_TTL: int = Field(default=300, env="CACHE_TTL")  # 5 minutes

    # Odoo Default Configuration
    ODOO_URL: str = Field(
        default="https://odoo.geniura.com",
        env="ODOO_URL"
    )

    # JWT
    JWT_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="JWT_SECRET_KEY"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")

    # Admin JWT (separate secret for admin tokens)
    ADMIN_SECRET_KEY: str = Field(
        default_factory=lambda: secrets.token_urlsafe(32),
        env="ADMIN_SECRET_KEY"
    )
    ADMIN_TOKEN_EXPIRE_MINUTES: int = Field(default=480, env="ADMIN_TOKEN_EXPIRE_MINUTES")  # 8 hours

    # Logging
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FILE_PATH: str = Field(default="logs/app.log", env="LOG_FILE_PATH")
    LOG_ROTATION: str = Field(default="10 MB", env="LOG_ROTATION")

    # CORS
    CORS_ORIGINS: List[str] = Field(
        default=["https://bridgecore.geniura.com", "http://bridgecore.geniura.com", "http://localhost:3000", "http://localhost:8001", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )

    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, env="RATE_LIMIT_ENABLED")
    RATE_LIMIT_PER_MINUTE: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")

    # Tenant Rate Limiting (default limits if not specified in plan)
    DEFAULT_TENANT_RATE_LIMIT_PER_HOUR: int = Field(default=1000, env="DEFAULT_TENANT_RATE_LIMIT_PER_HOUR")
    DEFAULT_TENANT_RATE_LIMIT_PER_DAY: int = Field(default=10000, env="DEFAULT_TENANT_RATE_LIMIT_PER_DAY")

    # Monitoring
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")

    # Webhook Push Authentication
    WEBHOOK_PUSH_API_KEY: Optional[str] = Field(
        default=None,
        env="WEBHOOK_PUSH_API_KEY",
        description="API Key for webhook push authentication (optional, can use Bearer Token instead)"
    )

    # Celery
    CELERY_BROKER_URL: str = Field(
        default="redis://localhost:6379/1",
        env="CELERY_BROKER_URL"
    )
    CELERY_RESULT_BACKEND: str = Field(
        default="redis://localhost:6379/2",
        env="CELERY_RESULT_BACKEND"
    )

    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# Global settings instance
settings = Settings()
