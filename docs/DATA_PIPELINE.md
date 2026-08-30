# HMIS Data Ingestion & Transformation Pipeline (Phase 2)

## 1. Overview
The CAREFlow Data Pipeline ingests, normalizes, standardizes, deduplicates, and evaluates Indian Government Health Management Information System (HMIS) monthly reporting datasets.

```
┌─────────────────────────────────────────────────────────────┐
│                 Raw HMIS Source Files                       │
│                   (data/raw/*.xlsx, *.csv)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                   HMIS File Inspector                       │
│    (Header Detection, Sheet Inspection, Type Inference)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Schema & Value Normalizer                  │
│   (Snake-case headers, NA/null parsing, Date ISO format)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  HMIS Indicator Catalog                     │
│  (Regex mapping to stable codes: OPD, IPD, ANC, PNC, etc.)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Entity Standardizer                        │
│   (Facility Code primary key, composite hash fallback)      │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                  Deduplication Engine                       │
│  (Facility + Indicator + Month logical uniqueness check)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 13-Point Quality Engine                     │
│     (Outlier detection, completeness, quality score)        │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                Processed Parquet Datasets                   │
│        (facilities.parquet, observations.parquet,           │
│       indicators.parquet, data_quality_report.json)         │
└─────────────────────────────────────────────────────────────┘
```

## 2. Ingestion Rules & Data Integrity
1. **Raw Preservation**: Files in `data/raw/` are treated as immutable source artifacts.
2. **Missing vs Zero vs Not Applicable**:
   - `MISSING`: Null, empty, "NA", "-", "None" (Value is absent).
   - `ZERO`: 0 or 0.0 (Value was reported as zero demand).
   - `NOT_APPLICABLE`: Explicit "Not Applicable" text token.
3. **Indicator Catalog Mapping**:
   - Standard stable indicators: `opd_attendance`, `inpatient_admissions`, `institutional_deliveries`, `antenatal_visits`, `postnatal_visits`, `immunisation`.
   - Extensible: Dynamic headers are normalized and auto-registered with `ind_` prefix if not present in standard regex catalog.

## 3. Command Line Execution

### Inspect Raw Files
```bash
python scripts/inspect_hmis_files.py
```

### Run Full Pipeline
```bash
python scripts/run_phase2_pipeline.py
```
If no real HMIS files exist in `data/raw/`, the command reports `REAL HMIS FILES FOUND: NO` and ready status.
