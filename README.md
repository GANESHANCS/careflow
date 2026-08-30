# CAREFlow India — Healthcare Workflow & Analytics Intelligence Platform

CAREFlow India is a production-grade healthcare analytics, workflow management, and service demand forecasting platform designed around the Ministry of Health & Family Welfare (MoHFW) Health Management Information System (HMIS) dataset.

## Core Capabilities
- **Operational Analytics**: Comprehensive facility and regional healthcare reporting.
- **HMIS Data Pipeline**: Data ingestion, normalization, quality validation, and provenance tracking.
- **Service Forecasting**: Time-series demand forecasting for Outpatient Department (OPD) attendance, inpatient admissions, and institutional deliveries.
- **Capacity Planning**: Operational intelligence insights for healthcare administrators, public health researchers, and government decision-makers.

## Architecture Stack
- **Frontend**: React 18, TypeScript, Vite, Tailwind CSS v4, Lucide Icons.
- **Backend**: FastAPI, Pydantic v2, SQLAlchemy 2.0, Uvicorn.
- **Database**: PostgreSQL (Production) / SQLite (Local Development Adapter).
- **Data & ML**: pandas, NumPy, scikit-learn, statsmodels.

## Quick Start

### 1. Prerequisites
- Python 3.12+
- Node.js v24+ / npm 11+

### 2. Backend Setup
```bash
# Activate virtual environment
.\.venv\Scripts\activate

# Run tests
pytest

# Start API server
uvicorn backend.app.main:app --reload --port 8000
```
API Documentation will be available at `http://127.0.0.1:8000/api/docs`.

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access the application UI at `http://localhost:5173`.

## Documentation
- [Architecture Blueprint](docs/ARCHITECTURE.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Project Status & Verification](docs/PROJECT_STATUS.md)
