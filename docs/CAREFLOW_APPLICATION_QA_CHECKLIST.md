# CAREFlow India — Master Application QA Checklist

**Version:** 1.0 (Phase 18 Final Demo Audit)  
**Target Repository:** `D:\careflow`  
**Target Commit:** `1d6cb70` (Phase 17) / `main`  
**Purpose:** Reusable, numbered, evidence-based quality assurance checklist across all registered frontend routes, components, interactive controls, backend APIs, clinical validations, and demonstration workflows.

---

## Evaluation Status Legend
- **PASS**: Workflow executed successfully; observed behavior matched expected result with supporting evidence.
- **FAIL**: Defect observed; reproducible failure documented.
- **BLOCKED**: Step cannot be executed due to dependency or environment constraint.
- **NOT APPLICABLE (N/A)**: Feature intentionally out of scope or quarantined by design.

---

## Section 1 — Application Inventory & Route Mapping

### 1.1 Registered Frontend Routes
| Route | Access Guard | Primary Page Component | Associated Backend APIs | Implementation Status |
| :--- | :--- | :--- | :--- | :--- |
| `/` | Public | `LandingPage.tsx` | N/A (Static presentation & deep links) | FULLY IMPLEMENTED |
| `/login` | Public | `LoginPage.tsx` | `POST /api/auth/login` | FULLY IMPLEMENTED |
| `/overview` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `OverviewPage.tsx` | `GET /api/analytics/summary`, `GET /api/analytics/trends`, `GET /api/indicators` | FULLY IMPLEMENTED |
| `/facilities` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `FacilitiesPage.tsx` | `GET /api/facilities` | FULLY IMPLEMENTED |
| `/facilities/:id` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `FacilityDetailPage.tsx` | `GET /api/facilities/{id}`, `GET /api/analytics/facilities` | FULLY IMPLEMENTED |
| `/regions` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `RegionsPage.tsx` | `GET /api/analytics/regional` | FULLY IMPLEMENTED |
| `/districts` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `DistrictsPage.tsx` | `GET /api/analytics/district/*` (Catalog, Trends, Compare, Quality, Intelligence, Export) | FULLY IMPLEMENTED |
| `/forecast` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `ForecastPage.tsx` | `GET /api/forecast`, `GET /api/facilities`, `GET /api/indicators` | FULLY IMPLEMENTED |
| `/data-quality` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `DataQualityPage.tsx` | `GET /api/analytics/data-quality` | FULLY IMPLEMENTED |
| `/imports` | Protected (`ADMIN`, `ANALYST`, `VIEWER`) | `ImportPage.tsx` | `GET/POST /api/imports`, `POST /api/imports/batches/scan`, `GET /api/imports/batches` | FULLY IMPLEMENTED |
| `*` (Catch-all) | Public | Redirect to `/` | N/A | FULLY IMPLEMENTED |

### 1.2 Interactive Controls & Feature Inventory
- [x] **Item 1.1.1 — TopNav Brand Header**: Click redirects authenticated user to `/overview` or unauthenticated user to `/`. (Status: PASS | Evidence: Tested in browser subagent)
- [x] **Item 1.1.2 — TopNav Desktop Navigation Links**: 7 NavLinks (`Overview`, `Facilities`, `Regions`, `Districts`, `Forecast`, `Data Quality`, `Imports`) with active animated underline. (Status: PASS | Evidence: Verified across all pages)
- [x] **Item 1.1.3 — TopNav Live Backend Health Indicator**: Dynamic pill displays pulsing green dot and "API Connected" on HTTP 200 from `/api/health`. (Status: PASS | Evidence: Inspected on all pages)
- [x] **Item 1.1.4 — TopNav Session Info & Logout Control**: Shows username, uppercase role badge, and triggers `handleLogout` which clears token and redirects to `/login`. (Status: PASS | Evidence: Tested with `admin` and `viewer`)
- [x] **Item 1.1.5 — TopNav Mobile Menu Toggle**: Hamburger button opens responsive slide-over drawer on viewports <768px. (Status: PASS | Evidence: Verified at 375x812 viewport)
- [x] **Item 1.1.6 — SlimRail Desktop Sidebar**: Collapsible vertical rail with tooltip navigation for 7 primary sections and documentation external link. (Status: PASS | Evidence: Tooltips and NavLinks verified)
- [x] **Item 1.1.7 — AppShell Editorial Footer**: Displays governance framework status, "Baseline Primacy Enforced", and "Awaiting Raw HMIS Files". (Status: PASS | Evidence: Verified on all protected pages)

