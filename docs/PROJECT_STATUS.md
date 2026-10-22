# CAREFlow Project Status & Progress Tracker

## Current Phase: PHASE 16 — PRODUCTION READINESS, SECURITY HARDENING & OPERATIONAL RELIABILITY (COMPLETE & VERIFIED)

### Completed Phases
- **PHASE 0 (Research & Architecture Review)**: Complete.
- **PHASE 1 (Foundation & Dev Setup)**: Complete & Verified.
- **PHASE 2 (HMIS Ingestion & Data Quality Pipeline)**: Complete & Verified.
- **PHASE 3 (Database Schema & Backend Foundation)**: Complete & Verified.
- **PHASE 4 (Analytics Engine & Analytics API)**: Complete & Verified.
- **PHASE 5 (Time-Series Forecasting + ML Engine)**: Complete & Verified.
- **PHASE 6A (Design System & Core UI Foundation)**: Complete & Verified.
- **PHASE 6B (Cinematic Landing Experience)**: Complete & Verified.
- **PHASE 6C (Executive Overview & Operational Intelligence)**: Complete & Verified.
- **PHASE 6D (Facility Intelligence Directory & Profile)**: Complete & Verified.
- **PHASE 6E (Regional Intelligence & Geographic Analytics)**: Complete & Verified.
- **PHASE 6F (Forecast Intelligence Workspace)**: Complete & Verified.
- **PHASE 6G (Data Quality Intelligence & Governance Workspace)**: Complete & Verified.
- **PHASE 6H (Cinematic Interaction & Visual Polish)**: Complete & Verified.
- **PHASE 7A (Production Configuration Strategy)**: Complete & Verified.
- **PHASE 7B (Database Production Readiness & Schema Hardening)**: Complete & Verified.
- **PHASE 7C (Authentication & Role-Based Access Control)**: Complete & Verified.
- **PHASE 7D (Secure API Layer & Middleware)**: Complete & Verified.
- **PHASE 7E (Real HMIS Ingestion Engine)**: Complete & Verified.
- **PHASE 7F (Import REST API)**: Complete & Verified.
- **PHASE 7G (HMIS Import & Audit Workspace)**: Complete & Verified.
- **PHASE 7H (Production Hardening, Deployment Readiness & CI/CD)**: Complete & Verified.
- **PHASE 8.1 (Production Bootstrapping & PostgreSQL Driver Hardening)**: Complete & Verified.
- **PHASE 8.2 (Safe HMIS Import Rollback, Audit Provenance & Data Reversibility)**: Complete & Verified.
- **PHASE 9A (Reliable Asynchronous HMIS Batch Ingestion & Large File Engine)**: Complete & Verified.
- **PHASE 9A.1 (Worker Cancellation-Race Safety & Identity-Map Isolation)**: Complete & Verified.
- **PHASE 9B (Automated Batch Orchestration & Incoming Directory Integration)**: Complete & Verified.
- **PHASE 10 (End-to-End Integration, Data Integrity & Release Validation)**: Complete & Verified.
- **PHASE 11 (District HMIS Ingestion, Adapter & Analytics Workspace)**: Complete & Verified.
- **PHASE 12 (Streaming CSV Exports, Indicator Registry & Security Audit)**: Complete & Verified.
- **PHASE 13 (Indicator Audit, Ambiguity Classifications & Export Subgroup Fix)**: Complete & Verified.
- **PHASE 14 (Healthcare Intelligence, Forecasting Foundation & Early-Warning Analytics)**: Complete & Verified.
- **PHASE 15 (Multi-Year HMIS Data Integration & Anomaly Review Workflow)**: Complete & Verified.
- **PHASE 16 (Production Readiness, Security Hardening & Operational Reliability)**: Complete & Verified.

---

