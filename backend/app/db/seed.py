import os
from typing import List, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.security import hash_password
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.user import User
from backend.app.services.data_pipeline.indicator_catalog import STANDARD_INDICATORS


def seed_standard_indicators(db: Session) -> List[Indicator]:
    """
    Seeds the standard core HMIS indicators into the database.
    Idempotent: skips indicators already present.
    """
    seeded = []
    for code, meta in STANDARD_INDICATORS.items():
        existing = db.query(Indicator).filter(Indicator.code == code).first()
        if not existing:
            ind_id = f"IND_{code}"
            indicator = Indicator(
                id=ind_id,
                code=code,
                name=meta.name,
                category=meta.category,
                unit=meta.unit,
                description=f"Standard HMIS indicator for {meta.name}",
                source_system="HMIS",
                active=True
            )
            db.add(indicator)
            seeded.append(indicator)
        else:
            seeded.append(existing)

    db.commit()
    return seeded


def seed_initial_users(db: Session) -> List[User]:
    """
    Seeds initial admin/analyst users for development and staging environments.
    Idempotent: skips users if username already exists.
    """
    seeded_users = []

    # Check environment variables for explicit initial admin configuration
    env_admin_user = os.getenv("INITIAL_ADMIN_USERNAME")
    env_admin_pass = os.getenv("INITIAL_ADMIN_PASSWORD")
    env_admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@careflow.gov.in")

    if env_admin_user and env_admin_pass:
        existing = db.query(User).filter(User.username == env_admin_user).first()
        if not existing:
            admin_user = User(
                username=env_admin_user,
                email=env_admin_email,
                hashed_password=hash_password(env_admin_pass),
                role="ADMIN",
                is_active=True
            )
            db.add(admin_user)
            seeded_users.append(admin_user)

    # In local development environment, seed default convenience admin & analyst if database is empty
    if settings.ENVIRONMENT.lower() == "development":
        dev_users = [
            ("admin", "admin@careflow.gov.in", "careflow_admin_dev_2026", "ADMIN"),
            ("analyst", "analyst@careflow.gov.in", "careflow_analyst_dev_2026", "ANALYST"),
            ("viewer", "viewer@careflow.gov.in", "careflow_viewer_dev_2026", "VIEWER"),
        ]

        for username, email, password, role in dev_users:
            existing = db.query(User).filter(User.username == username).first()
            if not existing:
                u = User(
                    username=username,
                    email=email,
                    hashed_password=hash_password(password),
                    role=role,
                    is_active=True
                )
                db.add(u)
                seeded_users.append(u)

    db.commit()
    return seeded_users