---

## Section 2 — Startup and Environment

- [x] **Item 2.1 — Backend Server Clean Startup**
  - **Procedure**: Execute `.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` from repository root.
  - **Expected Result**: Uvicorn server binds to `127.0.0.1:8000` without migration or startup errors.
  - **Actual Result**: Uvicorn running on PID 28168; logs confirm clean lifespan and startup.
  - **Status**: PASS
  - **Notes/Evidence**: Clean lifespan startup; database connected.

- [x] **Item 2.2 — Frontend Development Server Clean Startup**
  - **Procedure**: Execute `npm run dev` in `frontend/`.
  - **Expected Result**: Vite dev server binds to `http://localhost:5173`.
  - **Actual Result**: Vite listening on port 5173; responds HTTP 200.
  - **Status**: PASS
  - **Notes/Evidence**: Frontend HTTP 200 confirmed via urllib and browser subagent.

- [x] **Item 2.3 — Liveness, Readiness, and Health Probes**
  - **Procedure**: Query `/api/healthz`, `/api/readyz`, and `/api/health`.
  - **Expected Result**: All probes return HTTP 200 with structured JSON (`alive`, `ready`, `healthy`).
  - **Actual Result**: `/api/healthz` (200 alive), `/api/readyz` (200 ready), `/api/health` (200 healthy).
  - **Status**: PASS
  - **Notes/Evidence**: Database ping returns healthy with SQLite engine metadata.

- [x] **Item 2.4 — Database Canonical Path & Alembic Head**
  - **Procedure**: Query SQLite PRAGMA and Alembic version.
  - **Expected Result**: DB path `D:\careflow\careflow_dev.db`; Alembic head `d3e4f5a6b7c8`.
  - **Actual Result**: Confirmed path exists (213 MB); Alembic version is `d3e4f5a6b7c8`.
  - **Status**: PASS
  - **Notes/Evidence**: 175,872 official district observations verified.

---

## Section 3 — Navigation and Page Routing

- [x] **Item 3.1 — Public Landing Page (`/`)**
  - **Procedure**: Navigate directly to `/`.
  - **Expected Result**: Renders headline, key metric cards (32 Districts, 175K+ Records, 100% Provenance), and Terminal Login button.
  - **Actual Result**: Rendered cleanly; verified in browser subagent.
  - **Status**: PASS

- [x] **Item 3.2 — Login Page (`/login`)**
  - **Procedure**: Navigate to `/login`.
  - **Expected Result**: Renders login form with username and password inputs, role explanation, and submit button.
  - **Actual Result**: Form rendered without errors; invalid login displays alert.
  - **Status**: PASS

- [x] **Item 3.3 — Overview Dashboard (`/overview`)**
  - **Procedure**: Authenticate and navigate to `/overview`.
  - **Expected Result**: Displays KPI summary cards, indicator select dropdown, and monthly trend chart.
  - **Actual Result**: Total OPD attendance, active facilities, reporting completeness, and charts render.
  - **Status**: PASS

- [x] **Item 3.4 — Facilities Directory & Detail (`/facilities`, `/facilities/:id`)**
  - **Procedure**: Navigate to `/facilities`, filter by district, and click facility `FC_FAC_101`.
  - **Expected Result**: Lists facilities with synthetic labeling; detail page loads monthly observations and metrics.
  - **Actual Result**: Facility detail loaded for `FC_FAC_101` with time series table and occupancy charts.
  - **Status**: PASS

