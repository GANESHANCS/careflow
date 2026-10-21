import tempfile
import shutil
from pathlib import Path
import pytest
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from alembic.config import Config
from alembic import command

from backend.app.db.models.district_observation import DistrictObservation, classify_subgroup_total
from backend.app.db.models.observation import Observation
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.repositories.district_observation_repository import DistrictObservationRepository


# -------------------------------------------------------------------
# 1. MODEL CREATION & FIELD TESTS
# -------------------------------------------------------------------

def test_district_observation_creation_and_attributes(db_session: Session):
    obs = DistrictObservation(
        id="DOBS_TamilNadu_Ariyalur_1.1_TOTAL_2015-04",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="1.1",
        parameter_name="Total number of pregnant women Registered for ANC",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=1033.0,
        value_type="VALID",
        validation_status="VALIDATED",
        reported_annual_total=12130.0,
        source_file="hmis-item-rpt-tn-for-2015-16.csv",
        source_row=1,
        ingested_at="2026-10-21T17:00:00Z",
        transformation_version="1.0.0"
    )
    db_session.add(obs)
    db_session.commit()

    saved = db_session.query(DistrictObservation).filter(DistrictObservation.id == obs.id).first()
    assert saved is not None
    assert saved.state == "Tamil Nadu"
    assert saved.district == "Ariyalur"
    assert saved.s_no == "1.1"
    assert saved.value == 1033.0
    assert saved.value_type == "VALID"
    assert saved.reported_annual_total == 12130.0
    assert saved.is_subgroup_total is True
    assert saved.created_at is not None
    assert saved.updated_at is not None


# -------------------------------------------------------------------
# 2. UNIQUENESS CONSTRAINT TESTS
# -------------------------------------------------------------------

