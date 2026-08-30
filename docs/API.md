# CAREFlow API Documentation

## Overview

The CAREFlow Backend API is built using **FastAPI** and follows standard RESTful principles. All API endpoints are prefixed with `/api`.

- **Interactive API Documentation (Swagger)**: `http://127.0.0.1:8000/api/docs`
- **ReDoc Specifications**: `http://127.0.0.1:8000/api/redoc`

---

## Endpoint Specifications

### 1. Health & Database Verification
#### `GET /api/health`
Returns system status, software version, environment details, and real database connectivity test (`SELECT 1`).

**Response Example (200 OK)**:
```json
{
  "status": "healthy",
  "app_name": "CAREFlow India",
  "version": "0.1.0",
  "environment": "development",
  "python_version": "3.12.7",
  "database_status": "healthy",
  "timestamp": "2026-08-30T19:40:00+00:00",
  "database": {
    "status": "healthy",
    "engine": "sqlite",
    "error": null
  }
}
```

---

### 2. Facilities API
#### `GET /api/facilities`
List healthcare facilities with optional filtering and pagination.

**Query Parameters**:
- `state` *(optional, string)*: Filter by state name (case-insensitive substring)
- `district` *(optional, string)*: Filter by district name (case-insensitive substring)
- `facility_type` *(optional, string)*: Filter by type (`DH`, `CHC`, `PHC`, `SC`, etc.)
- `skip` *(optional, int, default=0)*: Pagination offset
- `limit` *(optional, int, default=50, max=200)*: Items per page

#### `GET /api/facilities/{facility_id}`
Get detailed metadata for a single facility by ID.

---

### 3. Indicators API
#### `GET /api/indicators`
List registered HMIS indicators.

---

### 4. Observations Timeseries API
#### `GET /api/facilities/{facility_id}/observations`
List monthly healthcare observations for a specific facility.

---

### 5. Healthcare Analytics Engine API (`/api/analytics/`)

#### `GET /api/analytics/summary`
Executive summary metrics across active facilities and indicators.
- **Parameters**: `state` *(optional)*, `district` *(optional)*

#### `GET /api/analytics/trends`
Monthly time-series aggregations (totals, averages, reporting facility count, completeness %).
- **Parameters**: `indicator_code` *(optional)*, `state` *(optional)*, `district` *(optional)*, `facility_id` *(optional)*, `start_month` *(optional)*, `end_month` *(optional)*

#### `GET /api/analytics/regional`
State and District level utilization aggregations, average per reporting facility, median per reporting facility, and MoM growth.
- **Parameters**: `level` *('state' or 'district', default='district')*, `indicator_code` *(optional)*, `state` *(optional)*, `district` *(optional)*, `reporting_month` *(optional)*

#### `GET /api/analytics/facilities`
Facility-level analytical details, historical indicator trends, reporting completeness, missing reporting periods, and MoM growth per indicator.
- **Parameters**: `facility_id` *(required)*, `indicator_code` *(optional)*

#### `GET /api/analytics/compare`
Side-by-side facility benchmarking across a target indicator.
- **Parameters**: `facility_ids` *(required, multi-value)*, `indicator_code` *(required)*, `start_month` *(optional)*, `end_month` *(optional)*

#### `GET /api/analytics/data-quality`
Database-backed data quality metrics, issue severity counts, issue category breakdowns, and incomplete reporting facility lists.

---

### 6. Forecasting & ML Engine API

#### `GET /api/forecast`
Generates or retrieves monthly healthcare demand forecasts for a facility/indicator.

- **Query Parameters**:
  - `facility_id` *(required, string)*: Facility ID or Facility Code (e.g. `fac_synth_dh_alpha`)
  - `indicator_code` *(optional, string, default="opd_attendance")*: Indicator code (e.g. `opd_attendance`, `inpatient_admissions`, `institutional_deliveries`)
  - `horizon` *(optional, int, default=12)*: Forecast horizon in months (allowed: `3`, `6`, `12`)