## REAL HMIS FILE AVAILABILITY STATUS
**OFFICIAL STATE HMIS DATA INGESTED**: **175,872 RECORDS INGESTED (TAMIL NADU FY 2015–16)**
*The platform hosts official consolidated district returns covering all 32 revenue districts across 12 calendar months (April 2015 – March 2016) in the dedicated `district_observations` table. Structural isolation is enforced between district-level administrative returns and granular clinical facility observations (`observations`: 362 records).*
*Multi-year cataloging: FY 2016–17 and FY 2017–18 official source files are cataloged with status `BLOCKED_MISSING_OFFICIAL_FILE` requiring authorized portal credentials/session on the MoHFW HMIS portal. Zero synthetic records have been fabricated; multi-year ingestion pipelines stand ready for ingestion upon official file acquisition.*

---

## Verification & Test Results

| Component / Test Suite | Command | Result | Details |
| :--- | :--- | :--- | :--- |
| **Full Pytest Backend Suite** | `pytest` | **PASSED** | **228/228 passed** (Phases 1–16 full suites passing without failures, 10 new Phase 16 tests) |
| **Full Vitest Frontend Suite** | `npm test -- --run` (in `frontend/`) | **PASSED** | **79/79 passed** (All 14 test files passing across Landing, Overview, Facilities, Forecast, Imports, and Districts intelligence tabs) |
| **Frontend Production Build** | `npm run build` (in `frontend/`) | **PASSED** | React 19 + TypeScript + Vite build succeeded with **0 errors, 0 warnings** |
| **Database Integrity** | `PRAGMA integrity_check` | **PASSED** | Integrity check OK; record counts exactly preserved across all 15 tables (175,872 district_observations, 362 observations) |
| **Git Diff Format & Hygiene** | `git diff --check` | **PASSED** | Exit code 0 (zero trailing whitespace, zero formatting anomalies) |

---

## Phase 7H Deliverables (Production Hardening, Deployment Readiness & CI/CD)

1. **Production Docker Deployment & Container Hardening**:
   * `Dockerfile`: Updated with `alembic.ini`, non-root user (`careflow`, UID 1000), container `HEALTHCHECK`, and `scripts/entrypoint.sh` applying database migrations before server launch.
   * `docker-compose.yml`: Multi-container stack configured with `postgres`, `backend`, and `frontend` services, environment variable substitution for `SECRET_KEY`, and persistent `uploads_data` volume.
   * `frontend/Dockerfile` & `frontend/nginx.conf`: Multi-stage build (Node 24 Alpine builder + Nginx Alpine runner) with SPA client-side routing fallback (`try_files $uri /index.html`), API reverse proxying `/api` to backend, and production security headers.
   * *Local Environment Note*: Docker Engine is not installed on the local Windows host; container specifications were statically verified and automated in the GitHub Actions CI pipeline without claiming local daemon execution.

2. **Health, Readiness & Error Sanitization**:
   * `backend/app/api/endpoints/health.py`:
     * `GET /api/health` and `GET /api/v1/health`: Returns HTTP 200 when healthy and HTTP 503 Service Unavailable when database connection is degraded.
     * `GET /api/healthz`: High-frequency liveness probe for orchestrators returning HTTP 200 immediately.
     * `GET /api/readyz`: Deep readiness probe verifying database connectivity, returning HTTP 200 on success or HTTP 503 on failure.
   * `backend/app/api/endpoints/imports.py`: Sanitized internal error handling, preventing exposure of raw tracebacks, filesystem paths, or database errors to API clients.

3. **Observability, Distributed Tracing & Frontend Resilience**:
   * `frontend/src/api/client.ts`: Extended `ApiError` with `requestId` and `code` properties, parsing `X-Request-ID` from response headers and structured error bodies.
   * `frontend/src/components/feedback/ErrorState.tsx`: Added incident reference ID display with one-click copy-to-clipboard action.
   * `frontend/src/components/feedback/ErrorBoundary.tsx`: React class-based Error Boundary wrapping the application in `App.tsx`, providing graceful error containment, incident tracking, and view recovery without white-screen crashes.

