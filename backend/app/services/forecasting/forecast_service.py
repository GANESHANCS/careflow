from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
import numpy as np

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.forecast import Forecast
from backend.app.services.forecasting.dataset import ForecastingSeries, ForecastingPoint
from backend.app.services.forecasting.eligibility import EligibilityEvaluator, EligibilityResult
from backend.app.services.forecasting.selection import ModelSelector
from backend.app.services.forecasting.intervals import PredictionIntervalEstimator
from backend.app.services.forecasting.registry import ForecastModelRegistry


ALLOWED_HORIZONS = {3, 6, 12}
MODEL_VERSION = "1.0.0"
SYNTHETIC_DATA_DISCLAIMER = "SYNTHETIC / NON-REPRESENTATIVE — Validation performed on synthetic fixtures for framework verification."


class ForecastingService:
    """
    Core Service Layer for Healthcare Demand Time-Series Forecasting.
    """

    @classmethod
    def load_forecasting_series(
        cls,
        db: Session,
        facility_id: str,
        indicator_code: str
    ) -> Tuple[Optional[Facility], Optional[Indicator], Optional[ForecastingSeries]]:
        # Fetch facility
        facility = db.query(Facility).filter(
            (Facility.id == facility_id) | (Facility.facility_code == facility_id)
        ).first()

        # Fetch indicator (case-insensitive code or ID)
        indicator = db.query(Indicator).filter(
            (Indicator.code == indicator_code) |
            (Indicator.code == indicator_code.lower()) |
            (Indicator.code == indicator_code.upper()) |
            (Indicator.id == indicator_code)
        ).first()


        if not facility or not indicator:
            return facility, indicator, None

        # Fetch observations
        obs_rows = db.query(Observation).filter(
            Observation.facility_id == facility.id,
            Observation.indicator_id == indicator.id
        ).order_by(Observation.observation_date.asc()).all()

        points = []
        for o in obs_rows:
            is_miss = o.value is None or o.value_type in ("MISSING", "INVALID")
            points.append(
                ForecastingPoint(
                    observation_month=o.reporting_month,
                    observation_date=o.observation_date,
                    observed_value=o.value,
                    status=o.value_type,
                    is_missing=is_miss,
                    is_imputed=o.value_type == "IMPUTED",
                    data_quality_status=o.validation_status
                )
            )

        valid_count = sum(1 for p in points if not p.is_missing)
        tot_count = len(points)
        completeness = valid_count / tot_count if tot_count > 0 else 0.0

        series = ForecastingSeries(
            facility_id=facility.id,
            facility_name=facility.facility_name,
            district=facility.district,
            indicator_code=indicator.code,
            points=points,
            reporting_completeness=completeness,
            data_quality_score=round(completeness * 100.0, 1)
        )

        return facility, indicator, series

    @classmethod
    def generate_forecast(
        cls,
        db: Session,
        facility_id: str,
        indicator_code: str,
        horizon: int = 12
    ) -> Dict[str, Any]:
        if horizon not in ALLOWED_HORIZONS:
            raise ValueError(f"Invalid forecast horizon: {horizon}. Must be one of {sorted(list(ALLOWED_HORIZONS))}.")

        facility, indicator, series = cls.load_forecasting_series(db, facility_id, indicator_code)

        if not facility:
            return {
                "status": "ERROR",
                "error_code": "FACILITY_NOT_FOUND",
                "message": f"Facility '{facility_id}' was not found."
            }

        if not indicator:
            return {
                "status": "ERROR",
                "error_code": "INDICATOR_NOT_FOUND",
                "message": f"Indicator '{indicator_code}' was not found."
            }

        if not series or series.total_observations == 0:
            return {
                "status": "NOT_ELIGIBLE",
                "facility": {"id": facility.id, "name": facility.facility_name, "district": facility.district},
                "indicator": {"code": indicator.code, "name": indicator.name},
                "forecast_horizon": horizon,
                "eligibility": {
                    "is_eligible": False,
                    "status": "NOT_ELIGIBLE",
                    "reason_code": "INSUFFICIENT_HISTORY",
                    "reason_message": "No historical observations found for this facility and indicator."
                },
                "disclaimer": SYNTHETIC_DATA_DISCLAIMER
            }

        # Step 1: Construct historical points list
        historical_points = [
            {
                "observation_month": p.observation_month,
                "observation_date": p.observation_date,
                "observed_value": p.observed_value,
                "is_missing": p.is_missing,
                "is_imputed": p.is_imputed,
                "status": p.status,
            }
            for p in series.points
        ]

        # Step 1: Check eligibility
        evaluator = EligibilityEvaluator()
        eligibility = evaluator.evaluate(series, forecast_horizon=horizon)

        if not eligibility.is_eligible:
            return {
                "status": "NOT_ELIGIBLE",
                "facility": {"id": facility.id, "name": facility.facility_name, "district": facility.district},
                "indicator": {"code": indicator.code, "name": indicator.name},
                "forecast_horizon": horizon,
                "historical_points": historical_points,
                "eligibility": eligibility.model_dump(),
                "data_quality": {
                    "reporting_completeness_pct": round(series.reporting_completeness * 100.0, 1),
                    "quality_score": series.data_quality_score,
                    "total_observations": series.total_observations,
                    "missing_count": series.missing_count
                },
                "disclaimer": SYNTHETIC_DATA_DISCLAIMER
            }

        # Step 2: Model Selection & Training
        selector = ModelSelector(val_horizon=horizon)
        winning_forecaster, selection_summary, eval_res = selector.select_best_model(series)

        # Step 3: Multi-step prediction
        predictions = winning_forecaster.predict(horizon)

        # Step 4: 95% Prediction Intervals
        interval_res = PredictionIntervalEstimator.calculate_intervals(
            predictions, eval_res.validation_residuals
        )

        # Generate future month dates starting after last observed month
        last_date = series.months_list[-1]
        yr, mo = int(last_date[:4]), int(last_date[5:7])

        forecast_points = []
        forecast_entities_to_upsert = []

        for p_val, l_bound, u_bound in zip(
            interval_res.predicted_values, interval_res.lower_bounds, interval_res.upper_bounds
        ):
            mo += 1
            if mo > 12:
                mo = 1
                yr += 1
            f_month = f"{yr:04d}-{mo:02d}"
            f_date_str = f"{f_month}-01"

            forecast_points.append({
                "forecast_month": f_month,
                "forecast_date": f_date_str,
                "predicted_value": p_val,
                "lower_bound": l_bound,
                "upper_bound": u_bound
            })

            fc_id = f"fc_{facility.id}_{indicator.id}_{f_date_str}_{MODEL_VERSION}"
            forecast_entities_to_upsert.append(
                Forecast(
                    id=fc_id,
                    facility_id=facility.id,
                    indicator_id=indicator.id,
                    forecast_date=f_date_str,
                    predicted_value=p_val,
                    lower_bound=l_bound,
                    upper_bound=u_bound,
                    model_version=MODEL_VERSION
                )
            )

        # Step 5: Idempotent Forecast Persistence
        for fc_item in forecast_entities_to_upsert:
            existing = db.query(Forecast).filter(Forecast.id == fc_item.id).first()
            if existing:
                existing.predicted_value = fc_item.predicted_value
                existing.lower_bound = fc_item.lower_bound
                existing.upper_bound = fc_item.upper_bound
            else:
                db.add(fc_item)

        # Step 6: Model Metadata Registry Persistence
        training_start = series.months_list[0]
        training_end = series.months_list[-1]
        ForecastModelRegistry.register_model_metadata(
            db=db,
            model_version=MODEL_VERSION,
            model_type=winning_forecaster.name,
            target_indicator=indicator.code,
            training_start=training_start,
            training_end=training_end,
            mae=eval_res.metrics.mae,
            rmse=eval_res.metrics.rmse,
            mape=eval_res.metrics.mape,
            baseline_mae=selection_summary.strongest_baseline_mae,
            features={"selected_model": winning_forecaster.name, "horizon": horizon}
        )

        db.commit()

        # Step 7: Construct Explainable Payload
        explainability = {
            "model_title": f"Forecast generated using {winning_forecaster.name}",
            "historical_months_count": series.total_observations,
            "reporting_completeness_pct": f"{series.reporting_completeness * 100.0:.1f}%",
            "validation_mae": eval_res.metrics.mae,
            "prediction_interval_description": "95% prediction interval (approximate residual-based bounds)",
            "baseline_benchmark_model": selection_summary.strongest_baseline_name,
            "improvement_over_baseline": f"{selection_summary.improvement_over_baseline_pct:.1f}%",
            "selection_rationale": selection_summary.selection_reason
        }

        return {
            "status": "SUCCESS",
            "facility": {
                "id": facility.id,
                "name": facility.facility_name,
                "district": facility.district,
                "facility_type": facility.facility_type
            },
            "indicator": {
                "id": indicator.id,
                "code": indicator.code,
                "name": indicator.name,
                "unit": indicator.unit
            },
            "forecast_horizon": horizon,
            "model": {
                "model_version": MODEL_VERSION,
                "model_type": winning_forecaster.name,
                "is_baseline": selection_summary.is_baseline_selected
            },
            "training_period": {
                "start_month": training_start,
                "end_month": training_end,
                "total_observations": series.total_observations
            },
            "historical_points": historical_points,
            "forecast_points": forecast_points,
            "prediction_intervals": {
                "interval_type": interval_res.interval_type,
                "residual_std_error": interval_res.residual_std_error
            },
            "validation_metrics": eval_res.metrics.model_dump(),
            "baseline_metrics": {
                "strongest_baseline_name": selection_summary.strongest_baseline_name,
                "strongest_baseline_mae": selection_summary.strongest_baseline_mae
            },
            "candidate_evaluations": selection_summary.all_evaluations,
            "improvement_over_baseline_pct": selection_summary.improvement_over_baseline_pct,
            "eligibility": eligibility.model_dump(),
            "explainability": explainability,
            "disclaimer": SYNTHETIC_DATA_DISCLAIMER
        }
