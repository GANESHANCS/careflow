from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.services.analytics.change_calc import calculate_mom_change


class ExecutiveSummaryService:
    def __init__(self, db: Session):
        self.db = db

    def get_summary(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates executive summary healthcare indicators, active facility counts,
        overall completeness, latest reporting period, and previous-period changes.
        """
        # Facility query base
        fac_query = self.db.query(Facility)
        if state:
            fac_query = fac_query.filter(Facility.state.ilike(f"%{state}%"))
        if district:
            fac_query = fac_query.filter(Facility.district.ilike(f"%{district}%"))
        
        total_facilities = fac_query.count()
        facility_ids = [f.id for f in fac_query.all()]

        if not facility_ids:
            return {
                "latest_period": None,
                "previous_period": None,
                "total_facilities": 0,
                "reporting_facilities": 0,
                "reporting_completeness_pct": 0.0,
                "totals_by_indicator": {},
                "mom_changes": {}
            }

        # Latest reporting month query
        obs_query = self.db.query(Observation).filter(Observation.facility_id.in_(facility_ids))
        latest_obs = obs_query.order_by(Observation.reporting_month.desc()).first()
        latest_period = latest_obs.reporting_month if latest_obs else None

        # Determine previous period
        previous_period = None
        if latest_period:
            periods = [r[0] for r in self.db.query(Observation.reporting_month).filter(Observation.facility_id.in_(facility_ids)).distinct().order_by(Observation.reporting_month.desc()).all()]
            if len(periods) > 1:
                previous_period = periods[1]

        # Indicator totals query
        indicators = self.db.query(Indicator).all()
        ind_map = {ind.id: ind.code for ind in indicators}
        ind_name_map = {ind.code: ind.name for ind in indicators}

        totals_latest: Dict[str, float] = {}
        totals_prev: Dict[str, float] = {}

        if latest_period:
            latest_rows = self.db.query(
                Observation.indicator_id,
                func.sum(Observation.value)
            ).filter(
                Observation.facility_id.in_(facility_ids),
                Observation.reporting_month == latest_period,
                Observation.value.isnot(None)
            ).group_by(Observation.indicator_id).all()

            for ind_id, total_val in latest_rows:
                code = ind_map.get(ind_id, ind_id)
                totals_latest[code] = float(total_val) if total_val is not None else 0.0

        if previous_period:
            prev_rows = self.db.query(
                Observation.indicator_id,
                func.sum(Observation.value)
            ).filter(
                Observation.facility_id.in_(facility_ids),
                Observation.reporting_month == previous_period,
                Observation.value.isnot(None)
            ).group_by(Observation.indicator_id).all()

            for ind_id, total_val in prev_rows:
                code = ind_map.get(ind_id, ind_id)
                totals_prev[code] = float(total_val) if total_val is not None else 0.0

        # Calculate MoM changes
        mom_changes = {}
        for code, curr_val in totals_latest.items():
            prev_val = totals_prev.get(code)
            mom_changes[code] = calculate_mom_change(curr_val, prev_val)

        # Reporting facilities in latest period
        reporting_fac_count = 0
        if latest_period:
            reporting_fac_count = self.db.query(Observation.facility_id).filter(
                Observation.facility_id.in_(facility_ids),
                Observation.reporting_month == latest_period
            ).distinct().count()

        # Reporting completeness %
        completeness_pct = round((reporting_fac_count / total_facilities) * 100.0, 1) if total_facilities > 0 else 0.0

        return {
            "latest_period": latest_period,
            "previous_period": previous_period,
            "total_facilities": total_facilities,
            "reporting_facilities": reporting_fac_count,
            "reporting_completeness_pct": completeness_pct,
            "totals_by_indicator": totals_latest,
            "indicator_names": ind_name_map,
            "mom_changes": mom_changes
        }
