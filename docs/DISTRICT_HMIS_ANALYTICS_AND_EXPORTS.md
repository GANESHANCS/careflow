# District HMIS Analytics, Verified Indicator Crosswalk, and Export Architecture

- **Document Version:** 1.0.0
- **Phase Coverage:** CAREFlow India Phases 11A–12E
- **Status:** Implemented, Tested, and Verified
- **Target Ingestion Dataset:** Official MoHFW Tamil Nadu District HMIS Returns (FY 2015–16)
- **Primary Database Models:** `DistrictObservation` (`district_observations`), `ImportJob` (`import_jobs`)

---

## 1. Executive Summary & Architecture Isolation

CAREFlow India provides a multi-echelon healthcare operations and epidemiological analytics platform. To support state-level and district-level health monitoring without compromising clinical operational integrity, CAREFlow establishes an absolute structural separation between:

1. **Facility Clinical Observations (`observations` table):**
   - Granular point-of-care observations tied directly to primary health centres (PHCs), community health centres (CHCs), and sub-district/district hospitals (`facility_id NOT NULL`).
   - Sourced from transactional HMIS monthly returns and internal EMR submissions.
   - Total database volume in development: **362 facility records**.

2. **Official District Administrative Returns (`district_observations` table):**
   - High-level consolidated returns covering all 31 revenue districts of Tamil Nadu across 12 calendar months (April 2015 – March 2016).
   - Ingested via wide-to-long transformation maintaining original fiscal reporting metadata, subgroup classifications, and reporting integrity.
   - Total database volume in development: **175,872 district records**.

### Structural Segregation Guarantee
```
                                +---------------------------------------------+
                                |             CAREFlow Core System            |
                                +---------------------------------------------+
                                                       |
                       +-------------------------------+-------------------------------+
                       |                                                               |
        [Facility Data Pipeline]                                        [District HMIS Pipeline]
                       |                                                               |
                       v                                                               v
         `observations` (Facility)                                   `district_observations` (District)
      - Key: facility_id, indicator_id, ...                       - Key: district, s_no, subgroup_type, month, FY
      - Records: 362                                              - Records: 175,872
      - Facility EMR / Tabular Imports                            - Official State Ministry Return Archives
                       |                                                               |
                       +-------------------------------+-------------------------------+
                                                       |
                                        [Platform Governance Rule]
                            * Zero aggregation mixing between tables
                            * District records NEVER summed into facilities
                            * Distinct zero events preserved from missing
```

---

## 2. Phase 12A — High-Throughput Streaming CSV Report Exports

### 2.1 Design Objectives
- **Streaming HTTP Response:** Reports stream directly over HTTP chunks (`StreamingResponse(export_generator(), media_type="text/csv")`) using an in-memory string buffer. Memory footprint is $O(1)$ with respect to total export size.
- **OWASP Formula-Injection Mitigation:** All exported cells pass through `sanitize_csv_cell()`. If a string begins with spreadsheet macro invocation characters (`=`, `+`, `-`, `@`, `\t`, `\r`), it is safely escaped with a single quote prefix (`'`).
- **Boolean Integrity:** Boolean values are explicitly mapped to `"true"` or `"false"` prior to numeric checks, avoiding integer subtype coercion (`isinstance(True, int)` pitfall).
- **Zero vs. Missing Distinction:**
  - Confirmed Zero Events: Exported as `"0"` or `"0.0"`.
  - Missing/Unreported Events: Exported as empty string `""` with explicit `value_type="MISSING"`.
- **Bounded Query Protection:** Every export query is capped at `MAX_EXPORT_ROWS = 10000` to prevent memory exhaustion and denial-of-service vulnerabilities.

### 2.2 Available Export Endpoints

