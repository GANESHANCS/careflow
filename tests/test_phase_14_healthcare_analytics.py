import pytest
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.healthcare_intelligence import (
    HealthcareIntelligenceService,
    IneligibleIndicatorError
)
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus


@pytest.fixture
def seed_test_observations(db_session: Session):
    """Seeds test district observations with known zeroes, valid values, and missing periods."""
    # Seed indicator 1.1 for Ariyalur with 10 months (2 months missing: 2016-02 and 2016-03)
    # Months 2015-04 through 2016-01:
    months = [
        ("2015-04", 1000.0, "VALID"),
        ("2015-05", 1100.0, "VALID"),
        ("2015-06", 0.0, "VALID"),      # Observed zero
        ("2015-07", 1050.0, "VALID"),
        ("2015-08", 950.0, "VALID"),
        ("2015-09", 1200.0, "VALID"),
        ("2015-10", 0.0, "VALID"),      # Observed zero
        ("2015-11", 1150.0, "VALID"),
        ("2015-12", 980.0, "VALID"),
        ("2016-01", 1020.0, "VALID"),
        # 2016-02 and 2016-03 omitted to test missing-month detection
    ]

    obs = []
    for mo, val, vtype in months:
        obs.append(
            DistrictObservation(
                id=f"DOBS_P14_TEST_Ariyalur_1.1_{mo}",
                state="Tamil Nadu",
                district="Ariyalur",
                s_no="1.1",
                parameter_name="Total number of pregnant women Registered for ANC",
                subgroup_type="TOTAL",
                is_subgroup_total=True,
                financial_year="2015-16",
                reporting_month=mo,
                observation_date=f"{mo}-01",
                value=val,
                value_type=vtype,
                validation_status="VALIDATED",
                source_file="test_sample.csv",
                ingested_at="2026-10-22T00:00:00Z"
            )
        )

    # Seed an ambiguous indicator observation (14.10.1.c)
    obs.append(
        DistrictObservation(
            id="DOBS_P14_TEST_Ariyalur_14.10.1.c_2015-04",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.10.1.c",
            parameter_name="Total inpatient admissions",
            subgroup_type="1. Children",
            is_subgroup_total=False,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=250.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test_sample.csv",
            ingested_at="2026-10-22T00:00:00Z"
        )
    )

    db_session.add_all(obs)
    db_session.commit()


def test_verified_indicator_eligibility_enforcement(db_session: Session):
    """Confirms only VERIFIED indicators are eligible, while AMBIGUOUS and UNMAPPED are rejected."""
    service = HealthcareIntelligenceService(db_session)

    # 1.1 is VERIFIED -> allowed
    mapping = service._validate_indicator_eligibility("1.1", allow_stock=True)
    assert mapping.status == MappingStatus.VERIFIED
    assert mapping.canonical_id == "IND_antenatal_visits"

    # 14.10.1.c is AMBIGUOUS -> rejected with explicit IneligibleIndicatorError
    with pytest.raises(IneligibleIndicatorError) as exc_ambig:
        service._validate_indicator_eligibility("14.10.1.c", allow_stock=True)
    assert "AMBIGUOUS" in str(exc_ambig.value)
    assert "Only VERIFIED indicators are eligible" in str(exc_ambig.value)

    # 99.99 is UNMAPPED -> rejected
    with pytest.raises(IneligibleIndicatorError) as exc_unmapped:
        service._validate_indicator_eligibility("99.99", allow_stock=True)
    assert "UNMAPPED" in str(exc_unmapped.value)


def test_timeseries_missing_months_and_zeros_detection(db_session: Session, seed_test_observations):
    """
    Verifies that the service retrieves the full 12-month expected sequence,
    accurately detecting 2 missing months and preserving 2 confirmed zeros.
    """
    service = HealthcareIntelligenceService(db_session)
    res = service.get_verified_indicator_timeseries(
        district="Ariyalur",
        s_no="1.1",
        financial_year="2015-16"
    )

    assert res.total_expected_months == 12
    assert res.reported_months_count == 10
    assert res.missing_months_count == 2
    assert res.zero_months_count == 2
    assert res.valid_months_count == 8
    assert res.completeness_ratio == round(10 / 12, 4)

    # Check that points contain exactly 12 items
    assert len(res.points) == 12

    # Check observed zero detection
    june_pt = next(p for p in res.points if p.month == "2015-06")
    assert june_pt.is_zero is True
    assert june_pt.is_missing is False
    assert june_pt.value == 0.0
    assert june_pt.value_type == "OBSERVED_ZERO"

    # Check missing month detection
    feb_pt = next(p for p in res.points if p.month == "2016-02")
    assert feb_pt.is_missing is True
    assert feb_pt.is_zero is False
    assert feb_pt.value is None
    assert feb_pt.value_type == "MISSING"

    mar_pt = next(p for p in res.points if p.month == "2016-03")
    assert mar_pt.is_missing is True
    assert mar_pt.value is None


def test_subgroup_isolation_prevents_double_counting(db_session: Session):
    """
    Verifies that when both TOTAL and disaggregated slices exist,
    the service targets the preferred total slice and prevents double counting.
    """
    # Seed one TOTAL and one slice for 2015-04
    obs1 = DistrictObservation(
        id="DOBS_P14_SG_TOT",
        state="Tamil Nadu",
        district="Chennai",
        s_no="2.2",
        parameter_name="Deliveries conducted at Public Institutions",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=5000.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test.csv",
        ingested_at="2026-10-22T00:00:00Z"
    )
    obs2 = DistrictObservation(
        id="DOBS_P14_SG_SLICE",
        state="Tamil Nadu",
        district="Chennai",
        s_no="2.2",
        parameter_name="Deliveries conducted at Public Institutions",
        subgroup_type="1. PHC",
        is_subgroup_total=False,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=1500.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="test.csv",
        ingested_at="2026-10-22T00:00:00Z"
    )
    db_session.add_all([obs1, obs2])
    db_session.commit()

    service = HealthcareIntelligenceService(db_session)
    res = service.get_verified_indicator_timeseries(
        district="Chennai",
        s_no="2.2",
        financial_year="2015-16"
    )

    # Resolved subgroup must be TOTAL, value must be 5000.0 (not 6500.0!)
    assert res.subgroup_type == "TOTAL"
    apr_pt = next(p for p in res.points if p.month == "2015-04")
    assert apr_pt.value == 5000.0


def test_provenance_and_metadata_fidelity(db_session: Session, seed_test_observations):
    """Confirms canonical metadata, provenance, and rationale are strictly attached."""
    service = HealthcareIntelligenceService(db_session)
    res = service.get_verified_indicator_timeseries(
        district="Ariyalur",
        s_no="1.1",
        financial_year="2015-16"
    )

    assert res.canonical_id == "IND_antenatal_visits"
    assert res.canonical_name == "Antenatal Care (ANC) Registered Visits"
    assert res.category == "Maternal Health"
    assert res.unit == "visits"
    assert "MoHFW HMIS Operational Guidelines" in res.provenance
    assert "Direct clinical equivalent" in res.rationale
    assert res.temporal_aggregation_permitted is True
