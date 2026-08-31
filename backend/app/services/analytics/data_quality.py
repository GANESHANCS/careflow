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
        all_months = sorted([r[0] for r in self.db.query(Observation.reporting_month).distinct().all() if r[0]])
        total_months = len(all_months)
        latest_period = all_months[-1] if all_months else None

        incomplete_facilities = []
        all_facilities = self.db.query(Facility).all()
        total_facilities_count = len(all_facilities)

        if total_months > 0:
            for fac in all_facilities:
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

        # Observation status breakdown (VALID, ZERO, MISSING, INVALID, IMPUTED)
        total_obs_count = self.db.query(Observation).count()
        zero_count = self.db.query(Observation).filter(
            (Observation.value == 0) | (Observation.value_type == "ZERO")
        ).count()
        missing_count = self.db.query(Observation).filter(
            Observation.value.is_(None) | (Observation.value_type == "MISSING")
        ).count()
        invalid_count = self.db.query(Observation).filter(Observation.value_type == "INVALID").count()
        imputed_count = self.db.query(Observation).filter(Observation.value_type == "IMPUTED").count()
        
        # Valid observations are non-zero, non-missing, non-invalid, non-imputed
        valid_count = self.db.query(Observation).filter(
            Observation.value > 0,
            Observation.value_type.notin_(["INVALID", "IMPUTED", "MISSING", "ZERO"])
        ).count()

        # If observations exist but counts didn't sum up precisely due to default value_type='VALID', handle remainder safely
        if total_obs_count > 0 and (valid_count + zero_count + missing_count + invalid_count + imputed_count) < total_obs_count:
            valid_count = total_obs_count - (zero_count + missing_count + invalid_count + imputed_count)

        observation_breakdown = {
            "valid_count": max(0, valid_count),
            "zero_count": zero_count,
            "missing_count": missing_count,
            "invalid_count": invalid_count,
            "imputed_count": imputed_count,
            "total_observations": total_obs_count
        }

        # Completeness summary
        reporting_facilities_count = self.db.query(Observation.facility_id).distinct().count()
        actual_reported_obs = self.db.query(Observation).filter(Observation.value.isnot(None)).count()
        
        # Estimate expected observations based on total facilities and months
        distinct_indicators_count = self.db.query(Observation.indicator_id).distinct().count()
        expected_obs = total_facilities_count * total_months * (distinct_indicators_count if distinct_indicators_count > 0 else 1)
        completeness_pct = round((actual_reported_obs / expected_obs) * 100.0, 1) if expected_obs > 0 else 100.0

        completeness_summary = {
            "expected_observations": expected_obs,
            "actual_reported_observations": actual_reported_obs,
            "completeness_pct": completeness_pct,
            "total_facilities": total_facilities_count,
            "reporting_facilities": reporting_facilities_count
        }

        # Monthly timeline quality points
        monthly_timeline = []
        for m in all_months:
            m_rep_facs = self.db.query(Observation.facility_id).filter(
                Observation.reporting_month == m
            ).distinct().count()
            
            m_completeness = round((m_rep_facs / total_facilities_count) * 100.0, 1) if total_facilities_count > 0 else 0.0
            m_issues = sum(1 for log in logs if m in log.audit_timestamp)

            m_status = "HEALTHY"
            if m_completeness < 60.0 or any(log.severity == "CRITICAL" for log in logs if m in log.audit_timestamp):
                m_status = "CRITICAL"
            elif m_completeness < 85.0 or any(log.severity in ["ERROR", "WARNING"] for log in logs if m in log.audit_timestamp):
                m_status = "WARNING"

            monthly_timeline.append({
                "reporting_month": m,
                "completeness_pct": m_completeness,
                "reporting_facilities": m_rep_facs,
                "total_facilities": total_facilities_count,
                "issue_count": m_issues,
                "status": m_status
            })

        return {
            "overall_quality_score": overall_score,
            "total_issues": len(logs),
            "severity_counts": severity_counts,
            "category_counts": category_counts,
            "incomplete_facilities_count": len(incomplete_facilities),
            "incomplete_facilities": incomplete_facilities,
            "issues": issues_list,
            "latest_period": latest_period,
            "observation_breakdown": observation_breakdown,
            "completeness_summary": completeness_summary,
            "monthly_timeline": monthly_timeline
        }