4. **Continuous Integration (GitHub Actions)**:
   * `.github/workflows/ci.yml`: Automated CI pipeline triggered on `push` and `pull_request` against `main`, running Python 3.12 pytest suite, Node 24 Vitest suite, Oxlint check, production bundle build, and Docker configuration validation.

5. **Test Suite Hygiene & Warning Remediation**:
   * `tests/conftest.py`: Added `isolate_test_upload_storage` autouse fixture redirecting all test uploads to pytest-managed `tmp_path`, eliminating filesystem pollution in `data/uploads/`.
   * `frontend/src/pages/OverviewPage.test.tsx`: Corrected asynchronous state transition awaiting in regional toggle test, eliminating all 5 React `act(...)` console warnings.

6. **Frontend Route-Level Code Splitting**:
   * `frontend/src/routes/AppRoutes.tsx`: Configured dynamic imports with `React.lazy` and `Suspense` for all operational page views, reducing the initial JavaScript bundle from 686 kB to 257 kB and eliminating Vite chunk size warnings.

7. **Production Operations Documentation**:
   * `docs/DEPLOYMENT_RUNBOOK.md`: Comprehensive step-by-step production deployment guide covering environment settings, Docker Compose, Nginx reverse proxy, TLS, backups, and disaster recovery.
   * `docs/OPERATIONS_AND_OBSERVABILITY.md`: Detailed operations runbook covering structured JSON log formats, `X-Request-ID` correlation, health probes, and incident triage scenarios.
   * `README.md`: Updated to accurately reflect React 19 stack and Docker deployment quickstart.

---

## Phase 8 Deliverables (Production Bootstrapping & Safe Import Rollback)

1. **Production Administrator Bootstrapping & Credential Hardening (Phase 8.1)**:
   * `scripts/bootstrap_admin.py` & `backend/app/core/admin_bootstrap.py`: Dedicated CLI onboarding command supporting interactive hidden password entry (`getpass`) and environment variable configuration (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `ADMIN_EMAIL`).
   * Cryptographic password complexity enforcement: Requires $\ge 12$ characters with mandatory uppercase, lowercase, numeric digits, and special symbols.
   * Strict idempotency: Returns clean exit code `0` if an administrator account already exists without modifying or overwriting credentials.
   * `backend/app/core/config.py`: Automatic normalization of PostgreSQL database schemes (`postgresql://` and `postgres://` $\rightarrow$ `postgresql+psycopg://`), ensuring seamless psycopg v3 driver selection across production runtimes.
   * `tests/test_admin_bootstrap.py`: 11 tests verifying complexity rules, CLI arguments, interactive hidden prompt mocks, and non-overwriting behavior.
   * `docs/DEPLOYMENT_RUNBOOK.md`: Updated Section 5 with step-by-step operator commands, security policies, and verification steps.

2. **Safe Import Rollback, Audit Provenance & Data Reversibility (Phase 8.2)**:
   * Database Migration `f14a8b7d9e23`: Added rollback metadata columns to `import_jobs`, added `last_import_job_id` foreign key index to `observations`, and created `import_observation_records` change-log table.
   * `backend/app/db/models/import_observation_record.py`: Tracks per-observation actions (`INSERT`, `UPDATE`, `UNCHANGED`) and full before-images.
   * `backend/app/services/imports/import_service.py`:
     * Ingestion change logging capturing previous observation values and metadata before applying updates.
     * Atomic `rollback_import_job` engine: Reverses insertions, restores updated before-images, reverses data quality log (`DQ_{job_code}`), and preserves disk files for audit trails.
     * Dependency conflict detection: Queries for subsequent active imports (`job.id > target.id`) modifying the same observations, safely rejecting rollback with HTTP `409 Conflict` (`ImportRollbackDependencyConflictError`).
   * `backend/app/api/endpoints/imports.py`: Exposed `POST /api/imports/{job_code}/rollback` with strict `ADMIN` role RBAC enforcement (HTTP 403 Forbidden for Analysts/Viewers).
   * `frontend/src/components/imports/ImportRollbackModal.tsx`: Visual modal with confirmation summary, reason input, risk warnings, and 409 conflict guidance.
   * `frontend/src/components/imports/ImportHistoryTable.tsx`: Added `ROLLED_BACK` badge, role-conditional "Rollback" action button visible strictly to administrators, and status filtering.
   * `frontend/src/pages/ImportPage.tsx`: Integrated rollback modal and auto-refreshing table state.
   * `tests/test_import_rollback.py`: 9 integration tests covering insertion deletion, before-image restoration, multi-import conflict detection (409), idempotency, and RBAC authorization.
   * `frontend/src/pages/ImportPage.test.tsx`: 3 frontend integration tests for Rollback action button visibility, modal opening, and successful rollback workflow execution.
   * `docs/IMPORT_PIPELINE.md`: Comprehensive specification of rollback architecture, change-tracking schema, and operational recovery instructions.

