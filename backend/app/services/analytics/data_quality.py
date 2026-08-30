from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.data_quality import DataQualityLog
from backend.app.db.models.facility import Facility
from backend.app.db.models.observation import Observation


class DataQualityAnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def get_quality_analytics(self) -> Dict[str, Any]:
        """
        Exposes data quality audit information, overall quality score, severity breakdowns,
        issue categories, and facilities with incomplete reporting.
        """
        logs = self.db.query(DataQualityLog).all()

        overall_score = 100.0
        if logs:
            scores = [l.quality_score for l in logs if l.quality_score is not None]
            if scores:
                overall_score = round(sum(scores) / len(scores), 1)

        # Breakdowns by Severity
        severity_counts = {"CRITICAL": 0, "ERROR": 0, "WARNING": 0, "INFO": 0}
        category_counts: Dict[str, int] = {}
        issues_list = []

        for log in logs:
            sev = log.severity.upper()
            if sev in severity_counts:
                severity_counts[sev] += 1
            else:
                severity_counts[sev] = 1

            cat = log.issue_category
            category_counts[cat] = category_counts.get(cat, 0) + 1

            issues_list.append({
                "id": log.id,
                "audit_timestamp": log.audit_timestamp,
                "category": log.issue_category,
                "severity": log.severity,
                "affected_records": log.affected_record_count,
                "description": log.description
            })

        # Facilities with incomplete reporting
        all_months = [r[0] for r in self.db.query(Observation.reporting_month).distinct().all()]
        total_months = len(all_months)

        incomplete_facilities = []
        if total_months > 0:
            facilities = self.db.query(Facility).all()
            for fac in facilities:
                rep_count = self.db.query(Observation.reporting_month).filter(
                    Observation.facility_id == fac.id
                ).distinct().count()
                
                if rep_count < total_months:
                    incomplete_facilities.append({
                        "facility_id": fac.id,
                        "facility_name": fac.facility_name,
                        "state": fac.state,
                        "district": fac.district,
                        "reported_months": rep_count,
                        "expected_months": total_months,
                        "completeness_pct": round((rep_count / total_months) * 100.0, 1)
                    })

        return {
            "overall_quality_score": overall_score,
            "total_issues": len(logs),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "incomplete_facilities_count": len(incomplete_facilities),
            "incomplete_facilities": incomplete_facilities,
            "issues": issues_list
        }
