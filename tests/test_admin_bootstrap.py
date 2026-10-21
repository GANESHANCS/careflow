import sys
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.core.admin_bootstrap import (
    validate_password_strength,
    validate_admin_username,
    validate_admin_email,
    bootstrap_production_admin,
    PasswordValidationError,
    BootstrapResultStatus,
)
from backend.app.core.security import verify_password
from backend.app.db.models.base import Base
from backend.app.db.models.user import User
from backend.app.main import lifespan, app
from backend.app.core.config import Settings
import scripts.bootstrap_admin as bootstrap_script


@pytest.fixture
def isolated_db():
    """Isolated in-memory database for testing bootstrap operations."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Password and Credential Validation Tests
# ---------------------------------------------------------------------------

def test_password_strength_validation_rules():
    # Empty password
    with pytest.raises(PasswordValidationError, match="cannot be empty"):
        validate_password_strength("")

    # Length < 12 characters
    with pytest.raises(PasswordValidationError, match="at least 12 characters"):
        validate_password_strength("Short1!Aa")

    # Missing uppercase
    with pytest.raises(PasswordValidationError, match="at least one uppercase"):
        validate_password_strength("all_lowercase_123!@#")

    # Missing lowercase
    with pytest.raises(PasswordValidationError, match="at least one lowercase"):
        validate_password_strength("ALL_UPPERCASE_123!@#")

    # Missing numeric digit
    with pytest.raises(PasswordValidationError, match="at least one numeric digit"):
        validate_password_strength("NoDigitsHere!@#Abc")

    # Missing special symbol
    with pytest.raises(PasswordValidationError, match="at least one special symbol"):
        validate_password_strength("NoSpecialChars1234Abc")

    # Valid strong passwords
    validate_password_strength("Super_Secure_Admin_P@ss_2026")
    validate_password_strength("Complex#Pass1234!")


def test_username_validation_rules():
    # Empty
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_admin_username("")

    # Short (< 3)
    with pytest.raises(ValueError, match="at least 3 characters"):
        validate_admin_username("ab")

    # Invalid characters (space, @)
    with pytest.raises(ValueError, match="invalid characters"):
        validate_admin_username("admin user")

    with pytest.raises(ValueError, match="invalid characters"):
        validate_admin_username("admin@domain")

    # Valid
    assert validate_admin_username("admin") == "admin"
    assert validate_admin_username("super_admin.1") == "super_admin.1"
    assert validate_admin_username("careflow-admin") == "careflow-admin"


def test_email_validation_rules():
    # Empty / None
    assert validate_admin_email(None) is None
    assert validate_admin_email("") is None
    assert validate_admin_email("   ") is None

    # Invalid email formats
    with pytest.raises(ValueError, match="Invalid administrator email"):
        validate_admin_email("not-an-email")

    with pytest.raises(ValueError, match="Invalid administrator email"):
        validate_admin_email("admin@")

    # Valid
    assert validate_admin_email("admin@careflow.gov.in") == "admin@careflow.gov.in"
    assert validate_admin_email("ops.lead@state.health.gov.in") == "ops.lead@state.health.gov.in"


# ---------------------------------------------------------------------------
# Administrator Bootstrap Functionality & Safety Tests
# ---------------------------------------------------------------------------

def test_bootstrap_production_admin_success(isolated_db):
    res = bootstrap_production_admin(
        db=isolated_db,
        username="careflow_admin",
        password="Super_Secure_Admin_P@ss_2026",
        email="admin@careflow.gov.in",
    )

    assert res.status == BootstrapResultStatus.CREATED
    assert res.user is not None
    assert res.user.username == "careflow_admin"
    assert res.user.email == "admin@careflow.gov.in"
    assert res.user.role == "ADMIN"
    assert res.user.is_active is True

    # Verify password was hashed with bcrypt and verifies correctly
    assert res.user.hashed_password != "Super_Secure_Admin_P@ss_2026"
    assert verify_password("Super_Secure_Admin_P@ss_2026", res.user.hashed_password) is True
    assert verify_password("wrong_password", res.user.hashed_password) is False


def test_bootstrap_production_admin_duplicate_rerun_prevention(isolated_db):
    # Initial creation
    res1 = bootstrap_production_admin(
        db=isolated_db,
        username="careflow_admin",
        password="Super_Secure_Admin_P@ss_2026",
        email="admin@careflow.gov.in",
    )
    assert res1.status == BootstrapResultStatus.CREATED
    first_hash = res1.user.hashed_password

    # Rerun with identical credentials - safe, idempotent exit
    res2 = bootstrap_production_admin(
        db=isolated_db,
        username="careflow_admin",
        password="Super_Secure_Admin_P@ss_2026",
        email="admin@careflow.gov.in",
    )
    assert res2.status == BootstrapResultStatus.ALREADY_EXISTS
    assert "already exists" in res2.message
    # Ensure password was not re-hashed or altered
    assert res2.user.hashed_password == first_hash

    # Attempt to bootstrap a different admin user when an admin already exists
    res3 = bootstrap_production_admin(
        db=isolated_db,
        username="second_admin",
        password="Another_Secure_Pass_2026!",
        email="second@careflow.gov.in",
    )
    assert res3.status == BootstrapResultStatus.ALREADY_EXISTS
    assert "Initial bootstrap can only create the first administrator" in res3.message

    # Verify database still has exactly 1 admin user
    admin_count = isolated_db.query(User).filter(User.role == "ADMIN").count()
    assert admin_count == 1


def test_bootstrap_refuses_to_overwrite_existing_non_admin_user(isolated_db):
    # Pre-seed an existing analyst user
    analyst = User(
        username="john_analyst",
        email="john@careflow.gov.in",
        hashed_password="some_hashed_password",
        role="ANALYST",
        is_active=True,
    )
    isolated_db.add(analyst)
    isolated_db.commit()

    # Attempting to bootstrap with the same username must fail with ValueError
    with pytest.raises(ValueError, match="already exists with role 'ANALYST'"):
        bootstrap_production_admin(
            db=isolated_db,
            username="john_analyst",
            password="Super_Secure_Admin_P@ss_2026",
        )


def test_bootstrap_refuses_conflicting_email(isolated_db):
    # Pre-seed an existing viewer user
    viewer = User(
        username="viewer_user",
        email="shared@careflow.gov.in",
        hashed_password="some_hashed_password",
        role="VIEWER",
        is_active=True,
    )
    isolated_db.add(viewer)
    isolated_db.commit()

    # Attempting to bootstrap with the same email must fail with ValueError
    with pytest.raises(ValueError, match="Email 'shared@careflow.gov.in' is already associated"):
        bootstrap_production_admin(
            db=isolated_db,
            username="admin_user",
            password="Super_Secure_Admin_P@ss_2026",
            email="shared@careflow.gov.in",
        )


# ---------------------------------------------------------------------------
# CLI Script Execution Tests
# ---------------------------------------------------------------------------

def test_bootstrap_cli_via_environment_variables(monkeypatch, isolated_db):
    # Redirect SessionLocal to isolated test db
    monkeypatch.setattr(bootstrap_script, "SessionLocal", lambda: isolated_db)
    monkeypatch.setenv("ADMIN_USERNAME", "prod_admin_env")
    monkeypatch.setenv("ADMIN_PASSWORD", "Prod_Secure_Admin_2026!")
    monkeypatch.setenv("ADMIN_EMAIL", "prod_admin@careflow.gov.in")
    monkeypatch.setattr(sys, "argv", ["bootstrap_admin.py"])

    # First run: successfully created (exits with code 0)
    with pytest.raises(SystemExit) as exit_info_1:
        bootstrap_script.main()
    assert exit_info_1.value.code == 0

    # Verify user exists in database
    user = isolated_db.query(User).filter(User.username == "prod_admin_env").first()
    assert user is not None
    assert user.role == "ADMIN"
    assert verify_password("Prod_Secure_Admin_2026!", user.hashed_password) is True

    # Second run: duplicate detection skips gracefully (exits with code 0)
    with pytest.raises(SystemExit) as exit_info_2:
        bootstrap_script.main()
    assert exit_info_2.value.code == 0


def test_bootstrap_cli_missing_password_in_non_interactive_mode(monkeypatch, isolated_db):
    monkeypatch.setattr(bootstrap_script, "SessionLocal", lambda: isolated_db)
    monkeypatch.setattr(sys.stdin, "isatty", lambda: False)
    monkeypatch.delenv("ADMIN_PASSWORD", raising=False)
    monkeypatch.delenv("INITIAL_ADMIN_PASSWORD", raising=False)
    monkeypatch.setattr(sys, "argv", ["bootstrap_admin.py", "--username", "testadmin"])

    with pytest.raises(SystemExit) as exit_info:
        bootstrap_script.main()
    assert exit_info.value.code == 1


def test_bootstrap_cli_weak_password_rejection(monkeypatch, isolated_db):
    monkeypatch.setattr(bootstrap_script, "SessionLocal", lambda: isolated_db)
    monkeypatch.setenv("ADMIN_USERNAME", "testadmin")
    monkeypatch.setenv("ADMIN_PASSWORD", "weakpass")  # Fails policy
    monkeypatch.setattr(sys, "argv", ["bootstrap_admin.py"])

    with pytest.raises(SystemExit) as exit_info:
        bootstrap_script.main()
    assert exit_info.value.code == 1


# ---------------------------------------------------------------------------
# Production Lifespan Non-Seeding Verification
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_production_startup_does_not_auto_seed_users(monkeypatch):
    """
    Verifies that when ENVIRONMENT='production', the FastAPI application lifespan
    does NOT seed default users or automatically create accounts.
    """
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    prod_settings = Settings(
        ENVIRONMENT="production",
        SECRET_KEY="super_secure_production_secret_key_1234567890_abcdef",
        DATABASE_URL="postgresql+psycopg://careflow:pass@localhost:5432/prod_db"
    )

    monkeypatch.setattr("backend.app.main.settings", prod_settings)
    monkeypatch.setattr("backend.app.main.SessionLocal", Session)
    monkeypatch.setattr("backend.app.main.engine", engine)

    # Run lifespan in production mode
    async with lifespan(app):
        pass

    # Verify no users were created
    session = Session()
    try:
        user_count = session.query(User).count()
        assert user_count == 0, "Production startup must not auto-seed users."
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
