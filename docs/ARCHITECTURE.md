# CAREFlow Architecture Blueprint

## System Overview
CAREFlow India uses a clean, decoupled 3-tier architecture:
1. **Presentation Layer**: React 18 + TypeScript SPA built with Vite.
2. **Application & API Layer**: FastAPI REST Service with Pydantic schemas and async route handlers.
3. **Data & Analytics Layer**: Normalized SQL Database (PostgreSQL) + Python ML & Time-Series Engine.

```
┌─────────────────────────────────────────────────────────────┐
│              React 18 + TypeScript + Vite SPA               │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON / HTTP REST APIs
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 FastAPI REST API Service                    │
│   (App Router, OpenAPI Schemas, Pydantic V2 Validation)     │
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               ▼                              ▼
┌──────────────────────────────┐┌─────────────────────────────┐
│   PostgreSQL / SQLAlchemy    ││  Python Data & ML Engine    │
│ (Facilities, Observations,   ││ (Pandas, Scikit-learn,     │
│  Forecasts, Indicators, MQ)  ││  Statsmodels Forecasting)   │
└──────────────────────────────┘└─────────────────────────────┘
```

## Data Schema Strategy (Extensible EAV/Timeseries Model)
To support hundreds of HMIS indicators dynamically without schema rewrites, the database model uses an extensible entity-attribute-value timeseries architecture:
- `facilities`: Facility metadata, region, district, facility type, ownership.
- `indicators`: Dynamic catalog of HMIS indicators (OPD, Inpatient, Immunisation, Antenatal, etc.).
- `observations`: Facility-level monthly report values with data-quality provenance flags.
- `forecasts`: Time-series demand forecasts with confidence intervals and model signature references.
- `model_metadata`: Model training signatures, parameters, and baseline comparison metrics.

## Data Directory Pipeline Layers
- `data/raw/`: Immutable HMIS source Excel/CSV files.
- `data/interim/`: Normalized and schema-validated intermediate datasets.
- `data/processed/`: Deduplicated, entity-standardized datasets ready for database ingestion and ML feature engineering.
