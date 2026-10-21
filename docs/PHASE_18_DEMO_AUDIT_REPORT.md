# Phase 18 Final Demo Audit & Reproducibility Report
**CAREFlow India: Full Application QA, End-to-End Validation & Faculty Demonstration Readiness**

**Repository:** `D:\careflow`  
**Branch:** `main`  
**Starting Commit:** `1d6cb70` (Phase 17)  
**Evaluation Date:** October 22, 2026  
**Final Status:** **READY WITH KNOWN LIMITATIONS** (Local Academic Demonstration Ready)

---

## 1. Executive Summary & Audit Scope

Phase 18 executed an evidence-based, end-to-end quality assurance audit and demonstration readiness evaluation of the CAREFlow India platform. The objective was to verify that the entire application operates correctly from a real user's perspective across the React frontend and FastAPI backend, validating clinical data integrity, security controls, and demonstration workflows without altering or compromising existing records.

### Key Audit Outcomes
- **10 of 10 Faculty Demonstration Stages Passed**: Rehearsed and verified all stages from `docs/FACULTY_DEMONSTRATION_CHECKLIST.md`.
- **42 of 42 Master QA Checklist Items Passed**: Evaluated in `docs/CAREFLOW_APPLICATION_QA_CHECKLIST.md`.
- **Database 100% Preserved**: Canonical SQLite database `careflow_dev.db` verified before and after audit (`PRAGMA integrity_check = ok`); exact record counts maintained (175,872 official district observations).
- **Online Backup Created & Verified**: `careflow_dev.db.bak_phase18` verified via SQLite backup API (SHA-256: `a969d8fac14c26414a437bf3b73ff8c433e3d49883ba0c7837ed31f71e5ac099`).
- **Complete Test Suites Passed**:
  - Backend Pytest Suite: **246 passed, 0 failures, 0 errors** (4 external warnings).
  - Frontend Vitest Suite: **81 passed across 14 test files, 0 failed**.
  - Frontend Static Linter (`oxlint`): **0 errors**, 23 warnings.
  - Production Build (`vite build`): **0 errors, 0 warnings** (compiled in 627ms).
- **Interactive Browser Testing Completed**: Automated browser sessions tested all pages, forms, modals, tabs, mobile drawer (375×812), and role-based workflows with session video artifacts recorded.

---

## 2. Demonstration Stages Outcome Matrix

| Stage | Verification Objective | Expected Result | Actual Result | Status |
| :---: | :--- | :--- | :--- | :---: |
| **1** | **Health & Readiness Probes** | `/api/healthz` (200 alive), `/api/readyz` (200 ready), `/api/health` (200 healthy). | HTTP 200 returned on all probes with database ping healthy. | **PASS** |
| **2** | **Authentication & RBAC Enforcement** | `admin` (full write), `analyst` (analysis/ingest), `viewer` (read-only). Direct API write by `viewer` returns HTTP 403. | Login succeeded for all 3 roles; `POST /api/imports/batches/scan` as `viewer` rejected with HTTP 403 Forbidden. | **PASS** |
| **3** | **Official District Catalog & FY Filters** | 32 revenue districts of Tamil Nadu returned with FY 2015–16 metadata and scope limitations. | 32 districts returned; 175,872 observations verified; FY 2015–16 temporal filters functional. | **PASS** |
| **4** | **Numeric Zero (0.0) vs Missing (None)** | Zero observations (`value_type="ZERO"`) distinct from unrecorded observations (`value_type="MISSING"`). | Month 2015-05 returned `value: 0.0, value_type: "ZERO"`; Month 2015-06 returned `value: null, value_type: "MISSING"`. | **PASS** |
| **5** | **Cross-District Comparison & Stock Metrics** | 32 districts compared on indicator `1.1`; state mean (2729.47), median (2419.5), total (87343.0). Non-additive stock flag on `14.01`. | Correct statistical calculations; stock metrics flagged with `is_stock_metric: true`. | **PASS** |
| **6** | **Ambiguous Indicator Quarantine (`14.10.1.c`)** | Intelligence overview/readiness reject `14.10.1.c` with HTTP 400 (`IneligibleIndicatorError`). | HTTP 400 returned with clinical rationale detailing demographic partitioning risk. | **PASS** |
| **7** | **Forecast Readiness & Anomaly Review** | 12 reporting months evaluated against 9-month threshold (`ELIGIBLE_FOR_BASELINE_EVALUATION`). Review state machine valid. | Returns `is_ready: true`; state transitions (`OPEN` -> `ACKNOWLEDGED` -> `UNDER_REVIEW` -> `RESOLVED`) pass. | **PASS** |
| **8** | **Rejection of Malformed HMIS Uploads** | Non-spreadsheet upload rejected without persistent side-effects or storage leaks. | Upload rejected with HTTP 422/400; zero corrupt records written. | **PASS** |
| **9** | **CSV Export & Formula-Injection Mitigation** | Streaming RFC 4180 CSV export; cells starting with `=`, `+`, `-`, `@`, `\t`, `\r` sanitized with `'`. | Export returned valid CSV with metadata headers and sanitized formula cells. | **PASS** |
| **10** | **Synthetic Facility-Level Modeling** | Facility-level bed and patient forecasts isolated from district returns and clearly labelled synthetic. | 9 facilities prefixed with `Synthetic ...`; occupancy models isolated from official district returns. | **PASS** |

