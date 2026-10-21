import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from pathlib import Path
from backend.app.core.config import settings

# Enforce testing environment during test sessions to prevent background thread race conditions
settings.ENVIRONMENT = "testing"
settings.ENABLE_IMPORT_WORKER = False

from backend.app.main import app
from backend.app.db.models.base import Base
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.core.security import hash_password, create_access_token
from backend.app.services.imports.storage import ImportStorageService

# Isolated in-memory SQLite database for fast isolated unit tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def isolate_test_upload_storage(tmp_path, monkeypatch):
    """
    Hermetic test isolation: Redirects all import file uploads during testing to a
    temporary directory managed by pytest, preventing directory accumulation in data/uploads.
    """
    test_upload_dir = tmp_path / "test_uploads"
    test_upload_dir.mkdir(parents=True, exist_ok=True)

    original_init = ImportStorageService.__init__

    def _mock_init(self, base_upload_dir: str = None):
        original_init(self, base_upload_dir=str(test_upload_dir))

    monkeypatch.setattr(ImportStorageService, "__init__", _mock_init)
    yield test_upload_dir


@pytest.fixture(scope="function")
def db_session():
    """Create fresh database tables for each test function."""
    Base.metadata.create_all(bind=test_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function", autouse=True)
def override_get_db(db_session, monkeypatch):
    """Override FastAPI get_db dependency and SessionLocal to use the isolated test database session."""
    def _override():
        try:
            yield db_session
        finally:
            pass

    monkeypatch.setattr("backend.app.db.session.SessionLocal", TestingSessionLocal)
    monkeypatch.setattr("backend.app.services.imports.worker.SessionLocal", TestingSessionLocal)
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db_session):
    """Test client bound to isolated database session."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def auth_headers(db_session):
    """Generates valid Bearer authentication headers for a seeded test analyst user."""
    user = User(
        username="test_analyst",
        email="analyst@careflow.gov.in",
        hashed_password=hash_password("Password123!"),
        role="ANALYST",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def admin_auth_headers(db_session):
    """Generates valid Bearer authentication headers for a seeded test admin user."""
    user = User(
        username="test_admin",
        email="admin@careflow.gov.in",
        hashed_password=hash_password("Password123!"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="function")
def viewer_auth_headers(db_session):
    """Generates valid Bearer authentication headers for a seeded test viewer user."""
    user = User(
        username="test_viewer",
        email="viewer@careflow.gov.in",
        hashed_password=hash_password("Password123!"),
        role="VIEWER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    token = create_access_token(subject=user.id, role=user.role)
    return {"Authorization": f"Bearer {token}"}
