from typing import List, Dict, Any, Tuple, Optional
from pydantic import BaseModel

from backend.app.services.forecasting.dataset import ForecastingSeries
from backend.app.services.forecasting.baselines import BaseForecaster, NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, HoltWintersForecaster
from backend.app.services.forecasting.models import SARIMAXForecaster, RidgeLagForecaster, RandomForestLagForecaster, GradientBoostingLagForecaster
from backend.app.services.forecasting.evaluation import TimeAwareValidator, EvaluationMetrics, calculate_metrics


MODEL_SIMPLICITY_RANK = {
    "Naive": 1,
    "Seasonal Naive": 2,
    "Moving Average (3m)": 3,
    "Holt-Winters": 4,
    "Ridge": 5,
    "SARIMAX": 6,
    "Random Forest": 7,
    "Gradient Boosting": 8
}


class ModelEvaluationResult(BaseModel):
    model_name: str
    model_type: str
    is_baseline: bool
    simplicity_rank: int
    metrics: EvaluationMetrics
    validation_residuals: List[float]
    val_true: List[float]
    val_pred: List[float]


class ModelSelectionSummary(BaseModel):
    selected_model_name: str
    selected_model_type: str
    is_baseline_selected: bool
    strongest_baseline_name: str
    strongest_baseline_mae: float
    selected_mae: float
    improvement_over_baseline_pct: float
    selection_reason: str
    all_evaluations: List[Dict[str, Any]]


class ModelSelector:
    """
    Evaluates candidate models against mandatory baselines using chronological validation split.
    Selects model based on validation MAE, strongest baseline benchmark, and explicit tie-breaking rules.
    """

    def __init__(self, val_horizon: int = 12):
        self.val_horizon = val_horizon

    def get_all_candidates(self) -> List[Tuple[BaseForecaster, bool]]:
        """
        Returns tuples of (forecaster_instance, is_baseline).
        """
        return [
            # 4 Mandatory Baselines
            (NaiveForecaster(), True),
            (SeasonalNaiveForecaster(), True),
            (MovingAverageForecaster(3), True),
            (HoltWintersForecaster(), True),
            # 4 ML Model Candidates
            (SARIMAXForecaster(), False),
            (RidgeLagForecaster(), False),
            (RandomForestLagForecaster(), False),
            (GradientBoostingLagForecaster(), False)
        ]

    def select_best_model(
        self,
        series: ForecastingSeries
    ) -> Tuple[BaseForecaster, ModelSelectionSummary, ModelEvaluationResult]:
        candidates = self.get_all_candidates()
        evaluations: List[ModelEvaluationResult] = []
        fitted_forecasters: Dict[str, BaseForecaster] = {}

        for forecaster, is_baseline in candidates:
            try:
                metrics, val_true, val_pred = TimeAwareValidator.validate_forecaster(
                    forecaster, series, self.val_horizon
                )
                residuals = [t - p for t, p in zip(val_true, val_pred)]
                rank = MODEL_SIMPLICITY_RANK.get(forecaster.name, 99)

                eval_res = ModelEvaluationResult(
                    model_name=forecaster.name,
                    model_type=forecaster.name,
                    is_baseline=is_baseline,
                    simplicity_rank=rank,
                    metrics=metrics,
                    validation_residuals=residuals,
                    val_true=val_true,
                    val_pred=val_pred
                )
                evaluations.append(eval_res)
                fitted_forecasters[forecaster.name] = forecaster
            except Exception:
                continue

        if not evaluations:
            # Fallback if validation failed for all
            fallback = NaiveForecaster()
            fallback.fit(series.values_list, series.months_list)
            eval_res = ModelEvaluationResult(
                model_name="Naive",
                model_type="Naive",
                is_baseline=True,
                simplicity_rank=1,
                metrics=EvaluationMetrics(mae=0.0, rmse=0.0, smape=0.0, wape=0.0, mape=0.0),
                validation_residuals=[0.0],
                val_true=[],
                val_pred=[]
            )
            summary = ModelSelectionSummary(
                selected_model_name="Naive",
                selected_model_type="Naive",
                is_baseline_selected=True,
                strongest_baseline_name="Naive",
                strongest_baseline_mae=0.0,
                selected_mae=0.0,
                improvement_over_baseline_pct=0.0,
                selection_reason="Fallback to Naive due to evaluation error.",
                all_evaluations=[]
            )
            return fallback, summary, eval_res

        # 1. Identify strongest baseline
        baselines_eval = [e for e in evaluations if e.is_baseline]
        strongest_baseline = min(baselines_eval, key=lambda e: (e.metrics.mae, e.simplicity_rank))

        # 2. Identify candidate ML models
        ml_eval = [e for e in evaluations if not e.is_baseline]

        # Filter ML models that beat strongest baseline MAE
        improving_ml = [
            e for e in ml_eval if e.metrics.mae < strongest_baseline.metrics.mae
        ]

        if improving_ml:
            # Sort ML models by MAE, then by simplicity rank
            improving_ml.sort(key=lambda e: (e.metrics.mae, e.simplicity_rank))
            best_eval = improving_ml[0]

            # Tie-breaking rule check against strongest baseline
            rel_diff = (strongest_baseline.metrics.mae - best_eval.metrics.mae) / (strongest_baseline.metrics.mae + 1e-8)
            if rel_diff <= 0.01:
                # Within 1% tie margin; prefer simpler baseline model
                winner_eval = strongest_baseline
                reason = f"Baseline '{strongest_baseline.model_name}' selected because candidate MAE ({best_eval.metrics.mae}) is within 1% tie threshold of baseline MAE ({strongest_baseline.metrics.mae}). Preferring simpler model."
            else:
                winner_eval = best_eval
                reason = f"Candidate ML model '{best_eval.model_name}' selected as it outperformed strongest baseline '{strongest_baseline.model_name}' (MAE: {best_eval.metrics.mae} vs {strongest_baseline.metrics.mae})."
        else:
            winner_eval = strongest_baseline
            reason = f"Strongest baseline '{strongest_baseline.model_name}' selected. No ML candidate demonstrated validation MAE improvement over baseline."

        # Calculate improvement percentage over strongest baseline
        base_mae = strongest_baseline.metrics.mae
        win_mae = winner_eval.metrics.mae
        imp_pct = ((base_mae - win_mae) / (base_mae + 1e-8)) * 100.0 if base_mae > 0 else 0.0

        all_eval_dicts = [
            {
                "model_name": e.model_name,
                "is_baseline": e.is_baseline,
                "mae": e.metrics.mae,
                "rmse": e.metrics.rmse,
                "smape": e.metrics.smape,
                "wape": e.metrics.wape
            }
            for e in evaluations
        ]

        summary = ModelSelectionSummary(
            selected_model_name=winner_eval.model_name,
            selected_model_type=winner_eval.model_name,
            is_baseline_selected=winner_eval.is_baseline,
            strongest_baseline_name=strongest_baseline.model_name,
            strongest_baseline_mae=strongest_baseline.metrics.mae,
            selected_mae=winner_eval.metrics.mae,
            improvement_over_baseline_pct=round(imp_pct, 2),
            selection_reason=reason,
            all_evaluations=all_eval_dicts
        )

        selected_forecaster = fitted_forecasters[winner_eval.model_name]
        # Re-fit winning model on FULL series history up to cutoff N
        series_vals = series.values_list
        series_dates = series.months_list
        from backend.app.services.forecasting.features import impute_training_series
        clean_vals = impute_training_series(series_vals)
        selected_forecaster.fit(clean_vals, series_dates)

        return selected_forecaster, summary, winner_eval
