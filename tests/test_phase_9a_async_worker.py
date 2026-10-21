import io
import os
import time
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command

from backend.app.core.config import settings
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_observation_record import ImportObservationRecord
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.observation import Observation
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.data_quality import DataQualityLog
from backend.app.services.imports.import_service import HMISImportService
from backend.app.services.imports.worker import HMISImportWorker
from backend.app.services.imports.watcher import HMISIncomingDirectoryWatcher
from backend.app.services.imports.schema_profiles import (
    SchemaProfileRegistry,
    MOHFWStandardV2Profile,
    FacilityMonthlyTabularV1Profile,
)


def create_csv_bytes(rows: list) -> bytes:
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# -------------------------------------------------------------------
# 1. ASYNC JOB CREATION & PROGRESS ENDPOINT TESTS
# -------------------------------------------------------------------

def test_async_job_creation_and_status_endpoint(client: TestClient, db_session: Session, auth_headers: dict):
    csv_bytes = create_csv_bytes([
        {
            "State": "StateAsync",
            "District": "DistrictA",
            "Facility Code": "FAC_ASYNC_1",
            "Facility Name": "Async Primary Health Centre",
            "Reporting Month": "2024-05",
            "OPD Attendance": 210.0,
            "Inpatient Admissions": 30.0,
        }
    ])

    res = client.post("/api/imports", files={"file": ("async_test.csv", csv_bytes, "text/csv")}, headers=auth_headers)
    assert res.status_code == 201
    job_data = res.json()

    assert job_data["status"] in ("QUEUED", "PROCESSING", "COMPLETED")
    job_code = job_data["job_code"]

    # Poll status endpoint
    status_res = client.get(f"/api/imports/{job_code}/status", headers=auth_headers)
    assert status_res.status_code == 200
    st = status_res.json()
    assert st["job_code"] == job_code
    assert "status" in st
    assert "progress_percent" in st
    assert "processed_records" in st