---

## Phase 9A Deliverables (Reliable Asynchronous HMIS Batch Ingestion & Large File Engine)

1. **Durable Database-Backed Background Import Job Lifecycle**:
   * Database Migration `a9b8c7d6e5f4`: Added `processed_records`, `claimed_at`, `claimed_by`, `heartbeat_at`, `retry_count`, `max_retries`, `error_summary`, and `schema_profile` to `import_jobs`.
   * `backend/app/db/models/import_job.py`: Extended model with Phase 9A batch columns and indexed state querying.
   * `backend/app/schemas/import_job.py`: Added progress models `ImportJobProgressResponse` and `ImportJobRetryResponse`.
   * State Machine: Enforced `QUEUED -> PROCESSING -> COMPLETED / COMPLETED_WITH_WARNINGS / FAILED / CANCELLED`.

2. **Durable Worker Engine & Concurrency Control**:
   * `backend/app/services/imports/worker.py`: `HMISImportWorker` with atomic claim query (`synchronize_session=False`), periodic heartbeat updates, and automated recovery of crashed/stale `PROCESSING` jobs.
   * `HMISImportWorkerThread`: Thread-safe in-process daemon started via FastAPI lifespan in `backend/app/main.py`. Protected by a mutex lock preventing duplicate worker spawns during dev reloads.
   * `scripts/run_import_worker.py`: Standalone CLI worker supporting daemon mode (`--interval 2.0`) or one-shot cron execution (`--once`).

3. **Large-File Chunked Ingestion & Provenance Preservation**:
   * `backend/app/core/config.py`: Added `IMPORT_CHUNK_SIZE=500` (configurable batch slice).
   * `backend/app/services/imports/import_service.py`: Chunked observation persistence with live progress updating, row-level validation, all-or-nothing rollback on partial failure (`cleanup_partial_import`), administrative retry (`retry_import_job`), and cancellation (`cancel_import_job`).
   * Maintained 100% Phase 8.2 change record provenance (`ImportObservationRecord`) across chunk boundaries, ensuring full atomic rollback remains correct.

4. **Versioned HMIS Schema Profiles Engine**:
   * `backend/app/services/imports/schema_profiles.py`: `BaseSchemaProfile`, `MOHFWStandardV2Profile` (`mohfw_standard_v2`), `FacilityMonthlyTabularV1Profile` (`facility_monthly_tabular_v1`), and `SchemaProfileRegistry`.
   * Pre-flight column detection and actionable structural validation before database insertion.

5. **REST API Extensions & RBAC**:
   * `POST /api/imports`: Fast async job enqueueing ($<100$ ms) with optional `?sync=true` bypass.
   * `GET /api/imports/{job_code}/status`: Real-time status, progress percentage, and row counter inspection.
   * `POST /api/imports/{job_code}/retry`: Admin-restricted endpoint to re-queue failed/cancelled jobs.
   * `POST /api/imports/{job_code}/cancel`: Admin-restricted endpoint to cancel running/queued jobs.

