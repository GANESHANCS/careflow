from typing import Dict, Any, List, Optional, Tuple
import math
from datetime import datetime, timezone
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.anomaly_review import DistrictAnomalyReview
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus
from backend.app.services.forecasting.baselines import NaiveForecaster, MovingAverageForecaster
from backend.app.services.forecasting.evaluation import calculate_metrics
from backend.app.schemas.district_analytics import (
    VerifiedIndicatorOverviewResponse,
    VerifiedIndicatorTimeSeriesPoint,
    ForecastingReadinessResponse,
    AnomalySignalItem,
    DistrictAnomalyReportResponse,
)


class IneligibleIndicatorError(Exception):
    """Raised when an indicator is not VERIFIED or is otherwise ineligible for trusted canonical analytics."""
    pass


class LinearDriftForecaster:
    """
    Simple deterministic linear drift forecaster fitting slope and intercept on training window.
    """
    def __init__(self):
        self.slope = 0.0
        self.intercept = 0.0
        self.history_len = 0

    def fit(self, history_values: List[float]) -> "LinearDriftForecaster":
        n = len(history_values)
        self.history_len = n
        if n < 2:
            self.slope = 0.0
            self.intercept = history_values[0] if n == 1 else 0.0
            return self

        x = np.arange(n, dtype=float)
        y = np.array(history_values, dtype=float)
        x_mean = float(np.mean(x))
        y_mean = float(np.mean(y))

        denom = float(np.sum((x - x_mean) ** 2))
        if denom > 1e-8:
            self.slope = float(np.sum((x - x_mean) * (y - y_mean)) / denom)
            self.intercept = y_mean - self.slope * x_mean
        else:
            self.slope = 0.0
            self.intercept = y_mean
        return self

    def predict(self, horizon: int) -> List[float]:
        preds = []
        for h in range(horizon):
            idx = self.history_len + h
            val = self.slope * idx + self.intercept
            preds.append(max(0.0, float(val)))
        return preds