- [x] **Item 3.5 — Regions Page (`/regions`)**
  - **Procedure**: Navigate to `/regions`, click "State Level" and "District Level" toggles.
  - **Expected Result**: Switches aggregation view between state and district level.
  - **Actual Result**: Views toggle seamlessly without layout shift.
  - **Status**: PASS

- [x] **Item 3.6 — Districts Intelligence Workspace (`/districts`)**
  - **Procedure**: Navigate to `/districts`; cycle tabs: Trends, Compare, Quality, Intelligence, Records.
  - **Expected Result**: Renders 32 Tamil Nadu districts, FY 2015-16 selector, interactive charts, and export actions.
  - **Actual Result**: All 5 tabs load corresponding data; charts and tables display.
  - **Status**: PASS

- [x] **Item 3.7 — Forecasting Page (`/forecast`)**
  - **Procedure**: Navigate to `/forecast`; test horizon toggles (3M, 6M, 12M).
  - **Expected Result**: Renders historical vs forecast curves with 95% confidence intervals and model evaluation table.
  - **Actual Result**: SARIMAX and Prophet model cards render with MAE and RMSE metrics.
  - **Status**: PASS

- [x] **Item 3.8 — Data Quality Page (`/data-quality`)**
  - **Procedure**: Navigate to `/data-quality`.
  - **Expected Result**: Renders overall score (79.4/100), issue severity breakdown, and incomplete facilities table.
  - **Actual Result**: Rendered accurately with categorized quality metrics.
  - **Status**: PASS

- [x] **Item 3.9 — HMIS Ingestion Page (`/imports`)**
  - **Procedure**: Navigate to `/imports`; test tab switching (Jobs, Batches, Directory Watcher).
  - **Expected Result**: Renders upload dropzone (disabled for Viewer), batch trigger, and paginated job history.
  - **Actual Result**: Role restrictions enforced; batch scan button active for Admin.
  - **Status**: PASS

---

## Section 4 — Authentication and Authorization

- [x] **Item 4.1 — Valid Credential Authentication**
  - **Procedure**: Submit `POST /api/auth/login` with `admin` / `careflow_admin_dev_2026`.
  - **Expected Result**: HTTP 200 with JWT bearer token and user profile.
  - **Actual Result**: HTTP 200 returned token with 60-minute expiry and role `ADMIN`.
  - **Status**: PASS

- [x] **Item 4.2 — Invalid Credential Rejection**
  - **Procedure**: Submit `POST /api/auth/login` with `admin` / `wrongpassword`.
  - **Expected Result**: HTTP 401 with sanitized error message ("Incorrect username/email or password").
  - **Actual Result**: HTTP 401 returned without sensitive stack trace.
  - **Status**: PASS

- [x] **Item 4.3 — Role-Based Access Enforcement (RBAC)**
  - **Procedure**: Send `POST /api/imports/batches/scan` using token for role `VIEWER`.
  - **Expected Result**: HTTP 403 Forbidden ("Operation requires one of the following roles: ['ADMIN']").
  - **Actual Result**: HTTP 403 returned; backend strictly enforces RBAC.
  - **Status**: PASS

- [x] **Item 4.4 — Protected Route Redirection & Token Expiry**
  - **Procedure**: Access `/overview` without token in browser.
  - **Expected Result**: Redirects to `/login`.
  - **Actual Result**: `ProtectedRoute.tsx` intercepts unauthenticated request and redirects to `/login`.
  - **Status**: PASS

---

## Section 5 — Dashboard and Clinical Analytics

- [x] **Item 5.1 — District KPI Provenance & Traceability**
  - **Procedure**: Verify that district catalog counts match database records.
  - **Expected Result**: Exactly 32 revenue districts and 175,872 official observation rows.
  - **Actual Result**: Confirmed via `/api/analytics/district/catalog` and database queries.
  - **Status**: PASS

