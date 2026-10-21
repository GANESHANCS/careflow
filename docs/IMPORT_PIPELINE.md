# CAREFlow India — HMIS Data Ingestion Pipeline & Import API Documentation

## Executive Overview

The CAREFlow HMIS Data Ingestion Engine provides an auditable, secure, and production-hardened pipeline for uploading, validating, standardizing, and persisting government Health Management Information System (HMIS) spreadsheet reports (`.csv`, `.xlsx`, `.xls`).

It bridges the raw file inspection, schema normalization, and data quality evaluation engines from Phase 2 with the operational relational database model and authenticated API endpoints introduced in Phase 7C/7D. In Phase 7G, this pipeline is surfaced through the interactive `/imports` frontend workspace, providing drag-and-drop spreadsheet upload, live job history tracking, quality scorecard modal inspection, and diagnostic audit error viewing with role-based access control.

---

## Architecture & Data Flow

```
                               ┌──────────────────────────┐
                               │  POST /api/imports       │
                               │  (Multipart Spreadsheet) │
                               └────────────┬─────────────┘
                                            │
                                  RBAC: ADMIN / ANALYST
                                            │
                                            ▼
                               ┌──────────────────────────┐
                               │ ImportStorageService     │
                               │ - Sanitize Filename      │
                               │ - SHA-256 Hash           │
                               │ - Idempotency Check      │
                               └────────────┬─────────────┘
                                            │ (Job: QUEUED)
                                            ▼
                               ┌──────────────────────────┐
                               │ HMISImportService        │
                               │ - File Inspection        │
                               │ - Schema Normalization   │
                               └────────────┬─────────────┘
                                            │ (Job: VALIDATED)
                                            ▼
                               ┌──────────────────────────┐
                               │ Pipeline Execution       │
                               │ - Deduplication Engine   │
                               │ - Quality Audit Engine   │
                               └────────────┬─────────────┘
                                            │
                                  Atomic DB Transaction
                                            │
                     ┌──────────────────────┴──────────────────────┐
                     ▼                                             ▼
       ┌──────────────────────────┐                  ┌──────────────────────────┐
       │ Operations Storage       │                  │ Audit Diagnostics        │
       │ - Facilities             │                  │ - ImportErrorLog         │
       │ - Indicators             │                  │ - DataQualityLog         │
       │ - Observations           │                  │ - ImportJob (COMPLETED) │
       └──────────────────────────┘                  └──────────────────────────┘
```

---

## Core Lifecycle States (`ImportJob.status`)

1. **`QUEUED`**: File upload accepted, constraint checks passed, storage path initialized, and unique `job_code` assigned.
2. **`PROCESSING`**: Pipeline runner reads binary content, parses worksheets, normalizes column headers, and classifies cell values.
3. **`VALIDATED`**: Structural layout, dates, and facility codes successfully extracted and verified.
4. **`COMPLETED`**: Operational entities created/updated; quality scores and audit logs persisted without blocking errors.
5. **`COMPLETED_WITH_WARNINGS`**: Data persisted successfully, but diagnostic warnings or non-fatal row-level validation issues were logged.
6. **`FAILED`**: Critical format error or transaction exception occurred. Operational DB changes rolled back completely.
7. **`ROLLED_BACK`**: Data changes previously applied by the import have been safely reverted via administrative rollback.

### Valid Status Transitions
```
QUEUED ──────────► PROCESSING ──────────► VALIDATED ──────────┬──► COMPLETED ──────────────┬──► ROLLED_BACK
  │                     │                     │               │                            │
  ▼                     ▼                     ▼               └──► COMPLETED_WITH_WARNINGS ┘
FAILED                FAILED                FAILED
```

---

## Key Technical Principles & Governance Rules

### 1. Data Integrity & Non-Destructive Ingestion
* **Missing Value Preservation**: Raw missing values (`None`, `""`, `"N/A"`, `"-"`, `pd.isna`) are assigned `ValueClassification.MISSING`. They are **never** coerced to `0.0`.
* **Zero Distinction**: Explicit zeros (`0`, `0.0`) are preserved as valid `0.0` with `ValueClassification.ZERO`.
* **Overwriting Safety**: When re-importing observations for an existing `(facility_id, indicator_id, observation_date)` tuple, existing valid numeric values are **never** overwritten by missing or null entries.

