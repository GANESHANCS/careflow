"""
Tests for Phase 15A & 15C: Source Discovery, Acquisition Registry, and Cross-Year Comparability.
"""

import pytest
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.source_registry import SourceRegistryCatalog
from backend.app.services.analytics.cross_year_comparability import CrossYearComparabilityService


@pytest.fixture
def seed_comparability_data(db_session: Session):
    months = [f"2015-{m:02d}" for m in range(4, 13)] + [f"2016-{m:02d}" for m in range(1, 4)]
    districts = [
        "Ariyalur", "Chennai", "Coimbatore", "Cuddalore", "Dharmapuri",
        "Dindigul", "Erode", "Kancheepuram", "Kanyakumari", "Karur",
        "Krishnagiri", "Madurai", "Nagapattinam", "Namakkal", "Nilgiris",
        "Perambalur", "Pudukkottai", "Ramanathapuram", "Salem", "Sivaganga",
        "Thanjavur", "Theni", "Thiruvallur", "Thiruvarur", "Thoothukkudi",
        "Tiruchirappalli", "Tirunelveli", "Tiruppur", "Tiruvannamalai",
        "Vellore", "Viluppuram", "Virudhunagar"
    ]
    obs = []
    for d in districts:
        for m in months:
            obs.append(
                DistrictObservation(
                    id=f"DOBS_TEST_{d}_{m}",
                    state="Tamil Nadu",
                    district=d,
                    s_no="1.1",
                    parameter_name="Total pregnant women registered for ANC",
                    subgroup_type="TOTAL",
                    is_subgroup_total=True,
                    financial_year="2015-16",
                    reporting_month=m,
                    observation_date=f"{m}-01",
                    value=100.0,
                    value_type="VALID",
                    validation_status="VALIDATED",
                    source_file="test.csv",
                    ingested_at="2026-10-22T00:00:00Z"
                )
            )
    db_session.add_all(obs)
    db_session.commit()


def test_source_registry_catalog():
    """Verifies official source catalog, file hashes, and acquisition blockers for Tamil Nadu."""
    summary = SourceRegistryCatalog.get_summary({"2015-16": 175872})
    assert summary.state == "Tamil Nadu"
    assert summary.total_registered_years == 3
    assert "2015-16" in summary.ingested_years
    assert "2016-17" in summary.pending_years
    assert "2017-18" in summary.pending_years

    # Check FY 2015-16 details
    fy15 = next(s for s in summary.sources if s.financial_year == "2015-16")
    assert fy15.status == "INGESTED"
    assert fy15.total_observations_ingested == 175872
    assert fy15.file_sha256 is not None
    assert fy15.acquisition_blocker is None

    # Check FY 2016-17 details
    fy16 = next(s for s in summary.sources if s.financial_year == "2016-17")
    assert fy16.status == "BLOCKED_MISSING_OFFICIAL_FILE"
    assert fy16.acquisition_blocker is not None
    assert "authenticated session" in fy16.acquisition_blocker.lower() or "captcha" in fy16.acquisition_blocker.lower()
    assert fy16.ingestion_readiness == "READY_FOR_UPLOAD"


def test_cross_year_comparability_empty_database(db_session: Session):
    """Verifies graceful handling when database has zero district observations."""
    report = CrossYearComparabilityService.get_comparability_report(db_session)
    assert report.available_financial_years == []
    assert report.multi_year_aggregation_permitted is False
    assert any("no district observations" in w.lower() for w in report.comparability_warnings)


def test_cross_year_comparability_report(db_session: Session, seed_comparability_data):
    """Verifies cross-year comparability analysis, boundary checks, and single-year limitation disclosure."""
    report = CrossYearComparabilityService.get_comparability_report(db_session)
    assert report.state == "Tamil Nadu"
    assert "2015-16" in report.available_financial_years

    # Verify boundary shifts catalog contains known Tamil Nadu bifurcations
    bifurcations = {b.bifurcated_district: b.parent_district for b in report.boundary_shifts_catalog}
    assert bifurcations.get("Tenkasi") == "Tirunelveli"
    assert bifurcations.get("Chengalpattu") == "Kancheepuram"
    assert bifurcations.get("Tirupathur") == "Vellore"
    assert bifurcations.get("Ranipet") == "Vellore"

    # Verify coverage details for FY 2015-16
    assert len(report.coverage_by_year) >= 1
    fy15_cov = next(c for c in report.coverage_by_year if c.financial_year == "2015-16")
    assert fy15_cov.distinct_districts_count == 32
    assert fy15_cov.distinct_months_count == 12
    assert len(fy15_cov.missing_months) == 0
    assert fy15_cov.coverage_percentage > 90.0

    # Verify single-year limitation warning
    assert any("single financial year" in w.lower() for w in report.comparability_warnings)
    assert report.multi_year_aggregation_permitted is False
