# CAREFlow API Architecture & Endpoint Specification

## Overview
This document specifies the CAREFlow REST API layer, authentication requirements, middleware correlation, error contracts, and versioning rules implemented in Phase 7D.

---

## 1. API Versioning & Routing Strategy
* **Canonical API Base Path**: `/api/v1`
* **Backwards-Compatible Alias**: `/api`
* Both `/api/*` and `/api/v1/*` routes are mounted simultaneously in `backend/app/main.py` to ensure legacy and current frontend clients operate without breaking.

---

## 2. API Endpoints Protection Matrix

| Endpoint Route | Method | Access Level | Description |
| :--- | :--- | :--- | :--- |
| `/api/health` | `GET` | **Public** | System & database health probe. Safe for external load balancers. |
| `/api/auth/login` | `POST` | **Public (Rate-Limited)** | Authenticates credentials and returns signed JWT access token. |
| `/api/auth/me` | `GET` | **Protected (Any Role)** | Returns authenticated user profile metadata. |
| `/api/auth/logout` | `POST` | **Protected (Any Role)** | Stateless client logout signal. |
| `/api/facilities/*` | `GET` | **Protected (Any Role)** | Healthcare facility directory and observation queries. |
| `/api/indicators/*` | `GET` | **Protected (Any Role)** | Indicator dictionary metadata. |
| `/api/analytics/*` | `GET` | **Protected (Any Role)** | Executive summary, time-series trends, regional, and facility comparison analytics. |
| `/api/forecast` | `GET` | **Protected (Any Role)** | Monthly demand forecasting engine and prediction intervals. |
| `/api/model/metrics` | `GET` | **Protected (Any Role)** | Forecasting model registry benchmarks and MAE/RMSE evaluation metrics. |

---

## 3. Middleware & Request Tracing (`X-Request-ID`)
Every HTTP request processed by CAREFlow is assigned a unique tracking ID:
* **Header**: `X-Request-ID`
* If the incoming request supplies an `X-Request-ID` header, it is preserved.
* If missing, a UUID is automatically generated.
* The `X-Request-ID` header is attached to all HTTP response headers and embedded within error payloads.

---

## 4. Standardized Error Response Contract
API exceptions (4xx and 5xx) return a sanitized, structured JSON payload:

```json
{
  "detail": "Descriptive error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Descriptive error message",
    "request_id": "8f2d5a1b-3c4e-4f5a-8b1c-9d0e1f2a3b4c"
  }
}
```

### Common Error Codes
* `UNAUTHORIZED` (401): Missing, invalid, or expired JWT token.
* `FORBIDDEN` (403): User role lacks permission.
* `NOT_FOUND` (404): Resource not found.
* `TOO_MANY_REQUESTS` (429): Login rate limit exceeded (5 attempts/min).
* `VALIDATION_ERROR` (422): Request schema or query parameter validation failure.
* `INTERNAL_SERVER_ERROR` (500): Sanitized internal server error (traceback suppressed from client).

---

## 5. Security Headers & CORS Policy
* **`X-Content-Type-Options`**: `nosniff`
* **`X-Frame-Options`**: `DENY`
* **`Referrer-Policy`**: `strict-origin-when-cross-origin`
* **`Cache-Control`**: `no-store, max-age=0` (on authenticated API routes)
* **CORS**: Restricted to configured origins (`CORS_ORIGINS`). Requests from unauthorized origins are rejected.
