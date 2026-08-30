import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.forecast import Forecast
from backend.app.db.models.model_metadata import ModelMetadata
from backend.app.db.models.data_quality import DataQualityLog


def test_facility_model_creation_and_uniqueness(db_session: Session):
    fac1 = Facility(
        id="FC_1001",
        facility_code="1001",
        facility_name="District Hospital Alpha",
        facility_type="DH",
        state="State_A",
        district="District_X",
        raw_facility_name="District Hospital Alpha"
    )
    db_session.add(fac1)
    db_session.commit()

    saved = db_session.query(Facility).filter(Facility.id == "FC_1001").first()
    assert saved is not None
    assert saved.facility_code == "1001"

    # Enforce unique facility code
    fac2 = Facility(
        id="FC_1002",
        facility_code="1001", # Duplicate code
        facility_name="Duplicate Hospital",
        facility_type="DH",
        state="State_A",
        district="District_X",
        raw_facility_name="Duplicate Hospital"
    )
    db_session.add(fac2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_indicator_model_creation(db_session: Session):
    ind = Indicator(
        id="IND_test_opd",
        code="test_opd",
        name="Test OPD Attendance",
        category="Outpatient",
        unit="visits"
    )
    db_session.add(ind)
    db_session.commit()

    saved = db_session.query(Indicator).filter(Indicator.code == "test_opd").first()
    assert saved is not None
    assert saved.category == "Outpatient"


def test_observation_model_unique_constraint(db_session: Session):
    fac = Facility(id="FC_2001", facility_code="2001", facility_name="Test PHC", facility_type="PHC", state="S", district="D", raw_facility_name="Test PHC")
    ind = Indicator(id="IND_test_ipd", code="test_ipd", name="Test IPD", category="Inpatient", unit="count")
    db_session.add_all([fac, ind])
    db_session.commit()

    obs1 = Observation(
        id="OBS_1",
        facility_id="FC_2001",
        indicator_id="IND_test_ipd",
        observation_date="2024-04-01",
        reporting_month="2024-04",
        value=50.0,
        value_type="VALID",
        source_file="test.csv",
        ingested_at="2026-08-30T00:00:00Z"
    )
    db_session.add(obs1)
    db_session.commit()

    # Enforce composite unique constraint (facility_id, indicator_id, observation_date)
    obs_dup = Observation(
        id="OBS_2",
        facility_id="FC_2001",
        indicator_id="IND_test_ipd",
        observation_date="2024-04-01", # Duplicate key
        reporting_month="2024-04",
        value=50.0,
        value_type="VALID",
        source_file="test2.csv",
        ingested_at="2026-08-30T00:00:00Z"
    )
    db_session.add(obs_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_observation_preserves_missing_vs_zero(db_session: Session):
    fac = Facility(id="FC_3001", facility_code="3001", facility_name="Test CHC", facility_type="CHC", state="S", district="D", raw_facility_name="Test CHC")
    ind = Indicator(id="IND_test_anc", code="test_anc", name="Test ANC", category="Maternal", unit="count")
    db_session.add_all([fac, ind])
    db_session.commit()

    # Zero value
    obs_zero = Observation(
        id="OBS_ZERO", facility_id="FC_3001", indicator_id="IND_test_anc",
        observation_date="2024-04-01", reporting_month="2024-04",
        value=0.0, value_type="ZERO", source_file="t.csv", ingested_at="2026-08-30T00:00:00Z"
    )
    # Missing value
    obs_null = Observation(
        id="OBS_NULL", facility_id="FC_3001", indicator_id="IND_test_anc",
        observation_date="2024-05-01", reporting_month="2024-05",
        value=None, value_type="MISSING", source_file="t.csv", ingested_at="2026-08-30T00:00:00Z"
    )
    db_session.add_all([obs_zero, obs_null])
    db_session.commit()

    saved_z = db_session.query(Observation).filter(Observation.id == "OBS_ZERO").first()
    saved_m = db_session.query(Observation).filter(Observation.id == "OBS_NULL").first()

    assert saved_z.value == 0.0
    assert saved_z.value_type == "ZERO"

    assert saved_m.value is None
    assert saved_m.value_type == "MISSING"
