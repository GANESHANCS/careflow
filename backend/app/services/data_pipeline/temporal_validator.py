from typing import List, Dict, Any, Set, Tuple, Optional
from datetime import datetime
import pandas as pd


class TemporalValidator:
    """
    Validates monthly reporting periods, detects missing reporting periods,
    and computes facility/district reporting completeness metrics.
    """

    @staticmethod
    def generate_expected_months(start_month: str, end_month: str) -> List[str]:
        """
        Generates full sequence of YYYY-MM months inclusive.
        """
        try:
            start_dt = datetime.strptime(start_month, "%Y-%m")
            end_dt = datetime.strptime(end_month, "%Y-%m")
        except ValueError:
            return []

        if start_dt > end_dt:
            return []

        months = []
        curr = start_dt
        while curr <= end_dt:
            months.append(curr.strftime("%Y-%m"))
            # Advance 1 month
            if curr.month == 12:
                curr = datetime(curr.year + 1, 1, 1)
            else:
                curr = datetime(curr.year, curr.month + 1, 1)
        return months

    @classmethod
    def evaluate_facility_completeness(
        cls, 
        facility_id: str, 
        reported_months: List[str],
        global_start_month: Optional[str] = None,
        global_end_month: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates temporal completeness for a single facility.
        """
        valid_months = sorted(list({m for m in reported_months if m and len(m) == 7}))
        
        if not valid_months:
            return {
                "facility_id": facility_id,
                "total_expected": 0,
                "total_reported": 0,
                "completeness_pct": 0.0,
                "missing_months": [],
                "temporal_gaps_count": 0
            }

        start = global_start_month or valid_months[0]
        end = global_end_month or valid_months[-1]
        
        expected_seq = cls.generate_expected_months(start, end)
        reported_set = set(valid_months)
        
        missing_months = [m for m in expected_seq if m not in reported_set]
        total_expected = len(expected_seq)
        total_reported = len(reported_set.intersection(set(expected_seq)))
        
        completeness_pct = round((total_reported / max(1, total_expected)) * 100.0, 2)
        
        return {
            "facility_id": facility_id,
            "period_start": start,
            "period_end": end,
            "total_expected": total_expected,
            "total_reported": total_reported,
            "completeness_pct": completeness_pct,
            "missing_months": missing_months,
            "temporal_gaps_count": len(missing_months)
        }