6. **Incoming Directory Watcher**:
   * `backend/app/services/imports/watcher.py`: `HMISIncomingDirectoryWatcher` monitoring `data/incoming/` (disabled by default via `ENABLE_DIRECTORY_WATCHER=False`).
   * File stability checking, SHA-256 idempotency verification, moving to `processed/`, and quarantining invalid files with `.error.txt` audit logs.

7. **Frontend Workspace Integration**:
   * `frontend/src/api/client.ts`: Added `getImportJobStatus`, `retryImport`, and `cancelImport`.
   * `frontend/src/pages/ImportPage.tsx`: Live background progress banner, auto-polling (every 2s while active jobs exist), and admin retry handler.
   * `frontend/src/components/imports/ImportHistoryTable.tsx`: Progress bar for `PROCESSING` rows, queued indicator, `CANCELLED` badge, and admin `Retry` button on `FAILED` rows.

8. **Verification & Testing**:
   * `tests/test_phase_9a_async_worker.py`: 14 comprehensive tests covering async job creation, worker atomic claiming, chunked commits, schema profiles, crash recovery, retries, admin endpoints, directory watcher, and rollback after chunked ingestion.
   * `tests/test_phase_9b_batch_orchestration.py`: 8 comprehensive tests covering batch lifecycle aggregation, directory watcher orchestration, concurrency locking, duplicate prevention, batch retry, batch cancellation, REST API permissions, and Alembic migrations.
   * **138/138 backend tests passed**.
   * **71/71 frontend tests passed**.
   * **Frontend production build clean (0 errors, 0 warnings)**.

---

## Phase 9A.1 Deliverables (Cancellation Safety & Concurrency Hardening)

1. **Elimination of Cancellation Fall-Through**:
   * Fixed critical control-flow flaw in `backend/app/services/imports/import_service.py` where in-flight cancellation during chunk processing could fall through into completion handling.
   * Replaced fall-through logic with immediate return of the cancelled job after rolling back uncommitted chunk transactions and executing `cleanup_partial_import()`.

2. **Session Identity-Map Cache Bypass**:
   * Implemented `_is_job_cancelled(job_id)` using `.scalar()` and `.execution_options(populate_existing=True)`.
   * Guarantees that external cancellation executed by an administrator in a concurrent session is immediately visible inside the worker's chunk loop, preventing cached ORM entity state from masking cancellation.

3. **Multi-Boundary Cancellation Probes**:
   * Verified cancellation checks at chunk entry, immediately before chunk database commit, and post-chunk-loop before quality log emission.
   * Prevents execution of any subsequent chunks once cancellation is signaled.

4. **Observation Deletion Scoping & Provenance Safety**:
   * Hardened `cleanup_partial_import()` to strictly scope observation deletions and restorations to `obs.last_import_job_id == job.id`.
   * Completely preserves unrelated existing observations and prior valid state.

5. **State Transition Completeness**:
   * Added `VALIDATED` intermediate status to `VALID_IMPORT_STATUS_TRANSITIONS` and `cancel_import_job`, ensuring in-flight datasets can be cancelled cleanly during pre-validation and ingestion.

---

## Phase 9B Deliverables (Automated Batch Orchestration & Incoming Directory Integration)

1. **Database Schema & Aggregated Batch Model**:
   * `backend/app/db/models/import_batch.py`: `ImportBatch` model tracking `batch_code`, `source`, `status`, `total_files`, `processed_files`, `successful_files`, `failed_files`, `total_records`, `imported_records`, `rejected_records`, `initiated_by`, `error_summary`, and relationship `import_jobs`.
   * `backend/app/db/models/import_job.py`: Added `batch_id` foreign key and bidirectional relationship to `ImportBatch`.
   * `backend/app/db/migrations/versions/b1c2d3e4f5a6_add_phase_9b_import_batches.py`: Alembic migration with bidirectional upgrade and downgrade.

