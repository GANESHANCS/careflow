import io
import os
import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone
import pytest
import pandas as pd
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from alembic.config import Config
from alembic import command

from backend.app.core.config import settings
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_batch import ImportBatch
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.services.imports.import_service import HMISImportService
from backend.app.services.imports.watcher import HMISIncomingDirectoryWatcher, get_directory_watcher
from backend.app.services.imports.worker import HMISImportWorker


def create_csv_bytes(rows: list) -> bytes:
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


# -------------------------------------------------------------------
# 1. BATCH CREATION & AGGREGATED METRICS LIFECYCLE
# -------------------------------------------------------------------

def test_batch_creation_and_aggregation_lifecycle(db_session: Session):
    service = HMISImportService(db_session)

    # 1. Create a new ImportBatch
    batch = service.create_import_batch(source="MANUAL_BULK", initiated_by="test_user", total_files=2)
    assert batch.id is not None
    assert batch.batch_code.startswith("BATCH_")
    assert batch.status == "QUEUED"
    assert batch.total_files == 2

    # 2. Create two jobs linked to the batch
    csv1 = create_csv_bytes([{
        "State": "BatchState1",
        "District": "BatchDist1",
        "Facility Code": "FAC_B1",
        "Facility Name": "Batch Hospital 1",
        "Reporting Month": "2024-06",
        "OPD Attendance": 100.0,
    }])
    job1, _ = service.create_import_job("file1.csv", csv1, mime_type="text/csv", batch_id=batch.id)

    csv2 = create_csv_bytes([{
        "State": "BatchState2",
        "District": "BatchDist2",
        "Facility Code": "FAC_B2",
        "Facility Name": "Batch Hospital 2",
        "Reporting Month": "2024-06",
        "OPD Attendance": 200.0,
    }])
    job2, _ = service.create_import_job("file2.csv", csv2, mime_type="text/csv", batch_id=batch.id)

    assert job1.batch_id == batch.id
    assert job2.batch_id == batch.id

    # 3. Process job1 to completion
    service.process_import_job(job1.id)
    db_session.refresh(job1)
    db_session.refresh(batch)

    assert job1.status == "COMPLETED"
    assert batch.status == "PROCESSING"  # job2 is still QUEUED
    assert batch.successful_files == 1
    assert batch.processed_files == 1

    # 4. Process job2 with a failure simulation (delete file to force failure)
    os.remove(job2.storage_path)
    service.process_import_job(job2.id)
    db_session.refresh(job2)
    db_session.refresh(batch)

    assert job2.status == "FAILED"
    assert batch.status == "PARTIALLY_FAILED"
    assert batch.total_files == 2
    assert batch.processed_files == 2
    assert batch.successful_files == 1
    assert batch.failed_files == 1
    assert batch.error_summary is not None
    assert "file2.csv" in batch.error_summary


def test_batch_all_completed_metrics(db_session: Session):
    service = HMISImportService(db_session)

    batch = service.create_import_batch(source="DIRECTORY_WATCHER", total_files=2)

    csv1 = create_csv_bytes([{
        "State": "StateC1",
        "District": "DistC1",
        "Facility Code": "FAC_C1",
        "Facility Name": "Center 1",
        "Reporting Month": "2024-07",
        "OPD Attendance": 50.0,
    }])
    job1, _ = service.create_import_job("complete1.csv", csv1, mime_type="text/csv", batch_id=batch.id)

    csv2 = create_csv_bytes([{
        "State": "StateC2",
        "District": "DistC2",
        "Facility Code": "FAC_C2",
        "Facility Name": "Center 2",
        "Reporting Month": "2024-07",
        "OPD Attendance": 60.0,
    }])
    job2, _ = service.create_import_job("complete2.csv", csv2, mime_type="text/csv", batch_id=batch.id)

    service.process_import_job(job1.id)
    service.process_import_job(job2.id)

    db_session.refresh(batch)
    assert batch.status == "COMPLETED"
    assert batch.total_files == 2
    assert batch.successful_files == 2
    assert batch.failed_files == 0
    assert batch.completed_at is not None


# -------------------------------------------------------------------
# 2. INCOMING DIRECTORY WATCHER BATCH ORCHESTRATION & QUARANTINE
# -------------------------------------------------------------------

