import io
import tempfile
import os
from datetime import datetime, timezone
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command

from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_observation_record import ImportObservationRecord
from backend.app.db.models.observation import Observation
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.data_quality import DataQualityLog
from backend.app.services.imports.import_service import (
    HMISImportService,
    ImportRollbackDependencyConflictError,
    ImportRollbackIneligibleStatusError,
)


def create_csv_payload(rows: list) -> bytes:
    """Helper to convert row dictionaries to CSV bytes."""
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def test_rollback_created_observations(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 1: Rolling back an import that created new observations deletes them cleanly."""
    csv_bytes = create_csv_payload([
        {
            "State": "StateAlpha",
            "District": "District1",
            "Facility Code": "FAC_ROLL_1",
            "Facility Name": "Rollback Test Clinic A",
            "Reporting Month": "2024-06",
            "OPD Attendance": 320.0,
            "Inpatient Admissions": 45.0,
        }
    ])

    # Upload and process synchronously for rollback testing
    upload_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("rollback_created.csv", csv_bytes, "text/csv")},
        headers=admin_auth_headers
    )
    assert upload_res.status_code == 201
    job_code = upload_res.json()["job_code"]

    # Verify observations were created
    obs_created = db_session.query(Observation).filter(Observation.reporting_month == "2024-06").all()
    assert len(obs_created) == 2
    obs_ids = [o.id for o in obs_created]

    # Verify change records were logged
    records = db_session.query(ImportObservationRecord).filter(
        ImportObservationRecord.import_job.has(job_code=job_code)
    ).all()
    assert len(records) == 2
    assert all(r.action == "INSERT" for r in records)

    # Perform Rollback as ADMIN
    rb_res = client.post(
        f"/api/imports/{job_code}/rollback",
        json={"reason": "Testing rollback of created observations"},
        headers=admin_auth_headers
    )
    assert rb_res.status_code == 200
    rb_data = rb_res.json()
    assert rb_data["status"] == "ROLLED_BACK"
    assert rb_data["records_deleted"] == 2
    assert rb_data["records_restored"] == 0
    assert rb_data["rolled_back_by"] == "test_admin"

    # Verify observations were removed from database
    obs_after = db_session.query(Observation).filter(Observation.id.in_(obs_ids)).all()
    assert len(obs_after) == 0

    # Verify import job status and metadata
    job = db_session.query(ImportJob).filter(ImportJob.job_code == job_code).first()
    assert job.status == "ROLLED_BACK"
    assert job.rolled_back_at is not None
    assert job.rolled_back_by == "test_admin"
    assert job.rollback_reason == "Testing rollback of created observations"

    # Verify raw file and error logs are NOT deleted
    assert os.path.exists(job.storage_path)

    # Verify DataQualityLog was cleaned up
    dq = db_session.query(DataQualityLog).filter(DataQualityLog.id == f"DQ_{job_code}").first()
    assert dq is None


def test_rollback_updated_observations_and_provenance(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 2 & 3: Rolling back an import that updated existing observations restores exact previous values and provenance."""
    # Seed facility and indicator
    fac = Facility(
        id="FC_FAC_ROLL_2",
        facility_code="FAC_ROLL_2",
        facility_name="Pre-existing Facility",
        facility_type="PHC",
        state="StateBeta",
        district="District2",
        raw_facility_name="Pre-existing Facility"
    )
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="OPD Attendance", category="General", unit="count", active=True)
    db_session.add_all([fac, ind])
    db_session.commit()

    # Pre-existing observation with baseline provenance
    original_obs = Observation(
        id="OBS_FC_FAC_ROLL_2_opd_attendance_2024-05",
        facility_id="FC_FAC_ROLL_2",
        indicator_id="IND_opd_attendance",
        observation_date="2024-05-01",
        reporting_month="2024-05",
        value=150.0,
        value_type="VALID",
        validation_status="VALIDATED",
        source_file="initial_baseline_2024.csv",
        source_sheet="Sheet1",
        source_row=10,
        ingested_at="2024-05-02T10:00:00Z",
        transformation_version="1.0.0",
        last_import_job_id=None
    )
    db_session.add(original_obs)
    db_session.commit()

    # Ingest new import that updates this observation
    update_csv = create_csv_payload([
        {
            "State": "StateBeta",
            "District": "District2",
            "Facility Code": "FAC_ROLL_2",
            "Facility Name": "Pre-existing Facility",
            "Reporting Month": "2024-05",
            "OPD Attendance": 450.0,  # Modified value
        }
    ])

    upload_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("updated_dataset.csv", update_csv, "text/csv")},
        headers=admin_auth_headers
    )
    assert upload_res.status_code == 201
    job_code = upload_res.json()["job_code"]

    # Verify observation was updated
    db_session.refresh(original_obs)
    assert original_obs.value == 450.0
    assert original_obs.source_file == "updated_dataset.csv"

    # Verify change record stored before-image
    change_rec = db_session.query(ImportObservationRecord).filter(
        ImportObservationRecord.observation_id == original_obs.id
    ).first()
    assert change_rec.action == "UPDATE"
    assert change_rec.previous_value == 150.0
    assert change_rec.previous_source_file == "initial_baseline_2024.csv"
    assert change_rec.previous_transformation_version == "1.0.0"
    assert change_rec.new_value == 450.0

    # Perform Rollback
    rb_res = client.post(
        f"/api/imports/{job_code}/rollback",
        json={"reason": "Revert erroneous updated attendance"},
        headers=admin_auth_headers
    )
    assert rb_res.status_code == 200
    assert rb_res.json()["records_restored"] == 1

    # Verify observation was restored to exact previous state
    db_session.refresh(original_obs)
    assert original_obs.value == 150.0
    assert original_obs.source_file == "initial_baseline_2024.csv"
    assert original_obs.source_sheet == "Sheet1"
    assert original_obs.source_row == 10
    assert original_obs.transformation_version == "1.0.0"
    assert original_obs.ingested_at == "2024-05-02T10:00:00Z"
    assert original_obs.last_import_job_id is None


