import statistics
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.services.analytics.change_calc import calculate_mom_change, calculate_yoy_change


class RegionalAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_regional_analytics(
        self,
        level: str = "district", # "state" or "district"
        indicator_code: Optional[str] = None,
        state: Optional[str] = None,
        district: Optional[str] = None,
        reporting_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates regional healthcare metrics grouped by State or District.
        Provides Total Utilization, Average Per Reporting Facility, Median Per Reporting Facility,
        Reporting Completeness, and MoM/YoY growth rates.
        """
        # Determine target reporting month (default: latest available)
        if not reporting_month:
            latest_obs = self.db.query(Observation).order_by(Observation.reporting_month.desc()).first()
            reporting_month = latest_obs.reporting_month if latest_obs else None

        if not reporting_month:
            return {"level": level, "reporting_month": None, "regions": []}

        # Resolve indicator ID
        ind = None
        if indicator_code:
            ind = self.db.query(Indicator).filter(Indicator.code == indicator_code).first()

        # Build regional facility query
        fac_query = self.db.query(Facility)
        if state:
            fac_query = fac_query.filter(Facility.state.ilike(f"%{state}%"))
        if district:
            fac_query = fac_query.filter(Facility.district.ilike(f"%{district}%"))

        facilities = fac_query.all()
        if not facilities:
            return {"level": level, "reporting_month": reporting_month, "regions": []}

        # Group facilities by region
        group_key = "state" if level.lower() == "state" else "district"
        region_facs: Dict[str, List[Facility]] = {}
        for f in facilities:
            r_name = getattr(f, group_key, "Unknown")
            region_facs.setdefault(r_name, []).append(f)

        regions_result = []

        # Previous month for MoM change
        prev_month = None
        all_months = [r[0] for r in self.db.query(Observation.reporting_month).distinct().order_by(Observation.reporting_month.desc()).all()]
        if reporting_month in all_months:
            idx = all_months.index(reporting_month)
            if idx + 1 < len(all_months):
                prev_month = all_months[idx + 1]

        for r_name, fac_list in region_facs.items():
            fac_ids = [f.id for f in fac_list]
            total_fac_count = len(fac_ids)

            # Query current month observations
            q_curr = self.db.query(Observation).filter(
                Observation.facility_id.in_(fac_ids),
                Observation.reporting_month == reporting_month,
                Observation.value.isnot(None)
            )
            if ind:
                q_curr = q_curr.filter(Observation.indicator_id == ind.id)

            curr_obs = q_curr.all()
            values = [o.value for o in curr_obs if o.value is not None]
            rep_fac_ids = list(set([o.facility_id for o in curr_obs]))
            rep_fac_count = len(rep_fac_ids)

            total_utilization = sum(values) if values else 0.0
            avg_per_reporting_fac = round(total_utilization / rep_fac_count, 2) if rep_fac_count > 0 else 0.0
            median_per_reporting_fac = round(float(statistics.median(values)), 2) if values else 0.0
            completeness_pct = round((rep_fac_count / total_fac_count) * 100.0, 1) if total_fac_count > 0 else 0.0

            # MoM change
            prev_total_utilization = None
            if prev_month:
                q_prev = self.db.query(func.sum(Observation.value)).filter(
                    Observation.facility_id.in_(fac_ids),
                    Observation.reporting_month == prev_month,
                    Observation.value.isnot(None)
                )
                if ind:
                    q_prev = q_prev.filter(Observation.indicator_id == ind.id)
                p_val = q_prev.scalar()
                if p_val is not None:
                    prev_total_utilization = float(p_val)

            mom_change = calculate_mom_change(total_utilization, prev_total_utilization)

            regions_result.append({
                "region_name": r_name,
                "level": level,
                "reporting_month": reporting_month,
                "total_facilities": total_fac_count,
                "reporting_facilities": rep_fac_count,
                "completeness_pct": completeness_pct,
                "total_utilization": total_utilization,
                "average_per_reporting_facility": avg_per_reporting_fac,
                "median_per_reporting_facility": median_per_reporting_fac,
                "mom_change_pct": mom_change
            })

        # Sort by total utilization descending
        regions_result.sort(key=lambda x: x["total_utilization"], reverse=True)

        return {
            "level": level,
            "reporting_month": reporting_month,
            "indicator_code": indicator_code,
            "regions": regions_result
        }
