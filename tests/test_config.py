import pytest
from backend.app.core.config import Settings, INSECURE_DEV_SECRET


def test_development_config_defaults():
    config = Settings(ENVIRONMENT="development")
    assert config.ENVIRONMENT == "development"
    assert config.DEBUG is True
    assert config.SECRET_KEY == INSECURE_DEV_SECRET
    assert config.DATABASE_URL.startswith("sqlite")


def test_production_config_rejects_insecure_secret_key():
    with pytest.raises(ValueError, match="requires a secure, non-default SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=INSECURE_DEV_SECRET,
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow_prod"
        )

    with pytest.raises(ValueError, match="requires a secure, non-default SECRET_KEY"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY="short-secret-key",
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow_prod"
        )


def test_production_config_rejects_sqlite_database():
    valid_secure_secret = "a_very_secure_random_production_secret_key_1234567890_abcdef"
    with pytest.raises(ValueError, match="cannot use SQLite"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_secure_secret,
            DATABASE_URL="sqlite:///./careflow_prod.db"
        )


def test_valid_production_config():
    valid_secure_secret = "a_very_secure_random_production_secret_key_1234567890_abcdef"
    config = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=valid_secure_secret,
        DATABASE_URL="postgresql://user:pass@localhost:5432/careflow_prod"
    )
    assert config.ENVIRONMENT == "production"
    assert config.DEBUG is False
    assert config.SECRET_KEY == valid_secure_secret