def test_rollback_preserves_unrelated_observations(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 4: Rolling back an import preserves completely unrelated observations."""
    # Create unrelated observation
    fac = Facility(
        id="FAC_UNRELATED",
        facility_code="FAC_UNRELATED",
        facility_name="Unrelated PHC",
        facility_type="PHC",
        state="StateX",
        district="DistX",
        raw_facility_name="Unrelated PHC"
    )
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="OPD Attendance", category="General", unit="count", active=True)
    db_session.add_all([fac, ind])
    db_session.commit()

    unrelated_obs = Observation(
        id="OBS_FAC_UNRELATED_opd_attendance_2024-01",
        facility_id="FAC_UNRELATED",
        indicator_id="IND_opd_attendance",
        observation_date="2024-01-01",
        reporting_month="2024-01",
        value=888.0,
        value_type="VALID",
        source_file="unrelated_file.csv",
        ingested_at="2024-01-02T10:00:00Z"
    )
    db_session.add(unrelated_obs)
    db_session.commit()

    # Import target job
    target_csv = create_csv_payload([
        {
            "State": "StateY",
            "District": "DistY",
            "Facility Code": "FAC_TARGET",
            "Facility Name": "Target Hospital",
            "Reporting Month": "2024-07",
            "OPD Attendance": 500.0,
        }
    ])
    upload_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("target_import.csv", target_csv, "text/csv")},
        headers=admin_auth_headers
    )
    job_code = upload_res.json()["job_code"]

    # Roll back target job
    rb_res = client.post(f"/api/imports/{job_code}/rollback", headers=admin_auth_headers)
    assert rb_res.status_code == 200

    # Verify unrelated observation remains completely untouched
    db_session.refresh(unrelated_obs)
    assert unrelated_obs.value == 888.0
    assert unrelated_obs.source_file == "unrelated_file.csv"


def test_rollback_dependency_conflict_prevention(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 5: Prevents rollback when subsequent active imports modified the same observation."""
    # Import Job 1: Creates observation
    csv_1 = create_csv_payload([
        {
            "State": "StateConflict",
            "District": "DistrictC",
            "Facility Code": "FAC_CONF_1",
            "Facility Name": "Conflict Clinic",
            "Reporting Month": "2024-08",
            "OPD Attendance": 100.0,
        }
    ])
    res1 = client.post("/api/imports?sync=true", files={"file": ("batch1.csv", csv_1, "text/csv")}, headers=admin_auth_headers)
    job_code_1 = res1.json()["job_code"]

    # Import Job 2: Modifies same observation
    csv_2 = create_csv_payload([
        {
            "State": "StateConflict",
            "District": "DistrictC",
            "Facility Code": "FAC_CONF_1",
            "Facility Name": "Conflict Clinic",
            "Reporting Month": "2024-08",
            "OPD Attendance": 200.0,
        }
    ])
    res2 = client.post("/api/imports?sync=true", files={"file": ("batch2.csv", csv_2, "text/csv")}, headers=admin_auth_headers)
    job_code_2 = res2.json()["job_code"]

    # Attempt to rollback Job 1 while Job 2 is active -> MUST FAIL WITH 409 CONFLICT
    rb_res = client.post(f"/api/imports/{job_code_1}/rollback", headers=admin_auth_headers)
    assert rb_res.status_code == 409
    err_detail = rb_res.json()["detail"]
    assert "subsequent active import job(s)" in err_detail.lower() or "dependent" in err_detail.lower()

    # Verify Job 1 was NOT rolled back
    job1 = db_session.query(ImportJob).filter(ImportJob.job_code == job_code_1).first()
    assert job1.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS")

    # If Job 2 is rolled back first, then Job 1 CAN be rolled back
    rb_res2 = client.post(f"/api/imports/{job_code_2}/rollback", headers=admin_auth_headers)
    assert rb_res2.status_code == 200

    # Now Job 1 rollback should succeed
    rb_res1_retry = client.post(f"/api/imports/{job_code_1}/rollback", headers=admin_auth_headers)
    assert rb_res1_retry.status_code == 200
    assert rb_res1_retry.json()["status"] == "ROLLED_BACK"


def test_rollback_ineligible_statuses(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 6: Reject rollback on jobs with ineligible statuses (QUEUED, PROCESSING, FAILED)."""
    # Create jobs directly with ineligible statuses
    job_queued = ImportJob(job_code="JOB_QUEUED", original_filename="queued.csv", status="QUEUED")
    job_processing = ImportJob(job_code="JOB_PROCESSING", original_filename="proc.csv", status="PROCESSING")
    job_failed = ImportJob(job_code="JOB_FAILED", original_filename="fail.csv", status="FAILED")
    db_session.add_all([job_queued, job_processing, job_failed])
    db_session.commit()

    for code in ["JOB_QUEUED", "JOB_PROCESSING", "JOB_FAILED"]:
        res = client.post(f"/api/imports/{code}/rollback", headers=admin_auth_headers)
        assert res.status_code == 400
        assert "Cannot roll back import job" in res.json()["detail"]


def test_rollback_unauthorized_roles(client: TestClient, db_session: Session, auth_headers: dict, viewer_auth_headers: dict):
    """Test 7: Reject rollback for ANALYST and VIEWER roles."""
    job = ImportJob(job_code="JOB_AUTH_TEST", original_filename="test.csv", status="COMPLETED")
    db_session.add(job)
    db_session.commit()

    # Analyst attempt -> 403
    res_analyst = client.post(f"/api/imports/{job.job_code}/rollback", headers=auth_headers)
    assert res_analyst.status_code == 403

    # Viewer attempt -> 403
    res_viewer = client.post(f"/api/imports/{job.job_code}/rollback", headers=viewer_auth_headers)
    assert res_viewer.status_code == 403

    # Unauthenticated attempt -> 401
    res_no_auth = client.post(f"/api/imports/{job.job_code}/rollback")
    assert res_no_auth.status_code == 401


def test_rollback_repeated_requests_idempotent(client: TestClient, db_session: Session, admin_auth_headers: dict):
    """Test 8: Repeated rollback requests are safe and idempotent."""
    csv_bytes = create_csv_payload([
        {
            "State": "StateIdemp",
            "District": "DistrictI",
            "Facility Code": "FAC_IDEMP",
            "Facility Name": "Idempotency Clinic",
            "Reporting Month": "2024-09",
            "OPD Attendance": 99.0,
        }
    ])
    upload_res = client.post("/api/imports?sync=true", files={"file": ("idemp.csv", csv_bytes, "text/csv")}, headers=admin_auth_headers)
    job_code = upload_res.json()["job_code"]

    # First rollback
    res1 = client.post(f"/api/imports/{job_code}/rollback", headers=admin_auth_headers)
    assert res1.status_code == 200
    assert res1.json()["records_deleted"] == 1

    # Second rollback (identical request)
    res2 = client.post(f"/api/imports/{job_code}/rollback", headers=admin_auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "ROLLED_BACK"
    assert data2["records_deleted"] == 0
    assert "already been rolled back" in data2["message"].lower()


def test_rollback_atomic_on_exception(db_session: Session, monkeypatch):
    """Test 9: Rollback operations are strictly atomic; any mid-operation failure triggers full transaction rollback."""
    service = HMISImportService(db_session)
    job = ImportJob(job_code="JOB_ATOMIC_FAIL", original_filename="atomic.csv", status="COMPLETED")
    db_session.add(job)
    db_session.flush()

    # Add change records
    rec = ImportObservationRecord(
        import_job_id=job.id,
        observation_id="OBS_ATOMIC_1",
        action="INSERT",
        new_value=123.0
    )
    obs = Observation(
        id="OBS_ATOMIC_1",
        facility_id="FAC_ATOMIC",
        indicator_id="IND_ATOMIC",
        observation_date="2024-10-01",
        reporting_month="2024-10",
        value=123.0,
        source_file="atomic.csv",
        ingested_at="2024-10-02"
    )
    db_session.add_all([rec, obs])
    db_session.commit()

    # Simulate an unexpected failure during deletion
    def mock_delete_fail(instance):
        raise RuntimeError("Simulated transient storage or database lock error")

    monkeypatch.setattr(db_session, "delete", mock_delete_fail)

    with pytest.raises(RuntimeError):
        service.rollback_import_job("JOB_ATOMIC_FAIL", rolled_back_by="admin")

    # Verify atomic rollback left the state intact
    db_session.rollback()
    job_refreshed = db_session.query(ImportJob).filter(ImportJob.job_code == "JOB_ATOMIC_FAIL").first()
    assert job_refreshed.status == "COMPLETED"
    obs_refreshed = db_session.query(Observation).filter(Observation.id == "OBS_ATOMIC_1").first()
    assert obs_refreshed is not None


def test_alembic_migration_upgrade_downgrade_isolated(monkeypatch, tmp_path):
    """Test 11: Validates database migration upgrade and downgrade behavior in an isolated temporary test database."""
    from backend.app.core.config import settings

    db_path = (tmp_path / "isolated_alembic_test.db").as_posix()
    db_url = f"sqlite:///{db_path}"

    monkeypatch.setattr(settings, "DATABASE_URL", db_url)
    monkeypatch.setenv("DATABASE_URL", db_url)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)

    # 1. Upgrade from scratch to head
    command.upgrade(cfg, "head")

    # Verify tables created
    engine = create_engine(db_url)
    try:
        with engine.connect() as conn:
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in result.fetchall()]
            assert "import_observation_records" in tables
            assert "import_jobs" in tables
            assert "observations" in tables

            # Verify columns
            res_obs = conn.exec_driver_sql("PRAGMA table_info(observations)")
            obs_cols = [r[1] for r in res_obs.fetchall()]
            assert "last_import_job_id" in obs_cols

            res_job = conn.exec_driver_sql("PRAGMA table_info(import_jobs)")
            job_cols = [r[1] for r in res_job.fetchall()]
            assert "rolled_back_at" in job_cols
            assert "rolled_back_by" in job_cols
            assert "rollback_reason" in job_cols
    finally:
        engine.dispose()

    # 2. Downgrade to previous revision (e63cafcc4f9d)
    command.downgrade(cfg, "e63cafcc4f9d")

    engine2 = create_engine(db_url)
    try:
        with engine2.connect() as conn:
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")
            tables_down = [r[0] for r in result.fetchall()]
            assert "import_observation_records" not in tables_down

            res_obs = conn.exec_driver_sql("PRAGMA table_info(observations)")
            obs_cols = [r[1] for r in res_obs.fetchall()]
            assert "last_import_job_id" not in obs_cols
    finally:
        engine2.dispose()

    # 3. Re-upgrade to head to verify repeatable upgrade
    command.upgrade(cfg, "head")

    engine3 = create_engine(db_url)
    try:
        with engine3.connect() as conn:
            result = conn.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table'")
            tables_reup = [r[0] for r in result.fetchall()]
            assert "import_observation_records" in tables_reup
    finally:
        engine3.dispose()
