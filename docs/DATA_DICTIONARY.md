# CAREFlow Data Dictionary & Schema Specification

## 1. Facilities Entity Schema (`data/processed/facilities.parquet`)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `facility_id` | String (PK) | Standardized internal ID (`FC_<code>` or `FKEY_<hash>`) |
| `facility_code` | String (Nullable)| Official HMIS Facility Code |
| `facility_name` | String | Standardized facility display name |
| `facility_type` | String | Facility type (DH, CHC, PHC, SC, MEDICAL_COLLEGE, etc.) |
| `state` | String | Standardized State name |
| `district` | String | Standardized District name |
| `sub_district` | String (Nullable)| Sub-district / Block name |
| `raw_facility_name`| String | Original facility name for provenance |
| `raw_district_name`| String (Nullable)| Original district name for provenance |

---

## 2. Observations Timeseries Schema (`data/processed/observations.parquet`)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `obs_id` | String (PK) | Unique observation record ID |
| `facility_id` | String (FK) | References `facilities.facility_id` |
| `facility_code` | String | Official HMIS code if available |
| `facility_name` | String | Facility display name |
| `district` | String | Administrative district name |
| `state` | String | Administrative state name |
| `indicator_code` | String | Stable indicator code (e.g. `opd_attendance`) |
| `raw_column_name` | String | Original Excel/CSV header name |
| `reporting_month` | String | Standardized reporting month (`YYYY-MM`) |
| `observation_date` | String | ISO first day of month (`YYYY-MM-01`) |
| `value` | Float64 (Nullable)| Numeric count value |
| `value_type` | String | Value semantic (`VALID`, `ZERO`, `MISSING`, `NOT_APPLICABLE`, `INVALID`) |
| `raw_value_str` | String (Nullable)| Original cell string for provenance |
| `source_file` | String | Raw file name |
| `source_sheet` | String | Raw Excel sheet name |
| `raw_row_number` | Int64 | Original row index in source file |
| `ingested_at` | String | UTC ISO timestamp of pipeline run |
| `transformation_version`| String | Version string of pipeline runner |

---

## 3. Indicators Catalog Schema (`data/processed/indicators.parquet`)

| Column Name | Data Type | Description |
| :--- | :--- | :--- |
| `code` | String (PK) | Stable indicator code |
| `name` | String | Standardized display name |
| `category` | String | Healthcare operational category |
| `unit` | String | Measurement unit (`visits`, `admissions`, `deliveries`, `children`) |
| `aliases` | List[String] | Recognized header aliases |
| `regex_patterns` | List[String] | Recognized regex matching patterns |
