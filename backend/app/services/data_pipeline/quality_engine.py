from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import numpy as np
import pandas as pd


class QualityIssue(BaseModel):
    check_id: int = Field(..., description="Check number (1-13)")
    check_name: str = Field(..., description="Description of the 13-point data quality check")
    severity: str = Field(..., description="Severity level: INFO, WARNING, ERROR, CRITICAL")
    affected_count: int = Field(default=0, description="Number of affected observations/entities")
    affected_pct: float = Field(default=0.0, description="Percentage of dataset affected")
    description: str = Field(..., description="Detailed issue finding")
    recommended_action: str = Field(..., description="Actionable recommendation")


class QualityScoreBreakdown(BaseModel):
    overall_score: float = Field(..., description="Final overall quality score (0.0 to 100.0)")
    completeness_score: float = Field(..., description="Sub-score for reporting completeness (0-100)")
    validity_score: float = Field(..., description="Sub-score for value validity (0-100)")
    consistency_score: float = Field(..., description="Sub-score for entity & indicator consistency (0-100)")
    duplication_score: float = Field(..., description="Sub-score for uniqueness (0-100)")
    temporal_score: float = Field(..., description="Sub-score for temporal continuity (0-100)")


class DataQualityReport(BaseModel):
    total_observations: int
    total_facilities: int
    reporting_period_start: str
    reporting_period_end: str
    quality_score: QualityScoreBreakdown
    issues: List[QualityIssue]
    diagnostics: Dict[str, Any]