def test_status_endpoint_404_for_unknown_job(client: TestClient, auth_headers: dict):
    res = client.get("/api/imports/JOB_NON_EXISTENT_9999/status", headers=auth_headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# -------------------------------------------------------------------
# 2. WORKER CLAIMING & CONCURRENCY TESTS
# -------------------------------------------------------------------

def test_worker_atomic_claiming_concurrency(db_session: Session):
    service = HMISImportService(db_session)
    csv_bytes = create_csv_bytes([{"col": "val"}])
    job1, _ = service.create_import_job("job1.csv", csv_bytes)
    job2, _ = service.create_import_job("job2.csv", csv_bytes + b"\n# extra")

    worker_a = HMISImportWorker(worker_id="worker-A")
    worker_b = HMISImportWorker(worker_id="worker-B")

    # Worker A claims first job
    claimed_a = worker_a.claim_job(db_session)
    assert claimed_a is not None
    assert claimed_a.claimed_by == "worker-A"
    assert claimed_a.status == "PROCESSING"

    # Worker B claims next job
    claimed_b = worker_b.claim_job(db_session)
    assert claimed_b is not None
    assert claimed_b.claimed_by == "worker-B"
    assert claimed_b.id != claimed_a.id

    # Queue is now empty for any other worker
    worker_c = HMISImportWorker(worker_id="worker-C")
    claimed_c = worker_c.claim_job(db_session)
    assert claimed_c is None


# -------------------------------------------------------------------
# 3. CHUNKED PROCESSING & COMMIT BOUNDARIES
# -------------------------------------------------------------------

def test_chunked_processing_and_counters(client: TestClient, db_session: Session, admin_auth_headers: dict, monkeypatch):
    # Set small chunk size to enforce chunking across multiple iterations
    monkeypatch.setattr(settings, "IMPORT_CHUNK_SIZE", 2)

    rows = []
    for i in range(6):
        rows.append({
            "State": "StateChunk",
            "District": "DistrictC",
            "Facility Code": f"FAC_CHUNK_{i}",
            "Facility Name": f"Chunk Clinic {i}",
            "Reporting Month": "2024-06",
            "OPD Attendance": 100.0 + i,
        })

    csv_bytes = create_csv_bytes(rows)
    res = client.post("/api/imports?sync=true", files={"file": ("chunked.csv", csv_bytes, "text/csv")}, headers=admin_auth_headers)
    assert res.status_code == 201
    job_code = res.json()["job_code"]

    job = db_session.query(ImportJob).filter(ImportJob.job_code == job_code).first()
    assert job.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS")
    assert job.total_records == 6
    assert job.processed_records == 6
    assert job.records_imported == 6
    assert job.records_rejected == 0


# -------------------------------------------------------------------
# 4. SCHEMA PROFILES ENGINE TESTS
# -------------------------------------------------------------------

def test_schema_profile_detection_and_validation(db_session: Session):
    # Valid MOHFW Standard format
    valid_headers = ["State", "District", "Facility Code", "Facility Name", "Reporting Month", "OPD Attendance"]
    detected = SchemaProfileRegistry.detect_profile(valid_headers)
    assert detected is not None
    assert detected.profile_id == "mohfw_standard_v2"
    assert detected.validate_headers(valid_headers).is_valid is True

    # Missing mandatory reporting month column
    invalid_headers = ["State", "District", "Facility Code", "Facility Name", "OPD Attendance"]
    detected_missing = SchemaProfileRegistry.detect_profile(invalid_headers)
    assert detected_missing is not None
    validation = detected_missing.validate_headers(invalid_headers)
    assert validation.is_valid is False
    assert any("reporting_month" in err.lower() or "temporal" in err.lower() for err in validation.errors)


# -------------------------------------------------------------------
# 5. STALE JOB CRASH RECOVERY & RETRY LIMITS
# -------------------------------------------------------------------

def test_stale_job_crash_recovery_and_retry_limits(db_session: Session):
    worker = HMISImportWorker(worker_id="worker-crash-test")
    service = HMISImportService(db_session)

    csv_bytes = create_csv_bytes([{"State": "S", "District": "D", "Facility Code": "F1", "Facility Name": "FN", "Reporting Month": "2024-01", "OPD Attendance": 50}])
    job, _ = service.create_import_job("crash_test.csv", csv_bytes)

    # Simulate worker crash mid-processing
    job.status = "PROCESSING"
    job.claimed_by = "worker-dead-pid-999"
    job.heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=600)  # 10 minutes ago (> 300s timeout)
    job.retry_count = 0
    job.max_retries = 2
    db_session.commit()

    # Recovery pass 1: Re-queues job for retry 1
    recovered_count = worker.recover_stale_jobs(db_session)
    assert recovered_count == 1
    db_session.refresh(job)
    assert job.status == "QUEUED"
    assert job.retry_count == 1
    assert job.claimed_by is None

    # Simulate crash on retry 1
    job.status = "PROCESSING"
    job.heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=600)
    db_session.commit()

    # Recovery pass 2: Re-queues job for retry 2
    worker.recover_stale_jobs(db_session)
    db_session.refresh(job)
    assert job.status == "QUEUED"
    assert job.retry_count == 2

    # Simulate crash on retry 2 (max_retries = 2 reached)
    job.status = "PROCESSING"
    job.heartbeat_at = datetime.now(timezone.utc) - timedelta(seconds=600)
    db_session.commit()

    # Recovery pass 3: Exceeds max retries -> Fails permanently
    worker.recover_stale_jobs(db_session)
    db_session.refresh(job)
    assert job.status == "FAILED"
    assert "exceeded maximum allowed retries" in job.error_summary.lower()


# -------------------------------------------------------------------
# 6. ADMIN RETRY & CANCEL ENDPOINT TESTS
# -------------------------------------------------------------------

