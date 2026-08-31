# CAREFlow Authentication & Role-Based Access Control (RBAC) Architecture

## Overview
This document details the authentication and authorization mechanism implemented in Phase 7C for the CAREFlow India platform.

---

## 1. Authentication Strategy & Principles
CAREFlow employs a stateless, token-based authentication architecture utilizing signed **JSON Web Tokens (JWT)** with **bcrypt** password hashing.

### Key Security Design Choices
* **Stateless Authorization**: JWT access tokens contain user subject (`sub`), role (`role`), issue timestamp (`iat`), and expiry timestamp (`exp`).
* **Zero Plaintext Persistence**: Passwords are hashed using bcrypt with salt factor 12 before being written to the database.
* **No Insecure Production Fallbacks**: `SECRET_KEY` must be configured via environment settings. Startup fails if default dev keys are detected in production.
* **Public Landing Experience**: Public visitors can access `/` without authentication.
* **Protected Terminal Workspaces**: Operational routes (`/overview`, `/facilities`, `/regions`, `/forecast`, `/data-quality`) require a valid Bearer token.

---

## 2. API Endpoints Matrix

| Endpoint | Method | Auth Required | Description |
| :--- | :--- | :--- | :--- |
| `/api/auth/login` | `POST` | Public | Authenticates user credentials and returns signed JWT access token. |
| `/api/auth/me` | `GET` | Bearer Token | Returns safe user profile (`id`, `username`, `email`, `role`, `is_active`). |
| `/api/auth/logout` | `POST` | Bearer Token | Client token disposal signal. Removes local token storage. |

---

## 3. Role-Based Access Control (RBAC) Matrix

CAREFlow defines three operational user roles:

| Role | Access Level | Description |
| :--- | :--- | :--- |
| **`ADMIN`** | Full System Access | Complete access to analytics, forecasting, data quality, user administration, and system configuration. |
| **`ANALYST`** | Intelligence Access | Full access to overview, facility details, regional analytics, ML forecasting, and data quality dashboards. Cannot manage users. |
| **`VIEWER`** | Read-Only Operational Access | Read-only access to operational intelligence dashboards. |

---

## 4. Development Admin Bootstrapping

For local development and testing, CAREFlow automatically seeds initial test users on application startup if the database is empty:

* **Admin User**: `admin` / `careflow_admin_dev_2026` (`ADMIN` role)
* **Analyst User**: `analyst` / `careflow_analyst_dev_2026` (`ANALYST` role)
* **Viewer User**: `viewer` / `careflow_viewer_dev_2026` (`VIEWER` role)

In production environments, initial admin users must be provisioned via explicit environment variables (`INITIAL_ADMIN_USERNAME`, `INITIAL_ADMIN_PASSWORD`, `INITIAL_ADMIN_EMAIL`).