---

## 3. Discovered Application Surface & Browser Testing

### 3.1 Application Surface
- **Total Frontend Routes Discovered**: 10 distinct routes + 1 catch-all (`/`, `/login`, `/overview`, `/facilities`, `/facilities/:id`, `/regions`, `/districts`, `/forecast`, `/data-quality`, `/imports`, `*`).
- **Total Frontend Routes Tested in Browser**: 10 of 10 routes (100% route coverage).
- **Interactive Controls Audited**: 42 controls including TopNav navigation links, live health indicator, role badges, mobile hamburger drawer, SlimRail sidebar, tab switches, dropdown selectors, horizon filters, CSV export triggers, and modal dialogs.

### 3.2 Browser UI Validation Artifacts
Browser interactions were executed on the live frontend (`http://localhost:5173`) using automated browser sessions. Full recordings of interactive testing sessions were captured:
- **Session 1 Recording**: `phase18_ui_audit_1792611495566.webp` (Landing, Invalid login rejection, Admin authentication, Overview dashboard, Districts workspace).
- **Session 2 Recording**: `phase18_ui_audit_p2_1792611746271.webp` (Facilities directory & detail, Regions level toggle, Forecasting horizon controls, Data Quality scorecard, HMIS Ingestion workspace, Mobile 375×812 viewport drawer, Logout flow).

---

## 4. Root Cause Analysis & Defect Remediation

### Defect 1: Full Test Suite Worker Race Condition
- **Symptom**: During full suite execution (`pytest -q`), `test_upload_valid_xlsx` and `test_missing_and_zero_preservation` failed intermittently with `'PROCESSING'` status.
- **Root Cause**: `settings.ENVIRONMENT` defaulted to `"development"` during test execution. In `backend/app/main.py`, the lifespan handler spawned an asynchronous background worker thread (`_worker_thread`) during `TestClient` creation unless `settings.ENVIRONMENT.lower() == "testing"`. The concurrent background thread competed with Starlette's synchronous background tasks on the single in-memory SQLite connection (`StaticPool`), resulting in race conditions.
- **Remediation**: In `tests/conftest.py`, explicitly configured `settings.ENVIRONMENT = "testing"` and `settings.ENABLE_IMPORT_WORKER = False` for all test sessions.
- **Verification**: Full suite execution (`pytest -q`) immediately passed all **246 of 246 tests** in 38.18s without failures.

---

## 5. Review of Code Quality & Warnings

### Backend Warnings (4 Total)
1. **StarletteDeprecationWarning** (`fastapi/testclient.py:1`):
   - *Message*: `StarletteDeprecationWarning: Using 'httpx' with 'starlette.testclient' is deprecated; install 'httpx2' instead.`
   - *Analysis*: Upstream warning from Starlette's internal testclient module importing httpx. Safe to leave unmodified; updating dependencies would violate safety rules.
2. **Statsmodels MLE ConvergenceWarning** (`statsmodels/tsa/statespace/mlemodel.py:737`):
   - *Message*: `ConvergenceWarning: Maximum Likelihood optimization failed to converge.`
   - *Analysis*: Occurs during SARIMAX parameter estimation on synthetic 12-month test fixtures. Expected behavior for short sample sizes; statistically sound.
3. **Statsmodels Seasonal ARMA EstimationWarning** (`statsmodels/tsa/statespace/sarimax.py:1022`):
   - *Message*: `EstimationWarning: Too few observations to estimate starting parameters for seasonal ARMA.`
   - *Analysis*: Expected behavior on short synthetic series; statsmodels gracefully falls back to zero-variance initialization.

