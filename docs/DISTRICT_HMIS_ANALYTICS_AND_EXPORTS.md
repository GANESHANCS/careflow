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

### 3.2 Clinical Crosswalk Specifications & Status Classifications (Phase 13A Audit)

| MoHFW Item | Raw Parameter Name in Source CSV | Canonical Indicator ID | Canonical Name | Category | Status | Clinical Rationale & Provenance |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1.1** | Total number of pregnant women Registered for ANC | `IND_antenatal_visits` | Antenatal Care (ANC) Registered Visits | Maternal Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 1.1 (`Type: TOTAL`). Covers primary trimester registrations and routine antenatal surveillance. Ref: MoHFW HMIS Operational Guidelines. |
| **2.2** | Deliveries conducted at Public Institutions (Including C-Sections) | `IND_institutional_deliveries` | Institutional Deliveries (Public Facilities) | Maternal Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 2.2 (`Type: TOTAL`). Captures deliveries in accredited public health sector facilities under skilled birth attendance. Ref: National Health Mission HMIS Standards. |
| **2.3** | Deliveries conducted at Private Institutions (Including C-Sections) | `IND_institutional_deliveries` | Institutional Deliveries (Private Facilities) | Maternal Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 2.3 (`Type: TOTAL`). Captures private sector maternity returns under skilled birth attendance. Ref: MoHFW HMIS Operational Guidelines. |
| **6.1** | Women getting post partum check-up within 48 hours after delivery | `IND_postnatal_visits` | Postnatal Care (PNC) Visits (≤48h) | Maternal Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 6.1 (`Type: TOTAL`). High-priority early maternal mortality prevention window within 48 hours postpartum. Ref: MoHFW HMIS Operational Guidelines. |
| **6.2** | Women getting a post partum check up between 48 hours and 14 days after delivery | `IND_postnatal_visits` | Postnatal Care (PNC) Visits (3–14d) | Maternal Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 6.2 (`Type: TOTAL`). Captures secondary PNC monitoring completed between 3 and 14 days following delivery. Ref: MoHFW HMIS Operational Guidelines. |
| **10.1.13.c** | Total number of children (9 to 11 months old) fully immunised (BCG+DPT123/Pentavalent123+OPV123+Measles) during the month | `IND_immunisation` | Full Immunisation Coverage (9–11m) | Child Health | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 10.1.13.c (`Type: TOTAL`). Composite count of infants completing full primary universal immunization schedule. Ref: Universal Immunization Programme (UIP). |
| **14.12.1** | OPD attendance (All) | `IND_opd_attendance` | Outpatient Department (OPD) Attendance | Outpatient Services | **VERIFIED** | Direct clinical equivalent to MoHFW HMIS Item 14.12.1 (`Type: TOTAL`). Captures total ambulatory outpatient consultation encounters across all district facilities. Ref: MoHFW HMIS Operational Guidelines. |
| **14.10.1.c** | Total number of patients admitted (Inpatients) during the month (sum of items 14.10.1.a and 14.10.1.b) | `IND_inpatient_admissions` | Inpatient Admissions (IPD) [Disaggregated Slices] | Inpatient Services | **AMBIGUOUS** | MoHFW Item 14.10.1.c sums male and female admissions, but in official source returns it is partitioned into demographic age slices (`1. Children` and `2. Adults`) with zero records under `TOTAL` (`is_subgroup_total=False`). Unqualified mapping to canonical `IND_inpatient_admissions` is AMBIGUOUS because queries defaulting to first available subgroup capture only pediatric admissions and exclude adult patients. |

### 3.3 Stock Metric Governance
Parameters representing point-in-time inventory (such as Item `9.12` and Items `14.01–14.09`) are classified as `is_stock_metric=True`. The analytics service prohibits temporal summation (adding months together) for these indicators, preventing misleading aggregate totals.

### 3.4 Registry Endpoints
- `GET /api/v1/districts/indicators/registry`: Returns complete list of indicators with mapping status and metadata. Supports `status` filter (`VERIFIED`, `AMBIGUOUS`, `UNMAPPED`).
- `GET /api/v1/districts/indicators/audit`: Generates comprehensive governance audit report with verified, ambiguous, provisional, and unmapped breakdown.

---

## 4. Phase 12C & Phase 13B — Multi-Year Reporting Readiness & Schema Architecture

