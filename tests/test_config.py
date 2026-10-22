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
    # Ensures postgresql:// was normalized to postgresql+psycopg://
    assert config.DATABASE_URL == "postgresql+psycopg://user:pass@localhost:5432/careflow_prod"


def test_database_url_normalization_with_psycopg_v3():
    from backend.app.core.config import normalize_database_url

    # postgresql:// -> postgresql+psycopg://
    assert (
        normalize_database_url("postgresql://careflow:secret@localhost:5432/careflow_db")
        == "postgresql+psycopg://careflow:secret@localhost:5432/careflow_db"
    )
    # postgres:// -> postgresql+psycopg://
    assert (
        normalize_database_url("postgres://careflow:secret@localhost:5432/careflow_db")
        == "postgresql+psycopg://careflow:secret@localhost:5432/careflow_db"
    )
    # already postgresql+psycopg:// -> unchanged
    assert (
        normalize_database_url("postgresql+psycopg://careflow:secret@localhost:5432/careflow_db")
        == "postgresql+psycopg://careflow:secret@localhost:5432/careflow_db"
    )
    # sqlite URLs remain unchanged
    assert normalize_database_url("sqlite:///./careflow_dev.db") == "sqlite:///./careflow_dev.db"
    assert normalize_database_url("sqlite:///:memory:") == "sqlite:///:memory:"


def test_postgresql_engine_construction_without_live_server():
    from sqlalchemy import create_engine
    from backend.app.core.config import normalize_database_url

    normalized_url = normalize_database_url("postgresql://careflow_user:mock_pass@localhost:5432/careflow_db")
    engine = create_engine(normalized_url)

    # Verifies that dialect resolves to PostgreSQL with psycopg v3 driver
    assert engine.dialect.name == "postgresql"
    assert engine.dialect.driver == "psycopg"
    assert "psycopg" in engine.dialect.dbapi.__name__


def test_production_config_rejects_wildcard_cors():
    valid_secure_secret = "a_very_secure_random_production_secret_key_1234567890_abcdef"
    with pytest.raises(ValueError, match="cannot use wildcard '\\*' in CORS_ORIGINS"):
        Settings(
            ENVIRONMENT="production",
            SECRET_KEY=valid_secure_secret,
            DATABASE_URL="postgresql://user:pass@localhost:5432/careflow_prod",
            CORS_ORIGINS=["*"]
        )


def test_environment_helper_properties():
    dev_config = Settings(ENVIRONMENT="development", DATABASE_URL="sqlite:///./careflow_dev.db")
    assert dev_config.is_production is False
    assert dev_config.canonical_database_type == "sqlite"

    valid_secure_secret = "a_very_secure_random_production_secret_key_1234567890_abcdef"
    prod_config = Settings(
        ENVIRONMENT="production",
        SECRET_KEY=valid_secure_secret,
        DATABASE_URL="postgresql://user:pass@localhost:5432/careflow_prod"
    )
    assert prod_config.is_production is True
    assert prod_config.canonical_database_type == "postgresql"
