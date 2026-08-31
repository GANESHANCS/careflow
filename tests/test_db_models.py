import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.forecast import Forecast
from backend.app.db.models.model_metadata import ModelMetadata
from backend.app.db.models.data_quality import DataQualityLog
from backend.app.db.models.user import User
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_error_log import ImportErrorLog


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


def test_user_model_creation_and_uniqueness(db_session: Session):
    user = User(
        username="health_admin",
        email="admin@careflow.gov.in",
        hashed_password="secure_hashed_password_string",
        role="ADMIN",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()

    saved_user = db_session.query(User).filter(User.username == "health_admin").first()
    assert saved_user is not None
    assert saved_user.role == "ADMIN"
    assert saved_user.is_active is True
    assert saved_user.created_at is not None

    # Duplicate username should fail
    dup_user = User(
        username="health_admin",
        hashed_password="another_password",
        role="ANALYST"
    )
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_import_job_and_error_log_relationship(db_session: Session):
    job = ImportJob(
        job_code="JOB-20260831-001",
        original_filename="hmis_2024_q1.xlsx",
        file_size_bytes=1048576,
        mime_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        status="PROCESSING",
        total_records=150,
        records_imported=140,
        records_rejected=10,
        quality_score=93.5
    )
    db_session.add(job)
    db_session.commit()

    saved_job = db_session.query(ImportJob).filter(ImportJob.job_code == "JOB-20260831-001").first()
    assert saved_job is not None
    assert saved_job.status == "PROCESSING"

    # Add error logs associated with this import job
    err1 = ImportErrorLog(
        import_job_id=saved_job.id,
        source_row=12,
        source_sheet="Maternal Health",
        error_code="INVALID_DATE_FORMAT",
        severity="WARNING",
        message="Date column contained ambiguous string value."
    )
    err2 = ImportErrorLog(
        import_job_id=saved_job.id,
        source_row=45,
        source_sheet="Outpatient",
        error_code="UNMAPPED_INDICATOR",
        severity="ERROR",
        message="Column header could not be mapped to catalog indicator."
    )
    db_session.add_all([err1, err2])
    db_session.commit()

    # Query job with relationships
    queried_job = db_session.query(ImportJob).filter(ImportJob.id == saved_job.id).first()
    assert queried_job is not None
    assert len(queried_job.error_logs) == 2
    assert queried_job.error_logs[0].error_code == "INVALID_DATE_FORMAT"