2. **Incoming Directory Orchestration (`HMISIncomingDirectoryWatcher`)**:
   * `backend/app/services/imports/watcher.py`: Thread-safe incoming directory scanner with `_active_files` lock preventing duplicate or concurrent processing across threads.
   * Temporary file exclusion: skips `.tmp`, `.temp`, `.part`, `.crdownload`, and hidden/system files.
   * Size stability delta and read-accessibility verification for incomplete writes.
   * SHA-256 idempotency check: relocates duplicate files to `processed/` with `duplicate_<job_code>` suffix without creating redundant jobs.
   * Corrupted/invalid file quarantine: relocates invalid files to `quarantine/` with `.error.txt` diagnostic notes.
   * Background daemon thread `HMISDirectoryWatcherThread` and singleton lifecycle controllers `start_directory_watcher()` and `stop_directory_watcher()`.

3. **Batch Lifecycle & Recovery Service**:
   * `HMISImportService.create_import_batch`: Enqueues consolidated batch records.
   * `HMISImportService.update_batch_metrics`: Dynamically aggregates status (`QUEUED`, `PROCESSING`, `COMPLETED`, `PARTIALLY_FAILED`, `FAILED`, `CANCELLED`) and record counters from child jobs.
   * `HMISImportService.retry_import_batch`: Resets failed/stalled child jobs to `QUEUED` for worker re-execution.
   * `HMISImportService.cancel_import_batch`: Cancels all in-flight child jobs safely and rolls back partial state.

4. **REST API Extensions**:
   * `GET /api/imports/batches`: Paginated batch history with filtering by status and source.
   * `GET /api/imports/batches/{batch_code}`: Detailed batch status, progress percentage, and constituent child jobs.
   * `POST /api/imports/batches/scan`: Admin-only endpoint triggering an on-demand directory scan.
   * `POST /api/imports/batches/{batch_code}/retry`: Admin-only endpoint retrying failed jobs in a batch.
   * `POST /api/imports/batches/{batch_code}/cancel`: Admin-only endpoint cancelling in-flight batch jobs.

5. **Frontend Batch Monitoring Panel**:
   * `frontend/src/components/imports/BatchMonitoringPanel.tsx`: Dedicated batch tracking UI with real-time status badges, file progress bars, record counters, error summary callouts, expandable child jobs view, on-demand scan button, and batch retry/cancel actions.
   * `frontend/src/pages/ImportPage.tsx`: Integrated tab switcher between "Individual Ingestion Jobs" and "Automated Batch Orchestration".

---

## Phase 10: End-to-End Release Validation Checklist

| Check / Domain | Verification Procedure | Status | Notes |
| :--- | :--- | :--- | :--- |
| **Backend Test Suite** | `pytest` (138 tests) | **PASSED** | 100% pass across all modules (0 failures, 0 errors) |
| **Frontend Test Suite** | `npm test -- --run` (71 tests) | **PASSED** | 100% pass across 13 test suites (0 failures, 0 warnings) |
| **Frontend Build** | `npm run build` | **PASSED** | Production bundle compiled cleanly |
| **Formatting & Hygiene** | `git diff --check` | **PASSED** | 0 whitespace or formatting anomalies |
| **Database Migrations** | `alembic upgrade head` | **PASSED** | Revision `b1c2d3e4f5a6` verified |
| **Database Integrity** | Development DB inspection | **PRESERVED** | User data and known index discrepancy preserved |
| **Authentication & RBAC** | JWT Auth + Role verification | **PASSED** | ADMIN, ANALYST, VIEWER permissions strictly enforced |
| **Batch Ingestion Flow** | Automated scan -> batch -> worker | **PASSED** | Enqueuing, chunking, progress telemetry verified |
| **Cancellation & Rollback** | Race condition tests + before-images | **PASSED** | Atomic reversibility verified with no data corruption |
| **Observability & Health** | `/api/health`, `/healthz`, `/readyz` | **PASSED** | Probes verified with distributed request tracing |
| **Real vs Synthetic Data** | Baseline disclosure | **DISCLOSED** | Transparently documented that development metrics use synthetic baselines |

---

## Phase 15 Deliverables (Multi-Year HMIS Ingestion & Anomaly Review Workflow)