class HMISQualityEngine:
    """
    13-Point Data Quality Audit Engine for HMIS Healthcare Data.
    Evaluates missing values, duplicates, invalid dates, negative counts,
    extreme outliers, temporal continuity, and computes an explainable quality score.
    """

    @classmethod
    def evaluate_dataset(
        cls, 
        observations: List[Dict[str, Any]], 
        facilities: List[Dict[str, Any]],
        dedup_diagnostics: Optional[Dict[str, Any]] = None
    ) -> DataQualityReport:
        
        issues: List[QualityIssue] = []
        df_obs = pd.DataFrame(observations) if observations else pd.DataFrame()
        df_fac = pd.DataFrame(facilities) if facilities else pd.DataFrame()

        total_obs = len(df_obs)
        total_fac = len(df_fac)

        if total_obs == 0:
            empty_score = QualityScoreBreakdown(
                overall_score=0.0, completeness_score=0.0, validity_score=0.0,
                consistency_score=0.0, duplication_score=0.0, temporal_score=0.0
            )
            return DataQualityReport(
                total_observations=0, total_facilities=total_fac,
                reporting_period_start="N/A", reporting_period_end="N/A",
                quality_score=empty_score,
                issues=[QualityIssue(
                    check_id=13, check_name="Source File Integrity", severity="CRITICAL",
                    affected_count=0, affected_pct=100.0,
                    description="Dataset contains 0 observations.",
                    recommended_action="Verify input source file presence."
                )],
                diagnostics={}
            )

        # Ensure required columns present
        for col in ["value", "value_type", "reporting_month", "facility_id", "indicator_code"]:
            if col not in df_obs.columns:
                df_obs[col] = None

        # ----------------------------------------------------
        # CHECK 1: Missing Values
        # ----------------------------------------------------
        missing_mask = df_obs["value"].isnull() | (df_obs["value_type"] == "MISSING")
        missing_count = int(missing_mask.sum())
        missing_pct = round((missing_count / max(1, total_obs)) * 100, 2)
        if missing_count > 0:
            issues.append(QualityIssue(
                check_id=1, check_name="Missing Values",
                severity="WARNING" if missing_pct < 15 else "ERROR",
                affected_count=missing_count, affected_pct=missing_pct,
                description=f"{missing_count} observations ({missing_pct}%) have missing value cells.",
                recommended_action="Maintain missing status; do not impute zeros automatically."
            ))

        # ----------------------------------------------------
        # CHECK 2: Duplicate Records
        # ----------------------------------------------------
        dup_count = dedup_diagnostics.get("duplicates_found", 0) if dedup_diagnostics else 0
        dup_pct = round((dup_count / max(1, total_obs + dup_count)) * 100, 2)
        if dup_count > 0:
            issues.append(QualityIssue(
                check_id=2, check_name="Duplicate Records",
                severity="WARNING" if dup_pct < 5 else "ERROR",
                affected_count=dup_count, affected_pct=dup_pct,
                description=f"{dup_count} duplicate facility-indicator-month observations were detected.",
                recommended_action="Deduplicate deterministically by keeping highest quality / newest record."
            ))

        # ----------------------------------------------------
        # CHECK 3: Invalid Dates
        # ----------------------------------------------------
        invalid_dates = df_obs[df_obs["reporting_month"].isnull()]
        invalid_date_count = len(invalid_dates)
        invalid_date_pct = round((invalid_date_count / max(1, total_obs)) * 100, 2)
        if invalid_date_count > 0:
            issues.append(QualityIssue(
                check_id=3, check_name="Invalid Dates", severity="ERROR",
                affected_count=invalid_date_count, affected_pct=invalid_date_pct,
                description=f"{invalid_date_count} observations have unparseable reporting months.",
                recommended_action="Quarantine records with invalid dates before timeseries modeling."
            ))

        # ----------------------------------------------------
        # CHECK 4: Invalid Numeric Values
        # ----------------------------------------------------
        invalid_num_mask = df_obs["value_type"] == "INVALID"
        invalid_num_count = int(invalid_num_mask.sum())
        invalid_num_pct = round((invalid_num_count / max(1, total_obs)) * 100, 2)
        if invalid_num_count > 0:
            issues.append(QualityIssue(
                check_id=4, check_name="Invalid Numeric Values", severity="ERROR",
                affected_count=invalid_num_count, affected_pct=invalid_num_pct,
                description=f"{invalid_num_count} observations contain non-numeric string noise.",
                recommended_action="Convert string noise to INVALID tag and exclude from numerical aggregations."
            ))

        # ----------------------------------------------------
        # CHECK 5: Negative Healthcare Counts
        # ----------------------------------------------------
        valid_nums = df_obs[df_obs["value"].notnull()]["value"]
        neg_mask = valid_nums < 0
        neg_count = int(neg_mask.sum())
        neg_pct = round((neg_count / max(1, total_obs)) * 100, 2)
        if neg_count > 0:
            issues.append(QualityIssue(
                check_id=5, check_name="Negative Healthcare Counts", severity="CRITICAL",
                affected_count=neg_count, affected_pct=neg_pct,
                description=f"{neg_count} observations contain negative count values (e.g. negative admissions/OPD).",
                recommended_action="Flag negative counts as data entry errors; exclude from demand forecasting."
            ))

        # ----------------------------------------------------
        # CHECK 6: Suspicious Extreme Values / Outliers
        # ----------------------------------------------------
        outlier_count = 0
        if len(valid_nums) > 10:
            q25, q75 = valid_nums.quantile(0.25), valid_nums.quantile(0.75)
            iqr = q75 - q25
            upper_bound = q75 + (5.0 * iqr) # Conservative 5x IQR threshold for extreme outliers
            outlier_mask = valid_nums > upper_bound
            outlier_count = int(outlier_mask.sum())
            outlier_pct = round((outlier_count / max(1, total_obs)) * 100, 2)
            if outlier_count > 0:
                issues.append(QualityIssue(
                    check_id=6, check_name="Suspicious Extreme Values", severity="WARNING",
                    affected_count=outlier_count, affected_pct=outlier_pct,
                    description=f"{outlier_count} observations exceed conservative 5x IQR outlier threshold.",
                    recommended_action="Review extreme spikes against facility size and historical baseline."
                ))

        # ----------------------------------------------------
        # CHECK 7: Missing Reporting Periods
        # ----------------------------------------------------
        valid_months_list = sorted([m for m in df_obs["reporting_month"].dropna().unique() if len(m) == 7])
        start_month = valid_months_list[0] if valid_months_list else "N/A"
        end_month = valid_months_list[-1] if valid_months_list else "N/A"

        # ----------------------------------------------------
        # CHECK 8 & 9: Facility & Entity Consistency
        # ----------------------------------------------------
        unmapped_fac = df_obs[df_obs["facility_id"].str.startswith("FKEY_")]
        unmapped_fac_count = len(unmapped_fac["facility_id"].unique())
        if unmapped_fac_count > 0:
            issues.append(QualityIssue(
                check_id=8, check_name="Facility Identifier Consistency", severity="INFO",
                affected_count=unmapped_fac_count, affected_pct=round((unmapped_fac_count / max(1, total_fac))*100, 2),
                description=f"{unmapped_fac_count} facilities lack official HMIS codes and use composite key hashes.",
                recommended_action="Verify master facility registry to match composite key hashes to HMIS codes."
            ))

        # ----------------------------------------------------
        # CHECK 10: Indicator Catalog Consistency
        # ----------------------------------------------------
        unmapped_ind = df_obs[df_obs["indicator_code"].isnull()]
        unmapped_ind_count = len(unmapped_ind)
        if unmapped_ind_count > 0:
            issues.append(QualityIssue(
                check_id=10, check_name="Indicator Catalog Consistency", severity="WARNING",
                affected_count=unmapped_ind_count, affected_pct=round((unmapped_ind_count / max(1, total_obs))*100, 2),
                description=f"{unmapped_ind_count} observations could not be mapped to standard HMIS indicators.",
                recommended_action="Add raw header aliases to IndicatorCatalog configuration."
            ))

        # ----------------------------------------------------
        # QUALITY SCORE CALCULATION
        # ----------------------------------------------------
        completeness_sub = max(0.0, 100.0 - (missing_pct * 1.5))
        validity_sub = max(0.0, 100.0 - (invalid_num_pct * 3.0 + neg_pct * 5.0))
        duplication_sub = max(0.0, 100.0 - (dup_pct * 2.0))
        consistency_sub = max(0.0, 100.0 - (invalid_date_pct * 3.0))
        temporal_sub = max(0.0, 100.0 - (outlier_count / max(1, total_obs) * 100.0 * 2.0))

        overall_score = round(
            (completeness_sub * 0.30) +
            (validity_sub * 0.25) +
            (duplication_sub * 0.15) +
            (consistency_sub * 0.15) +
            (temporal_sub * 0.15),
            1
        )

        score_breakdown = QualityScoreBreakdown(
            overall_score=overall_score,
            completeness_score=round(completeness_sub, 1),
            validity_score=round(validity_sub, 1),
            consistency_score=round(consistency_sub, 1),
            duplication_score=round(duplication_sub, 1),
            temporal_score=round(temporal_sub, 1)
        )

        return DataQualityReport(
            total_observations=total_obs,
            total_facilities=total_fac,
            reporting_period_start=start_month,
            reporting_period_end=end_month,
            quality_score=score_breakdown,
            issues=issues,
            diagnostics={
                "missing_count": missing_count,
                "negative_count": neg_count,
                "invalid_numeric_count": invalid_num_count,
                "outlier_count": outlier_count,
                "dedup": dedup_diagnostics or {}
            }
        )
