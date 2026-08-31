import pytest
from fastapi import status, HTTPException
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from backend.app.core.security import hash_password, verify_password, create_access_token
from backend.app.db.models.user import User
from backend.app.api.deps import require_roles


def test_password_hashing_and_verification():
    raw_pass = "SecureP@ssw0rd2026!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_login_success(client: TestClient, db_session: Session):
    # Seed user
    u = User(
        username="dr_sharma",
        email="sharma@careflow.gov.in",
        hashed_password=hash_password("DocPass123!"),
        role="ANALYST",
        is_active=True
    )
    db_session.add(u)
    db_session.commit()

    # Perform login
    response = client.post("/api/auth/login", json={"username": "dr_sharma", "password": "DocPass123!"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "dr_sharma"
    assert data["user"]["role"] == "ANALYST"
    assert "hashed_password" not in data["user"]


def test_login_invalid_password(client: TestClient, db_session: Session):
    u = User(
        username="dr_verma",
        hashed_password=hash_password("ValidPassword"),
        role="VIEWER",
        is_active=True
    )
    db_session.add(u)
    db_session.commit()

    response = client.post("/api/auth/login", json={"username": "dr_verma", "password": "WrongPassword"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username/email or password"


def test_login_unknown_user(client: TestClient):
    response = client.post("/api/auth/login", json={"username": "non_existent_user", "password": "any"})
    assert response.status_code == 401


def test_auth_me_endpoint(client: TestClient, db_session: Session):
    u = User(
        username="admin_user",
        email="admin@careflow.gov.in",
        hashed_password=hash_password("AdminPass123!"),
        role="ADMIN",
        is_active=True
    )
    db_session.add(u)
    db_session.commit()

    # Generate token directly
    token = create_access_token(subject=u.id, role=u.role)

    # Call /api/auth/me with valid Bearer header
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    user_data = res.json()
    assert user_data["username"] == "admin_user"
    assert user_data["role"] == "ADMIN"


def test_auth_me_invalid_token(client: TestClient):
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"})
    assert res.status_code == 401


def test_inactive_user_rejection(client: TestClient, db_session: Session):
    u = User(
        username="deactivated_user",
        hashed_password=hash_password("Pass123!"),
        role="VIEWER",
        is_active=False
    )
    db_session.add(u)
    db_session.commit()

    response = client.post("/api/auth/login", json={"username": "deactivated_user", "password": "Pass123!"})
    assert response.status_code == 400
    assert "deactivated" in response.json()["detail"].lower()


def test_rbac_require_roles_dependency():
    admin = User(id=1, username="a", role="ADMIN", is_active=True)
    analyst = User(id=2, username="b", role="ANALYST", is_active=True)
    viewer = User(id=3, username="c", role="VIEWER", is_active=True)

    admin_checker = require_roles(["ADMIN"])
    analyst_checker = require_roles(["ANALYST"])

    # Admin passes any requirement
    assert admin_checker(admin) == admin
    assert analyst_checker(admin) == admin

    # Analyst passes ANALYST requirement
    assert analyst_checker(analyst) == analyst

    # Viewer fails ADMIN or ANALYST requirement
    with pytest.raises(HTTPException) as exc_info:
        analyst_checker(viewer)
    assert exc_info.value.status_code == 403