def test_district_observation_natural_key_uniqueness(db_session: Session):
    obs1 = DistrictObservation(
        id="DOBS_TN_Ariyalur_1.1_TOTAL_2015-04_1",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="1.1",
        parameter_name="ANC Registration",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=500.0,
        value_type="VALID",
        source_file="test1.csv",
        ingested_at="t"
    )
    db_session.add(obs1)
    db_session.commit()

    # Attempt to insert identical (district, s_no, subgroup_type, reporting_month)
    obs2 = DistrictObservation(
        id="DOBS_TN_Ariyalur_1.1_TOTAL_2015-04_2",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="1.1",
        parameter_name="ANC Registration Duplicate Attempt",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=600.0,
        value_type="VALID",
        source_file="test2.csv",
        ingested_at="t"
    )
    db_session.add(obs2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# -------------------------------------------------------------------
# 3. MEASUREMENT PRESERVATION: ZERO VS MISSING
# -------------------------------------------------------------------

def test_district_observation_zero_preservation(db_session: Session):
    obs = DistrictObservation(
        id="DOBS_TN_Salem_1.6.2_TOTAL_2015-04",
        state="Tamil Nadu",
        district="Salem",
        s_no="1.6.2",
        parameter_name="Eclampsia cases",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=0.0,
        value_type="ZERO",
        reported_annual_total=0.0,
        source_file="test.csv",
        ingested_at="t"
    )
    db_session.add(obs)
    db_session.commit()

    saved = db_session.query(DistrictObservation).filter(DistrictObservation.id == obs.id).first()
    assert saved.value == 0.0
    assert saved.value_type == "ZERO"
    assert saved.value is not None


def test_district_observation_missing_preservation(db_session: Session):
    obs = DistrictObservation(
        id="DOBS_TN_Ariyalur_17.4.1_6-14yrs_2015-04",
        state="Tamil Nadu",
        district="Ariyalur",
        s_no="17.4.1",
        parameter_name="Adolescent deaths",
        subgroup_type="1. 6-14 yrs",
        is_subgroup_total=False,
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=None,
        value_type="MISSING",
        reported_annual_total=None,
        source_file="test.csv",
        ingested_at="t"
    )
    db_session.add(obs)
    db_session.commit()

    saved = db_session.query(DistrictObservation).filter(DistrictObservation.id == obs.id).first()
    assert saved.value is None
    assert saved.value_type == "MISSING"
    assert saved.reported_annual_total is None


# -------------------------------------------------------------------
# 4. SUBGROUP TOTAL CLASSIFICATION TESTS
# -------------------------------------------------------------------

def test_classify_subgroup_total_semantics():
    # True totals
    assert classify_subgroup_total("TOTAL") is True
    assert classify_subgroup_total("Total") is True
    assert classify_subgroup_total("4. Total") is True
    assert classify_subgroup_total("3. Total") is True
    assert classify_subgroup_total("") is True
    assert classify_subgroup_total(None) is True

    # Demographic / event component slices
    assert classify_subgroup_total("1. Children") is False
    assert classify_subgroup_total("2. Adults") is False
    assert classify_subgroup_total("1. 6-14 yrs") is False
    assert classify_subgroup_total("2. 15-55 yrs.") is False
    assert classify_subgroup_total("3. Above 55 yrs.") is False

    # Diagnostic test slices
    assert classify_subgroup_total("1. Number tested") is False
    assert classify_subgroup_total("2. Number Positive") is False
    assert classify_subgroup_total("Number tested") is False

    # Critical inventory lifecycle checks: "5. Total Stock" is NOT an additive demographic total!
    assert classify_subgroup_total("1. Balance From Previous Month") is False
    assert classify_subgroup_total("2. Stocks Received") is False
    assert classify_subgroup_total("3. Unusable Stock") is False
    assert classify_subgroup_total("4. Stock Distributed") is False
    assert classify_subgroup_total("5. Total Stock") is False


# -------------------------------------------------------------------
# 5. COEXISTENCE WITH FACILITY OBSERVATIONS
# -------------------------------------------------------------------

def test_coexistence_with_facility_observations(db_session: Session):
    # 1. Facility level observation
    fac = Facility(
        id="FC_COEX_1",
        facility_code="COEX_1",
        facility_name="Coexistence Hospital",
        facility_type="DH",
        state="Tamil Nadu",
        district="Madurai",
        raw_facility_name="Coexistence Hospital"
    )
    db_session.add(fac)
    db_session.commit()

    fac_obs = Observation(
        id="OBS_FC_COEX_1_antenatal_visits_2024-04",
        facility_id="FC_COEX_1",
        indicator_id="IND_antenatal_visits",
        observation_date="2024-04-01",
        reporting_month="2024-04",
        value=150.0,
        value_type="VALID",
        source_file="facility.csv",
        ingested_at="t"
    )
    db_session.add(fac_obs)

    # 2. District level observation
    dist_obs = DistrictObservation(
        id="DOBS_TN_Madurai_1.1_TOTAL_2015-04",
        state="Tamil Nadu",
        district="Madurai",
        s_no="1.1",
        parameter_name="Total ANC",
        subgroup_type="TOTAL",
        is_subgroup_total=True,
        indicator_id="IND_antenatal_visits",
        financial_year="2015-16",
        reporting_month="2015-04",
        observation_date="2015-04-01",
        value=2450.0,
        value_type="VALID",
        source_file="district.csv",
        ingested_at="t"
    )
    db_session.add(dist_obs)
    db_session.commit()

    # Query facility observations: district obs must not appear
    facility_records = db_session.query(Observation).filter(Observation.facility_id == "FC_COEX_1").all()
    assert len(facility_records) == 1
    assert facility_records[0].value == 150.0

    # Query district observations: facility obs must not appear
    district_records = db_session.query(DistrictObservation).filter(DistrictObservation.district == "Madurai").all()
    assert len(district_records) >= 1
    assert any(d.value == 2450.0 for d in district_records)


# -------------------------------------------------------------------
# 6. REPOSITORY CRUD & FILTERING TESTS
# -------------------------------------------------------------------

def test_district_observation_repository_crud_and_filters(db_session: Session):
    repo = DistrictObservationRepository(db_session)

    records = [
        DistrictObservation(
            id=f"DOBS_D1_{i}",
            state="Tamil Nadu",
            district="Dharmapuri",
            s_no="1.1",
            parameter_name="Total ANC",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month=f"2015-{i:02d}",
            observation_date=f"2015-{i:02d}-01",
            value=float(100 * i),
            value_type="VALID",
            source_file="d.csv",
            ingested_at="t"
        )
        for i in range(4, 9) # April through August
    ]
    # Add a disaggregated slice
    records.append(
        DistrictObservation(
            id="DOBS_D1_SLICE",
            state="Tamil Nadu",
            district="Dharmapuri",
            s_no="14.10.1.c",
            parameter_name="Inpatients",
            subgroup_type="1. Children",
            is_subgroup_total=False,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=45.0,
            value_type="VALID",
            source_file="d.csv",
            ingested_at="t"
        )
    )
    repo.bulk_add(records)
    db_session.commit()

    # 1. Fetch by natural key
    item = repo.get_by_natural_key("Dharmapuri", "1.1", "TOTAL", "2015-04")
    assert item is not None
    assert item.value == 400.0

    # 2. List with totals filter
    totals, count_totals = repo.list_observations(
        district="Dharmapuri",
        is_subgroup_total=True
    )
    assert count_totals == 5
    assert len(totals) == 5

    # 3. List with slices filter
    slices, count_slices = repo.list_observations(
        district="Dharmapuri",
        is_subgroup_total=False
    )
    assert count_slices == 1
    assert slices[0].subgroup_type == "1. Children"

    # 4. List with date range filter
    range_items, count_range = repo.list_observations(
        district="Dharmapuri",
        start_month="2015-05",
        end_month="2015-07"
    )
    assert count_range == 3

    # 5. Distinct queries
    districts = repo.list_distinct_districts(state="Tamil Nadu")
    assert "Dharmapuri" in districts

    params = repo.list_distinct_parameters()
    s_nos = [p["s_no"] for p in params]
    assert "1.1" in s_nos
    assert "14.10.1.c" in s_nos


# -------------------------------------------------------------------
# 7. ISOLATED ALEMBIC MIGRATION TEST
# -------------------------------------------------------------------

def test_isolated_phase_11b_alembic_migration(monkeypatch):
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_migration_11b.db"
    test_db_url = f"sqlite:///{test_db_path.resolve()}"

    from backend.app.core.config import settings
    monkeypatch.setattr(settings, "DATABASE_URL", test_db_url)

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

    try:
        # Upgrade to head (includes Phase 11B c2d3e4f5a6b7)
        command.upgrade(alembic_cfg, "head")

        # Downgrade to Phase 9B (b1c2d3e4f5a6)
        command.downgrade(alembic_cfg, "b1c2d3e4f5a6")

        # Re-upgrade to head
        command.upgrade(alembic_cfg, "head")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