class HealthcareIntelligenceService:
    """
    Phase 14 Reusable Healthcare Intelligence Service.
    Enforces strict verified-indicator eligibility, transparent single-year forecasting readiness,
    chronological train/hold-out separation, and conservative non-parametric early-warning analytics.
    """

    STANDARD_FY_MONTHS = {
        "2015-16": [
            "2015-04", "2015-05", "2015-06", "2015-07",
            "2015-08", "2015-09", "2015-10", "2015-11",
            "2015-12", "2016-01", "2016-02", "2016-03"
        ]
    }

    def __init__(self, db: Session):
        self.db = db

    # =========================================================================
    # Helpers
    # =========================================================================

    def _resolve_expected_months(self, financial_year: Optional[str]) -> List[str]:
        fy = financial_year or "2015-16"
        if fy in self.STANDARD_FY_MONTHS:
            return list(self.STANDARD_FY_MONTHS[fy])

        # Attempt to parse standard Indian FY format: YYYY-YY
        parts = fy.split("-")
        if len(parts) == 2 and len(parts[0]) == 4:
            try:
                start_year = int(parts[0])
                months = []
                for m in range(4, 13):
                    months.append(f"{start_year:04d}-{m:02d}")
                for m in range(1, 4):
                    months.append(f"{start_year + 1:04d}-{m:02d}")
                return months
            except ValueError:
                pass

        # Query distinct observed months from database as fallback
        query = self.db.query(DistrictObservation.reporting_month).distinct()
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year)
        months = [r[0] for r in query.order_by(DistrictObservation.reporting_month.asc()).all()]
        return months or list(self.STANDARD_FY_MONTHS["2015-16"])

    def _resolve_preferred_subgroup(self, s_no: str, reporting_month: Optional[str] = None) -> str:
        q = self.db.query(DistrictObservation.subgroup_type).filter(
            func.lower(DistrictObservation.s_no) == s_no.lower().strip()
        )
        if reporting_month:
            q = q.filter(DistrictObservation.reporting_month == reporting_month.strip())
        avail = [r[0] for r in q.distinct().all()]

        for pref in ["TOTAL", "Total", "4. Total", "3. Total"]:
            if pref in avail:
                return pref
        return avail[0] if avail else "TOTAL"

    def _validate_indicator_eligibility(self, s_no: str, allow_stock: bool = False) -> Any:
        mapping = IndicatorMappingRegistry.get_mapping(s_no)
        if mapping.status != MappingStatus.VERIFIED:
            raise IneligibleIndicatorError(
                f"Indicator '{s_no}' has status '{mapping.status.value}'. "
                "Only VERIFIED indicators are eligible for trusted canonical analytics. "
                f"Rationale: {mapping.rationale}"
            )
        if not allow_stock and mapping.is_stock_metric:
            raise IneligibleIndicatorError(
                f"Indicator '{s_no}' is classified as a point-in-time stock metric. "
                "Temporal aggregation and demand forecasting on stock indicators are prohibited."
            )
        return mapping

    # =========================================================================
    # Phase 14B: Verified Indicator Time-Series Analytics Foundation
    # =========================================================================

    def get_verified_indicator_timeseries(
        self,
        district: str,
        s_no: str,
        subgroup_type: Optional[str] = None,
        financial_year: Optional[str] = "2015-16"
    ) -> VerifiedIndicatorOverviewResponse:
        mapping = self._validate_indicator_eligibility(s_no, allow_stock=True)
        resolved_sg = subgroup_type or self._resolve_preferred_subgroup(s_no)
        expected_months = self._resolve_expected_months(financial_year)

        # Query database observations
        query = self.db.query(DistrictObservation).filter(
            func.lower(DistrictObservation.district) == district.lower().strip(),
            func.lower(DistrictObservation.s_no) == s_no.lower().strip(),
            func.lower(DistrictObservation.subgroup_type) == resolved_sg.lower().strip()
        )
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year.strip())

        obs_map = {row.reporting_month: row for row in query.all()}

        # Build chronologically ordered point series with zero vs missing distinction
        points: List[VerifiedIndicatorTimeSeriesPoint] = []
        valid_numeric_values: List[float] = []
        zero_count = 0
        missing_count = 0

        param_name = mapping.parameter_name

        for m in expected_months:
            obs = obs_map.get(m)
            if obs is not None:
                param_name = obs.parameter_name
                is_zero = (obs.value == 0.0) and (obs.value_type != "MISSING")
                is_miss = (obs.value is None) or (obs.value_type in ("MISSING", "INVALID"))

                if is_zero:
                    zero_count += 1
                    valid_numeric_values.append(0.0)
                elif not is_miss and obs.value is not None:
                    valid_numeric_values.append(float(obs.value))
                else:
                    missing_count += 1

                points.append(
                    VerifiedIndicatorTimeSeriesPoint(
                        month=m,
                        date=obs.observation_date,
                        value=float(obs.value) if obs.value is not None and not is_miss else None,
                        value_type="OBSERVED_ZERO" if is_zero else ("MISSING" if is_miss else obs.value_type),
                        is_zero=is_zero,
                        is_missing=is_miss
                    )
                )
            else:
                missing_count += 1
                points.append(
                    VerifiedIndicatorTimeSeriesPoint(
                        month=m,
                        date=f"{m}-01",
                        value=None,
                        value_type="MISSING",
                        is_zero=False,
                        is_missing=True
                    )
                )

        total_expected = len(expected_months)
        reported_count = total_expected - missing_count
        valid_count = len(valid_numeric_values) - zero_count
        completeness = round(reported_count / max(1, total_expected), 4)

        mean_val = round(float(np.mean(valid_numeric_values)), 2) if valid_numeric_values else None
        median_val = round(float(np.median(valid_numeric_values)), 2) if valid_numeric_values else None
        min_val = round(float(np.min(valid_numeric_values)), 2) if valid_numeric_values else None
        max_val = round(float(np.max(valid_numeric_values)), 2) if valid_numeric_values else None
        std_val = round(float(np.std(valid_numeric_values)), 2) if len(valid_numeric_values) >= 2 else 0.0

        stock_warning = None
        if mapping.is_stock_metric:
            stock_warning = (
                "Indicator represents point-in-time capacity or inventory stock. "
                "Temporal summation across reporting months is statistically invalid and prohibited."
            )

        return VerifiedIndicatorOverviewResponse(
            s_no=s_no,
            parameter_name=param_name,
            canonical_id=mapping.canonical_id or f"IND_{s_no}",
            canonical_name=mapping.canonical_name or param_name,
            category=mapping.category or "General Health",
            unit=mapping.unit or "counts",
            mapping_status=mapping.status.value,
            provenance=mapping.provenance,
            rationale=mapping.rationale,
            is_stock_metric=mapping.is_stock_metric,
            temporal_aggregation_permitted=not mapping.is_stock_metric,
            district=district,
            subgroup_type=resolved_sg,
            financial_year=financial_year or "2015-16",
            total_expected_months=total_expected,
            reported_months_count=reported_count,
            valid_months_count=valid_count,
            zero_months_count=zero_count,
            missing_months_count=missing_count,
            completeness_ratio=completeness,
            mean_value=mean_val,
            median_value=median_val,
            min_value=min_val,
            max_value=max_val,
            std_dev=std_val,
            points=points,
            stock_warning=stock_warning
        )

    # =========================================================================
    # Phase 14C: Forecasting Readiness & Baseline Models
    # =========================================================================

    def evaluate_forecasting_readiness(
        self,
        district: str,
        s_no: str,
        horizon: int = 3,
        subgroup_type: Optional[str] = None,
        financial_year: Optional[str] = "2015-16"
    ) -> ForecastingReadinessResponse:
        mapping = self._validate_indicator_eligibility(s_no, allow_stock=True)
        resolved_sg = subgroup_type or self._resolve_preferred_subgroup(s_no)

        dataset_limitation = (
            "Current HMIS archive contains single-year administrative returns (12 calendar months: 2015-04 to 2016-03). "
            "Single-year data cannot establish reliable multi-year seasonal cycles or long-horizon forecasts. "
            "Evaluation is strictly constrained to short-horizon (1–3 months) baseline models evaluated on chronological hold-outs."
        )
        clinical_disclaimer = (
            "Statistical baseline models are descriptive algorithmic projections based strictly on historical trends. "
            "They are not clinically validated and do not incorporate epidemiological transmission dynamics or health system shocks."
        )

        # Check stock metric eligibility
        if mapping.is_stock_metric:
            return ForecastingReadinessResponse(
                district=district,
                s_no=s_no,
                parameter_name=mapping.parameter_name,
                canonical_id=mapping.canonical_id,
                canonical_name=mapping.canonical_name,
                subgroup_type=resolved_sg,
                financial_year=financial_year or "2015-16",
                requested_horizon=horizon,
                is_ready=False,
                readiness_status="INELIGIBLE_STOCK_METRIC",
                readiness_reason="Point-in-time stock and capacity metrics are ineligible for volume forecasting.",
                dataset_limitation=dataset_limitation,
                clinical_validation_disclaimer=clinical_disclaimer,
                historical_months_available=12,
                historical_months_required=12
            )

        # Fetch time-series
        ts = self.get_verified_indicator_timeseries(
            district=district,
            s_no=s_no,
            subgroup_type=resolved_sg,
            financial_year=financial_year
        )

        avail_months = ts.reported_months_count

        # Horizon limit check: with 12 months, horizon > 3 is rejected
        if horizon > 3:
            return ForecastingReadinessResponse(
                district=district,
                s_no=s_no,
                parameter_name=ts.parameter_name,
                canonical_id=ts.canonical_id,
                canonical_name=ts.canonical_name,
                subgroup_type=resolved_sg,
                financial_year=financial_year or "2015-16",
                requested_horizon=horizon,
                is_ready=False,
                readiness_status="INSUFFICIENT_HISTORY",
                readiness_reason=(
                    f"Requested forecast horizon of {horizon} months requires at least 24 months of longitudinal history "
                    f"to establish seasonal stability. Only {avail_months} historical months are available."
                ),
                dataset_limitation=dataset_limitation,
                clinical_validation_disclaimer=clinical_disclaimer,
                historical_months_available=avail_months,
                historical_months_required=24
            )

        # Completeness requirement: at least 9 valid months out of 12
        if avail_months < 9:
            return ForecastingReadinessResponse(
                district=district,
                s_no=s_no,
                parameter_name=ts.parameter_name,
                canonical_id=ts.canonical_id,
                canonical_name=ts.canonical_name,
                subgroup_type=resolved_sg,
                financial_year=financial_year or "2015-16",
                requested_horizon=horizon,
                is_ready=False,
                readiness_status="EXCESSIVE_MISSINGNESS",
                readiness_reason=(
                    f"Series contains only {avail_months} reported months (minimum required is 9). "
                    "Data completeness is insufficient for credible baseline evaluation."
                ),
                dataset_limitation=dataset_limitation,
                clinical_validation_disclaimer=clinical_disclaimer,
                historical_months_available=avail_months,
                historical_months_required=9
            )

        # Extract values (imputing missing with series median for clean continuous evaluation)
        raw_vals = [p.value for p in ts.points]
        non_null_vals = [v for v in raw_vals if v is not None]
        fallback_val = float(np.median(non_null_vals)) if non_null_vals else 0.0
        imputed_vals = [v if v is not None else fallback_val for v in raw_vals]
        all_months = [p.month for p in ts.points]

        n = len(imputed_vals)
        val_horizon = max(1, min(horizon, 3))
        train_len = n - val_horizon

        train_vals = imputed_vals[:train_len]
        eval_true = imputed_vals[train_len:]
        train_months = all_months[:train_len]
        eval_months = all_months[train_len:]

        # Chronological hold-out evaluation on baselines
        candidates = [
            ("Naive Forecaster", NaiveForecaster().fit(train_vals, train_months)),
            ("Moving Average (3m)", MovingAverageForecaster(window_size=3).fit(train_vals, train_months)),
            ("Linear Drift", LinearDriftForecaster().fit(train_vals))
        ]

        evaluated_models = []
        best_model_name = None
        best_mae = float("inf")
        best_metrics: Optional[Dict[str, float]] = None

        for name, model in candidates:
            preds = model.predict(len(eval_true))
            m = calculate_metrics(eval_true, preds)
            m_dict = {
                "mae": m.mae,
                "rmse": m.rmse,
                "smape": m.smape,
                "wape": m.wape,
                "mape": m.mape
            }
            evaluated_models.append({
                "model_name": name,
                "evaluation_metrics": m_dict,
                "predictions": [round(float(p), 1) for p in preds],
                "ground_truth": [round(float(y), 1) for y in eval_true]
            })
            if m.mae < best_mae:
                best_mae = m.mae
                best_model_name = name
                best_metrics = m_dict

        # Forward projection using winning baseline retrained on full 12 months
        forward_preds: List[float] = []
        if best_model_name == "Naive Forecaster":
            forward_preds = NaiveForecaster().fit(imputed_vals, all_months).predict(horizon)
        elif best_model_name == "Linear Drift":
            forward_preds = LinearDriftForecaster().fit(imputed_vals).predict(horizon)
        else:
            forward_preds = MovingAverageForecaster(window_size=3).fit(imputed_vals, all_months).predict(horizon)

        # Generate forward month labels: e.g. 2016-04, 2016-05, 2016-06
        last_m = all_months[-1]
        last_y, last_mo = int(last_m[:4]), int(last_m[5:7])
        forecast_points = []
        rmse_val = best_metrics["rmse"] if best_metrics else 0.0

        for h in range(horizon):
            mo = last_mo + h + 1
            yr = last_y
            if mo > 12:
                yr += 1
                mo -= 12
            f_month = f"{yr:04d}-{mo:02d}"
            pred_v = round(max(0.0, float(forward_preds[h])), 1)
            # 95% conservative confidence interval based on hold-out RMSE
            lower_bound = round(max(0.0, pred_v - 1.96 * rmse_val), 1)
            upper_bound = round(pred_v + 1.96 * rmse_val, 1)

            forecast_points.append({
                "month": f_month,
                "predicted_value": pred_v,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "model_used": best_model_name
            })

        return ForecastingReadinessResponse(
            district=district,
            s_no=s_no,
            parameter_name=ts.parameter_name,
            canonical_id=ts.canonical_id,
            canonical_name=ts.canonical_name,
            subgroup_type=resolved_sg,
            financial_year=financial_year or "2015-16",
            requested_horizon=horizon,
            is_ready=True,
            readiness_status="ELIGIBLE_FOR_BASELINE_EVALUATION",
            readiness_reason=(
                f"Historical series has {avail_months} reporting months, passing the 9-month threshold. "
                f"Evaluated on chronological hold-out ({len(train_vals)}m train / {len(eval_true)}m test). "
                f"Selected best baseline '{best_model_name}' (Hold-out MAE: {best_mae:.1f})."
            ),
            dataset_limitation=dataset_limitation,
            clinical_validation_disclaimer=clinical_disclaimer,
            historical_months_available=avail_months,
            historical_months_required=9,
            training_period={
                "start_month": train_months[0],
                "end_month": train_months[-1],
                "months_count": len(train_months)
            },
            evaluation_period={
                "start_month": eval_months[0],
                "end_month": eval_months[-1],
                "months_count": len(eval_months)
            },
            baseline_models_evaluated=evaluated_models,
            selected_baseline_model=best_model_name,
            held_out_metrics=best_metrics,
            baseline_forecast=forecast_points
        )

    # =========================================================================
    # Phase 14D: Conservative Anomaly & Change Detection
    # =========================================================================

    def detect_anomalies(
        self,
        district: Optional[str] = None,
        s_no: Optional[str] = None,
        reporting_month: Optional[str] = None,
        subgroup_type: Optional[str] = None,
        financial_year: Optional[str] = "2015-16"
    ) -> DistrictAnomalyReportResponse:
        """
        Conservative statistical anomaly detection for verified indicators:
        - Outliers via Median Absolute Deviation (MAD, modified z > 3.5)
        - Abrupt Month-over-Month swings (> 50% shift and > 3 sigma)
        - Missing reporting periods in expected monthly sequence
        - Spatial outliers relative to state distribution
        """
        # Determine target indicators
        target_snos: List[str] = []
        if s_no:
            self._validate_indicator_eligibility(s_no, allow_stock=True)
            target_snos = [s_no]
        else:
            # All verified indicators
            target_snos = [
                rec.s_no for rec in IndicatorMappingRegistry.list_all_mappings()
                if rec.status == MappingStatus.VERIFIED
            ]

        # Determine target districts
        target_districts: List[str] = []
        if district:
            target_districts = [district]
        else:
            target_districts = [
                r[0] for r in self.db.query(DistrictObservation.district).distinct().order_by(DistrictObservation.district).all()
            ]

        signals: List[AnomalySignalItem] = []
        eval_summary = {
            "districts_evaluated": len(target_districts),
            "indicators_evaluated": len(target_snos),
            "methods_applied": [
                "Median Absolute Deviation (MAD, cutoff > 3.5)",
                "Abrupt Month-over-Month Shift (>50% & >3 sigma)",
                "Missing Reporting Period Audit",
                "Cross-District Spatial Outlier Detection"
            ]
        }

        # 1. Evaluate Time-Series Signals (MAD, MoM shift, Missing periods) per district and indicator
        for cur_sno in target_snos:
            mapping = IndicatorMappingRegistry.get_mapping(cur_sno)
            pref_sg = subgroup_type or self._resolve_preferred_subgroup(cur_sno)

            for cur_dist in target_districts:
                ts = self.get_verified_indicator_timeseries(
                    district=cur_dist,
                    s_no=cur_sno,
                    subgroup_type=pref_sg,
                    financial_year=financial_year
                )

                # Filter by reporting_month if specified
                points_to_check = ts.points
                if reporting_month:
                    points_to_check = [p for p in ts.points if p.month == reporting_month]

                # Missing period signal
                for pt in points_to_check:
                    if pt.is_missing:
                        sig_id = f"SIG_MISS_{cur_dist}_{cur_sno}_{pt.month}"
                        signals.append(
                            AnomalySignalItem(
                                signal_id=sig_id,
                                signal_type="MISSING_REPORTING_PERIOD",
                                severity="WARNING",
                                district=cur_dist,
                                s_no=cur_sno,
                                parameter_name=ts.parameter_name,
                                reporting_month=pt.month,
                                observed_value=None,
                                expected_baseline=ts.median_value,
                                deviation_score=1.0,
                                metric_unit=ts.unit,
                                statistical_method="Calendar Sequence Completeness Audit",
                                rationale=(
                                    f"Expected reporting month {pt.month} is missing or unreported in the district return."
                                ),
                                data_points_used=ts.total_expected_months
                            )
                        )

                # Historical Outlier (MAD)
                valid_vals = [p.value for p in ts.points if p.value is not None]
                if len(valid_vals) >= 6:
                    arr = np.array(valid_vals, dtype=float)
                    med = float(np.median(arr))
                    mad = float(np.median(np.abs(arr - med)))
                    mean_ad = float(np.mean(np.abs(arr - med)))
                    effective_mad = mad if mad > 1e-4 else (mean_ad if mean_ad > 1e-4 else 1.0)

                    if effective_mad > 1e-4:
                        for pt in points_to_check:
                            if pt.value is not None and not pt.is_missing:
                                mod_z = round((0.6745 * abs(pt.value - med)) / effective_mad, 2)
                                if mod_z > 3.5:
                                    sig_id = f"SIG_MAD_{cur_dist}_{cur_sno}_{pt.month}"
                                    severity = "ELEVATED" if mod_z > 5.0 else "WARNING"
                                    direction = "above" if pt.value > med else "below"
                                    signals.append(
                                        AnomalySignalItem(
                                            signal_id=sig_id,
                                            signal_type="HISTORICAL_OUTLIER_MAD",
                                            severity=severity,
                                            district=cur_dist,
                                            s_no=cur_sno,
                                            parameter_name=ts.parameter_name,
                                            reporting_month=pt.month,
                                            observed_value=round(pt.value, 1),
                                            expected_baseline=round(med, 1),
                                            deviation_score=mod_z,
                                            metric_unit=ts.unit,
                                            statistical_method="Median Absolute Deviation (Modified Z-score)",
                                            rationale=(
                                                f"Observed value ({pt.value:.1f}) is {mod_z:.1f}x MAD {direction} the district "
                                                f"historical median ({med:.1f}) across {len(valid_vals)} months."
                                            ),
                                            data_points_used=len(valid_vals)
                                        )
                                    )

                # Month-over-Month abrupt shifts
                ordered_pts = [p for p in ts.points if p.value is not None]
                if len(ordered_pts) >= 4:
                    vals_seq = [p.value for p in ordered_pts]
                    diffs = np.diff(vals_seq)
                    std_diff = float(np.std(diffs))

                    for idx in range(1, len(ordered_pts)):
                        prev_pt = ordered_pts[idx - 1]
                        cur_pt = ordered_pts[idx]
                        if reporting_month and cur_pt.month != reporting_month:
                            continue

                        diff = cur_pt.value - prev_pt.value
                        pct_change = abs(diff) / max(prev_pt.value, 10.0)

                        if abs(diff) > 3.0 * max(std_diff, 5.0) and pct_change > 0.50:
                            sig_id = f"SIG_MOM_{cur_dist}_{cur_sno}_{cur_pt.month}"
                            severity = "ELEVATED" if pct_change > 1.0 else "WARNING"
                            direction = "increase" if diff > 0 else "drop"
                            signals.append(
                                AnomalySignalItem(
                                    signal_id=sig_id,
                                    signal_type="MONTH_OVER_MONTH_SHIFT",
                                    severity=severity,
                                    district=cur_dist,
                                    s_no=cur_sno,
                                    parameter_name=ts.parameter_name,
                                    reporting_month=cur_pt.month,
                                    observed_value=round(cur_pt.value, 1),
                                    expected_baseline=round(prev_pt.value, 1),
                                    deviation_score=round(pct_change * 100.0, 1),
                                    metric_unit=ts.unit,
                                    statistical_method="Month-over-Month Delta & Volatility Threshold",
                                    rationale=(
                                        f"Abrupt {pct_change * 100.0:.1f}% {direction} from previous month "
                                        f"({prev_pt.value:.1f} -> {cur_pt.value:.1f}) exceeding 3σ historical volatility."
                                    ),
                                    data_points_used=len(vals_seq)
                                )
                            )

        # 2. Cross-District Spatial Outlier Detection (if reporting_month is specified or across all observed months)
        sample_months = [reporting_month] if reporting_month else self._resolve_expected_months(financial_year)

        for cur_sno in target_snos:
            mapping = IndicatorMappingRegistry.get_mapping(cur_sno)
            pref_sg = subgroup_type or self._resolve_preferred_subgroup(cur_sno)

            for m in sample_months:
                q = self.db.query(DistrictObservation.district, DistrictObservation.value).filter(
                    func.lower(DistrictObservation.s_no) == cur_sno.lower().strip(),
                    DistrictObservation.reporting_month == m,
                    func.lower(DistrictObservation.subgroup_type) == pref_sg.lower().strip()
                )
                if financial_year:
                    q = q.filter(DistrictObservation.financial_year == financial_year.strip())

                rows = q.all()
                valid_dist_values = {r[0]: float(r[1]) for r in rows if r[1] is not None}

                if len(valid_dist_values) >= 15:
                    all_vals = np.array(list(valid_dist_values.values()), dtype=float)
                    st_med = float(np.median(all_vals))
                    st_mad = float(np.median(np.abs(all_vals - st_med)))

                    if st_mad > 1e-4:
                        for cur_dist in target_districts:
                            if cur_dist in valid_dist_values:
                                d_val = valid_dist_values[cur_dist]
                                mod_z = round((0.6745 * abs(d_val - st_med)) / st_mad, 2)
                                if mod_z > 3.5:
                                    sig_id = f"SIG_SPATIAL_{cur_dist}_{cur_sno}_{m}"
                                    direction = "above" if d_val > st_med else "below"
                                    signals.append(
                                        AnomalySignalItem(
                                            signal_id=sig_id,
                                            signal_type="SPATIAL_DEVIATION",
                                            severity="WARNING",
                                            district=cur_dist,
                                            s_no=cur_sno,
                                            parameter_name=mapping.parameter_name,
                                            reporting_month=m,
                                            observed_value=round(d_val, 1),
                                            expected_baseline=round(st_med, 1),
                                            deviation_score=mod_z,
                                            metric_unit=mapping.unit,
                                            statistical_method="Cross-District Median & Spatial Dispersion",
                                            rationale=(
                                                f"District value ({d_val:.1f}) is {mod_z:.1f}x state MAD {direction} the "
                                                f"state median ({st_med:.1f}) across {len(valid_dist_values)} reporting districts in {m}."
                                            ),
                                            data_points_used=len(valid_dist_values)
                                        )
                                    )

        # De-duplicate signals by signal_id
        seen_ids = set()
        dedup_signals = []
        for s in signals:
            if s.signal_id not in seen_ids:
                seen_ids.add(s.signal_id)
                dedup_signals.append(s)

        if dedup_signals:
            sig_ids = [s.signal_id for s in dedup_signals]
            reviews = self.db.query(DistrictAnomalyReview).filter(
                DistrictAnomalyReview.signal_id.in_(sig_ids)
            ).all()
            review_map = {r.signal_id: r for r in reviews}
            for s in dedup_signals:
                rev = review_map.get(s.signal_id)
                if rev:
                    s.review_status = rev.current_status
                    s.last_reviewed_by_username = rev.last_reviewed_by_username
                    s.last_reviewed_at = rev.last_reviewed_at.isoformat() if rev.last_reviewed_at else None

        return DistrictAnomalyReportResponse(
            s_no=s_no,
            district=district,
            reporting_month=reporting_month,
            financial_year=financial_year,
            total_signals_detected=len(dedup_signals),
            signals=dedup_signals,
            evaluation_summary=eval_summary
        )
