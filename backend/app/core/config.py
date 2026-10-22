import os
from typing import List, Union, Any
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_SECRET = "dev_secret_key_change_in_production_1234567890"


def normalize_database_url(url: str) -> str:
    """
    Normalizes standard PostgreSQL URL schemes (postgresql:// and postgres://)
    to explicitly use the psycopg v3 driver (postgresql+psycopg://).
    Leaves SQLite and explicitly specified driver schemes untouched.
    """
    if not url:
        return url
    trimmed = url.strip()
    if trimmed.startswith("postgres://"):
        return "postgresql+psycopg://" + trimmed[len("postgres://"):]
    elif trimmed.startswith("postgresql://"):
        return "postgresql+psycopg://" + trimmed[len("postgresql://"):]
    return trimmed


class Settings(BaseSettings):
    PROJECT_NAME: str = "CAREFlow India"
    PROJECT_VERSION: str = "0.1.0"
    API_V1_STR: str = "/api"
    API_BASE_URL: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = INSECURE_DEV_SECRET

    # CORS Configuration
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]

    # Database Configuration (Defaults to SQLite for local development & testing; configurable for PostgreSQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./careflow_dev.db"
    )

    # Database Connection Pool Settings (PostgreSQL Production)
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 1800

    # Phase 9A Asynchronous Batch Ingestion & Worker Settings
    IMPORT_CHUNK_SIZE: int = 500
    ENABLE_IMPORT_WORKER: bool = True
    WORKER_POLL_INTERVAL: float = 2.0
    WORKER_STALE_TIMEOUT_SECONDS: int = 300
    WORKER_MAX_RETRIES: int = 3
    ASYNC_IMPORT_DEFAULT: bool = False
    ENABLE_DIRECTORY_WATCHER: bool = False
    INCOMING_IMPORT_DIR: str = "data/incoming"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_database_url(cls, v: Union[str, Any]) -> str:
        if isinstance(v, str):
            return normalize_database_url(v)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                import json
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return []

    @model_validator(mode="after")
    def validate_environment_and_security(self) -> "Settings":
        env = self.ENVIRONMENT.lower().strip()
        if env == "production":
            self.DEBUG = False
            # Enforce non-default secure SECRET_KEY in production
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY == INSECURE_DEV_SECRET
                or self.SECRET_KEY in ["change-me", "secret", "default", "password", "123456"]
                or len(self.SECRET_KEY) < 32
            ):
                raise ValueError(
                    "CRITICAL PRODUCTION CONFIGURATION ERROR: ENVIRONMENT='production' requires a secure, "
                    "non-default SECRET_KEY with at least 32 characters."
                )
            # Enforce non-SQLite database in production
            if self.DATABASE_URL.startswith("sqlite"):
                raise ValueError(
                    "CRITICAL PRODUCTION CONFIGURATION ERROR: ENVIRONMENT='production' cannot use SQLite. "
                    "Provide a valid PostgreSQL DATABASE_URL."
                )
            # Enforce non-wildcard CORS in production
            if "*" in self.CORS_ORIGINS:
                raise ValueError(
                    "CRITICAL PRODUCTION CONFIGURATION ERROR: ENVIRONMENT='production' cannot use wildcard '*' in CORS_ORIGINS when credentials are enabled. Specify explicit domain origins."
                )
        return self

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower().strip() == "production"

    @property
    def canonical_database_type(self) -> str:
        if self.DATABASE_URL.startswith("sqlite"):
            return "sqlite"
        elif "postgres" in self.DATABASE_URL:
            return "postgresql"
        return "other"

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