1. **Source Discovery & Data Acquisition Readiness (Phase 15A)**:
   * Cataloged official state returns in `backend/app/services/analytics/source_registry.py` (`SourceRegistryCatalog`).
   * FY 2015–16: 175,872 observations ingested from official MoHFW consolidated return file `District wise Monthly report 2015-16.xlsx` (`sha256: 7e73d32ef3...`).
   * FY 2016–17 & FY 2017–18: Documented with status `BLOCKED_MISSING_OFFICIAL_FILE` requiring authenticated portal retrieval. Zero synthetic records fabricated.
   * REST Endpoint: `GET /api/analytics/district/intelligence/source-registry`.

2. **Multi-Year Ingestion Pipeline (Phase 15B)**:
   * Dynamic financial year extraction via `detect_financial_year()` in `backend/app/services/imports/district_adapter.py`.
   * Normalization of FY string formats (`YYYY-YY`) and calendar months (`1..12`).
   * Ingestion service (`import_service.py`) dynamically creates `ImportJob` with extracted financial year metadata, preserving idempotency and district/facility isolation.

3. **Cross-Year Data Quality & Comparability Service (Phase 15C)**:
   * `backend/app/services/analytics/cross_year_comparability.py` checks 12-month calendar completeness per financial year.
   * Tracks 32 historical districts (FY 2015–16 baseline) and catalogs 6 post-2018 administrative bifurcations (Tenkasi, Chengalpattu, Tirupathur, Ranipet, Kallakurichi, Mayiladuthurai) to prevent misleading cross-year comparisons.
   * Compares indicator definitions, units, and code stability across years.
   * REST Endpoint: `GET /api/analytics/district/intelligence/cross-year-comparability`.

4. **Multi-Year Forecasting Evaluation (Phase 15D)**:
   * Chronological rolling-origin/expanding-window forecasting evaluation framework in `backend/app/services/analytics/healthcare_intelligence.py`.
   * Explicit `INSUFFICIENT_HISTORY` diagnostic emitted when historical observations span $<24$ months, preventing premature or invalid seasonal forecasting claims.
   * Zero data leakage: strict separation between training horizons and evaluation periods.

5. **Anomaly Administrative Review & Audit Workflow (Phase 15E)**:
   * Database Models: `DistrictAnomalyReview` and `DistrictAnomalyReviewAction` in `backend/app/db/models/anomaly_review.py`.
   * Alembic Migration: `d3e4f5a6b7c8_add_phase_15_anomaly_review_workflow.py`.
   * State Machine: `OPEN -> ACKNOWLEDGED -> UNDER_REVIEW -> RESOLVED -> REOPENED`.
   * RBAC Enforcement: `ADMIN` and `ANALYST` permitted; `VIEWER` rejected with HTTP 403 Forbidden.
   * Immutable audit logging preserving user ID, action timestamp, transition state, and resolution notes.
   * REST Endpoints:
     * `GET /api/analytics/district/intelligence/anomalies/reviews`
     * `POST /api/analytics/district/intelligence/anomalies/reviews/{signal_id}/action`

6. **Frontend District Intelligence Workspace Integration (Phase 15F)**:
   * `frontend/src/components/districts/DistrictIntelligenceTab.tsx`:
     * Multi-year Source Registry table showing reporting period, record counts, and provenance.
     * Cross-year comparability notices detailing reporting completeness and district boundary shifts.
     * Interactive Anomaly Review modal allowing review state transitions, note additions, and audit history inspection.
   * `frontend/src/api/client.ts` & `frontend/src/api/types.ts`: API clients and type definitions for Phase 15 endpoints.
   * `frontend/src/pages/DistrictsPage.test.tsx`: Extended tests to mock all Phase 15 client calls cleanly.

---

## Phase 16 Deliverables (Production Readiness, Security Hardening & Operational Reliability)