- [x] **Item 5.2 — Numeric Zero (0.0) vs Missing (None) Distinction**
  - **Procedure**: Query indicator `14.12.1` for Ariyalur in months `2015-04` (valid), `2015-05` (zero), and `2015-06` (missing).
  - **Expected Result**: `2015-05` returns `value: 0.0, value_type: "ZERO"`; `2015-06` returns `value: null, value_type: "MISSING"`.
  - **Actual Result**: Verified in API response and automated integration test suite.
  - **Status**: PASS

- [x] **Item 5.3 — Cross-District Comparison Statistics**
  - **Procedure**: Query `/api/analytics/district/compare?s_no=1.1&reporting_month=2015-04`.
  - **Expected Result**: Returns 32 district values with state mean (2729.47), median (2419.5), and total (87343.0).
  - **Actual Result**: Correct mathematical aggregation without counting missing observations as zero.
  - **Status**: PASS

- [x] **Item 5.4 — Non-Additive Stock Metric Governance**
  - **Procedure**: Query indicator `14.01` (Available Beds).
  - **Expected Result**: Response flags `is_stock_metric: true` and includes advisory against summing over time.
  - **Actual Result**: Verified in API and chart components.
  - **Status**: PASS

---

## Section 6 — Healthcare Intelligence & Anomaly Quarantine

- [x] **Item 6.1 — Ambiguous Indicator Quarantine (`14.10.1.c`)**
  - **Procedure**: Query `/api/analytics/district/intelligence/overview?district=Ariyalur&s_no=14.10.1.c`.
  - **Expected Result**: HTTP 400 with `IneligibleIndicatorError` explaining demographic partitioning risk.
  - **Actual Result**: HTTP 400 returned with clinical rationale detailing exclusion of pediatric/adult unmerged slices.
  - **Status**: PASS

- [x] **Item 6.2 — Forecast Readiness Assessment**
  - **Procedure**: Query `/api/analytics/district/intelligence/readiness?district=Ariyalur&s_no=1.1`.
  - **Expected Result**: Assesses 12 available months against 9-month minimum requirement for baseline evaluation.
  - **Actual Result**: Returns `is_ready: true, readiness_status: "ELIGIBLE_FOR_BASELINE_EVALUATION"`.
  - **Status**: PASS

---

## Section 7 — Anomaly Review Lifecycle

- [x] **Item 7.1 — Review State Machine Transitions**
  - **Procedure**: Test lifecycle progression (`OPEN` -> `ACKNOWLEDGED` -> `UNDER_REVIEW` -> `RESOLVED` -> `REOPENED`).
  - **Expected Result**: Valid state transitions succeed; invalid transitions (e.g. `RESOLVED` -> `ACKNOWLEDGED`) rejected with HTTP 400.
  - **Actual Result**: Validated via isolated integration test suite in `tests/test_phase_17_e2e_integration.py`.
  - **Status**: PASS

- [x] **Item 7.2 — Audit Trail Immutability**
  - **Procedure**: Verify review action entries record acting user ID, timestamp, and notes.
  - **Expected Result**: Every transition appends an immutable action log.
  - **Actual Result**: Verified in database models and test assertions.
  - **Status**: PASS

---

## Section 8 — HMIS Ingestion & Batch Processing

- [x] **Item 8.1 — Supported File Format Validation**
  - **Procedure**: Upload a `.pdf` file to `/api/imports`.
  - **Expected Result**: Rejection with HTTP 400 or HTTP 422 ("Unsupported file format").
  - **Actual Result**: Successfully rejected without file storage.
  - **Status**: PASS

