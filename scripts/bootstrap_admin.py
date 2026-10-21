#!/usr/bin/env python3
"""
CAREFlow India — Initial Production Administrator Bootstrap CLI
Usage:
    # Non-interactive (Environment Variables):
    export ADMIN_USERNAME="admin"
    export ADMIN_PASSWORD="<strong_password_here>"
    export ADMIN_EMAIL="admin@careflow.gov.in"
    python scripts/bootstrap_admin.py

    # Interactive (Hidden Password Prompt):
    python scripts/bootstrap_admin.py --username admin --email admin@careflow.gov.in
"""

import os
import sys
import getpass
import argparse
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.admin_bootstrap import (
    bootstrap_production_admin,
    BootstrapResultStatus,
    PasswordValidationError,
)
from backend.app.db.session import SessionLocal


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap the initial production administrator account for CAREFlow India."
    )
    parser.add_argument(
        "--username",
        "-u",
        dest="username",
        help="Administrator username (or set ADMIN_USERNAME / INITIAL_ADMIN_USERNAME environment variable)",
        default=None,
    )
    parser.add_argument(
        "--email",
        "-e",
        dest="email",
        help="Administrator email (or set ADMIN_EMAIL / INITIAL_ADMIN_EMAIL environment variable)",
        default=None,
    )
    return parser.parse_args()


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str, str | None]:
    # 1. Resolve Username
    username = (
        args.username
        or os.getenv("ADMIN_USERNAME")
        or os.getenv("INITIAL_ADMIN_USERNAME")
    )
    if not username:
        if sys.stdin.isatty():
            username = input("Enter administrator username: ").strip()
        else:
            sys.stderr.write(
                "[ERROR] Administrator username must be provided via --username argument or "
                "ADMIN_USERNAME / INITIAL_ADMIN_USERNAME environment variable in non-interactive mode.\n"
            )
            sys.exit(1)

    if not username:
        sys.stderr.write("[ERROR] Administrator username cannot be empty.\n")
        sys.exit(1)

    # 2. Resolve Email
    email = (
        args.email
        or os.getenv("ADMIN_EMAIL")
        or os.getenv("INITIAL_ADMIN_EMAIL")
    )
    if email is None and sys.stdin.isatty():
        prompt_email = input("Enter administrator email (optional, press Enter to skip): ").strip()
        email = prompt_email if prompt_email else None

    # 3. Resolve Password
    password = (
        os.getenv("ADMIN_PASSWORD")
        or os.getenv("INITIAL_ADMIN_PASSWORD")
    )
    if not password:
        if sys.stdin.isatty():
            password_1 = getpass.getpass("Enter administrator password: ")
            password_2 = getpass.getpass("Confirm administrator password: ")
            if password_1 != password_2:
                sys.stderr.write("[ERROR] Passwords do not match. Bootstrap aborted.\n")
                sys.exit(1)
            password = password_1
        else:
            sys.stderr.write(
                "[ERROR] Administrator password must be provided via ADMIN_PASSWORD or "
                "INITIAL_ADMIN_PASSWORD environment variable in non-interactive mode.\n"
            )
            sys.exit(1)

    if not password:
        sys.stderr.write("[ERROR] Administrator password cannot be empty.\n")
        sys.exit(1)

    return username, password, email


def main():
    args = parse_arguments()
    username, password, email = resolve_credentials(args)

    db = SessionLocal()
    try:
        result = bootstrap_production_admin(
            db=db,
            username=username,
            password=password,
            email=email
        )

        print("=" * 80)
        print("  CAREFLOW INDIA — PRODUCTION ADMINISTRATOR BOOTSTRAP")
        print("=" * 80)

        if result.status == BootstrapResultStatus.CREATED:
            print(f"  [SUCCESS] {result.message}")
            print(f"  • Username : {result.user.username}")
            print(f"  • Email    : {result.user.email or 'N/A'}")
            print(f"  • Role     : {result.user.role}")
            print(f"  • Active   : {result.user.is_active}")
            print("=" * 80)
            sys.exit(0)
        elif result.status == BootstrapResultStatus.ALREADY_EXISTS:
            print(f"  [NOTICE] Bootstrap skipped: {result.message}")
            print("=" * 80)
            sys.exit(0)

    except PasswordValidationError as e:
        sys.stderr.write(f"[ERROR] Password complexity policy violation: {str(e)}\n")
        sys.exit(1)
    except ValueError as e:
        sys.stderr.write(f"[ERROR] Invalid administrator parameter: {str(e)}\n")
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f"[ERROR] Unexpected error during administrator bootstrap: {str(e)}\n")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