1. **Database Path Audit & Canonical Resolution (Critical Safety Requirement)**:
   * **Audit Findings**: The application configuration (`Settings.DATABASE_URL` default `"sqlite:///./careflow_dev.db"`) resolves relative to the project root when launched from `D:\careflow`, targeting `D:\careflow\careflow_dev.db`.
   * **Deleted File Investigation**: Confirmed that `data\careflow_dev.db` was an empty 0-byte artifact created when an inline CLI scratch command connected to `data/careflow_dev.db` during Phase 15 testing. The file was immediately removed, and no application data was lost.
   * **Integrity & Row Preservation**: Active database `careflow_dev.db` verified with `PRAGMA integrity_check` = `ok`. All 175,872 district observations, 362 facility observations, 108 forecasts, and 351,764 rollback change-log records remain 100% intact.
   * **Pre-Audit Backup**: Created and verified atomic online backup at `data/backups/careflow_dev_backup_phase16_preaudit.db` (213,311,488 bytes).

2. **Production Security & Configuration Hardening (Phase 16A)**:
   * `backend/app/core/config.py`: Hardened `validate_environment_and_security()`:
     * Mandates $\ge 32$-character non-default `SECRET_KEY` in production.
     * Enforces PostgreSQL and strictly rejects SQLite in production.
     * Enforces explicit production domain origins and strictly rejects wildcard `*` in `CORS_ORIGINS` when credentials are enabled.
     * Added `is_production` and `canonical_database_type` helper properties.
   * `backend/app/core/middleware.py`: Global exception handler sanitizes uncaught 500 exceptions into a uniform `INTERNAL_SERVER_ERROR` contract with request ID propagation (`X-Request-ID`), preventing disclosure of database queries, stack traces, or local filesystem paths.

3. **System Health & Orchestrator Probes (Phase 16A)**:
   * `backend/app/api/endpoints/health.py`:
     * `GET /api/health`: Public system health probe with real database connectivity check (`SELECT 1`), returning 200 when healthy or 503 when disconnected, without disclosing connection credentials or internal driver details.
     * `GET /api/healthz`: High-frequency liveness probe returning HTTP 200 alive without database dependency.
     * `GET /api/readyz`: Deep readiness probe verifying database connectivity and returning HTTP 503 if unreachable.

4. **Authentication & Granular RBAC Verification (Phase 16B)**:
   * Audited all protected operational routes: unauthenticated, expired, or corrupted JWT tokens are rejected with HTTP 401 Unauthorized across all endpoints.
   * Granular role permissions verified:
     * `ADMIN`: Full access to upload, view, rollback, retry, directory scan, and anomaly reviews.
     * `ANALYST`: Authorized for file upload, analytics viewing, and anomaly review state transitions; prohibited from rollback (403), directory scan triggers (403), or batch cancellation (403).
     * `VIEWER`: Restricted to read-only views; prohibited from file uploads (403), rollback (403), and anomaly review actions (403).
   * Abuse protection: Sliding-window rate limiter protects authentication endpoints (`InMemoryRateLimiter`).

5. **Operational Reliability & Ingestion Workers (Phase 16D)**:
   * In-process background worker (`HMISImportWorkerThread`) verified with singleton lock preventing duplicate thread spawns on server reload.
   * Atomic job claiming (`claim_job()`) and heartbeat tracking (`heartbeat_at`) preventing worker race conditions.
   * Automatic crash recovery: identifies stale jobs exceeding `WORKER_STALE_TIMEOUT_SECONDS` (300s) and safely resets them for re-execution up to `WORKER_MAX_RETRIES` (3).
   * Rollback dependency conflict protection: detects subsequent active imports modifying the same observations and safely returns `HTTP 409 Conflict`.

6. **Operational Documentation & Runbooks (Phase 16F)**:
   * `docs/DEPLOYMENT_RUNBOOK.md`: Added Section 8 (Database Architecture & Canonical Path Selection), Section 9 (Backup Verification & Integrity Audit Procedures), and Section 10 (HMIS Import Recovery & Operational Troubleshooting).
   * Zero secret values, credentials, or private environmental keys committed.
