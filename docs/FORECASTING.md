# CAREFlow India — Time-Series Forecasting Architecture

## 1. Overview

The forecasting module (`backend/app/services/forecasting/`) provides a clean, modular, and reproducible time-series prediction framework.

---

## 2. Directory & Module Structure

```
backend/app/services/forecasting/
├── dataset.py            # Forecasting Data Contract (ForecastingSeries, ForecastingPoint)
├── eligibility.py        # Configurable diagnostic eligibility evaluator
├── features.py           # Strictly time-aware feature engineering (lags t-1..t-12, rolling stats, calendar)
├── baselines.py          # Naive, Seasonal Naive, Moving Average, Holt-Winters
├── models.py             # SARIMAX, Ridge, Random Forest, Gradient Boosting
├── evaluation.py        # Expanding-window chronological validator & zero-safe metrics
├── intervals.py         # 95% approximate prediction interval estimator
├── selection.py          # Strongest baseline benchmark & candidate model selector
├── registry.py           # ModelMetadata registry DB interface
├── forecast_service.py   # High-level pipeline orchestrator & REST API service
└── __init__.py           # Package export interface
```

---

## 3. Reproducible CLI Training

Run training and evaluation across all facility-indicator time series:

```bash
python scripts/train_forecasting_models.py
```

### Seeding Synthetic Observations for Local Development:
```bash
python scripts/seed_forecasting_data.py
```

---

## 4. Idempotent Database Persistence

- **Forecast Table (`forecasts`)**: Primary key `fc_{facility_id}_{indicator_id}_{forecast_date}_{model_version}` prevents duplicate rows across repeated training runs.
- **Model Registry (`model_metadata`)**: Primary key `meta_{model_version}_{target_indicator}` updates model evaluation history.

---

## 5. REST API Endpoints

### `GET /api/forecast`
- **Parameters**: `facility_id` (str, required), `indicator_code` (str, default `"opd_attendance"`), `horizon` (int: 3, 6, 12, default 12).
- **Response**: Full forecast points, prediction bounds, validation metrics, baseline comparison, eligibility diagnostic, explainability text, and synthetic disclaimer.

### `GET /api/model/metrics`
- **Parameters**: `target_indicator` (optional str).
- **Response**: Summary list of registered model metadata, training periods, MAE, RMSE, sMAPE, and improvement percentages over baselines.