def test_admin_retry_and_cancel_endpoints(client: TestClient, db_session: Session, admin_auth_headers: dict, auth_headers: dict):
    # Seed a failed job
    job = ImportJob(
        job_code="JOB_FAILED_RETRY_TEST",
        original_filename="fail.csv",
        status="FAILED",
        error_summary="Synthetic processing error"
    )
    db_session.add(job)
    db_session.commit()

    # Non-admin attempt to retry -> 403 Forbidden
    res_analyst = client.post(f"/api/imports/{job.job_code}/retry", headers=auth_headers)
    assert res_analyst.status_code == 403

    # Admin retry -> 200 OK and job becomes QUEUED
    res_admin = client.post(f"/api/imports/{job.job_code}/retry", headers=admin_auth_headers)
    assert res_admin.status_code == 200
    assert res_admin.json()["status"] == "QUEUED"

    db_session.refresh(job)
    assert job.status in ("QUEUED", "PROCESSING")

    # Admin cancel -> 200 OK and job becomes CANCELLED
    res_cancel = client.post(f"/api/imports/{job.job_code}/cancel", headers=admin_auth_headers)
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    db_session.refresh(job)
    assert job.status == "CANCELLED"


# -------------------------------------------------------------------
# 7. INCOMING DIRECTORY WATCHER WORKFLOW
# -------------------------------------------------------------------

def test_incoming_directory_watcher_workflow(tmp_path: Path, db_session: Session, monkeypatch):
    incoming_dir = tmp_path / "incoming"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    watcher = HMISIncomingDirectoryWatcher(
        incoming_dir=str(incoming_dir),
        stability_wait_seconds=0.01,
        session_factory=lambda: db_session
    )

    # 1. Invalid file extension -> quarantined
    bad_file = incoming_dir / "unsupported_data.pdf"
    bad_file.write_bytes(b"%PDF dummy content")

    # 2. Valid CSV file -> enqueued and moved to processed
    valid_csv = incoming_dir / "incoming_valid.csv"
    csv_bytes = create_csv_bytes([{
        "State": "StateWatch",
        "District": "DistrictW",
        "Facility Code": "FAC_WATCH_1",
        "Facility Name": "Watcher PHC",
        "Reporting Month": "2024-05",
        "OPD Attendance": 75.0,
    }])
    valid_csv.write_bytes(csv_bytes)

    # Run single scan pass
    results = watcher.scan_once()
    assert len(results) == 2

    # Verify bad file was quarantined
    assert any(r["status"] == "QUARANTINED" and r["filename"] == "unsupported_data.pdf" for r in results)
    assert not bad_file.exists()
    quarantined_files = list(watcher.quarantine_dir.glob("*.pdf"))
    assert len(quarantined_files) == 1

    # Verify valid file was enqueued and moved to processed
    assert any(r["status"] == "ENQUEUED" and r["filename"] == "incoming_valid.csv" for r in results)
    assert not valid_csv.exists()
    processed_files = list(watcher.processed_dir.glob("incoming_valid*"))
    assert len(processed_files) == 1


# -------------------------------------------------------------------
# 8. PROVENANCE & ROLLBACK FOLLOWING CHUNKED INGESTION
# -------------------------------------------------------------------

def test_rollback_following_chunked_ingestion(client: TestClient, db_session: Session, admin_auth_headers: dict, monkeypatch):
    monkeypatch.setattr(settings, "IMPORT_CHUNK_SIZE", 2)

    rows = [
        {
            "State": "StateRollChunk",
            "District": "DistrictRC",
            "Facility Code": f"FAC_RC_{i}",
            "Facility Name": f"Rollback Chunk Clinic {i}",
            "Reporting Month": "2024-07",
            "OPD Attendance": 300.0 + i,
        }
        for i in range(4)
    ]
    csv_bytes = create_csv_bytes(rows)

    upload_res = client.post(
        "/api/imports?sync=true",
        files={"file": ("chunk_rollback.csv", csv_bytes, "text/csv")},
        headers=admin_auth_headers
    )
    assert upload_res.status_code == 201
    job_code = upload_res.json()["job_code"]

    # Verify change records exist for all 4 inserted observations
    records = db_session.query(ImportObservationRecord).filter(
        ImportObservationRecord.import_job.has(job_code=job_code)
    ).all()
    assert len(records) == 4
    assert all(r.action == "INSERT" for r in records)

    # Execute rollback
    rb_res = client.post(
        f"/api/imports/{job_code}/rollback",
        json={"reason": "Testing rollback after chunked batch ingestion"},
        headers=admin_auth_headers
    )
    assert rb_res.status_code == 200
    rb_data = rb_res.json()
    assert rb_data["status"] == "ROLLED_BACK"
    assert rb_data["records_deleted"] == 4

    # Verify all 4 observations were removed
    remaining = db_session.query(Observation).filter(Observation.reporting_month == "2024-07").all()
    assert len(remaining) == 0


