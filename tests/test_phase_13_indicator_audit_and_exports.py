import csv
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.indicator import Indicator
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus
from backend.app.services.analytics.district_export import DistrictExportService


@pytest.fixture
def seed_phase_13_data(db_session: Session):
    """Seeds multi-subgroup observations (e.g. 14.10.1.c with Children & Adults) to test export isolation."""
    districts = ["Ariyalur", "Chennai", "Coimbatore"]
    obs = []

    # Seed 14.10.1.c with both Children and Adults slices for reporting_month 2015-04
    for idx, dist in enumerate(districts):
        # 1. Children slice
        obs.append(
            DistrictObservation(
                id=f"DOBS_P13_{dist}_14.10.1.c_Children_2015-04",
                state="Tamil Nadu",
                district=dist,
                s_no="14.10.1.c",
                parameter_name="Total number of patients admitted (Inpatients) during the month (sum of items 14.10.1.a and 14.10.1.b)",
                subgroup_type="1. Children",
                is_subgroup_total=False,
                financial_year="2015-16",
                reporting_month="2015-04",
                observation_date="2015-04-01",
                value=float((idx + 1) * 100),  # 100, 200, 300
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test_p13.csv",
                ingested_at="2026-10-21T00:00:00Z"
            )
        )
        # 2. Adults slice
        obs.append(
            DistrictObservation(
                id=f"DOBS_P13_{dist}_14.10.1.c_Adults_2015-04",
                state="Tamil Nadu",
                district=dist,
                s_no="14.10.1.c",
                parameter_name="Total number of patients admitted (Inpatients) during the month (sum of items 14.10.1.a and 14.10.1.b)",
                subgroup_type="2. Adults",
                is_subgroup_total=False,
                financial_year="2015-16",
                reporting_month="2015-04",
                observation_date="2015-04-01",
                value=float((idx + 1) * 500),  # 500, 1000, 1500
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test_p13.csv",
                ingested_at="2026-10-21T00:00:00Z"
            )
        )

    # Seed 14.12.1 with single TOTAL slice
    for idx, dist in enumerate(districts):
        obs.append(
            DistrictObservation(
                id=f"DOBS_P13_{dist}_14.12.1_TOTAL_2015-04",
                state="Tamil Nadu",
                district=dist,
                s_no="14.12.1",
                parameter_name="OPD attendance (All)",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month="2015-04",
                observation_date="2015-04-01",
                value=float((idx + 1) * 1000),
                value_type="VALID",
                validation_status="VALIDATED",
                source_file="test_p13.csv",
                ingested_at="2026-10-21T00:00:00Z"
            )
        )

    db_session.add_all(obs)
    db_session.commit()


# ===========================================================================
# Phase 13A: Indicator Registry & Provenance Classification Tests
# ===========================================================================

def test_phase_13a_indicator_14_12_1_is_verified():
    """Confirms 14.12.1 is classified as VERIFIED based on raw MoHFW CSV evidence."""
    mapping = IndicatorMappingRegistry.get_mapping("14.12.1")
    assert mapping.status == MappingStatus.VERIFIED
    assert mapping.canonical_id == "IND_opd_attendance"
    assert mapping.canonical_name == "Outpatient Department (OPD) Attendance"
    assert mapping.category == "Outpatient Services"
    assert mapping.unit == "visits"
    assert mapping.is_stock_metric is False
    assert "14.12.1" in mapping.rationale
    assert "Outpatient Department attendance" in mapping.rationale


def test_phase_13a_indicator_14_10_1_c_is_ambiguous():
    """
    Confirms 14.10.1.c is classified as AMBIGUOUS because official state HMIS returns
    only provide demographic slices ('1. Children' and '2. Adults') without a unified TOTAL row.
    """
    mapping = IndicatorMappingRegistry.get_mapping("14.10.1.c")
    assert mapping.status == MappingStatus.AMBIGUOUS
    assert mapping.canonical_id == "IND_inpatient_admissions"
    assert "Disaggregated Slices" in mapping.canonical_name
    assert "AMBIGUOUS" in mapping.rationale
    assert "Children" in mapping.rationale
    assert "Adults" in mapping.rationale


def test_phase_13a_all_core_registered_indicators_status():
    """Validates the exact status classification across all registered core indicators."""
    expected_statuses = {
        "1.1": MappingStatus.VERIFIED,        # ANC registered visits
        "2.2": MappingStatus.VERIFIED,        # Institutional Deliveries (Public)
        "2.3": MappingStatus.VERIFIED,        # Institutional Deliveries (Private)
        "6.1": MappingStatus.VERIFIED,        # PNC within 48h
        "6.2": MappingStatus.VERIFIED,        # PNC between 48h and 14 days
        "10.1.13.c": MappingStatus.VERIFIED,  # Full immunisation 9-11m
        "14.12.1": MappingStatus.VERIFIED,    # OPD attendance (All)
        "14.10.1.c": MappingStatus.AMBIGUOUS, # IPD admissions (Disaggregated slices only)
    }
    for s_no, exp_status in expected_statuses.items():
        rec = IndicatorMappingRegistry.get_mapping(s_no)
        assert rec.status == exp_status, f"Indicator {s_no} status mismatch: expected {exp_status}, got {rec.status}"


