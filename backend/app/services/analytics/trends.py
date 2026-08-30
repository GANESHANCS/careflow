from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation


class TimeSeriesTrendsService:
    def __init__(self, db: Session):
        self.db = db

    def get_monthly_trends(
        self,
        indicator_code: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        facility_id: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates monthly time-series aggregations (total, average, reporting facility count, completeness).
        """
        # Facility query base
        fac_query = self.db.query(Facility)
        if facility_id:
            fac_query = fac_query.filter(Facility.id == facility_id)
        if state:
            fac_query = fac_query.filter(Facility.state.ilike(f"%{state}%"))
        if district:
            fac_query = fac_query.filter(Facility.district.ilike(f"%{district}%"))

        facility_ids = [f.id for f in fac_query.all()]
        total_facilities = len(facility_ids)

        if not facility_ids:
            return {
                "filters": {
                    "indicator_code": indicator_code,
                    "state": state,
                    "district": district,
                    "facility_id": facility_id,
                    "start_month": start_month,
                    "end_month": end_month
                },
                "total_facilities": 0,
                "series": []
            }

        # Observations query base
        obs_query = self.db.query(Observation).filter(Observation.facility_id.in_(facility_ids))

        if indicator_code:
            obs_query = obs_query.join(Indicator).filter(Indicator.code == indicator_code)
        if start_month:
            obs_query = obs_query.filter(Observation.reporting_month >= start_month)
        if end_month:
            obs_query = obs_query.filter(Observation.reporting_month <= end_month)

        # Monthly aggregation query
        monthly_stats = self.db.query(
            Observation.reporting_month,
            func.sum(Observation.value).label("total_value"),
            func.avg(Observation.value).label("avg_value"),
            func.count(func.distinct(Observation.facility_id)).label("reporting_facilities"),
            func.count(Observation.id).label("observation_count")
        ).group_by(Observation.reporting_month).order_by(Observation.reporting_month.asc()).all()

        series = []
        for rep_month, tot_val, avg_val, rep_facs, obs_count in monthly_stats:
            tot = float(tot_val) if tot_val is not None else 0.0
            avg = round(float(avg_val), 2) if avg_val is not None else 0.0
            completeness = round((rep_facs / total_facilities) * 100.0, 1) if total_facilities > 0 else 0.0

            series.append({
                "reporting_month": rep_month,
                "observation_date": f"{rep_month}-01",
                "total_value": tot,
                "average_per_facility": avg,
                "reporting_facilities": rep_facs,
                "total_facilities": total_facilities,
                "completeness_pct": completeness,
                "observation_count": obs_count
            })

        return {
            "filters": {
                "indicator_code": indicator_code,
                "state": state,
                "district": district,
                "facility_id": facility_id,
                "start_month": start_month,
                "end_month": end_month
            },
            "total_facilities": total_facilities,
            "series": series
        }