def test_directory_watcher_scan_and_batch_orchestration(tmp_path: Path, db_session: Session):
    incoming_dir = tmp_path / "incoming_test"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    watcher = HMISIncomingDirectoryWatcher(
        incoming_dir=str(incoming_dir),
        stability_wait_seconds=0.01,
        session_factory=lambda: db_session
    )

    # 1. Valid CSV file
    valid_csv = incoming_dir / "valid_data.csv"
    valid_csv.write_bytes(create_csv_bytes([{
        "State": "WatchState",
        "District": "WatchDist",
        "Facility Code": "FAC_W1",
        "Facility Name": "Watcher Clinic",
        "Reporting Month": "2024-08",
        "OPD Attendance": 85.0,
    }]))

    # 2. Unsupported extension -> quarantine with diagnostic note
    bad_ext = incoming_dir / "invalid_archive.zip"
    bad_ext.write_bytes(b"PK\x03\x04 fake zip content")

    # 3. Empty (0-byte) file -> quarantine with diagnostic note
    empty_file = incoming_dir / "empty_report.csv"
    empty_file.write_bytes(b"")

    # 4. Incomplete/temporary file -> skipped
    temp_file = incoming_dir / "uploading_file.tmp"
    temp_file.write_bytes(b"temporary content")

    # Run scan
    results = watcher.scan_once()
    assert len(results) >= 3

    # Check valid file
    enqueued = [r for r in results if r["status"] == "ENQUEUED"]
    assert len(enqueued) == 1
    assert enqueued[0]["filename"] == "valid_data.csv"
    assert not valid_csv.exists()

    # Check quarantined files and diagnostic notes
    quarantined = [r for r in results if r["status"] == "QUARANTINED"]
    assert len(quarantined) == 2
    assert not bad_ext.exists()
    assert not empty_file.exists()

    quarantine_files = list(watcher.quarantine_dir.glob("*"))
    # Expect quarantined files + .error.txt notes
    error_notes = list(watcher.quarantine_dir.glob("*.error.txt"))
    assert len(error_notes) == 2

    # Check temporary file untouched
    assert temp_file.exists()

    # Verify ImportBatch in database
    batch = db_session.query(ImportBatch).filter(ImportBatch.batch_code == watcher.last_batch_code).first()
    assert batch is not None
    assert batch.source == "DIRECTORY_WATCHER"
    assert len(batch.import_jobs) == 1
    assert batch.import_jobs[0].job_code == enqueued[0]["job_code"]


def test_directory_watcher_duplicate_prevention(tmp_path: Path, db_session: Session):
    incoming_dir = tmp_path / "incoming_dup_test"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    watcher = HMISIncomingDirectoryWatcher(
        incoming_dir=str(incoming_dir),
        stability_wait_seconds=0.01,
        session_factory=lambda: db_session
    )

    csv_content = create_csv_bytes([{
        "State": "DupState",
        "District": "DupDist",
        "Facility Code": "FAC_DUP1",
        "Facility Name": "Duplicate Test PHC",
        "Reporting Month": "2024-09",
        "OPD Attendance": 42.0,
    }])

    # 1. First scan enqueues
    file1 = incoming_dir / "initial_data.csv"
    file1.write_bytes(csv_content)
    results1 = watcher.scan_once()
    assert len(results1) == 1
    assert results1[0]["status"] == "ENQUEUED"

    # 2. Place identical content with a different name
    file2 = incoming_dir / "duplicate_copy.csv"
    file2.write_bytes(csv_content)
    results2 = watcher.scan_once()
    assert len(results2) == 1
    assert results2[0]["status"] == "DUPLICATE"
    assert results2[0]["job_code"] == results1[0]["job_code"]

    # Verify duplicate was moved to processed with duplicate_ suffix
    dup_processed = list(watcher.processed_dir.glob("*duplicate_*"))
    assert len(dup_processed) == 1


def test_directory_watcher_concurrency_lock(tmp_path: Path, db_session: Session):
    incoming_dir = tmp_path / "incoming_lock_test"
    incoming_dir.mkdir(parents=True, exist_ok=True)

    watcher = HMISIncomingDirectoryWatcher(
        incoming_dir=str(incoming_dir),
        stability_wait_seconds=0.01,
        session_factory=lambda: db_session
    )

    locked_file = incoming_dir / "locked_report.csv"
    locked_file.write_bytes(create_csv_bytes([{"State": "LockState"}]))

    # Simulate that this file is actively being processed in another thread
    with watcher._lock:
        watcher._active_files.add("locked_report.csv")

    results = watcher.scan_once()
    assert len(results) == 0
    assert locked_file.exists()  # Not moved or processed

    # Release lock and scan again
    with watcher._lock:
        watcher._active_files.discard("locked_report.csv")

    results2 = watcher.scan_once()
    assert len(results2) == 1
    assert results2[0]["status"] == "ENQUEUED"


# -------------------------------------------------------------------
# 3. BATCH RETRY AND CANCELLATION
# -------------------------------------------------------------------

