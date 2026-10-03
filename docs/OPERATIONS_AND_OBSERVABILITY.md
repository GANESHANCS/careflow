# CAREFlow India — Operations, Observability & Troubleshooting Runbook

## Overview
This runbook details operational monitoring, structured logging formats, distributed request tracing (`X-Request-ID`), health check semantics, and diagnostic incident triage workflows for CAREFlow India.

---

## 1. Observability Architecture

```
 User / Client Browser ────────► Ingress / Nginx (Port 80)
      │                                │
      ▼                                ▼
 X-Request-ID Header              FastAPI Backend (Port 8000)
 (Captured in ApiError)                │
                                       ├─► request_context_and_security_middleware
                                       │   ├─ Injects/Preserves X-Request-ID
                                       │   ├─ Measures duration_ms
                                       │   └─ Emits JSON Access Log
                                       │
                                       ├─► Standardized Exception Handlers
                                       │   └─ Masks tracebacks; returns { error: { request_id } }
                                       │
                                       └─► PostgreSQL Database
                                           └─ Evaluated via /api/health and /api/readyz
```

---

## 2. Structured Log Format

When `ENVIRONMENT=production`, CAREFlow emits all logs to `sys.stdout` in structured JSON format using `JSONFormatter` ([backend/app/core/logging.py](file:///d:/careflow/backend/app/core/logging.py)).

### Standard Log Event Schema
```json
{
  "timestamp": "2026-10-03T20:15:30.123456+00:00",
  "level": "INFO",
  "logger": "careflow.api",
  "message": "POST /api/imports HTTP/1.1 201 45.2ms",
  "request_id": "c7a8e9d2-3b4f-4a1c-8e9d-0f1a2b3c4d5e",
  "method": "POST",
  "path": "/api/imports",
  "status_code": 201,
  "duration_ms": 45.2,
  "client_ip": "10.0.1.45"
}
```

### Sensitive Data Redaction
The logging formatter automatically redacts values associated with sensitive keys:
* Keys scrubbed: `password`, `authorization`, `token`, `secret`, `access_token`, `secret_key`.
* Replaced with string `"[REDACTED]"`.

---

## 3. Request Correlation & Distributed Tracing

Every inbound request is assigned or preserves a UUID in the `X-Request-ID` HTTP header:
1. **Server Header Injection**: `X-Request-ID` is returned in every HTTP response header.
2. **Error Envelope Attachment**: Every API exception body embeds `"request_id"` inside `error`:
   ```json
   {
     "detail": "Descriptive user message",
     "error": {
       "code": "ERROR_CODE",
       "message": "Descriptive user message",
       "request_id": "c7a8e9d2-3b4f-4a1c-8e9d-0f1a2b3c4d5e"
     }
   }
   ```
3. **Frontend Client Capture**: The frontend API client ([client.ts](file:///d:/careflow/frontend/src/api/client.ts)) extracts `requestId` from both HTTP headers and JSON bodies into `ApiError.requestId`.
4. **User-Facing Incident Identification**: The frontend [ErrorState](file:///d:/careflow/frontend/src/components/feedback/ErrorState.tsx) and [ErrorBoundary](file:///d:/careflow/frontend/src/components/feedback/ErrorBoundary.tsx) display a compact incident reference with a one-click copy button (`Ref: c7a8e9d2-...`). Users provide this reference to operations engineers for instantaneous log lookup.

### Correlating an Incident in Logs
Given an incident reference provided by an end user or support ticket:
```bash
# Docker Compose log search
docker compose logs backend | grep "c7a8e9d2-3b4f-4a1c-8e9d-0f1a2b3c4d5e"

# Kubernetes / CloudWatch / Datadog query
json.request_id="c7a8e9d2-3b4f-4a1c-8e9d-0f1a2b3c4d5e"
```

---

## 4. Health & Readiness Probes

CAREFlow implements three distinct health endpoints:

### 1. Unified System Health (`GET /api/health` and `GET /api/v1/health`)
* **Purpose**: General status dashboard and external load balancer probe.
* **Database Check**: Executes `SELECT 1`.
* **Healthy State**: Returns `HTTP 200 OK` with `status: "healthy"`.
* **Degraded State**: Returns `HTTP 503 Service Unavailable` with `status: "degraded"` and `database_status: "unhealthy"`.

### 2. Container Liveness Probe (`GET /api/healthz`)
* **Purpose**: Verifies that the web server process is responsive and not in a deadlock or infinite loop.
* **Behavior**: Returns `HTTP 200 OK` (`{"status": "alive"}`) immediately without querying downstream databases.
* **Kubernetes Spec**:
  ```yaml
  livenessProbe:
    httpGet:
      path: /api/healthz
      port: 8000
    initialDelaySeconds: 5
    periodSeconds: 10
  ```

### 3. Container Readiness Probe (`GET /api/readyz`)
* **Purpose**: Verifies that dependencies (database connectivity) are fully functional before routing client traffic.
* **Behavior**:
  * If database is accessible: returns `HTTP 200 OK` (`{"status": "ready"}`).
  * If database is unreachable: returns `HTTP 503 Service Unavailable` (`{"status": "not_ready"}`).
* **Kubernetes Spec**:
  ```yaml
  readinessProbe:
    httpGet:
      path: /api/readyz
      port: 8000
    initialDelaySeconds: 10
    periodSeconds: 5
  ```

---

## 5. Troubleshooting & Incident Remediation

### Scenario 1: Database Connection Failure (HTTP 503)
* **Symptom**: `/api/health` returns HTTP 503; error logs display `Database connection failed`.
* **Diagnosis**:
  1. Check PostgreSQL container health:
     ```bash
     docker compose ps postgres
     ```
  2. Inspect PostgreSQL logs:
     ```bash
     docker compose logs postgres --tail=100
     ```
  3. Verify connection pool utilization:
     If pool exhaustion occurs, increase `DB_POOL_SIZE` (default 10) and `DB_MAX_OVERFLOW` (default 20) in `.env`.
  4. Ensure network connectivity:
     ```bash
     docker compose exec backend nc -zv postgres 5432
     ```

### Scenario 2: HMIS Import Job Marked `FAILED`
* **Symptom**: User uploads HMIS spreadsheet; status shows `FAILED` in the `/imports` workspace.
* **Diagnosis**:
  1. Retrieve the `job_code` from the UI or API (e.g. `JOB_20261003_120000_abc123`).
  2. Query diagnostic error logs via the authenticated API:
     ```bash
     curl -H "Authorization: Bearer <TOKEN>" \
       https://careflow.gov.in/api/imports/JOB_20261003_120000_abc123/errors
     ```
  3. Inspect backend logs using the job code:
     ```bash
     docker compose logs backend | grep "JOB_20261003_120000_abc123"
     ```
  4. Common Causes:
     * **`UNSUPPORTED_FORMAT`**: Missing expected columns (e.g. `Facility Name`, `Facility Code`, `Reporting Month`).
     * **`EMPTY_DATASET`**: Spreadsheet contains zero parseable rows.
     * **`CORRUPT_SHEET`**: File header is truncated or password-protected.

### Scenario 3: Login Rate Limit Exceeded (HTTP 429)
* **Symptom**: User receives `HTTP 429 Too Many Requests` (`TOO_MANY_REQUESTS`).
* **Root Cause**: The client IP or username exceeded the threshold of 5 failed login attempts per minute.
* **Remediation**: The sliding window rate limit expires automatically after 60 seconds. In horizontal multi-node deployments, ensure client IP forwarding is configured with `X-Forwarded-For` in edge ingress proxies.

### Scenario 4: Frontend Blank Screen / Render Exception
* **Symptom**: Client encounters a runtime rendering failure.
* **Behavior**: The top-level [ErrorBoundary](file:///d:/careflow/frontend/src/components/feedback/ErrorBoundary.tsx) intercepts the exception, prevents app termination, and renders the CAREFlow recovery view displaying an `ERR_*` incident reference.
* **Action**: End users can click "Recover View" or "Return Home". Developers can inspect browser console logs for the corresponding `[CAREFLOW_ERROR_BOUNDARY]` event.
