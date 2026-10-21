# CAREFlow India — Faculty Demonstration Checklist & Verification Protocol

## Executive Summary & System Overview
**CAREFlow India** is a clinical healthcare intelligence, analytics, and epidemiological surveillance platform tailored for public health administrations in India.

This document serves as the **official demonstration guide and verification checklist** for faculty evaluators, technical reviewers, and administrative stakeholders. It provides a structured 10-stage walkthrough covering authentication, role-based governance, official district administrative returns, time-series forecasting, statistical anomaly detection, and data ingestion rollback.

---

## Mandatory Ethical & Data Integrity Disclosure

> [!IMPORTANT]
> **Data Tier Demarcation**:
> 1. **Official State HMIS Data Tier (`district_observations`)**:
>    * Contains **175,872 consolidated administrative records** across all **32 revenue districts** of Tamil Nadu for **Financial Year 2015–16** (April 2015 through March 2016).
>    * Sourced from official MoHFW / National Health Mission (NHM) Tamil Nadu State Performance Report archives.
>    * Zero synthetic observations have been added to this tier. Missing values are preserved verbatim and strictly segregated from genuine zeros.
> 2. **Facility Demonstration Tier (`facilities`, `observations`, `forecasts`)**:
>    * Contains **9 facilities**, **362 monthly observations**, and **108 ML forecasts** designed to demonstrate micro-level facility time-series modeling.
>    * All facility records are explicitly prefixed with `Synthetic` or `SYNTHETIC` to eliminate any risk of conflating mock facility profiles with official district returns.
>    * In accordance with platform governance rules, district administrative returns and facility clinical observations are structurally separated in distinct database tables.

---

## Pre-Demonstration Verification Checklist

Run these terminal checks prior to starting the presentation to verify system health:

```powershell
# 1. Database Integrity & Record Verification
python -c "
import sqlite3
con = sqlite3.connect('careflow_dev.db')
print('SQLite PRAGMA Integrity:', con.execute('PRAGMA integrity_check;').fetchall())
tables = ['district_observations', 'observations', 'facilities', 'forecasts', 'users', 'import_jobs']
for t in tables:
    cnt = con.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    print(f'Table {t}: {cnt} rows')
con.close()
"
```
**Expected Output**:
* SQLite PRAGMA Integrity: `[('ok',)]`
* `district_observations`: `175872` rows
* `observations`: `362` rows
* `facilities`: `9` rows
* `forecasts`: `108` rows
* `users`: `3` rows (`admin`, `analyst`, `viewer`)

```powershell
# 2. Database Migration Head
python -m alembic current
```
**Expected Output**: `d3e4f5a6b7c8 (head)`

```powershell
# 3. Backend Test Suite Execution
pytest -q
```
**Expected Output**: `246 passed, 4 warnings in ~38s`

```powershell
# 4. Frontend Production Test Suite
cd frontend; npm test -- --run
```
**Expected Output**: `14 passed (14 test files, 81 passed in ~7.5s)`

---

## 10-Stage Demonstration Protocol

### Stage 1: System Health Probes & API Gateway
* **Goal**: Demonstrate enterprise container readiness and observability.
* **Action**:
  1. Navigate to `http://127.0.0.1:8000/api/healthz` (Liveness probe: returns `{"status": "alive"}`).
  2. Navigate to `http://127.0.0.1:8000/api/readyz` (Readiness probe: validates database connectivity, returns `{"status": "ready"}`).
  3. Navigate to `http://127.0.0.1:8000/api/health` (Health metadata: returns service name, version, and database status).
  4. Open Swagger documentation at `http://127.0.0.1:8000/docs` to review endpoint contracts.

### Stage 2: Authentication & Role-Based Access Control (RBAC)
* **Goal**: Validate security segregation across administrative roles.
* **Development Demonstration Credentials**:
  * `admin` / `careflow_admin_dev_2026` (ADMIN: unrestricted administrative & ingestion operations)
  * `analyst` / `careflow_analyst_dev_2026` (ANALYST: operational analytics, reviews & exports)
  * `viewer` / `careflow_viewer_dev_2026` (VIEWER: read-only inspection)
* **Verification Steps**:
  1. Open `http://localhost:5173/login`.
  2. Log in as `viewer`. Notice the header badge indicates `VIEWER Session`.
  3. Navigate to **HMIS Ingestion Workspace** (`/imports`).
  4. Verify the amber restriction banner: *"Read-Only Access Restricted — Your account role (VIEWER) has permission to inspect historical imports, quality scorecards, and audit logs, but cannot upload new datasets."*
  5. Log out and log in as `admin` to verify upload zone is active and accessible.