def test_batch_retry_and_cancellation(db_session: Session):
    service = HMISImportService(db_session)

    batch = service.create_import_batch(source="MANUAL_BULK", total_files=2)

    csv1 = create_csv_bytes([{
        "State": "RetryState1",
        "District": "RetryDist1",
        "Facility Code": "FAC_R1",
        "Facility Name": "Retry PHC 1",
        "Reporting Month": "2024-10",
        "OPD Attendance": 90.0,
    }])
    job1, _ = service.create_import_job("retry1.csv", csv1, mime_type="text/csv", batch_id=batch.id)

    csv2 = create_csv_bytes([{
        "State": "RetryState2",
        "District": "RetryDist2",
        "Facility Code": "FAC_R2",
        "Facility Name": "Retry PHC 2",
        "Reporting Month": "2024-10",
        "OPD Attendance": 95.0,
    }])
    job2, _ = service.create_import_job("retry2.csv", csv2, mime_type="text/csv", batch_id=batch.id)

    # Fail job1 manually
    service._fail_job(job1, "SIMULATED_FAILURE", "Manual failure for test")
    db_session.refresh(batch)
    assert batch.failed_files == 1

    # Retry batch
    retried_batch, count = service.retry_import_batch(batch.batch_code, requested_by="test_admin")
    assert count == 1
    assert retried_batch.status == "QUEUED"
    db_session.refresh(job1)
    assert job1.status == "QUEUED"

    # Now cancel the batch while both are queued
    cancelled_batch = service.cancel_import_batch(batch.batch_code, cancelled_by="test_admin", reason="Test cancel")
    assert cancelled_batch.status == "CANCELLED"
    db_session.refresh(job1)
    db_session.refresh(job2)
    assert job1.status == "CANCELLED"
    assert job2.status == "CANCELLED"


# -------------------------------------------------------------------
# 4. BATCH REST API ENDPOINTS
# -------------------------------------------------------------------

def test_batch_api_endpoints(client: TestClient, db_session: Session, auth_headers: dict, admin_auth_headers: dict):
    service = HMISImportService(db_session)
    batch = service.create_import_batch(source="MANUAL_BULK", total_files=1)

    csv = create_csv_bytes([{
        "State": "ApiState",
        "District": "ApiDist",
        "Facility Code": "FAC_API1",
        "Facility Name": "API Hospital",
        "Reporting Month": "2024-11",
        "OPD Attendance": 110.0,
    }])
    job, _ = service.create_import_job("api_test.csv", csv, mime_type="text/csv", batch_id=batch.id)

    # 1. GET /api/imports/batches (analyst can view)
    res = client.get("/api/imports/batches", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(b["batch_code"] == batch.batch_code for b in data["items"])

    # 2. GET /api/imports/batches/{batch_code}
    res_detail = client.get(f"/api/imports/batches/{batch.batch_code}", headers=auth_headers)
    assert res_detail.status_code == 200
    detail_data = res_detail.json()
    assert detail_data["batch_code"] == batch.batch_code
    assert len(detail_data["import_jobs"]) == 1
    assert detail_data["import_jobs"][0]["job_code"] == job.job_code

    # 3. POST /api/imports/batches/scan (analyst forbidden -> 403, admin allowed -> 200)
    res_scan_forbidden = client.post("/api/imports/batches/scan", headers=auth_headers)
    assert res_scan_forbidden.status_code == 403

    res_scan_admin = client.post("/api/imports/batches/scan", headers=admin_auth_headers)
    assert res_scan_admin.status_code == 200
    scan_data = res_scan_admin.json()
    assert "files_discovered" in scan_data
    assert "jobs_created" in scan_data

    # 4. POST /api/imports/batches/{batch_code}/retry (analyst forbidden -> 403, admin -> 200)
    service._fail_job(job, "ERR", "Fail for retry test")
    res_retry_forbidden = client.post(f"/api/imports/batches/{batch.batch_code}/retry", headers=auth_headers)
    assert res_retry_forbidden.status_code == 403

    res_retry = client.post(f"/api/imports/batches/{batch.batch_code}/retry", headers=admin_auth_headers)
    assert res_retry.status_code == 200
    assert res_retry.json()["retried_jobs"] == 1

    # 5. POST /api/imports/batches/{batch_code}/cancel (analyst forbidden -> 403, admin -> 200)
    res_cancel_forbidden = client.post(f"/api/imports/batches/{batch.batch_code}/cancel", headers=auth_headers)
    assert res_cancel_forbidden.status_code == 403

    res_cancel_admin = client.post(f"/api/imports/batches/{batch.batch_code}/cancel", headers=admin_auth_headers, json={"reason": "Admin cancel"})
    assert res_cancel_admin.status_code == 200
    assert res_cancel_admin.json()["status"] == "CANCELLED"


# -------------------------------------------------------------------
# 5. ALEMBIC MIGRATION TEST
# -------------------------------------------------------------------

def test_phase_9b_alembic_migration():
    temp_dir = tempfile.mkdtemp()
    test_db_path = Path(temp_dir) / "test_migration_9b.db"
    test_db_url = f"sqlite:///{test_db_path.resolve()}"

    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", test_db_url)

    try:
        # Upgrade to head (includes Phase 9B b1c2d3e4f5a6)
        command.upgrade(alembic_cfg, "head")

        # Downgrade to Phase 9A (a9b8c7d6e5f4)
        command.downgrade(alembic_cfg, "a9b8c7d6e5f4")

        # Re-upgrade to head
        command.upgrade(alembic_cfg, "head")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
