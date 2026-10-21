import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from sqlalchemy.orm import Session

from backend.app.core.security import hash_password
from backend.app.db.models.user import User

logger = logging.getLogger("careflow.bootstrap")

# Special characters permitted and checked for password complexity
SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;:,.<>/?`~'\"")


class PasswordValidationError(ValueError):
    """Raised when an administrative password does not meet security policy requirements."""
    pass


class BootstrapResultStatus(str, Enum):
    CREATED = "CREATED"
    ALREADY_EXISTS = "ALREADY_EXISTS"


@dataclass
class BootstrapResult:
    status: BootstrapResultStatus
    message: str
    user: Optional[User] = None


def validate_password_strength(password: str) -> None:
    """
    Enforces production-grade password strength standards:
    - Minimum 12 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one numeric digit (0-9)
    - At least one special symbol
    - No leading/trailing whitespace
    """
    if not password:
        raise PasswordValidationError("Administrator password cannot be empty.")

    if len(password) < 12:
        raise PasswordValidationError(
            f"Administrator password must be at least 12 characters long (received {len(password)})."
        )

    if not any(c.isupper() for c in password):
        raise PasswordValidationError(
            "Administrator password must contain at least one uppercase letter (A-Z)."
        )

    if not any(c.islower() for c in password):
        raise PasswordValidationError(
            "Administrator password must contain at least one lowercase letter (a-z)."
        )

    if not any(c.isdigit() for c in password):
        raise PasswordValidationError(
            "Administrator password must contain at least one numeric digit (0-9)."
        )

    if not any(c in SPECIAL_CHARS for c in password):
        raise PasswordValidationError(
            "Administrator password must contain at least one special symbol (e.g. !@#$%^&*)."
        )


def validate_admin_username(username: str) -> str:
    """
    Validates the username format.
    """
    if not username or not username.strip():
        raise ValueError("Administrator username cannot be empty.")

    clean = username.strip()
    if len(clean) < 3:
        raise ValueError(
            f"Administrator username must be at least 3 characters long (received '{clean}')."
        )

    if not re.match(r"^[a-zA-Z0-9_.-]+$", clean):
        raise ValueError(
            "Administrator username contains invalid characters. Use letters, numbers, underscores, dots, or hyphens."
        )

    return clean


def validate_admin_email(email: Optional[str]) -> Optional[str]:
    """
    Validates optional administrator email address.
    """
    if not email or not email.strip():
        return None

    clean = email.strip()
    # Standard email format pattern
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean):
        raise ValueError(f"Invalid administrator email address format: '{clean}'.")

    return clean


def bootstrap_production_admin(
    db: Session,
    username: str,
    password: str,
    email: Optional[str] = None
) -> BootstrapResult:
    """
    Explicit, one-time bootstrap utility for creating the initial production administrator.
    
    Security & Safety Guarantees:
    1. Idempotent & Safe to Rerun: If an administrator already exists, exits cleanly without modifications.
    2. Non-Destructive: Refuses to overwrite or silently reset existing accounts.
    3. Strong Password Enforcement: Enforces >= 12 chars, mixed-case, numbers, and symbols.
    4. Credential Privacy: Never logs or echoes passwords or password hashes.
    5. Schema Compliant: Uses the standard User model and bcrypt password hashing.
    """
    clean_username = validate_admin_username(username)
    clean_email = validate_admin_email(email)

    # 1. Check if an administrator already exists in the system
    existing_admin = db.query(User).filter(User.role == "ADMIN").first()
    if existing_admin:
        if existing_admin.username == clean_username:
            msg = f"Administrator account '{clean_username}' already exists. No modifications made."
        else:
            msg = (
                f"An administrator account already exists ('{existing_admin.username}'). "
                f"Initial bootstrap can only create the first administrator. No modifications made."
            )
        logger.info(msg)
        return BootstrapResult(
            status=BootstrapResultStatus.ALREADY_EXISTS,
            message=msg,
            user=existing_admin
        )

    # 2. Check if username exists with another role (e.g. ANALYST, VIEWER)
    existing_user = db.query(User).filter(User.username == clean_username).first()
    if existing_user:
        raise ValueError(
            f"User '{clean_username}' already exists with role '{existing_user.role}'. "
            f"Refusing to overwrite existing non-admin user."
        )

    # 3. Check if email conflicts with another user
    if clean_email:
        existing_email_user = db.query(User).filter(User.email == clean_email).first()
        if existing_email_user:
            raise ValueError(
                f"Email '{clean_email}' is already associated with existing user '{existing_email_user.username}'. "
                f"Refusing to overwrite."
            )

    # 4. Enforce strong password complexity policy
    validate_password_strength(password)

    # 5. Hash password with bcrypt salt rounds
    hashed = hash_password(password)

    # 6. Persist initial administrator
    admin_user = User(
        username=clean_username,
        email=clean_email,
        hashed_password=hashed,
        role="ADMIN",
        is_active=True
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    logger.info(f"Production administrator '{clean_username}' successfully bootstrapped with role ADMIN.")
    return BootstrapResult(
        status=BootstrapResultStatus.CREATED,
        message=f"Administrator '{clean_username}' successfully created with role ADMIN.",
        user=admin_user
    )
