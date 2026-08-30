# HMIS Data Quality Framework & Scoring Methodology

## 1. 13-Point Quality Audit Checks

| Check # | Check Name | Severity | Description & Threshold |
| :--- | :--- | :--- | :--- |
| **1** | Missing Values | WARNING / ERROR | Percentage of missing value cells (>15% triggers ERROR). |
| **2** | Duplicate Records | WARNING / ERROR | Composite key duplicates (`facility_id` + `indicator` + `month`). |
| **3** | Invalid Dates | ERROR | Unparseable or malformed reporting period strings. |
| **4** | Invalid Numeric Values | ERROR | Non-numeric string noise in count columns. |
| **5** | Negative Healthcare Counts | CRITICAL | Impossible negative healthcare counts (e.g. -50 admissions). |
| **6** | Suspicious Extreme Values | WARNING | Outliers exceeding conservative 5x IQR distance. |
| **7** | Missing Reporting Periods | WARNING | Temporal gaps in monthly facility timeseries. |
| **8** | Facility Identifier Consistency | INFO | Facilities lacking official HMIS codes (composite hash assigned). |
| **9** | State / District Consistency | WARNING | Unrecognized or inconsistent administrative region names. |
| **10**| Indicator Catalog Consistency | WARNING | Raw headers unmapped to standard HMIS catalog. |
| **11**| Reporting Completeness | WARNING / ERROR | Percentage of expected monthly reports present per facility. |
| **12**| Temporal Continuity | WARNING | Consecutive missing reporting months. |
| **13**| Source File Integrity | CRITICAL | File corruption or 0-row empty dataset flags. |

---

## 2. Quality Score Formula (0 - 100)

$$\text{Overall Score} = 0.30 \cdot S_{\text{completeness}} + 0.25 \cdot S_{\text{validity}} + 0.15 \cdot S_{\text{duplication}} + 0.15 \cdot S_{\text{consistency}} + 0.15 \cdot S_{\text{temporal}}$$

- **Completeness Sub-Score ($S_{\text{completeness}}$)**: $100 - (\%\text{ missing} \times 1.5)$
- **Validity Sub-Score ($S_{\text{validity}}$)**: $100 - (\%\text{ invalid numeric} \times 3.0 + \%\text{ negative} \times 5.0)$
- **Duplication Sub-Score ($S_{\text{duplication}}$)**: $100 - (\%\text{ duplicates} \times 2.0)$
- **Consistency Sub-Score ($S_{\text{consistency}}$)**: $100 - (\%\text{ invalid dates} \times 3.0)$
- **Temporal Sub-Score ($S_{\text{temporal}}$)**: $100 - (\%\text{ outliers} \times 2.0)$

Outputs are capped at $[0.0, 100.0]$ and rounded to 1 decimal place.