### 2. Idempotency & Duplicate Prevention
* Every uploaded file content is hashed using SHA-256 (`file_hash`).
* Re-uploading an identical file returns the existing completed `ImportJob` payload immediately (`201 Created` with identical job code) without re-executing pipeline steps or duplicating database records.
* Operational records feature unique database constraint `(facility_id, indicator_id, observation_date)` to ensure deterministic upsert behavior.

### 3. Security & Access Control (RBAC)
* **Write Access (`POST /api/imports`)**: Restricted strictly to `ADMIN` and `ANALYST` roles. `VIEWER` access returns `403 Forbidden`.
* **Read Access (`GET /api/imports`, `GET /api/imports/{code}`)**: Accessible to `ADMIN`, `ANALYST`, and `VIEWER` roles.
* **Path Traversal Protection**: Filenames are strictly sanitized with `ImportStorageService.sanitize_filename` to strip path separators (`/`, `\`), relative tokens (`..`), null bytes, and unsafe shell characters.
* **File Limits**: Enforces a strict 50 MB size ceiling (`MAX_FILE_SIZE_BYTES`) and allows only `.csv`, `.xlsx`, and `.xls` formats.

---

## REST API Specification

### 1. Upload HMIS File
* **`POST /api/imports`**
* **Headers**: `Authorization: Bearer <token>`, `Content-Type: multipart/form-data`
* **Roles**: `ADMIN`, `ANALYST`
* **Response (201 Created)**:
```json
{
  "id": 1,
  "job_code": "JOB_20260831_153000_a1b2c3",
  "original_filename": "hmis_delhi_2024.csv",
  "file_size_bytes": 1048576,
  "mime_type": "text/csv",
  "status": "COMPLETED",
  "total_records": 1250,
  "records_imported": 1245,
  "records_rejected": 5,
  "quality_score": 94.5,
  "created_at": "2026-08-31T15:30:00Z",
  "completed_at": "2026-08-31T15:30:05Z"
}
```

### 2. List Import History
* **`GET /api/imports?skip=0&limit=50&status=COMPLETED&search=delhi`**
* **Roles**: `ADMIN`, `ANALYST`, `VIEWER`
* **Response (200 OK)**:
```json
{
  "total": 1,
  "items": [...],
  "page": 1,
  "page_size": 50
}
```

### 3. Get Import Job Details
* **`GET /api/imports/{job_code_or_id}`**
* **Roles**: `ADMIN`, `ANALYST`, `VIEWER`

### 4. Get Quality Audit Report
* **`GET /api/imports/{job_code_or_id}/quality`**
* **Roles**: `ADMIN`, `ANALYST`, `VIEWER`
* **Response (200 OK)**:
```json
{
  "job_code": "JOB_20260831_153000_a1b2c3",
  "overall_quality_score": 94.5,
  "total_issues": 3,
  "severity_counts": { "CRITICAL": 0, "WARNING": 2, "ERROR": 1, "INFO": 0 },
  "category_scores": {
    "completeness": 92.0,
    "validity": 96.5,
    "consistency": 95.0,
    "timeliness": 94.0,
    "accuracy": 95.0
  },
  "findings": [
    {
      "code": "CHECK_1",
      "severity": "WARNING",
      "message": "[Missing Values] 12 observations (0.96%) have missing value cells.",
      "row": null,
      "sheet": null
    }
  ]
}
```

### 5. Get Diagnostic Error Logs
* **`GET /api/imports/{job_code_or_id}/errors?skip=0&limit=50`**
* **Roles**: `ADMIN`, `ANALYST`, `VIEWER`

---

## Safe Import Rollback & Data Provenance (Phase 8.2)

### 1. Data Provenance & Change-Tracking Model
To guarantee non-destructive rollbacks when multiple datasets are ingested over time, CAREFlow implements per-observation change-tracking via `ImportObservationRecord` (`import_observation_records` table):

| Field | Type | Description |
|---|---|---|
| `id` | `INTEGER` | Auto-increment primary key |
| `import_job_id` | `INTEGER` | Foreign key referencing `import_jobs.id` (`CASCADE`) |
| `observation_id` | `VARCHAR(128)` | Unique ID of the affected observation |
| `action` | `VARCHAR(20)` | `INSERT`, `UPDATE`, or `UNCHANGED` |
| `previous_value` | `FLOAT` | Before-image numeric value prior to this import |
| `previous_value_type` | `VARCHAR(32)` | Before-image classification (`VALID`, `MISSING`, `ZERO`) |
| `previous_validation_status` | `VARCHAR(32)` | Before-image validation state |
| `previous_source_file` | `VARCHAR(255)` | Before-image file origin |
| `previous_source_sheet` | `VARCHAR(128)` | Before-image worksheet origin |
| `previous_source_row` | `INTEGER` | Before-image row number |
| `previous_ingested_at` | `VARCHAR(64)` | Before-image ISO timestamp |
| `previous_transformation_version` | `VARCHAR(32)` | Before-image pipeline version |
| `previous_import_job_id` | `INTEGER` | Import job previously responsible for this observation |
| `new_value` | `FLOAT` | Value assigned by this import |
| `new_value_type` | `VARCHAR(32)` | Classification assigned by this import |
| `created_at` | `DATETIME` | Timestamp of change record logging |

### 2. Rollback Endpoint Specification
* **`POST /api/imports/{job_code}/rollback`**
* **Authorization**: Strictly restricted to `ADMIN` role. (`ANALYST` and `VIEWER` return `403 Forbidden`).
* **Request Body** (optional):
```json
{
  "reason": "Ingested incorrect monthly report; re-uploading revised dataset"
}
```
* **Response (200 OK)**:
```json
{
  "job_code": "JOB_20260831_153000_a1b2c3",
  "status": "ROLLED_BACK",
  "records_deleted": 1200,
  "records_restored": 45,
  "records_unchanged": 5,
  "rolled_back_at": "2026-10-10T12:00:00Z",
  "rolled_back_by": "admin_user",
  "message": "Successfully rolled back import job 'JOB_20260831_153000_a1b2c3'. Reverted 1200 inserted and 45 updated observation records."
}
```

### 3. Rollback Semantics & Safeguards
1. **Created Records (`INSERT`)**: Permanently deleted from `observations` only if no subsequent active import modified them.
2. **Updated Records (`UPDATE`)**: Restored to their exact before-image (`previous_value`, `previous_value_type`, `previous_source_file`, `previous_ingested_at`, `previous_transformation_version`, `previous_import_job_id`).
3. **Unchanged Records (`UNCHANGED`)**: Preserved without modification.
4. **Dependent Import Limitation (Conflict Prevention)**:
   - If a subsequent import job (e.g. Job B, where `B.id > A.id` with active status `COMPLETED` or `COMPLETED_WITH_WARNINGS`) modified an observation touched by Job A, attempting to roll back Job A is **safely rejected** with **`409 Conflict`**:
     ```json
     {
       "detail": "Cannot roll back import job 'JOB_A' because subsequent active import job(s) ['JOB_B'] modified the same observation(s). Roll back subsequent dependent imports first."
     }
     ```
   - This prevents silent overwrites or unexpected data erasure of newer datasets.
5. **Idempotency**: Repeated calls to rollback an already rolled back job safely return `200 OK` with `records_deleted: 0, records_restored: 0`.
6. **Data Quality Telemetry Reversal**: Associated `DataQualityLog` (`DQ_{job_code}`) is removed upon rollback so downstream audit dashboards and compliance reports accurately reflect the rollback.
7. **Audit Preservation**: The physical file on disk in `data/uploads/` and `import_error_logs` are **never deleted**, preserving full evidentiary audit trails.

### 4. Operational Recovery Instructions
When rolling back datasets in production environments:
1. Navigate to `/imports` in the web application (must be authenticated as Administrator).
2. Locate the target job in the Ingestion History table.
3. Click the **Rollback** button in the Actions column.
4. Review the confirmation dialog summarizing affected records and enter an operational audit justification.
5. If a **409 Conflict** error appears indicating newer dependent imports, identify the newer job codes listed in the prompt and roll them back in reverse chronological order first.
6. Once rolled back, the dataset file can be re-uploaded with corrected values if desired.

---

## Phase 9A: Reliable Asynchronous HMIS Batch Ingestion & Large File Engine

### 1. Architectural Design & Worker Mechanism
To prevent HTTP gateway timeouts (e.g. 30s/60s proxy timeouts on Nginx or cloud load balancers) during ingestion of large health datasets, Phase 9A introduces a database-backed, persistent job processing lifecycle.

The worker architecture provides:
* **Immediate HTTP Response**: The upload endpoint `POST /api/imports` creates an `ImportJob` record with status `QUEUED`, writes raw content to storage, and returns `201 Created` within $< 100$ ms. Clients receive the `job_code` and immediately track progress via polling or UI banners. (Synchronous execution remains available when requested via `?sync=true`).
* **In-Process & Standalone Worker Modes**:
  1. **In-Process Worker (`HMISImportWorkerThread`)**: Managed automatically by the FastAPI lifespan in `backend/app/main.py`. Starts on server boot and shuts down cleanly on SIGTERM/SIGINT. Thread startup is protected by a mutex lock to prevent duplicate worker spawns during Uvicorn hot-reloads.
  2. **Standalone Worker Process (`scripts/run_import_worker.py`)**: Can be executed as an independent OS daemon or Kubernetes background worker pod:
     ```bash
     python scripts/run_import_worker.py --interval 2.0
     # Or run a single sweep for scheduled cron jobs:
     python scripts/run_import_worker.py --once
     ```
* **Dialect-Agnostic Atomic Job Claiming**:
  Worker instances claim jobs using an atomic database query:
  ```python
  candidate = db.query(ImportJob).filter(ImportJob.status == "QUEUED").order_by(ImportJob.id.asc()).first()
  if candidate:
      updated = db.query(ImportJob).filter(
          ImportJob.id == candidate.id,
          ImportJob.status == "QUEUED"
      ).update({
          "status": "PROCESSING",
          "claimed_at": now,
          "claimed_by": worker_id,
          "heartbeat_at": now
      }, synchronize_session=False)
      if updated:
          db.commit()
  ```
  This is 100% compatible with SQLite development environments as well as multi-node PostgreSQL deployments, ensuring that multiple concurrent worker processes never process the same job simultaneously.

### 2. Job Lifecycle States & State Machine
The extended job state machine guarantees strict forward transitions:
```
QUEUED ──────────► PROCESSING ──────────► VALIDATED ──────────┬──► COMPLETED ──────────────┬──► ROLLED_BACK
  │                     │                     │               │                            │
  ├─────────────────────┼─────────────────────┼───────────────┼──► COMPLETED_WITH_WARNINGS ┘
  │                     │                     │               │
  ▼                     ▼                     ▼               ▼
CANCELLED             CANCELLED             FAILED          FAILED
```

* **`QUEUED`**: Persisted in database, pending claim by an active worker.
* **`PROCESSING`**: Claimed by a worker; heartbeat updated periodically.
* **`COMPLETED` / `COMPLETED_WITH_WARNINGS`**: All observation chunks validated and committed with before-images.
* **`FAILED`**: Row or format error exceeded thresholds; partial chunk observations purged cleanly.
* **`CANCELLED`**: Cancelled by Administrator via `POST /api/imports/{code}/cancel`. Any partial observations created during processing are immediately cleaned up.

### 3. Worker Crash Recovery, Heartbeat, and Stale Job Management
* **Heartbeat Monitoring**: While actively reading or committing chunks, the worker updates `heartbeat_at` at regular intervals.
* **Stale Job Sweep**: On every polling cycle, the worker checks for jobs in `PROCESSING` status whose `heartbeat_at` is older than `WORKER_STALE_TIMEOUT_SECONDS` (default: 300 seconds).
* **Automated Retry Rules**:
  * If `job.retry_count < job.max_retries` (default: 3 retries), the worker increments `retry_count`, resets `claimed_by = None`, and moves the job back to `QUEUED` for immediate reprocessing. Partial observations from interrupted attempts are wiped cleanly before re-queueing to eliminate duplicate observations.
  * If `retry_count >= max_retries`, the job is marked `FAILED` with error summary: `"Job exceeded maximum allowed retries due to worker timeout or crash."`

### 4. Large-File & Chunked Processing (`IMPORT_CHUNK_SIZE=500`)
To support spreadsheet files with tens of thousands of rows without exhausting RAM or holding open long-lived database locks:
1. **Incremental Streaming & Chunking**:
   Input records are sliced into chunks governed by `settings.IMPORT_CHUNK_SIZE` (default 500 rows).
2. **Transaction Boundaries**:
   Each chunk processes validations and executes atomic database flushes, updating `processed_records` and `records_imported` progress counters.
3. **Observation Change Provenance**:
   For every created or updated observation across every chunk, an `ImportObservationRecord` is created recording its `action` (`INSERT` or `UPDATE`) and full before-image.
4. **All-or-Nothing Finality**:
   If an unhandled exception or critical violation occurs on chunk $N$, `cleanup_partial_import()` deletes any inserted observations and restores any updated before-images before marking the job `FAILED`. Completed imports maintain 100% complete provenance records, allowing Phase 8.2 administrative rollback to function identically across single-chunk and multi-chunk imports.

### 5. Versioned HMIS Schema Profiles Engine
Located in `backend/app/services/imports/schema_profiles.py`:
* **`mohfw_standard_v2`**: Matches Ministry of Health & Family Welfare standard tabular layout (State, District, Facility Code, Facility Name, Reporting Month, and clinical metrics).
* **`facility_monthly_tabular_v1`**: Simplified tabular profile for facility-specific monthly reports.
* **Pre-Flight Validation**: `SchemaProfileRegistry.detect_profile(headers)` analyzes header columns before database writes. If required groups (Temporal Period, Facility Identifier, Spatial District/State) are missing, validation errors are logged immediately without wasting compute cycles on data processing.
* **Synthetic vs Real Data Labeling**: Schema profiles are explicitly documented as grounded in integration test contracts; unvalidated against unindexed Ministry spreadsheets until real production files are supplied.

### 6. Phase 9A REST API Endpoints
* **`GET /api/imports/{job_code}/status`**: Public / authenticated status query returning live progress percentage, processed row count, accepted/rejected counts, claimed worker, and safe error summaries.
* **`POST /api/imports/{job_code}/retry`**: Restricted to `ADMIN`. Resets a `FAILED` or `CANCELLED` job back to `QUEUED` and resets error logs.
* **`POST /api/imports/{job_code}/cancel`**: Restricted to `ADMIN`. Halts a `QUEUED` or `PROCESSING` job, purges partial changes, and transitions status to `CANCELLED`.

### 7. Incoming Directory Watcher (`HMISIncomingDirectoryWatcher`)
Automated directory ingestion service in `backend/app/services/imports/watcher.py`:
* **Configurable Target Directory**: Watches `settings.INCOMING_IMPORT_DIR` (default: `data/incoming`).
* **Disabled by Default**: Controlled via `ENABLE_DIRECTORY_WATCHER=False` in configuration.
* **File Stability Check**: Checks file size stability across an interval (`stability_wait_seconds`) and attempts non-destructive exclusive read to verify file transfer completion before ingestion.
* **Quarantine Workflow**: Files with unsupported extensions or corrupted formats are immediately isolated in `data/incoming/quarantine/<filename>` with a companion `<filename>.error.txt` audit trace.
* **Processed Archive**: Successfully ingested files are moved to `data/incoming/processed/<filename>_<job_code>`.

### 8. Known Reliability, Concurrency & Production Limitations
1. **In-Process Thread vs Distributed Celery/Redis**: The in-process worker thread runs inside the FastAPI process. In multi-replica container environments (e.g., Kubernetes with $> 1$ replica), running `scripts/run_import_worker.py` as a dedicated worker deployment is recommended over multi-pod in-process workers.
2. **SQLite Dev Concurrency vs PostgreSQL**: While SQLite with WAL mode supports concurrent reads, write locks are serialized. In local development, avoid launching more than one worker thread. In production PostgreSQL, row-level locks and `synchronize_session=False` support multiple parallel worker instances.
3. **Spreadsheet Streaming Limits**: Binary `.xlsx` files require parsing worksheet XML structures via Pandas/OpenpyXL; streaming is emulated in chunked row batches. For files exceeding 100,000 rows, CSV format is strongly recommended for optimal memory efficiency.
