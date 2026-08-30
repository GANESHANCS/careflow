from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.services.analytics.change_calc import calculate_mom_change


class FacilityAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_facility_analytics(
        self,
        facility_id: str,
        indicator_code: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Calculates facility-level historical trends, latest metrics, completeness,
        missing reporting months, and MoM growth per indicator.
        """
        facility = self.db.query(Facility).filter(Facility.id == facility_id).first()
        if not facility:
            return None

        # Determine all expected reporting months in system (min to max sequence)
        obs_months = [r[0] for r in self.db.query(Observation.reporting_month).distinct().order_by(Observation.reporting_month.asc()).all()]
        
        all_system_months = []
        if obs_months:
            min_m = obs_months[0]
            max_m = obs_months[-1]
            try:
                min_yr, min_mo = map(int, min_m.split("-"))
                max_yr, max_mo = map(int, max_m.split("-"))
                
                curr_yr, curr_mo = min_yr, min_mo
                while (curr_yr < max_yr) or (curr_yr == max_yr and curr_mo <= max_mo):
                    all_system_months.append(f"{curr_yr:04d}-{curr_mo:02d}")
                    curr_mo += 1
                    if curr_mo > 12:
                        curr_mo = 1
                        curr_yr += 1
            except Exception:
                all_system_months = obs_months

        # Query facility observations
        obs_query = self.db.query(Observation).filter(Observation.facility_id == facility_id)
        if indicator_code:
            obs_query = obs_query.join(Indicator).filter(Indicator.code == indicator_code)

        observations = obs_query.order_by(Observation.reporting_month.asc()).all()

        # Facility reporting months present
        facility_reported_months = sorted(list(set([o.reporting_month for o in observations])))

        # Missing reporting periods
        missing_months = [m for m in all_system_months if m not in facility_reported_months]
        total_expected_months = len(all_system_months)
        completeness_pct = round((len(facility_reported_months) / total_expected_months) * 100.0, 1) if total_expected_months > 0 else 0.0

        # Latest values per indicator
        indicators = self.db.query(Indicator).all()
        ind_map = {ind.id: ind for ind in indicators}

        latest_metrics = []
        if facility_reported_months:
            latest_month = facility_reported_months[-1]
            prev_month = facility_reported_months[-2] if len(facility_reported_months) > 1 else None

            # Latest month values
            latest_obs = self.db.query(Observation).filter(
                Observation.facility_id == facility_id,
                Observation.reporting_month == latest_month
            ).all()

            # Previous month values
            prev_obs = {}
            if prev_month:
                p_rows = self.db.query(Observation).filter(
                    Observation.facility_id == facility_id,
                    Observation.reporting_month == prev_month
                ).all()
                prev_obs = {o.indicator_id: o.value for o in p_rows}

            for o in latest_obs:
                ind_obj = ind_map.get(o.indicator_id)
                ind_c = ind_obj.code if ind_obj else o.indicator_id
                ind_n = ind_obj.name if ind_obj else ind_c

                curr_val = o.value
                prev_val = prev_obs.get(o.indicator_id)
                mom = calculate_mom_change(curr_val, prev_val)

                latest_metrics.append({
                    "indicator_code": ind_c,
                    "indicator_name": ind_n,
                    "latest_reporting_month": latest_month,
                    "latest_value": curr_val,
                    "value_type": o.value_type,
                    "previous_value": prev_val,
                    "mom_change_pct": mom
                })

        # Format historical timeseries items
        history = []
        for o in observations:
            ind_obj = ind_map.get(o.indicator_id)
            history.append({
                "reporting_month": o.reporting_month,
                "observation_date": o.observation_date,
                "indicator_code": ind_obj.code if ind_obj else o.indicator_id,
                "indicator_name": ind_obj.name if ind_obj else o.indicator_id,
                "value": o.value,
                "value_type": o.value_type
            })

        return {
            "facility_id": facility.id,
            "facility_code": facility.facility_code,
            "facility_name": facility.facility_name,
            "facility_type": facility.facility_type,
            "state": facility.state,
            "district": facility.district,
            "sub_district": facility.sub_district,
            "total_expected_months": total_expected_months,
            "reported_months_count": len(facility_reported_months),
            "completeness_pct": completeness_pct,
            "missing_months": missing_months,
            "latest_metrics": latest_metrics,
            "history": history
        }