### Stage 3: Official District Healthcare Intelligence Workspace
* **Goal**: Demonstrate official administrative returns across Tamil Nadu districts.
* **Navigation**: Navigate to `/districts` tab **Monthly Trends**.
* **Filter Controls**:
  * District: `Ariyalur`
  * Indicator: `14.12.1 — Outpatient attendance - All`
  * Subgroup: `TOTAL`
  * Financial Year: `2015-16`
* **Verification Points**:
  * Header clearly indicates: `Official State HMIS Returns | Jurisdiction: District | FY 2015–16 (12 Months)`.
  * Amber notice emphasizes data architecture separation: district administrative data is never combined or averaged with facility data.
  * Graph displays 12 monthly observations (April 2015 through March 2016).

### Stage 4: Zero vs. Missing Data Integrity & Non-Additive Stock Metrics
* **Goal**: Verify clinical data fidelity: genuine zeroes must never be conflated with missing returns.
* **Verification Steps**:
  1. Inspect the Monthly Trends table and cards in `/districts`.
  2. Note how months with numeric zero report `0` with green `Valid Zero` badge.
  3. Note how unrecorded months display `Missing / Unreported` with amber badge.
  4. Select indicator `14.01 — Available Beds`: notice the `Non-Additive Stock Metric` badge. Annual summation is disabled because capacity counts cannot be summed across months.

### Stage 5: Cross-District Comparison & Spatial Rankings
* **Goal**: Demonstrate macro epidemiological comparison across all 32 revenue districts.
* **Navigation**: Click tab **District Comparison** on `/districts`.
* **Controls**:
  * S.No.: `14.12.1` (Outpatient Attendance)
  * Reporting Period: `2015-06`
  * Subgroup: `TOTAL`
* **Verification Points**:
  * Bar chart compares all 32 districts with calculated State Mean, Median, and Total.
  * Sort options allow descending, ascending, or alphabetical ordering.
  * Districts with missing values are placed at the end without breaking summary statistics.

### Stage 6: RFC 4180 Streaming CSV Export & Formula-Injection Defense
* **Goal**: Verify government audit export standards and security protection against CSV macro injection.
* **Verification Steps**:
  1. On the District Monthly Trends view, click **Export RFC 4180 CSV**.
  2. Open the downloaded file `district_trends_ariyalur_14_12_1.csv` in a text editor.
  3. Verify top provenance header lines:
     ```csv
     # CAREFlow India — District HMIS Observations Export
     # Source: MoHFW / NHM Tamil Nadu State Performance Report Archives
     # District: Ariyalur | Indicator S.No: 14.12.1
     # Integrity Rule: Missing values are represented as empty cells; numeric zero is represented as '0'.
     ```
  4. Verify that missing values are empty strings `""` while zero is `"0"`.
  5. Note OWASP formula injection protection: any field starting with `=`, `+`, `-`, `@`, `\t`, or `\r` is escaped with a leading `'`.

### Stage 7: Clinical Indicator Registry & Explicit Ambiguity Governance
* **Goal**: Show that ambiguous indicators are explicitly quarantined rather than silently treated as authoritative.
* **Navigation**: Click tab **Quality & Provenance** on `/districts`, scroll to **Verified Indicator Registry**.
* **Key Observations**:
  * **Verified Indicators** (`1.1` ANC Visits, `2.2` Institutional Deliveries, `14.12.1` OPD Attendance): Linked to canonical IDs with clinical definitions and rationales.
  * **Ambiguous Indicator (`14.10.1.c` Inpatient Admissions)**:
    * Marked with amber **AMBIGUOUS** badge.
    * Explicit rationale explains that in official state returns, this parameter is partitioned into demographic age slices (*Children* and *Adults*) without an authoritative unified total row.
    * The platform refuses to map this directly to canonical `IND_inpatient_admissions`, preventing partial pediatric-only counts from misleading administrators.