- **Response Example (200 OK — SUCCESS)**:
```json
{
  "status": "SUCCESS",
  "facility": {
    "id": "fac_synth_dh_alpha",
    "name": "SYNTHETIC District Hospital Alpha",
    "district": "SYNTHETIC_District_X",
    "facility_type": "District Hospital"
  },
  "indicator": {
    "id": "IND_opd_attendance",
    "code": "opd_attendance",
    "name": "Outpatient Department (OPD) Attendance",
    "unit": "visits"
  },
  "forecast_horizon": 12,
  "model": {
    "model_version": "1.0.0",
    "model_type": "Holt-Winters",
    "is_baseline": true
  },
  "training_period": {
    "start_month": "2022-01",
    "end_month": "2024-12",
    "total_observations": 36
  },
  "forecast_points": [
    {
      "forecast_month": "2025-01",
      "forecast_date": "2025-01-01",
      "predicted_value": 1150.5,
      "lower_bound": 996.3,
      "upper_bound": 1304.7
    }
  ],
  "prediction_intervals": {
    "interval_type": "95% prediction interval (approximate)",
    "residual_std_error": 78.66
  },
  "validation_metrics": {
    "mae": 78.66,
    "rmse": 99.88,
    "smape": 3.93,
    "wape": 4.12,
    "mape": 4.05
  },
  "baseline_metrics": {
    "strongest_baseline_name": "Holt-Winters",
    "strongest_baseline_mae": 78.66
  },
  "improvement_over_baseline_pct": 0.0,
  "eligibility": {
    "is_eligible": true,
    "status": "ELIGIBLE",
    "reason_code": null,
    "reason_message": "Series meets all time-series forecasting eligibility criteria."
  },
  "explainability": {
    "model_title": "Forecast generated using Holt-Winters",
    "historical_months_count": 36,
    "reporting_completeness_pct": "100.0%",
    "validation_mae": 78.66,
    "prediction_interval_description": "95% prediction interval (approximate residual-based bounds)",
    "baseline_benchmark_model": "Holt-Winters",
    "improvement_over_baseline": "0.0%",
    "selection_rationale": "Strongest baseline 'Holt-Winters' selected. No ML candidate demonstrated validation MAE improvement over baseline."
  },
  "disclaimer": "SYNTHETIC / NON-REPRESENTATIVE — Validation performed on synthetic fixtures for framework verification."
}
```

- **Response Example (200 OK — NOT_ELIGIBLE)**:
```json
{
  "status": "NOT_ELIGIBLE",
  "facility": {
    "id": "fac_01",
    "name": "District Hospital 1",
    "district": "District X"
  },
  "indicator": {
    "code": "opd_attendance",
    "name": "Outpatient Department (OPD) Attendance"
  },
  "forecast_horizon": 12,
  "eligibility": {
    "is_eligible": false,
    "status": "NOT_ELIGIBLE",
    "reason_code": "INSUFFICIENT_HISTORY",
    "reason_message": "Series has only 5 observation(s), minimum required is 12."
  },
  "disclaimer": "SYNTHETIC / NON-REPRESENTATIVE — Validation performed on synthetic fixtures for framework verification."
}
```

#### `GET /api/model/metrics`
Returns model registry summary across registered forecasting models.

- **Query Parameters**:
  - `target_indicator` *(optional, string)*: Filter by indicator code (e.g. `opd_attendance`)

- **Response Example (200 OK)**:
```json
[
  {
    "model_version": "1.0.0",
    "model_type": "SARIMAX",
    "target_indicator": "inpatient_admissions",
    "training_start": "2022-01",
    "training_end": "2024-12",
    "mae": 8.88,
    "rmse": 11.71,
    "mape": 4.25,
    "baseline_mae": 10.89,
    "improvement_over_baseline_pct": 18.41,
    "created_at": "2026-08-30T15:52:45"
  }
]
```

---

## Standardized Error Response Format

Errors return structured JSON with standard HTTP status codes:
```json
{
  "detail": "Facility with ID 'FC_INVALID' not found."
}
```

