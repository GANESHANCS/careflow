# CAREFlow India — Machine Learning & Time-Series Methodology

> [!IMPORTANT]
> **SYNTHETIC DATA INTEGRITY DISCLAIMER**
> Real HMIS data is NOT available yet. All forecasting models, feature engineering pipelines, time-aware validations, and baseline benchmark comparisons documented in Phase 5 were evaluated using synthetic fixtures (`SYNTHETIC / NON-REPRESENTATIVE`). These metrics validate system mechanics and reproducibility; they do NOT claim to represent actual HMIS predictive accuracy.

---

## 1. Problem Formulation & Forecasting Targets

The CAREFlow India forecasting engine provides reproducible, time-aware monthly healthcare demand forecasts for facility and district-level decision support.

### Targets:
- **Primary Target**: Monthly Outpatient Department (OPD) Attendance (`opd_attendance`)
- **Secondary Targets**:
  - Inpatient Admissions / IPD (`inpatient_admissions`)
  - Institutional Deliveries (`institutional_deliveries`)

---

## 2. Time-Series Eligibility Guardrails

Before fitting any model, time-series eligibility is strictly evaluated to prevent fitting models onto inadequate data.

| Eligibility Rule | Threshold / Condition | Machine-Readable Reason Code |
| :--- | :--- | :--- |
| **Minimum History** | $< 12$ observations (3m/6m horizons) | `INSUFFICIENT_HISTORY` |
| **Seasonal History** | $< 24$ observations (12m primary horizon) | `INSUFFICIENT_SEASONAL_HISTORY` |
| **Excessive Missingness** | $> 30\%$ missing observation ratio | `EXCESSIVE_MISSINGNESS` |
| **Consecutive Gaps** | $> 3$ consecutive missing months | `EXCESSIVE_GAPS` |
| **Reporting Completeness** | $< 70\%$ reporting completeness | `LOW_REPORTING_COMPLETENESS` |

Series failing any criterion are assigned status `NOT_ELIGIBLE` with descriptive diagnostic metadata.

---

## 3. Missing Data & Outlier Strategy

### Missingness Handling:
- Missing observations are NEVER silently converted to zero.
- Preserved statuses: `OBSERVED_ZERO`, `MISSING`, `INVALID`, `IMPUTED`.
- Imputation (historical linear/forward-fill) is executed **strictly within the training fold**. Future/validation data is never used for training imputation.

### Outlier Handling:
- Healthcare spikes (e.g. seasonal epidemic surges) are treated as legitimate demand events rather than automatically removed. Extreme anomalies due to recorded data-quality errors are flagged with `SUSPECT` quality status.

---

## 4. Time-Aware Validation & Data Leakage Prevention

- **Chronological Split**: Expanding-window chronological validation split ($training\_end < validation\_start$).
- **No Future Data Leakage**: Supervised feature engineering at cutoff $t$ uses information strictly at or before $t-1$.
- **Validation Horizon**: Primary horizon of 12 months (supported: 3, 6, 12 months).

---

## 5. Candidate Models & Baseline Primacy

Every candidate model is evaluated against the **strongest baseline**:

### 4 Mandatory Baselines:
1. **Naive**: $y_{t+h} = y_t$
2. **Seasonal Naive**: $y_{t+h} = y_{t+h-12}$
3. **Moving Average (3m)**: Rolling average of last 3 months
4. **Holt-Winters**: Exponential smoothing with additive trend and seasonality

### 4 ML Model Candidates:
5. **SARIMAX**: $(1,1,1) \times (1,1,0)_{12}$ Seasonal ARIMA
6. **Ridge Regression**: L2 regularized linear model with lag/calendar features
7. **Random Forest**: Ensemble decision tree regressor with lag features
8. **Gradient Boosting**: Gradient boosted decision tree regressor with lag features

### Model Selection Logic & Tie-Breaking Rule:
- All 4 baselines are evaluated first; the baseline with the lowest validation MAE is designated the **strongest baseline**.
- An ML candidate is selected ONLY if its validation MAE improves upon the strongest baseline by $> 1\%$.
- If no ML model improves upon the strongest baseline, the strongest baseline is selected ("Baseline performs best").
- **Tie-Breaking Order** (Simpler preferred): Naive < Seasonal Naive < Moving Average < Holt-Winters < Ridge < SARIMAX < Random Forest < Gradient Boosting.

---

## 6. Uncertainty Prediction Intervals

- **Interval Type**: `95% prediction interval (approximate)`
- **Calculation**: $\hat{y} \pm 1.96 \cdot s_{residuals}$ where $s_{residuals}$ is sample standard deviation of validation residuals.
- **Constraints**: Non-negative lower bounds ($\max(0.0, \text{bound})$) for volume count metrics.

---

## 7. Model Metrics & Evaluation Metrics

- **MAE**: Mean Absolute Error (Primary Selection Metric)
- **RMSE**: Root Mean Squared Error
- **sMAPE**: Symmetric Mean Absolute Percentage Error (handles zero values safely)
- **WAPE**: Weighted Absolute Percentage Error
- **MAPE**: Mean Absolute Percentage Error (zero-safe)
