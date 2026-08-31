import os
from typing import List, Union
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

INSECURE_DEV_SECRET = "dev_secret_key_change_in_production_1234567890"


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
        return self

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="ignore"
    )


settings = Settings()
