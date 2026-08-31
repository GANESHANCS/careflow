# CAREFlow Security & Governance Policy

## 1. Password Hashing & Secret Management
* Passwords are strictly hashed with `bcrypt` (12 rounds). Plaintext passwords are never logged, stored, or returned in API responses.
* Cryptographic signing keys (`SECRET_KEY`) must be at least 32 characters long in production environments.
* Insecure default keys strictly cause application startup failure in production mode (`ENVIRONMENT=production`).

## 2. JWT Security & Expiry
* Signed using HMAC-SHA256 (`HS256`).
* Standard token expiry is set to 24 hours.
* Expiry (`exp`) and active user checks are enforced on every protected request.

## 3. Data Governance & Privacy
* No real personal health information (PHI) or real passwords are committed to source control.
* Repositories strictly ignore `.env`, `*.sqlite`, and credential files.
* Sanitized error messages prevent stack traces or internal schema disclosure to unauthenticated clients.
