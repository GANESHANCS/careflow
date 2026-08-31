# CAREFlow India — HMIS Data Ingestion Pipeline & Import API Documentation

## Executive Overview

The CAREFlow HMIS Data Ingestion Engine provides an auditable, secure, and production-hardened pipeline for uploading, validating, standardizing, and persisting government Health Management Information System (HMIS) spreadsheet reports (`.csv`, `.xlsx`, `.xls`).

It bridges the raw file inspection, schema normalization, and data quality evaluation engines from Phase 2 with the operational relational database model and authenticated API endpoints introduced in Phase 7C/7D.

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
