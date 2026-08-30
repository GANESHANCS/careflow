import statistics
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.services.analytics.change_calc import calculate_mom_change


class FacilityComparisonService:
    def __init__(self, db: Session):
        self.db = db

    def compare_facilities(
        self,
        facility_ids: List[str],
        indicator_code: str,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Benchmarking comparison for multiple facilities across an indicator.
        Returns time-series grid and normalized summary statistics (avg, median, latest, trend).
        """
        # Resolve indicator
        indicator = self.db.query(Indicator).filter(Indicator.code == indicator_code).first()
        if not indicator:
            return {
                "indicator_code": indicator_code,
                "error": f"Indicator '{indicator_code}' not found.",
                "facilities": [],
                "timeseries": []
            }

        # Query facilities
        facilities = self.db.query(Facility).filter(Facility.id.in_(facility_ids)).all()
        if not facilities:
            return {
                "indicator_code": indicator_code,
                "indicator_name": indicator.name,
                "facilities": [],
                "timeseries": []
            }

        fac_map = {f.id: f for f in facilities}
        all_system_months = [r[0] for r in self.db.query(Observation.reporting_month).distinct().order_by(Observation.reporting_month.asc()).all()]
        
        if start_month:
            all_system_months = [m for m in all_system_months if m >= start_month]
        if end_month:
            all_system_months = [m for m in all_system_months if m <= end_month]

        # Query observations
        obs_query = self.db.query(Observation).filter(
            Observation.facility_id.in_(facility_ids),
            Observation.indicator_id == indicator.id
        )
        if start_month:
            obs_query = obs_query.filter(Observation.reporting_month >= start_month)
        if end_month:
            obs_query = obs_query.filter(Observation.reporting_month <= end_month)

        observations = obs_query.order_by(Observation.reporting_month.asc()).all()

        # Build grid map: (facility_id, month) -> value
        grid: Dict[str, Dict[str, Optional[float]]] = {f_id: {} for f_id in facility_ids}
        for o in observations:
            if o.facility_id in grid:
                grid[o.facility_id][o.reporting_month] = o.value

        facility_summaries = []
        for f_id in facility_ids:
            fac_obj = fac_map.get(f_id)
            f_name = fac_obj.facility_name if fac_obj else f_id
            f_type = fac_obj.facility_type if fac_obj else "UNKNOWN"

            month_vals = grid.get(f_id, {})
            valid_vals = [v for v in month_vals.values() if v is not None]
            
            total_expected = len(all_system_months)
            reported_count = len([v for v in month_vals.values() if v is not None])
            completeness_pct = round((reported_count / total_expected) * 100.0, 1) if total_expected > 0 else 0.0

            avg_val = round(float(statistics.mean(valid_vals)), 2) if valid_vals else None
            median_val = round(float(statistics.median(valid_vals)), 2) if valid_vals else None
            
            latest_val = None
            trend_direction = "STABLE"
            if all_system_months:
                for m in reversed(all_system_months):
                    if m in month_vals and month_vals[m] is not None:
                        latest_val = month_vals[m]
                        break

            # Calculate trend direction
            if len(valid_vals) >= 2:
                mom = calculate_mom_change(valid_vals[-1], valid_vals[-2])
                if mom is not None:
                    if mom > 2.0:
                        trend_direction = "UP"
                    elif mom < -2.0:
                        trend_direction = "DOWN"

            facility_summaries.append({
                "facility_id": f_id,
                "facility_name": f_name,
                "facility_type": f_type,
                "district": fac_obj.district if fac_obj else "Unknown",
                "average_value": avg_val,
                "median_value": median_val,
                "latest_value": latest_val,
                "trend_direction": trend_direction,
                "completeness_pct": completeness_pct
            })

        # Structured timeseries rows suitable for charting
        timeseries_rows = []
        for m in all_system_months:
            row = {"reporting_month": m, "observation_date": f"{m}-01"}
            for f_id in facility_ids:
                row[f_id] = grid.get(f_id, {}).get(m)
            timeseries_rows.append(row)

        return {
            "indicator_code": indicator_code,
            "indicator_name": indicator.name,
            "interpretation_note": "Comparing raw totals across facilities of different bed counts or facility types may be misleading. Use average/median metrics for fairer comparison.",
            "facilities": facility_summaries,
            "timeseries": timeseries_rows
        }
