import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.models.base import Base
from backend.app.db.models.user import User
from backend.app.db.session import get_db
from backend.app.core.security import hash_password, create_access_token

# Isolated in-memory SQLite database for fast isolated unit tests
TEST_SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


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
def override_get_db(db_session):
    """Override FastAPI get_db dependency to use the isolated test database session."""
    def _override():
        try:
            yield db_session
        finally:
            pass

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
