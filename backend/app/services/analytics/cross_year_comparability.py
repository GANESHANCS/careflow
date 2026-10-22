"""
CAREFlow Cross-Year Data Quality & Comparability Service (Phase 15C).
Evaluates schema consistency, reporting completeness, district boundary shifts,
and indicator semantic equivalence across financial years.
"""

from typing import Dict, Any, List, Optional, Set
from collections import defaultdict
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus


class DistrictBoundaryShift(BaseModel):
    bifurcated_district: str
    parent_district: str
    effective_year: str
    notes: str


class IndicatorStabilityCheck(BaseModel):
    s_no: str
    canonical_id: Optional[str]
    audit_status: str
    parameter_names_by_fy: Dict[str, str]
    subgroups_by_fy: Dict[str, List[str]]
    is_stable: bool
    drift_notes: Optional[str]


class FinancialYearCoverageDetail(BaseModel):
    financial_year: str
    total_observations: int
    distinct_districts_count: int
    districts: List[str]
    distinct_months_count: int
    reporting_months: List[str]
    missing_months: List[str]
    coverage_percentage: float
    confirmed_zero_count: int
    missing_value_count: int
    valid_value_count: int


class CrossYearComparabilityReport(BaseModel):
    state: str = "Tamil Nadu"
    available_financial_years: List[str]
    coverage_by_year: List[FinancialYearCoverageDetail]
    boundary_shifts_catalog: List[DistrictBoundaryShift]
    indicator_stability: List[IndicatorStabilityCheck]
    comparability_warnings: List[str]
    multi_year_aggregation_permitted: bool
    governance_notice: str