### Stage 8: Healthcare Intelligence & Single-Year Forecast Readiness
* **Goal**: Evaluate machine learning readiness under strict scientific standards.
* **Navigation**: Click tab **Intelligence & Early Warning** on `/districts`.
* **Key Observations**:
  * Select District: `Ariyalur`, Indicator: `1.1 — Antenatal Care (ANC) Registered Visits`.
  * **Single-Year Dataset Limitation Banner**: The system explicitly warns that 12 monthly data points are sufficient only for short-term (1–3 month) baseline evaluations.
  * **Hold-Out Split**: 9 months train (April–December 2015), 3 months hold-out test (January–March 2016). Zero future-data leakage.
  * **Model Evaluation**: Naïve Forecaster and Moving Average baselines are evaluated against hold-out ground truth with MAE, RMSE, and WAPE metrics.
  * **Ineligible Indicator Defense**: Attempting to query intelligence on ambiguous indicator `14.10.1.c` is rejected by the backend with HTTP 400 (`IneligibleIndicatorError`), demonstrating rigorous scientific guardrails.

### Stage 9: Administrative Anomaly Review State Machine
* **Goal**: Demonstrate operational review, human-in-the-loop audit, and status transitions.
* **Navigation**: In **Intelligence & Early Warning**, scroll to **Statistical Anomaly & Operational Change Signals**.
* **Verification Steps**:
  1. Inspect detected MAD outliers (>3.5 modified z-score) and abrupt MoM shift signals.
  2. Every signal displays the required disclaimer: `STATISTICAL_SIGNAL — Requires human review; not a clinical diagnosis`.
  3. Click **Review & Audit** on a signal.
  4. Execute status transition: `OPEN` $\rightarrow$ `ACKNOWLEDGED` $\rightarrow$ `UNDER_REVIEW` $\rightarrow$ `RESOLVED`.
  5. Add audit notes. Verify that the action log permanently captures the username, timestamp, and transition note.
  6. Attempt an invalid transition (e.g. attempting to resolve without reopening) to demonstrate server-side validation error rejection.

### Stage 10: HMIS File Ingestion, Idempotency & Safe Rollback
* **Goal**: Demonstrate automated spreadsheet ingestion, deduplication, and atomic rollback.
* **Navigation**: Navigate to `/imports`.
* **Verification Steps**:
  1. Drag and drop a valid HMIS spreadsheet (or click upload).
  2. Observe background ingestion worker polling and progress bar update.
  3. Re-upload the identical spreadsheet: observe SHA-256 idempotency check preventing duplicate record insertion.
  4. Click **Inspect Quality**: view 13-point automated data quality scorecard.
  5. (Admin only) Click **Rollback**: supply a rollback reason and execute atomic deletion with audit log recording.

---

## Metric Verification Reference

| Indicator Code / S.No. | Parameter Name | Canonical Mapping | Classification | Data Stream | Record Count |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`1.1`** | Total pregnant women registered for ANC | `IND_antenatal_visits` | **VERIFIED** | District HMIS | 384 rows (32 dist × 12 mo) |
| **`2.2`** | Institutional deliveries (Public Facilities) | `IND_institutional_deliveries` | **VERIFIED** | District HMIS | 384 rows |
| **`6.1`** | Post-partum check-up within 48 hours | `IND_postnatal_visits` | **VERIFIED** | District HMIS | 384 rows |
| **`10.1.13.c`** | Fully immunised children (9-11 months) | `IND_immunisation` | **VERIFIED** | District HMIS | 384 rows |
| **`14.10.1.c`** | Total inpatient admissions | — | **AMBIGUOUS** | District HMIS | Quarantined (Subgroup age slice) |
| **`14.12.1`** | Outpatient attendance (All services) | `IND_opd_attendance` | **VERIFIED** | District HMIS | 384 rows |
| **`14.01`** | Available Inpatient Beds | — | **STOCK METRIC** | District HMIS | Non-additive bed count |
| **`FAC_1001.0`** | Synthetic District Hospital Alpha | — | **SYNTHETIC** | Facility Micro | 362 observations |

---

## Known Operational Scope & Academic Roadmap
1. **Single-Year District Scope**: The ingested official dataset covers FY 2015–16 (12 months). Multi-year datasets (FY 2016–17 and FY 2017–18) are cataloged in the Source Registry with status `BLOCKED_MISSING_OFFICIAL_FILE` pending acquisition from the MoHFW HMIS portal.
2. **Seasonal Decomposition & Advanced ML**: 12 monthly data points are scientifically insufficient for multi-year seasonal decomposition (STL/SARIMA requires $\ge 24$ months). The platform enforces this boundary by offering single-year naïve/moving-average baselines while reserving deep recurrent neural networks for multi-year data.
3. **Data Protection**: Official government records in `careflow_dev.db` must never be dropped, truncated, or overwritten.