### 4.1 Schema Natural Key Architecture
The `DistrictObservation` model and database migration `c2d3e4f5a6b7` enforce the natural key constraint:
```python
UniqueConstraint(
    "district",
    "s_no",
    "subgroup_type",
    "reporting_month",
    name="uq_district_obs_natural_key"
)
```
**Architecture Note on Multi-Year Uniqueness:**
`financial_year` is not part of the database constraint itself. Because Indian HMIS fiscal months are normalized into ISO calendar representations (e.g. FY 2015–16 is `2015-04` through `2016-03`, while FY 2016–17 is `2016-04` through `2017-03`), natural key collisions across standard consecutive fiscal years are prevented by the `reporting_month` coordinate. If observations share the same `reporting_month`, the database enforces strict single-occupancy.

### 4.2 Dynamic Query Filtering
All district analytics endpoints accept an optional `financial_year: Optional[str] = Query(None)` parameter. When provided, calculations, time-series projections, and exports strictly isolate observations matching the designated fiscal year. When omitted, queries filter dynamically by target district, indicator, and reporting periods.

---

## 5. Phase 13 — Indicator Audit, Subgroup Resolution Defect Fix, and Regression Testing

### 5.1 Evidence-Backed Indicator Audit Findings (Phase 13A)
- **14.12.1 Verified:** Verified as `OPD attendance (All)` with Type `TOTAL` across all 32 districts in the MoHFW Tamil Nadu FY 2015–16 return. Mapped to `IND_opd_attendance`.
- **14.10.1.c Ambiguity Identified:** Source CSV contains 64 rows for 14.10.1.c (32 districts × 2 demographic age slices: `1. Children` and `2. Adults`). Zero records exist with Type `TOTAL`. Reclassified from `VERIFIED` to `AMBIGUOUS` with explicit rationale preventing pediatric under-reporting.
- **Crosswalk Provenance Correction:** Vetted raw parameter labels against `hmis-item-rpt-tn-for-2015-16.csv`, eliminating documentation label shifts from prior drafts.

### 5.2 Cross-District Comparison Export Subgroup Resolution (Phase 13C)
- **Defect Fixed:** When `subgroup_type` was omitted in `GET /api/analytics/district/export/compare`, the export query previously fetched all demographic slices simultaneously. For multi-subgroup parameters (such as `14.10.1.c`), this generated duplicate rows per district (64 rows instead of 32), caused `rank_map` dictionary overwrites, and conflated state mean/median calculations.
- **Resolution:** `DistrictExportService.export_comparison_csv` now resolves the default subgroup (preferring `TOTAL`, `Total`, `4. Total`, `3. Total`, or first available slice), guaranteeing exactly 1 record per district, unique non-colliding ranks 1..N, clean state statistics, and declared subgroup metadata.

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
| `tests/test_phase_12a_csv_exports.py` | CSV streaming, formula sanitization, zero vs missing, 10k bounds | 6 | **PASSED** |
| `tests/test_phase_12b_indicator_registry.py` | Crosswalk registry, 8 indicators, non-fabrication rule, audit | 6 | **PASSED** |
| `tests/test_phase_12c_multi_year.py` | Multi-year queries, natural key unique constraint, fiscal filtering | 4 | **PASSED** |
| `tests/test_phase_12d_security_audit.py` | Authentication enforcement on all 9 endpoints, bounds checking | 4 | **PASSED** |
| `tests/test_phase_13_indicator_audit_and_exports.py` | Ambiguity classifications, subgroup resolution defect regression | 7 | **PASSED** |
| `tests/test_phase_14_healthcare_analytics.py` | Verified indicator eligibility, 12m completeness, missing vs zero | 4 | **PASSED** |
| `tests/test_phase_14_forecasting_readiness.py` | Chronological split, holdout evaluation, horizon limits, disclaimers | 4 | **PASSED** |
| `tests/test_phase_14_anomaly_detection.py` | Robust MAD outliers, MoM volatility, small-sample safety | 4 | **PASSED** |
| `tests/test_phase_14_endpoints.py` | Auth enforcement, parameter validation, schema compliance | 5 | **PASSED** |
| `frontend/src/pages/DistrictsPage.test.tsx` | UI tabs, filter dropdowns, Intelligence tab, Quality & Registry audit | 8 | **PASSED** |
| Full Frontend Suite (`npm test -- --run`) | Comprehensive frontend regression check across 14 suites | 79 | **PASSED** |

---

## 8. Phase 14 — Healthcare Intelligence, Forecasting Foundation & Early-Warning Analytics

### 8.1 Architecture and Endpoints

CAREFlow India Phase 14 introduces dedicated operational intelligence endpoints under `/api/analytics/district/intelligence/`:

| Endpoint | Method | Query Parameters | Description |
| :--- | :--- | :--- | :--- |
| `/api/analytics/district/intelligence/overview` | `GET` | `district`, `s_no`, `subgroup_type`, `financial_year` | Retrieves chronological time-series for a VERIFIED indicator, reporting completeness, missing month detection, observed zero tracking, and official MoHFW provenance. |
| `/api/analytics/district/intelligence/readiness` | `GET` | `district`, `s_no`, `horizon` (1-12), `subgroup_type`, `financial_year` | Evaluates historical depth, enforces chronological hold-out train/test split, calculates baseline error metrics (MAE, RMSE, sMAPE, WAPE) on held-out test months, and provides forward baseline projections. |
| `/api/analytics/district/intelligence/anomalies` | `GET` | `district` (optional), `s_no` (optional), `reporting_month` (optional), `subgroup_type`, `financial_year` | Runs conservative non-parametric anomaly detection: Median Absolute Deviation (MAD > 3.5), abrupt Month-over-Month shifts (>50% jump & >3σ), missing reporting period detection, and cross-district spatial outliers. |

### 8.2 Strict Indicator Eligibility & Exclusions

Only indicators classified with `status="VERIFIED"` in the `IndicatorMappingRegistry` are eligible for canonical healthcare intelligence:

1. **Eligible VERIFIED Indicators:**
   - `1.1` (`IND_antenatal_visits`): Antenatal Care (ANC) Registered Visits
   - `2.2` (`IND_institutional_deliveries`): Institutional Deliveries (Public Facilities)
   - `2.3` (`IND_institutional_deliveries`): Institutional Deliveries (Private Facilities)
   - `6.1` (`IND_postnatal_visits`): Postnatal Care (PNC) Visits (≤48h)
   - `6.2` (`IND_postnatal_visits`): Postnatal Care (PNC) Visits (3–14d)
   - `10.1.13.c` (`IND_immunisation`): Full Immunisation Coverage (9–11m)
   - `14.12.1` (`IND_opd_attendance`): Outpatient Department (OPD) Attendance

2. **Explicit Exclusions & Governance Rules:**
   - **`14.10.1.c` (Inpatient Admissions):** Excluded from canonical intelligence because official returns only provide demographic slices (`1. Children` and `2. Adults`) without an authoritative unified total row (`is_subgroup_total=False`), preventing accidental pediatric under-reporting.
   - **Stock/Capacity Metrics (`is_stock_metric=True`, e.g. Items `9.12`, `14.01–14.09`):** Excluded from volume demand forecasting and temporal summation.
   - **Unmapped Parameters (253 metrics):** Excluded from canonical analytics and preserved verbatim.

### 8.3 Forecasting Readiness & Single-Year Dataset Limitations

1. **Dataset Limitation Disclosure:**
   The current HMIS archive contains single-year administrative returns (12 calendar months: `2015-04` through `2016-03`). A single fiscal year cannot establish multi-year seasonal cycles or support long-horizon forecasting. Requests for horizons $>3$ months or seasonal models return an explicit `INSUFFICIENT_HISTORY` status.
2. **Chronological Hold-Out Evaluation (Zero Leakage):**
   - Training Window: First 9 months (`2015-04` through `2015-12`).
   - Evaluation Window: Final 3 months (`2016-01` through `2016-03`).
   - Models are fitted strictly on the training window and evaluated against unseen ground-truth values in the hold-out window.
3. **Candidate Baseline Models:**
   - **Naïve Forecaster:** Extrapolates the most recent observed training value.
   - **Moving Average Forecaster (3m):** Averages the final 3 months of the training window.
   - **Linear Drift Forecaster:** Extrapolates deterministic slope and intercept fitted on training indices.
4. **Clinical Validation Disclaimer:**
   Baseline forecasts are descriptive statistical projections. They are not clinically validated and do not account for external epidemiological shocks or interventions.

### 8.4 Conservative Anomaly & Change Detection

1. **Robust Median Absolute Deviation (MAD):**
   Identifies outliers using the modified Z-score $M_i = \frac{0.6745 \cdot |x_i - \text{median}|}{\text{effective\_MAD}}$. Flagged when $M_i > 3.5$. To prevent zero-division when $>50\%$ of observations are identical, effective scale falls back to Mean Absolute Deviation.
2. **Month-over-Month Shift Detection:**
   Flags abrupt volume swings where both the percentage change exceeds $50\%$ and the absolute jump exceeds $3\sigma$ of historical month-to-month volatility.
3. **Missing Period Audit:**
   Surfaces expected calendar months in the 12-month sequence that were unreported or submitted with missing values.
4. **Cross-District Spatial Outlier Detection:**
   Compares district values against the state cross-district median and state MAD across all reporting districts in that month.
5. **Regulatory Labeling & Governance:**
   All alerts are labeled as `STATISTICAL_SIGNAL`. They do not constitute clinical diagnoses, disease outbreak declarations, or evidence of reporting fraud.