# -------------------------------------------------------------------
# 9. ISOLATED DATABASE MIGRATION CHECK (UPGRADE & DOWNGRADE)
# -------------------------------------------------------------------

def test_isolated_migration_upgrade_and_downgrade():
    """Validates that Phase 9A migration applies and downgrades cleanly in an isolated SQLite database."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        temp_db_path = tf.name

    try:
        temp_db_url = f"sqlite:///{temp_db_path}"
        alembic_cfg = Config("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", temp_db_url)

        # Upgrade to head (includes a9b8c7d6e5f4)
        command.upgrade(alembic_cfg, "head")

        # Downgrade back to Phase 8.2 (f14a8b7d9e23)
        command.downgrade(alembic_cfg, "f14a8b7d9e23")

        # Re-upgrade to head
        command.upgrade(alembic_cfg, "head")

    finally:
        if os.path.exists(temp_db_path):
            os.remove(temp_db_path)


# -------------------------------------------------------------------
# 10. DETERMINISTIC CANCELLATION & MULTI-CHUNK ROLLBACK REGRESSION TESTS
# -------------------------------------------------------------------

def test_deterministic_cancellation_during_multi_chunk_import(client: TestClient, db_session: Session, admin_auth_headers: dict, monkeypatch):
    """
    Regression check:
    Multi-chunk import cancelled between chunks.
    Asserts:
    - Final status is CANCELLED (never falls through to COMPLETED or FAILED).
    - No later chunks are committed.
    - Inserted rows from earlier committed chunks are completely removed.
    - Updated rows from earlier committed chunks are restored to exact prior values.
    - Unrelated pre-existing data is preserved untouched.
    - No DataQualityLog is committed.
    - Change records are purged.
    """
    monkeypatch.setattr(settings, "IMPORT_CHUNK_SIZE", 2)

    # 1. Seed pre-existing records:
    fac_target = Facility(id="FAC_MC_1", facility_code="FAC_MC_1", facility_name="Multi Clinic 1", facility_type="PHC", state="StateM", district="DistrictM", raw_facility_name="Multi Clinic 1")
    fac_unrelated = Facility(id="FAC_MC_UNREL", facility_code="FAC_MC_UNREL", facility_name="Unrelated Clinic", facility_type="PHC", state="StateM", district="DistrictM", raw_facility_name="Unrelated Clinic")
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="OPD Attendance", category="General", unit="count", active=True)
    db_session.add_all([fac_target, fac_unrelated, ind])
    db_session.commit()

    now_iso = datetime.now(timezone.utc).isoformat()
    # Pre-existing observation to be updated by chunk 0
    obs_existing = Observation(
        id="OBS_FAC_MC_1_opd_attendance_2024-08",
        facility_id="FAC_MC_1",
        indicator_id="IND_opd_attendance",
        observation_date="2024-08-01",
        reporting_month="2024-08",
        value=111.0,
        value_type="VALID",
        source_file="initial.csv",
        ingested_at=now_iso
    )
    # Pre-existing unrelated observation that must NOT be touched
    obs_unrelated = Observation(
        id="OBS_FAC_MC_UNREL_opd_attendance_2024-08",
        facility_id="FAC_MC_UNREL",
        indicator_id="IND_opd_attendance",
        observation_date="2024-08-01",
        reporting_month="2024-08",
        value=777.0,
        value_type="VALID",
        source_file="initial.csv",
        ingested_at=now_iso
    )
    db_session.add_all([obs_existing, obs_unrelated])
    db_session.commit()

    # 2. Multi-chunk payload (6 rows = 3 chunks of 2 rows)
    rows = [
        # Chunk 0: updates FAC_MC_1, inserts FAC_MC_2
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_1", "Facility Name": "Multi Clinic 1", "Reporting Month": "2024-08", "OPD Attendance": 222.0},
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_2", "Facility Name": "Multi Clinic 2", "Reporting Month": "2024-08", "OPD Attendance": 230.0},
        # Chunk 1: inserts FAC_MC_3, inserts FAC_MC_4
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_3", "Facility Name": "Multi Clinic 3", "Reporting Month": "2024-08", "OPD Attendance": 240.0},
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_4", "Facility Name": "Multi Clinic 4", "Reporting Month": "2024-08", "OPD Attendance": 250.0},
        # Chunk 2: inserts FAC_MC_5, inserts FAC_MC_6
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_5", "Facility Name": "Multi Clinic 5", "Reporting Month": "2024-08", "OPD Attendance": 260.0},
        {"State": "StateM", "District": "DistrictM", "Facility Code": "FAC_MC_6", "Facility Name": "Multi Clinic 6", "Reporting Month": "2024-08", "OPD Attendance": 270.0},
    ]
    csv_bytes = create_csv_bytes(rows)

    service = HMISImportService(db_session)
    job, _ = service.create_import_job("multi_chunk_cancel.csv", csv_bytes)

    # Deterministic hook: when chunk 0 commits, trigger cancellation via cancel_import_job
    orig_commit = service.db.commit
    cancelled_triggered = False

    def commit_hook():
        nonlocal cancelled_triggered
        orig_commit()
        # After chunk 0 commits, job.processed_records becomes 2
        db_session.refresh(job)
        if job.processed_records == 2 and not cancelled_triggered:
            cancelled_triggered = True
            service.cancel_import_job(job.job_code, cancelled_by="admin_concurrency_test", reason="Testing mid-chunk cancellation")

    monkeypatch.setattr(service.db, "commit", commit_hook)

    # Execute processing
    processed_job = service.process_import_job(job.id, worker_id="worker-test-cancel")

    # 3. Assertions
    db_session.expire_all()
    db_session.refresh(job)

    # Assert final status is CANCELLED
    assert processed_job.status == "CANCELLED"
    assert job.status == "CANCELLED"
    assert "Cancelled by admin_concurrency_test" in (job.error_summary or "")

    # Assert no later chunks were committed
    chunk1_obs = db_session.query(Observation).filter(Observation.facility_id.in_(["FAC_MC_3", "FAC_MC_4"])).all()
    chunk2_obs = db_session.query(Observation).filter(Observation.facility_id.in_(["FAC_MC_5", "FAC_MC_6"])).all()
    assert len(chunk1_obs) == 0, "Chunk 1 observations should never be committed"
    assert len(chunk2_obs) == 0, "Chunk 2 observations should never be committed"

    # Assert chunk 0 inserted rows are removed
    chunk0_inserted = db_session.query(Observation).filter(Observation.facility_id == "FAC_MC_2").first()
    assert chunk0_inserted is None, "Chunk 0 inserted observation must be removed by cancellation cleanup"

    # Assert chunk 0 updated rows are restored to before-image
    chunk0_updated = db_session.query(Observation).filter(Observation.facility_id == "FAC_MC_1").first()
    assert chunk0_updated is not None
    assert chunk0_updated.value == 111.0, f"Expected restored value 111.0, got {chunk0_updated.value}"
    assert chunk0_updated.source_file == "initial.csv"

    # Assert unrelated data is preserved
    unrelated_after = db_session.query(Observation).filter(Observation.facility_id == "FAC_MC_UNREL").first()
    assert unrelated_after is not None
    assert unrelated_after.value == 777.0, "Unrelated observation was modified or corrupted"

    # Assert change records are removed
    records = db_session.query(ImportObservationRecord).filter(ImportObservationRecord.import_job_id == job.id).all()
    assert len(records) == 0, "Change records must be purged upon cancellation"

    # Assert no DataQualityLog was created
    dq = db_session.query(DataQualityLog).filter(DataQualityLog.id == f"DQ_{job.job_code}").first()
    assert dq is None, "DataQualityLog should not exist for cancelled import"


def test_cancellation_right_before_chunk_commit(db_session: Session, monkeypatch):
    """
    Tests cancellation arriving right before a chunk commits:
    Verifies that the uncommitted chunk is discarded via db.rollback(),
    partial state cleaned up, and status is CANCELLED.
    """
    monkeypatch.setattr(settings, "IMPORT_CHUNK_SIZE", 2)

    rows = [
        {"State": "StateB", "District": "DistrictB", "Facility Code": "FAC_BC_1", "Facility Name": "Before Commit 1", "Reporting Month": "2024-09", "OPD Attendance": 500.0},
        {"State": "StateB", "District": "DistrictB", "Facility Code": "FAC_BC_2", "Facility Name": "Before Commit 2", "Reporting Month": "2024-09", "OPD Attendance": 510.0},
    ]
    csv_bytes = create_csv_bytes(rows)

    service = HMISImportService(db_session)
    job, _ = service.create_import_job("before_commit_cancel.csv", csv_bytes)

    cancelled_once = False
    orig_is_job_cancelled = service._is_job_cancelled

    def check_cancelled_hook(job_id):
        nonlocal cancelled_once
        if not cancelled_once and job.status == "VALIDATED":
            cancelled_once = True
            job.status = "CANCELLED"
            job.error_summary = "Simulated cancellation before chunk commit"
            db_session.commit()
            return True
        return orig_is_job_cancelled(job_id)

    monkeypatch.setattr(service, "_is_job_cancelled", check_cancelled_hook)

    processed_job = service.process_import_job(job.id, worker_id="worker-before-commit")

    db_session.refresh(job)
    assert processed_job.status == "CANCELLED"
    assert job.status == "CANCELLED"

    # Verify no observations committed
    obs = db_session.query(Observation).filter(Observation.facility_id.in_(["FAC_BC_1", "FAC_BC_2"])).all()
    assert len(obs) == 0


def test_process_import_job_on_already_cancelled_job(db_session: Session):
    """Verifies that calling process_import_job on an already CANCELLED job returns immediately without processing."""
    service = HMISImportService(db_session)
    job, _ = service.create_import_job("already_cancelled.csv", create_csv_bytes([{"State": "S", "District": "D", "Facility Code": "F", "Facility Name": "N", "Reporting Month": "2024-01", "OPD Attendance": 10}]))
    job.status = "CANCELLED"
    job.error_summary = "Cancelled while queued"
    db_session.commit()

    processed_job = service.process_import_job(job.id, worker_id="worker-wont-run")
    assert processed_job.status == "CANCELLED"
    assert processed_job.total_records == 0
    assert processed_job.processed_records == 0


def test_cancellation_post_chunk_loop_boundary(db_session: Session, monkeypatch):
    """Verifies that if cancellation arrives after the chunk loop, completion logic does NOT mark it COMPLETED."""
    monkeypatch.setattr(settings, "IMPORT_CHUNK_SIZE", 10)
    rows = [
        {"State": "StateP", "District": "DistrictP", "Facility Code": "FAC_POST_1", "Facility Name": "Post Loop Clinic", "Reporting Month": "2024-09", "OPD Attendance": 400.0}
    ]
    csv_bytes = create_csv_bytes(rows)

    service = HMISImportService(db_session)
    job, _ = service.create_import_job("post_loop_cancel.csv", csv_bytes)

    orig_is_job_cancelled = service._is_job_cancelled
    call_count = 0

    def mock_is_cancelled(job_id):
        nonlocal call_count
        call_count += 1
        if call_count >= 3:
            job.status = "CANCELLED"
            db_session.commit()
            return True
        return orig_is_job_cancelled(job_id)

    monkeypatch.setattr(service, "_is_job_cancelled", mock_is_cancelled)

    processed_job = service.process_import_job(job.id, worker_id="worker-post-loop")
    db_session.refresh(job)

    assert processed_job.status == "CANCELLED"
    assert job.status == "CANCELLED"

    # Confirm observation was cleaned up and no DQ log exists
    obs = db_session.query(Observation).filter(Observation.facility_id == "FAC_POST_1").first()
    assert obs is None
    dq = db_session.query(DataQualityLog).filter(DataQualityLog.id == f"DQ_{job.job_code}").first()
    assert dq is None