class CrossYearComparabilityService:
    """Service assessing data quality and comparability across financial years."""

    # Historical 32 revenue districts of Tamil Nadu (FY 2015-16 standard)
    HISTORICAL_32_DISTRICTS = {
        "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kancheepuram", "Kanyakumari", "Karur",
        "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga",
        "Thanjavur", "Theni", "Thiruvallur", "Thiruvarur", "Thoothukkudi",
        "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvannamalai",
        "Vellore", "Viluppuram", "Virudhunagar"
    }

    # Documented bifurcations in Tamil Nadu administrative history
    KNOWN_BIFURCATIONS = [
        DistrictBoundaryShift(
            bifurcated_district="Tenkasi",
            parent_district="Tirunelveli",
            effective_year="2019-20",
            notes="Carved out of Tirunelveli district in Nov 2019; prior to 2019-20, data was reported under Tirunelveli."
        ),
        DistrictBoundaryShift(
            bifurcated_district="Chengalpattu",
            parent_district="Kancheepuram",
            effective_year="2019-20",
            notes="Carved out of Kancheepuram district in Nov 2019; prior to 2019-20, data was reported under Kancheepuram."
        ),
        DistrictBoundaryShift(
            bifurcated_district="Tirupathur",
            parent_district="Vellore",
            effective_year="2019-20",
            notes="Carved out of Vellore district in Nov 2019; prior to 2019-20, data was reported under Vellore."
        ),
        DistrictBoundaryShift(
            bifurcated_district="Ranipet",
            parent_district="Vellore",
            effective_year="2019-20",
            notes="Carved out of Vellore district in Nov 2019; prior to 2019-20, data was reported under Vellore."
        ),
        DistrictBoundaryShift(
            bifurcated_district="Kallakurichi",
            parent_district="Viluppuram",
            effective_year="2019-20",
            notes="Carved out of Viluppuram district in Nov 2019; prior to 2019-20, data was reported under Viluppuram."
        ),
        DistrictBoundaryShift(
            bifurcated_district="Mayiladuthurai",
            parent_district="Nagapattinam",
            effective_year="2020-21",
            notes="Carved out of Nagapattinam district in Dec 2020; prior to 2020-21, data was reported under Nagapattinam."
        ),
    ]

    @classmethod
    def get_comparability_report(cls, db: Session) -> CrossYearComparabilityReport:
        """Generates comprehensive cross-year data quality and comparability findings."""
        # 1. Inspect available financial years in district_observations
        fy_rows = db.query(
            DistrictObservation.financial_year,
            func.count(DistrictObservation.id)
        ).group_by(DistrictObservation.financial_year).order_by(DistrictObservation.financial_year).all()

        available_fys = [r[0] for r in fy_rows]
        coverage_details: List[FinancialYearCoverageDetail] = []
        warnings: List[str] = []

        if not available_fys:
            warnings.append("No district observations exist in the database.")
            return CrossYearComparabilityReport(
                available_financial_years=[],
                coverage_by_year=[],
                boundary_shifts_catalog=cls.KNOWN_BIFURCATIONS,
                indicator_stability=[],
                comparability_warnings=warnings,
                multi_year_aggregation_permitted=False,
                governance_notice="Dataset contains 0 district observations."
            )

        if len(available_fys) == 1:
            warnings.append(
                f"Only a single financial year ({available_fys[0]}) is currently ingested in the database. "
                "Cross-year comparisons and multi-year seasonal models cannot be validated until FY 2016-17+ data is uploaded."
            )

        # 2. Analyze each financial year
        for fy, obs_count in fy_rows:
            districts_query = db.query(DistrictObservation.district).filter(
                DistrictObservation.financial_year == fy
            ).distinct().all()
            districts = sorted([d[0] for d in districts_query])

            months_query = db.query(DistrictObservation.reporting_month).filter(
                DistrictObservation.financial_year == fy
            ).distinct().all()
            reporting_months = sorted([m[0] for m in months_query])

            # Expected 12 months for this financial year
            start_yr = int(fy.split("-")[0])
            expected_months = [f"{start_yr}-{m:02d}" for m in range(4, 13)] + [f"{start_yr+1}-{m:02d}" for m in range(1, 4)]
            missing_months = [m for m in expected_months if m not in reporting_months]

            # Value type breakdown
            val_type_counts = db.query(
                DistrictObservation.value_type,
                func.count(DistrictObservation.id)
            ).filter(DistrictObservation.financial_year == fy).group_by(DistrictObservation.value_type).all()
            vt_dict = {vt: c for vt, c in val_type_counts}

            valid_cnt = vt_dict.get("VALID", 0)
            zero_cnt = vt_dict.get("ZERO", 0)
            missing_cnt = vt_dict.get("MISSING", 0)
            total_cnt = obs_count or 1
            coverage_pct = round(((valid_cnt + zero_cnt) / total_cnt) * 100.0, 2)

            coverage_details.append(
                FinancialYearCoverageDetail(
                    financial_year=fy,
                    total_observations=obs_count,
                    distinct_districts_count=len(districts),
                    districts=districts,
                    distinct_months_count=len(reporting_months),
                    reporting_months=reporting_months,
                    missing_months=missing_months,
                    coverage_percentage=coverage_pct,
                    confirmed_zero_count=zero_cnt,
                    missing_value_count=missing_cnt,
                    valid_value_count=valid_cnt
                )
            )

            # Check district boundaries
            unrecognized = set(districts) - cls.HISTORICAL_32_DISTRICTS
            if unrecognized:
                warnings.append(
                    f"Financial year {fy} contains districts not present in historical 32-district baseline: {sorted(list(unrecognized))}. "
                    "Ensure boundary bifurcation adjustments before longitudinal trend comparison."
                )

        # 3. Check indicator stability across years for registered indicators
        distinct_snos = db.query(DistrictObservation.s_no).distinct().all()
        stability_checks: List[IndicatorStabilityCheck] = []

        audit_by_sno: Dict[str, str] = {}
        canonical_by_sno: Dict[str, Optional[str]] = {}
        for sno_row in distinct_snos:
            s = sno_row[0]
            rec = IndicatorMappingRegistry.get_mapping(s)
            audit_by_sno[s] = rec.status.value
            canonical_by_sno[s] = rec.canonical_id

        for sno_row in distinct_snos[:30]:  # sample top items
            s_no = sno_row[0]
            param_rows = db.query(
                DistrictObservation.financial_year,
                DistrictObservation.parameter_name,
                DistrictObservation.subgroup_type
            ).filter(DistrictObservation.s_no == s_no).distinct().all()

            param_by_fy: Dict[str, str] = {}
            subgroups_by_fy: Dict[str, Set[str]] = defaultdict(set)

            for fy_item, p_name, s_type in param_rows:
                param_by_fy[fy_item] = p_name
                subgroups_by_fy[fy_item].add(s_type)

            subgroups_list_by_fy = {k: sorted(list(v)) for k, v in subgroups_by_fy.items()}

            audit_status = audit_by_sno.get(s_no, MappingStatus.UNVERIFIED.value)
            canonical_id = canonical_by_sno.get(s_no)

            is_stable = True
            drift_notes = None

            if audit_status == MappingStatus.AMBIGUOUS.value:
                is_stable = False
                drift_notes = "Indicator contains non-additive demographic slices. Cross-year multi-year summation is disallowed."
            elif len(param_by_fy) > 1 and len(set(param_by_fy.values())) > 1:
                is_stable = False
                drift_notes = f"Parameter description shifted across years: {param_by_fy}."

            stability_checks.append(
                IndicatorStabilityCheck(
                    s_no=s_no,
                    canonical_id=canonical_id,
                    audit_status=audit_status,
                    parameter_names_by_fy=param_by_fy,
                    subgroups_by_fy=subgroups_list_by_fy,
                    is_stable=is_stable,
                    drift_notes=drift_notes
                )
            )

        multi_year_allowed = len(available_fys) > 1 and not any("boundary" in w.lower() for w in warnings)

        return CrossYearComparabilityReport(
            state="Tamil Nadu",
            available_financial_years=available_fys,
            coverage_by_year=coverage_details,
            boundary_shifts_catalog=cls.KNOWN_BIFURCATIONS,
            indicator_stability=stability_checks,
            comparability_warnings=warnings,
            multi_year_aggregation_permitted=multi_year_allowed,
            governance_notice=(
                "CAREFlow Rule 7 & 8: Only indicators classified as VERIFIED may be aggregated or compared longitudinally. "
                "Do not automatically merge indicators or districts without verifying boundary definitions and unit equivalence."
            )
        )