| Endpoint | Method | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/v1/districts/export/trends` | `GET` | `district`, `s_no`, `subgroup_type` (optional), `financial_year` (optional) | Streams 12-month time-series trend records for a single district and indicator. |
| `/api/v1/districts/export/compare` | `GET` | `s_no`, `reporting_month`, `subgroup_type` (optional), `financial_year` (optional) | Streams state-wide cross-district comparison rankings for a specific month. |

### 2.3 CSV Header Formats

**Monthly Trends CSV Schema:**
```csv
district,s_no,parameter_name,subgroup_type,financial_year,reporting_month,observation_date,value,value_type,reported_annual_total
Ariyalur,1.1,Total number of pregnant women registered for ANC,Total,2015-16,2015-04,2015-04-01,1000.0,VALID,12000.0
```

**District Comparison CSV Schema:**
```csv
rank,district,s_no,parameter_name,subgroup_type,financial_year,reporting_month,value,value_type,reported_annual_total
1,Chennai,1.1,Total number of pregnant women registered for ANC,Total,2015-16,2015-04,2500.0,VALID,30000.0
```

---

## 3. Phase 12B — Verified Indicator Mapping Registry & Clinical Crosswalk

### 3.1 Strict Non-Fabrication Rule
MoHFW district HMIS returns contain 261 distinct raw parameters identified by serial codes (e.g., `1.1`, `2.2`, `14.12.1`). Rather than guessing or fabricating clinical indicator bindings for all 261 metrics, CAREFlow implements a **strict non-fabrication governance policy**:
- Exactly **8 clinically vetted indicators** have been mapped with formal provenance against official MoHFW Operational Guidelines.
- Exactly **8 stock status parameters** have been classified as non-additive stock metrics.
- All remaining 253 indicators are explicitly preserved with `status="UNMAPPED"` and their raw MoHFW parameter names untouched.

### 3.2 Clinical Crosswalk Specifications (8 Verified Indicators)

| MoHFW Item | Raw Parameter Name | Canonical Indicator ID | Canonical Name | Category | Unit | Clinical Rationale & Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | Total number of pregnant women registered for ANC | `IND_antenatal_visits` | Antenatal Care (ANC) Registered Visits | Maternal Health | visits | Direct clinical equivalent to MoHFW HMIS Item 1.1. Ref: MoHFW HMIS Operational Guidelines. |
| **2.2** | Institutional Deliveries (Public Facilities) | `IND_institutional_deliveries` | Institutional Deliveries (Public Facilities) | Maternal Health | deliveries | Deliveries conducted at Govt. hospitals, CHCs, and PHCs. Ref: National Health Mission HMIS Standards. |
| **2.3** | Total Institutional Deliveries | `IND_total_institutional_deliveries` | Total Institutional Deliveries | Maternal Health | deliveries | Comprehensive institutional delivery volume across public and accredited private facilities. Ref: MoHFW HMIS Operational Guidelines. |
| **6.1** | Number of Infants received BCG | `IND_bcg_vaccination` | BCG Vaccination Coverage | Child Immunization | doses | Primary newborn tuberculosis immunization. Ref: Universal Immunization Programme (UIP) India. |
| **6.2** | Number of Infants received DPT3 / Pentavalent 3 | `IND_pentavalent_vaccination` | Pentavalent / DPT3 Vaccination Coverage | Child Immunization | doses | Third dose milestone for diphtheria, pertussis, tetanus, Hep B, Hib. Ref: UIP Guidelines. |
| **10.1.13.c** | Total Inpatient Admissions | `IND_inpatient_admissions` | Inpatient Department (IPD) Admissions | Hospital Services | admissions | Consolidated IPD volume across secondary and tertiary public facilities. Ref: MoHFW HMIS Dictionary. |
| **14.10.1.c** | Total Outpatient Attendance | `IND_outpatient_attendance` | Outpatient Department (OPD) Attendance | Hospital Services | visits | Overall ambulatory clinical consultation volume. Ref: MoHFW HMIS Dictionary. |
| **14.12.1** | Total Laboratory Tests Done | `IND_lab_tests_performed` | Diagnostic Laboratory Investigations | Diagnostics | tests | Aggregate diagnostic investigation volume conducted across clinical laboratories. Ref: MoHFW HMIS Standards. |

### 3.3 Stock Metric Governance
Parameters representing point-in-time inventory (such as Item `9.12` and Items `14.01–14.09`) are classified as `is_stock_metric=True`. The analytics service prohibits temporal summation (adding months together) for these indicators, preventing misleading aggregate totals.

### 3.4 Registry Endpoints
- `GET /api/v1/districts/indicators/registry`: Returns complete list of indicators with mapping status and metadata. Supports `status` filter (`VERIFIED`, `UNMAPPED`).
- `GET /api/v1/districts/indicators/audit`: Generates comprehensive governance audit report with mapping percentages, unmapped samples, and governance declarations.

---

## 4. Phase 12C — Multi-Year Reporting Readiness

### 4.1 Schema Natural Key Architecture
The `DistrictObservation` model enforces a composite natural key index:
```python
Index(
    "uq_district_obs_natural_key",
    "district",
    "s_no",
    "subgroup_type",
    "reporting_month",
    "financial_year",
    unique=True,
)
```
This guarantees complete idempotency across multi-year imports. Ingesting future fiscal years (e.g., FY 2016–17, 2017–18) will not conflict with or overwrite FY 2015–16 observations.

### 4.2 Dynamic Query Filtering
All district analytics endpoints accept an optional `financial_year: Optional[str] = Query(None)` parameter. When provided, calculations, time-series projections, and exports strictly isolate observations matching the designated fiscal year. When omitted, queries automatically default to the primary reporting fiscal year (`2015-16`).

---

## 5. Phase 12D — Security, Authentication, and Reliability Audit

### 5.1 Security Controls Summary
1. **Endpoint Protection:** All 9 district analytics and export endpoints require an active, authenticated user session validated via JWT bearer tokens through `Depends(get_current_active_user)`.
2. **SQL Injection Resilience:** All database operations utilize SQLAlchemy ORM parameterized queries with bound variables. User-supplied parameters (`district`, `s_no`, `reporting_month`, `financial_year`) are strongly typed and sanitized.
3. **Spreadsheet Formula Injection Defense:** String values starting with spreadsheet formula control characters (`=`, `+`, `-`, `@`, `\t`, `\r`) are sanitized with single-quote escaping.
4. **Denial-of-Service Defense:** Streaming queries enforce a maximum row bound (`10,000` records) and streaming generator memory chunks.

---

## 6. Phase 12E — Frontend User Interface Integration

The CAREFlow frontend provides a unified, interactive workspace for district intelligence at `/districts`:

1. **Editorial Workspace Header:**
   - Visual badges: *Official State HMIS Returns*, *Jurisdiction: District*, *FY 2015–16 (12 Months)*, and *Segregated Data Stream*.
   - Prominent source separation alert clarifying non-aggregation with facility observations.
2. **Four Dedicated Workspace Tabs:**
   - **Monthly Trends:** Interactive SVG trend chart visualizing 12-month trajectory, complete with distinct visual markers for Valid, Zero, and Missing states, and instant CSV export.
   - **District Comparison:** Ranked cross-district comparison with state mean/median indicators and direct CSV export.
   - **Observation Records:** Raw observation log with zero/missing status tags and search filtering.
   - **Quality & Provenance:** Ingestion audit KPIs, job execution metadata, and the Phase 12B Verified Indicator Registry audit table.
3. **Filter Toolbar:**
   - Financial Year dropdown selector (`FY 2015-16`).
   - District, Indicator, Reporting Month, and Subgroup filters.
   - Verified Indicator mapping status pills (`All`, `Verified`, `Unmapped`).

---

## 7. Verification and Test Coverage Matrix

| Test Suite | Scope | Tests Run | Result |
| :--- | :--- | :--- | :--- |
| `tests/test_phase_12a_csv_exports.py` | CSV streaming, formula sanitization, zero vs missing, 10k bounds | 5 | **PASSED** |
| `tests/test_phase_12b_indicator_registry.py` | Crosswalk registry, 8 indicators, non-fabrication rule, audit | 6 | **PASSED** |
| `tests/test_phase_12c_multi_year.py` | Multi-year queries, natural key unique constraint, fiscal filtering | 4 | **PASSED** |
| `tests/test_phase_12d_security_audit.py` | Authentication enforcement on all 9 endpoints, bounds checking | 5 | **PASSED** |
| `frontend/src/pages/DistrictsPage.test.tsx` | UI tabs, filter dropdowns, export actions, Quality & Registry audit | 7 | **PASSED** |
| Full Frontend Suite (`vitest run`) | Comprehensive frontend regression check | 78 | **PASSED** |