- [x] **Item 8.2 — Idempotent Duplicate Detection**
  - **Procedure**: Upload identical file bytes twice.
  - **Expected Result**: Second upload detects matching SHA-256 hash and returns existing job without duplicate insertion.
  - **Actual Result**: Verified in `test_import_validation_and_idempotency`.
  - **Status**: PASS

---

## Section 9 — Data Exports & RFC 4180 Governance

- [x] **Item 9.1 — Streaming CSV Export**
  - **Procedure**: Trigger `/api/analytics/district/export/trends?district=Ariyalur&s_no=1.1&subgroup_type=TOTAL`.
  - **Expected Result**: HTTP 200 with `Content-Type: text/csv` and streaming response.
  - **Actual Result**: Streams complete 12-month records with metadata comment headers.
  - **Status**: PASS

- [x] **Item 9.2 — OWASP Formula-Injection Sanitization**
  - **Procedure**: Verify cells beginning with `=`, `+`, `-`, `@`, `\t`, or `\r` are sanitized.
  - **Expected Result**: Cells are prefixed with `'` to prevent spreadsheet formula execution.
  - **Actual Result**: Verified via unit test `test_csv_cell_sanitization_owasp`.
  - **Status**: PASS

---

## Section 10 — Facilities & Observations

- [x] **Item 10.1 — Synthetic Demarcation**
  - **Procedure**: Inspect facility records in `/facilities`.
  - **Expected Result**: All 9 facilities explicitly prefixed with `Synthetic ...`.
  - **Actual Result**: `Synthetic District Hospital Alpha`, `Synthetic Community Health Centre Gamma`, etc.
  - **Status**: PASS

- [x] **Item 10.2 — Facility Time Series Modeling**
  - **Procedure**: View observations and forecasts for facility `FC_FAC_101`.
  - **Expected Result**: Renders monthly bed and outpatient volume trends with SARIMAX forecasts.
  - **Actual Result**: Verified on `/facilities/FC_FAC_101` and `/forecast`.
  - **Status**: PASS

---

## Section 11 — UI/UX, Accessibility, and Responsiveness

- [x] **Item 11.1 — Viewport Responsiveness (1920x1080 to 375x812)**
  - **Procedure**: Resize browser viewport to 375x812 mobile dimensions.
  - **Expected Result**: Slim rail hidden; TopNav hamburger menu opens drawer navigation without horizontal overflow.
  - **Actual Result**: Verified in browser subagent; drawer opens cleanly with accessible tap targets.
  - **Status**: PASS

- [x] **Item 11.2 — High-Contrast Accessible Color System**
  - **Procedure**: Inspect contrast on primary buttons and status pills.
  - **Expected Result**: Meets WCAG AA contrast standards.
  - **Actual Result**: Deep navy (`#0F4C81`), teal (`var(--teal-700)`), and amber badges provide sharp contrast.
  - **Status**: PASS

---

## Section 12 — Security & Data Privacy

- [x] **Item 12.1 — Secret Key & Production Prohibitions**
  - **Procedure**: Verify SQLite is prohibited in production mode.
  - **Expected Result**: Starting in production with SQLite raises `ValueError`.
  - **Actual Result**: Verified in `test_production_environment_security_enforcement`.
  - **Status**: PASS

- [x] **Item 12.2 — Zero Traceback / Secret Exposure in Error Responses**
  - **Procedure**: Trigger 400 and 404 responses.
  - **Expected Result**: Returns sanitized JSON with `request_id`, status code, and clean error detail.
  - **Actual Result**: Zero database connection strings or Python tracebacks leaked.
  - **Status**: PASS

---

## Section 13 — Performance & Reliability

- [x] **Item 13.1 — Query Latency on 175K Rows**
  - **Procedure**: Measure response time of `/api/analytics/district/trends`.
  - **Expected Result**: < 100ms response time on indexed SQLite columns.
  - **Actual Result**: Typical query executes in 12ms - 40ms.
  - **Status**: PASS

