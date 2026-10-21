# CAREFlow Synthetic HMIS Test Fixtures

This directory contains synthetic test fixtures engineered for testing CAREFlow import validations, schema profile matching, idempotency, and data quality pipelines.

> **Privacy & Compliance Notice**:
> All records in these fixtures contain **100% synthetic, non-patient data** utilizing simulated facility names, standard indicator categories, and synthetic monthly aggregates.

---

## 1. Fixture Inventory

| File Name | Schema Profile | Purpose | Expected Outcome |
| :--- | :--- | :--- | :--- |
| [`mohfw_valid_monthly_sample.csv`](file:///D:/careflow/data/test_fixtures/mohfw_valid_monthly_sample.csv) | `mohfw_standard_v2` | Baseline valid dataset | **Success (`COMPLETED`)**: All facilities, periods, and observations ingested. Quality audit calculated. |
| [`mohfw_invalid_missing_column.csv`](file:///D:/careflow/data/test_fixtures/mohfw_invalid_missing_column.csv) | `mohfw_standard_v2` (Target) | Deliberately missing `Reporting Month` | **Rejection (`FAILED`)**: Pre-flight schema validation error (`SCHEMA_VALIDATION_ERROR`). 0 records ingested. |
| [`mohfw_duplicate_monthly_sample.csv`](file:///D:/careflow/data/test_fixtures/mohfw_duplicate_monthly_sample.csv) | `mohfw_standard_v2` | Byte-for-byte duplicate of valid dataset | **Idempotent Response**: Matches SHA-256 hash of prior job. Existing job returned; 0 duplicates inserted. |

---

## 2. Supported Schema Profiles Overview

### A. `mohfw_standard_v2` (MoHFW Standard Tabular HMIS Profile)
* **Required Column Groups**:
  * **Temporal Period**: `reporting_month`, `month`, `observation_date`, `date`, `period`
  * **Facility Identifier**: `facility_code`, `facility_name`, `facility`, `facility_id`, `code`
  * **Spatial District/State**: `district`, `state`, `district_name`, `state_name`
* **Canonical Headers**: `State, District, Facility Code, Facility Name, Reporting Month, [Clinical/Operational Indicators...]`

### B. `facility_monthly_tabular_v1` (Facility Monthly Tabular Profile)
* **Required Column Groups**:
  * **Temporal Period**: `reporting_month`, `month`, `date`, `period`
  * **Facility Identifier**: `facility_code`, `facility_name`, `facility`, `facility_id`
* **Use Case**: Simplified facility-centric reporting without explicit state/district geographic hierarchy columns.

---

## 3. UI Ingestion Instructions

1. Log into CAREFlow as an **ADMIN** or **ANALYST** (`/imports`).
2. Navigate to the **HMIS Spreadsheet Ingestion** upload zone.
3. Drag and drop or browse to select the desired fixture file.
4. **Schema Profile Selection**: The CAREFlow backend incorporates an automated pre-flight profile detection engine (`SchemaProfileRegistry.detect_profile`).
   * When uploading `mohfw_valid_monthly_sample.csv`, the backend detects and binds `mohfw_standard_v2`.
   * The active profile is displayed in the UI progress banner as: `Schema Profile: mohfw_standard_v2`.