def test_phase_13a_audit_report_reflects_ambiguous_mappings(client: TestClient, auth_headers: dict, seed_phase_13_data):
    """Verifies that /api/analytics/district/indicators/audit exposes ambiguous mappings."""
    res = client.get("/api/analytics/district/indicators/audit", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert "ambiguous_mappings_count" in data
    assert "ambiguous_mappings" in data
    assert data["ambiguous_mappings_count"] == 1  # 14.10.1.c is ambiguous
    ambig_snos = [m["s_no"] for m in data["ambiguous_mappings"]]
    assert "14.10.1.c" in ambig_snos


# ===========================================================================
# Phase 13B & 13C: Comparison Export Subgroup Resolution Defect Regression Tests
# ===========================================================================

def test_phase_13c_export_comparison_resolves_subgroup_when_omitted(
    client: TestClient, auth_headers: dict, seed_phase_13_data
):
    """
    Regression test for comparison export defect:
    When exporting 14.10.1.c (which has multiple subgroups) with subgroup_type omitted,
    the service must resolve a default subgroup rather than returning interleaved duplicate
    rows with conflicting ranks for each district.
    """
    res = client.get(
        "/api/analytics/district/export/compare?s_no=14.10.1.c&reporting_month=2015-04",
        headers=auth_headers
    )
    assert res.status_code == 200
    content = res.text

    # Header comment must declare the resolved subgroup
    assert "# Indicator S.No: 14.10.1.c | Reporting Period: 2015-04" in content
    assert "Subgroup:" in content

    lines = [l for l in content.splitlines() if not l.startswith("#")]
    reader = csv.reader(lines)
    header = next(reader)
    assert "district" in header
    assert "rank" in header

    rows = list(reader)
    # Exactly 3 districts seeded -> must yield exactly 3 rows (not 6!)
    assert len(rows) == 3, f"Expected 3 rows for 3 districts, got {len(rows)} (duplicate district rows detected!)"

    # Distinct districts
    districts = [r[0] for r in rows]
    assert len(districts) == len(set(districts)), f"Duplicate districts detected in comparison export: {districts}"

    # Rankings must be strictly 1, 2, 3 with no duplicates
    ranks = [int(r[7]) for r in rows if r[7]]
    assert sorted(ranks) == [1, 2, 3], f"Invalid ranks in export: {ranks}"


def test_phase_13c_export_comparison_explicit_subgroup(
    client: TestClient, auth_headers: dict, seed_phase_13_data
):
    """Verifies that passing an explicit subgroup filters correctly."""
    res = client.get(
        "/api/analytics/district/export/compare?s_no=14.10.1.c&reporting_month=2015-04&subgroup_type=2.+Adults",
        headers=auth_headers
    )
    assert res.status_code == 200
    lines = [l for l in res.text.splitlines() if not l.startswith("#")]
    reader = csv.reader(lines)
    next(reader)
    rows = list(reader)
    assert len(rows) == 3
    # Values for Adults were 500, 1000, 1500
    values = sorted([float(r[5]) for r in rows])
    assert values == [500.0, 1000.0, 1500.0]


# ===========================================================================
# Phase 13B: Multi-Year Natural Key Constraint Verification
# ===========================================================================

def test_phase_13b_actual_natural_key_constraint(db_session: Session):
    """
    Verifies that the actual SQLite/PostgreSQL database constraint is:
    UniqueConstraint('district', 's_no', 'subgroup_type', 'reporting_month', name='uq_district_obs_natural_key')
    and does NOT include financial_year.
    """
    first_obs = DistrictObservation(
        id="DOBS_P13_KEY_1",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="14.12.1",
        parameter_name="OPD attendance",
        subgroup_type="TOTAL",
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=100.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="f1.csv",
        ingested_at="2026-10-21T00:00:00Z"
    )
    db_session.add(first_obs)
    db_session.flush()

    # Attempt inserting identical natural key coordinates with a different financial_year
    second_obs = DistrictObservation(
        id="DOBS_P13_KEY_2",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="14.12.1",
        parameter_name="OPD attendance",
        subgroup_type="TOTAL",
        financial_year="2016-17",  # Different FY, but same (district, s_no, subgroup_type, reporting_month)
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=200.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="f2.csv",
        ingested_at="2026-10-21T00:00:00Z"
    )
    db_session.add(second_obs)
    # Must raise IntegrityError because financial_year is NOT part of uq_district_obs_natural_key
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()
