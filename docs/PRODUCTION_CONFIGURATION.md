# CAREFlow Production Configuration & Database Hardening Guide

## Overview
This document outlines the environment configuration strategy, production validation rules, and database schema hardening implemented in Phase 7A & 7B.

---

## 1. Environment Configuration Strategy

CAREFlow supports three distinct runtime environments:
* `development` (Default for local development)
* `testing` (Used during unit and integration test execution)
* `production` (Enforced production environment)

All environment variables are declared and validated using Pydantic Settings in `backend/app/core/config.py`.

### Environment Variables Matrix

| Variable | Type | Default (Dev) | Description | Production Requirement |
| :--- | :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | string | `"development"` | Application runtime environment | Must be set to `"production"` |
| `DEBUG` | boolean | `true` | Enables verbose stack traces | Automatically forced to `false` in production |
| `SECRET_KEY` | string | `"dev_secret_key_..."` | Cryptographic signing secret | **Mandatory**: Minimum 32 chars, non-default string |
| `DATABASE_URL` | string | `"sqlite:///..."` | SQLAlchemy database URI | **Mandatory**: Must be a PostgreSQL URI (SQLite forbidden) |
| `CORS_ORIGINS` | list/json | `["http://localhost:5173", ...]` | Allowed HTTP origins | Strictly defined production frontend URLs |
| `LOG_LEVEL` | string | `"INFO"` | Standard logging threshold | `"INFO"` or `"WARNING"` |
| `DB_POOL_SIZE` | integer | `10` | SQLAlchemy pool connection size | Configured for server concurrency |
| `DB_MAX_OVERFLOW` | integer | `20` | Maximum pool connection burst | Configured for server concurrency |
| `DB_POOL_RECYCLE` | integer | `1800` | Connection recycling interval | Prevents stale database connections |

---

## 2. Production Validation Enforcement

During application initialization, `Settings` executes a `@model_validator` hook:
1. If `ENVIRONMENT == 'production'`:
   - `DEBUG` is strictly overridden to `False`.
   - If `SECRET_KEY` is missing, less than 32 characters, or matches default dev placeholders, startup **fails immediately** with a descriptive `ValueError`.
   - If `DATABASE_URL` starts with `sqlite`, startup **fails immediately** with a descriptive `ValueError`.

---

## 3. Database Schema & Migration Management

### New Models (Phase 7B)
1. **`users` (`User`)**:
   - Stores user credentials and RBAC roles (`ADMIN`, `ANALYST`, `VIEWER`).
   - Indexed fields: `id`, `username`, `email`.
2. **`import_jobs` (`ImportJob`)**:
   - Tracks asynchronous HMIS ingestion lifecycle states (`QUEUED`, `PROCESSING`, `VALIDATED`, `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `FAILED`).
   - Indexed fields: `id`, `job_code`, `status`, `created_at`.
3. **`import_error_logs` (`ImportErrorLog`)**:
   - Preserves row-level rejected record logs and quality warnings tied to an `ImportJob`.
   - Indexed fields: `id`, `import_job_id`.

### Alembic Migrations
- Production database schema migrations are managed deterministically via Alembic.
- Migration revision: `56a26ed15259` (`add users import jobs and import error logs`).
- Automatic `Base.metadata.create_all()` is **disabled** during production startup. Schema migrations must be applied using:
  ```bash
  alembic upgrade head
  ```
