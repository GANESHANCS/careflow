# CAREFlow Healthcare Analytics Architecture & Definitions

## 1. Overview

The CAREFlow Analytics Engine (`backend/app/services/analytics/`) provides a production-grade analytical processing layer between the relational database and future ML forecasting / UI experiences.

---

## 2. Core Metrics & Calculation Logic

### 2.1 Executive Summary Metrics
- **Total Indicator Utilization**: Aggregate sum of monthly count values across facilities for standard HMIS indicators (`opd_attendance`, `inpatient_admissions`, `institutional_deliveries`, `antenatal_visits`, `postnatal_visits`, `immunisation`).
- **Active Facilities**: Number of distinct facilities with registered records.
- **Reporting Facilities**: Number of distinct facilities contributing valid observations in the target reporting period.
- **Reporting Completeness (%)**:
  $$\text{Completeness (\%)} = \left( \frac{\text{Reporting Facilities}}{\text{Total Facilities}} \right) \times 100.0$$

---

### 2.2 Growth Rate Formulas & Zero-Denominator Safety
- **Month-over-Month (MoM) Growth (%)**:
  $$\text{MoM Change (\%)} = \left( \frac{\text{Value}_{\text{current}} - \text{Value}_{\text{previous}}}{\text{Value}_{\text{previous}}} \right) \times 100.0$$
- **Year-over-Year (YoY) Growth (%)**:
  $$\text{YoY Change (\%)} = \left( \frac{\text{Value}_{\text{current}} - \text{Value}_{\text{previous\_year}}}{\text{Value}_{\text{previous\_year}}} \right) \times 100.0$$

#### Zero-Denominator & Missing Value Protection Rule
- If $\text{Value}_{\text{previous}} = 0.0$ or is `None`, the growth calculation returns **`null`** (prevents `ZeroDivisionError` or misleading $\infty$ percentages).
- Implemented in `backend/app/services/analytics/change_calc.py`.

---

### 2.3 Regional Analytics (State & District)
- **Total Utilization**: Sum of observations in the region.
- **Average Per Reporting Facility**:
  $$\text{Avg per Facility} = \frac{\text{Total Utilization}}{\text{Reporting Facilities Count}}$$
- **Median Per Reporting Facility**: Median value of individual reporting facility counts.
- **Interpretation Rule**: *Comparing regions using raw total volume alone can be misleading when facility counts differ. The analytics engine explicitly exposes normalized per-facility metrics alongside totals.*

---

### 2.4 Facility Analytics & Missing Period Detection
- **Missing Reporting Periods**: The analytics engine generates the full monthly calendar sequence between `min_month` and `max_month`. Any month lacking an observation for a facility is flagged in `missing_months`.
- **Missing vs. Zero Distinction**: Missing months remain `None` (`MISSING`) and are **never** silently converted to `0.0`.

---

### 2.5 Facility Benchmarking & Comparison
- Exposes side-by-side timeseries grids for multi-facility comparison.
- Provides normalized summary stats: Average, Median, Latest Value, Completeness %, and Trend Direction (`UP`, `DOWN`, `STABLE`).

---

## 3. Preparing Clean Timeseries Datasets for Phase 5 Forecasting

Phase 5 forecasting models require clean timeseries vectors:
- **Clean Structure**: `(facility_id, indicator_code, reporting_month, value, completeness_pct, value_type)`
- **No Data Fabrication**: Missing values are preserved as `None` or flagged with `MISSING` so that imputation/interpolation strategies can be chosen explicitly by forecasting algorithms.