### Frontend Lint Warnings (23 Total)
- All 23 warnings generated by `oxlint` are `react(set-state-in-effect): Calling setState synchronously within an effect can trigger cascading renders`.
- *Analysis*: React Compiler strict advisory warnings in data-fetching effects (e.g. `setLoading(true)`). As directed by project instructions, warnings are transparently documented rather than suppressed with unsafe refactoring.

---

## 6. Database Preservation & Integrity Verification

A strict pre- and post-audit verification was conducted on `D:\careflow\careflow_dev.db`:

```
========================================================================
METRIC / TABLE                     PRE-AUDIT COUNT     POST-AUDIT COUNT
========================================================================
Database Size                      213 MB              213 MB
PRAGMA integrity_check             ok                  ok
Alembic Migration Version          d3e4f5a6b7c8        d3e4f5a6b7c8
district_observations (Official)   175,872             175,872
import_observation_records         351,764             351,764
observations (Synthetic Facility)  362                 362
facilities (Synthetic Facility)    9                   9
forecasts (ML Series)              108                 108
users (Role Accounts)              3                   3
indicators (Catalog Items)         6                   6
import_batches                     0                   0
========================================================================
```
- **Integrity**: Zero records added, dropped, modified, or truncated in canonical tables.
- **Backup Snapshot**: `careflow_dev.db.bak_phase18` verified (SHA-256: `a969d8fac14c26414a437bf3b73ff8c433e3d49883ba0c7837ed31f71e5ac099`).
- **Git Hygiene**: `.gitignore` excludes `*.bak` and `*.bak*`; `git status` verifies no database or backup artifacts staged.

---

## 7. Clean Startup & Failure Recovery Procedures

### Clean Startup (Fresh Terminals)

**Terminal 1 — Backend API:**
```powershell
cd D:\careflow
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```
- Verified Health Probe: `http://127.0.0.1:8000/api/healthz`
- Interactive API Docs: `http://127.0.0.1:8000/docs`

**Terminal 2 — Frontend Application:**
```powershell
cd D:\careflow\frontend
npm run dev
```
- User Interface: `http://localhost:5173`

### Development Demonstration Credentials
- **Administrator**: `admin` / `careflow_admin_dev_2026` (Full system and batch scan permissions)
- **District Analyst**: `analyst` / `careflow_analyst_dev_2026` (Analytics, comparisons, anomaly review)
- **Auditor / Viewer**: `viewer` / `careflow_viewer_dev_2026` (Read-only inspection)

### Safe Recovery from Common Startup Errors
If port binding conflicts or stale processes occur:
1. **Identify Stale Process**:
   ```powershell
   Get-NetTCPConnection -LocalPort 8000,5173 -ErrorAction SilentlyContinue | Select-Object LocalPort,OwningProcess
   ```
2. **Terminate Only Stale Process**:
   ```powershell
   Stop-Process -Id <PID> -Force
   ```
3. **Database Lock Release**:
   Do NOT delete `careflow_dev.db`. Check for temporary lock files (`careflow_dev.db-wal` or `careflow_dev.db-shm`) and restart the backend cleanly.
4. **Verify Database Integrity**:
   ```powershell
   python -c "import sqlite3; con=sqlite3.connect('careflow_dev.db'); print(con.execute('PRAGMA integrity_check;').fetchone()[0])"
   ```

---

## 8. Clinical Data Demarcation & Known Limitations

> [!CAUTION]
> **Academic Demonstration & Evaluation Boundaries**:
> 1. **Temporal Horizon Constraint**: Official HMIS observations strictly represent historical administrative returns from Tamil Nadu for **Financial Year 2015–16** (April 2015 to March 2016). They must not be utilized for real-time clinical decisions.
> 2. **Facility Modeling Insulation**: Facility-level time series (9 facilities, 362 observations) are synthetic fixtures created to demonstrate bed capacity and admissions forecasting. They must never be described as real hospital data.
> 3. **Non-Additive Stock Indicators**: Instantaneous inventory/capacity indicators (e.g., available beds) must not be summed cumulatively across time periods.
> 4. **Quarantine of Ambiguous Indicators**: Indicator `14.10.1.c` is strictly quarantined from trusted intelligence summaries because official state returns partition it into demographic slices without an authoritative total.
> 5. **Local Demonstration Only**: The platform is configured for local evaluation (`localhost:8000` / `localhost:5173`) and is not approved or certified for public internet deployment or clinical operation.
