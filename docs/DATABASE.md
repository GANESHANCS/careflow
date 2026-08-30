# CAREFlow Database Architecture & Migration Guide

## 1. Overview & Target Database

CAREFlow uses **SQLAlchemy 2.0** as its Object-Relational Mapper (ORM) and **Alembic** for schema migrations.

- **Production Target Database**: **PostgreSQL** (`postgresql+psycopg://...`)
- **Local & Automated Testing Database**: **SQLite** (`sqlite:///./careflow_dev.db` and `:memory:`)

The database architecture is designed with full PostgreSQL compatibility, including:
- Type-safe mapped columns (`Mapped[T]`)
- Explicit Foreign Keys with `ON DELETE CASCADE`
- Standardized composite indexing (`(facility_id, indicator_id, observation_date)`)
- Composite unique constraints to prevent duplicate timeseries records

---

## 2. Table Schemas & Constraints

### 2.1 Facilities (`facilities`)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | String(64) | PRIMARY KEY | Standardized facility ID (`FC_<code>` or `FKEY_<hash>`) |
| `facility_code` | String(64) | UNIQUE, INDEX, NULLABLE | Official HMIS Facility Code |
| `facility_name` | String(255) | NOT NULL | Standardized display name |
| `facility_type` | String(64) | INDEX, NOT NULL | Hospital classification (DH, CHC, PHC, SC, etc.) |
| `state` | String(128) | INDEX, NOT NULL | Administrative State |
| `district` | String(128) | INDEX, NOT NULL | Administrative District |
| `sub_district` | String(128) | NULLABLE | Administrative Sub-District / Block |
| `raw_facility_name` | String(255) | NOT NULL | Source name for audit provenance |
| `raw_district_name` | String(128) | NULLABLE | Source district name |
| `created_at` | DateTime(tz) | NOT NULL | UTC record creation timestamp |
| `updated_at` | DateTime(tz) | NOT NULL | UTC record modification timestamp |

**Indexes**:
- `ix_facilities_facility_code` on `(facility_code)`
- `idx_facility_state_district` on `(state, district)`

---

### 2.2 Indicators (`indicators`)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | String(64) | PRIMARY KEY | Indicator ID (`IND_<code>`) |
| `code` | String(64) | UNIQUE, INDEX, NOT NULL | Stable indicator code (`opd_attendance`) |
| `name` | String(255) | NOT NULL | Human-readable indicator title |
| `description` | Text | NULLABLE | Detailed indicator definition |
| `category` | String(128) | INDEX, NOT NULL | Operational category (Outpatient, Maternal, Child Health) |
| `unit` | String(64) | NOT NULL | Measurement unit (`visits`, `admissions`, `deliveries`, `children`) |
| `source_system` | String(64) | NOT NULL | Source system (`HMIS`) |
| `active` | Boolean | NOT NULL (default true) | Operational status flag |

---

### 2.3 Observations (`observations`)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | String(128) | PRIMARY KEY | Unique observation record ID |
| `facility_id` | String(64) | FK -> `facilities.id`, INDEX | References facility |
| `indicator_id` | String(64) | FK -> `indicators.id`, INDEX | References indicator |
| `observation_date` | String(10) | INDEX, NOT NULL | First day of month ISO string (`YYYY-MM-01`) |
| `reporting_month` | String(7) | NOT NULL | Reporting period string (`YYYY-MM`) |
| `value` | Float | NULLABLE | Numeric count (**NULL preserves explicit missingness**) |
| `value_type` | String(32) | NOT NULL | Semantic type (`VALID`, `ZERO`, `MISSING`, `NOT_APPLICABLE`, `INVALID`) |
| `validation_status`| String(32) | NOT NULL | Data audit status (`VALIDATED`, `FLAGGED`) |
| `source_file` | String(255) | NOT NULL | Provenance: raw file name |
| `source_sheet` | String(128) | NULLABLE | Provenance: Excel sheet |
| `source_row` | Integer | NULLABLE | Provenance: raw row index |
| `ingested_at` | String(64) | NOT NULL | Pipeline ingestion timestamp |
| `transformation_version`| String(32)| NOT NULL | Pipeline software version |

**Composite Unique Constraint**:
- `UniqueConstraint("facility_id", "indicator_id", "observation_date", name="uq_facility_indicator_date")`

**Composite Index**:
- `idx_obs_fac_ind_date` on `(facility_id, indicator_id, observation_date)`

---

### 2.4 Forecasts (`forecasts`)
| Column Name | Data Type | Constraints | Description |
| :--- | :--- | :--- | :--- |
| `id` | String(128) | PRIMARY KEY | Unique forecast record ID |
| `facility_id` | String(64) | FK -> `facilities.id`, INDEX | References facility |
| `indicator_id` | String(64) | FK -> `indicators.id`, INDEX | References indicator |
| `forecast_date` | String(10) | INDEX, NOT NULL | Forecast target date (`YYYY-MM-01`) |
| `predicted_value` | Float | NOT NULL | Predicted healthcare demand count |
| `lower_bound` | Float | NULLABLE | Lower 95% confidence interval bound |
| `upper_bound` | Float | NULLABLE | Upper 95% confidence interval bound |
| `model_version` | String(32) | NOT NULL | ML model version tag |

---

### 2.5 Model Metadata (`model_metadata`)
Stores model evaluation metrics (MAE, RMSE, MAPE, baseline MAE) and JSON feature configurations.

### 2.6 Data Quality Logs (`data_quality_logs`)
Persists historical 13-point quality audit findings and sub-scores.

---

## 3. Database Migration Workflow (Alembic)

1. **Apply Migrations to Latest Schema**:
   ```bash
   alembic upgrade head
   ```
2. **Generate New Migration Revision**:
   ```bash
   alembic revision --autogenerate -m "Describe schema change"
   ```
3. **Rollback Last Migration**:
   ```bash
   alembic downgrade -1
   ```

---

## 4. Seeding & Processed Parquet Loader

- **Seed Standard Indicators**:
  ```bash
  python scripts/seed_indicators.py
  ```
- **Load Processed Parquet Datasets**:
  ```bash
  python scripts/load_processed_data.py
  ```
  *The loader is 100% idempotent and can be run safely multiple times without creating duplicate records or throwing constraint errors.*
