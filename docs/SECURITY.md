# CAREFlow Security & Governance Policy

## 1. Password Hashing & Secret Management
* Passwords are strictly hashed with `bcrypt` (12 rounds). Plaintext passwords are never logged, stored, or returned in API responses.
* Cryptographic signing keys (`SECRET_KEY`) must be at least 32 characters long in production environments.
* Insecure default keys strictly cause application startup failure in production mode (`ENVIRONMENT=production`).

## 2. JWT Security & Expiry
* Signed using HMAC-SHA256 (`HS256`).
* Standard token expiry is set to 24 hours.
* Expiry (`exp`) and active user checks are enforced across all operational endpoints (`/api/facilities`, `/api/indicators`, `/api/analytics`, `/api/forecast`, `/api/model`).

## 3. Login Abuse Protection & Rate Limiting
* `POST /api/auth/login` is protected by an in-memory sliding window rate limiter.
* Threshold: Maximum 5 failed login attempts per minute per IP/username.
* Exceeding threshold triggers HTTP `429 Too Many Requests` (`TOO_MANY_REQUESTS`).
* Distributed Redis-backed rate limiting is evaluated for multi-node deployments when scaling horizontally.

## 4. HTTP Security Headers
* `X-Content-Type-Options: nosniff` (prevents MIME-type sniffing).
* `X-Frame-Options: DENY` (prevents clickjacking attacks).
* `Referrer-Policy: strict-origin-when-cross-origin`.
* `Cache-Control: no-store, max-age=0` (prevents sensitive API data caching).
* *Note on Content-Security-Policy (CSP)*: Standard headers are enforced. Rigid script-src directives are omitted in local development to preserve Vite Hot Module Replacement (HMR) script injection.

## 5. Structured Logging & Error Sanitization
* **Structured Logging**: Production logs are emitted as JSON objects (`careflow.api`). `Authorization` headers, JWT tokens, and passwords are redacted automatically.
* **Error Sanitization**: Uncaught Python exceptions (500) return generic user messages. Database tracebacks, SQL queries, and filesystem paths are never leaked in HTTP response bodies.

## 6. Data Governance & Privacy
* No real personal health information (PHI) or real passwords are committed to source control.
* Repositories strictly ignore `.env`, `*.sqlite`, `.venv`, and credential files.
