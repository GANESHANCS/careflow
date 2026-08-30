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

## Standardized Error Response Format

Errors return structured JSON with standard HTTP status codes:
```json
{
  "detail": "Facility with ID 'FC_INVALID' not found."
}
```