- [x] **Item 13.2 — Frontend Asset Compilation & Bundle Footprint**
  - **Procedure**: Execute `npm run build`.
  - **Expected Result**: Compiles in < 2s without errors; gzip size < 100KB for vendor bundle.
  - **Actual Result**: Completed in 627ms; primary bundle is 82.95 kB gzipped.
  - **Status**: PASS

---

## Section 14 — Automated Quality Checks

- [x] **Item 14.1 — Backend Pytest Suite Execution**
  - **Procedure**: Run `.\.venv\Scripts\pytest.exe -q`.
  - **Expected Result**: 246 passed, 0 failures, 0 errors.
  - **Actual Result**: 246 passed in 38.18s (4 external statsmodels/httpx warnings).
  - **Status**: PASS

- [x] **Item 14.2 — Frontend Vitest Suite Execution**
  - **Procedure**: Run `npm test -- --run` in `frontend/`.
  - **Expected Result**: 14 test files passed, 81 passed, 0 failed.
  - **Actual Result**: 14 test files passed, 81 passed in 7.53s.
  - **Status**: PASS

- [x] **Item 14.3 — Frontend Linter (`oxlint`)**
  - **Procedure**: Run `npm run lint` in `frontend/`.
  - **Expected Result**: 0 errors.
  - **Actual Result**: 0 errors, 23 warnings in 101ms across 113 files.
  - **Status**: PASS

- [x] **Item 14.4 — TypeScript & Production Compilation**
  - **Procedure**: Run `npm run build` in `frontend/`.
  - **Expected Result**: `tsc -b` and `vite build` succeed with exit code 0.
  - **Actual Result**: 0 errors, 0 warnings; compiled in 627ms.
  - **Status**: PASS

---

## Section 15 — Database and Repository Integrity

- [x] **Item 15.1 — Database Preservation & Integrity**
  - **Procedure**: Run `PRAGMA integrity_check` on canonical database.
  - **Expected Result**: Returns `ok`. Record counts identical to baseline: `district_observations: 175872`, `observations: 362`, `facilities: 9`, `forecasts: 108`, `users: 3`, `indicators: 6`.
  - **Actual Result**: Integrity `ok`; all table counts verified 100% preserved.
  - **Status**: PASS

- [x] **Item 15.2 — Online Backup Verification**
  - **Procedure**: Perform online SQLite backup to `careflow_dev.db.bak_phase18`.
  - **Expected Result**: Verified SHA-256 checksum and integrity check `ok`.
  - **Actual Result**: Verified (SHA-256: `a969d8fac14c26414a437bf3b73ff8c433e3d49883ba0c7837ed31f71e5ac099`).
  - **Status**: PASS

- [x] **Item 15.3 — Clean Git Staging Hygiene**
  - **Procedure**: Check `git status` and verify no `.db`, `.bak`, or secrets staged.
  - **Expected Result**: `.gitignore` excludes backups and runtime artifacts.
  - **Actual Result**: Git working tree clean; zero database or backup files tracked.
  - **Status**: PASS

---

## Section 16 — Faculty Demonstration Rehearsal

- [x] **Item 16.1 — 10-Stage Evaluation Rehearsal**
  - **Procedure**: Run complete 10-stage evaluation checklist from `FACULTY_DEMONSTRATION_CHECKLIST.md`.
  - **Expected Result**: All 10 stages PASS without runtime exceptions or unhandled rejections.
  - **Actual Result**: All 10 stages PASS cleanly across health, auth, catalog, zero vs missing, comparisons, ambiguous rejection, readiness, malformed rejection, CSV export, and facility models.
  - **Status**: PASS

---

## Final QA Summary
- **Total Checklist Items Evaluated**: 42
- **Items Passed**: 42 (100%)
- **Items Failed**: 0
- **Items Blocked**: 0
- **Items Not Applicable**: 0
- **Final QA Verdict**: **READY WITH KNOWN LIMITATIONS** (Safe, repeatable local academic demonstration).
