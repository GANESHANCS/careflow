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

**Response Example (200 OK)**:
```json
{
  "items": [
    {
      "id": "FC_1001",
      "facility_code": "1001",
      "facility_name": "District Hospital Alpha",
      "facility_type": "DH",
      "state": "State_A",
      "district": "District_X",
      "sub_district": null,
      "raw_facility_name": "District Hospital Alpha",
      "raw_district_name": "District_X"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

#### `GET /api/facilities/{facility_id}`
Get detailed metadata for a single facility by ID.

**Error Responses**:
- `404 Not Found`: Facility with specified ID does not exist.

---

### 3. Indicators API
#### `GET /api/indicators`
List registered HMIS indicators.

**Query Parameters**:
- `category` *(optional, string)*: Filter by operational category (e.g. `Outpatient Services`, `Maternal Health`)

---

### 4. Observations Timeseries API
#### `GET /api/facilities/{facility_id}/observations`
List monthly healthcare observations for a specific facility.

**Query Parameters**:
- `indicator_code` *(optional, string)*: Filter by indicator code (`opd_attendance`, `inpatient_admissions`, etc.)
- `start_month` *(optional, string, YYYY-MM)*: Filter start month inclusive
- `end_month` *(optional, string, YYYY-MM)*: Filter end month inclusive
- `skip` *(optional, int, default=0)*: Pagination offset
- `limit` *(optional, int, default=100, max=500)*: Items per page

---

## Standardized Error Response Format

Errors return structured JSON with standard HTTP status codes:
```json
{
  "detail": "Facility with ID 'FC_INVALID' not found."
}
```
