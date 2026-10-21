import os
import sys
import time
import logging
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.services.imports.import_service import HMISImportService

logger = logging.getLogger("careflow.worker")


class HMISImportWorker:
    """
    Durable, database-backed background worker engine for asynchronous HMIS batch ingestion.
    Provides atomic job claiming, heartbeat tracking, stale job crash recovery,
    and chunked execution independently of the HTTP request lifecycle.
    """

    def __init__(self, worker_id: Optional[str] = None):
        self.worker_id = worker_id or f"worker-{os.getpid()}-{threading.get_ident()}"
        self.stale_timeout_seconds = settings.WORKER_STALE_TIMEOUT_SECONDS
        self.max_retries = settings.WORKER_MAX_RETRIES

    def claim_job(self, db: Session, job_id: Optional[int] = None) -> Optional[ImportJob]:
        """
        Atomically claims a QUEUED job for this worker.
        Returns the claimed ImportJob instance, or None if no job was claimed.
        """
        now = datetime.now(timezone.utc)

        query = db.query(ImportJob).filter(ImportJob.status == "QUEUED")
        if job_id is not None:
            query = query.filter(ImportJob.id == job_id)
        else:
            query = query.order_by(ImportJob.created_at.asc())

        candidate = query.first()
        if not candidate:
            return None

        # Atomic claim: verify status is still QUEUED
        rows_affected = (
            db.query(ImportJob)
            .filter(ImportJob.id == candidate.id, ImportJob.status == "QUEUED")
            .update(
                {
                    "status": "PROCESSING",
                    "claimed_at": now,
                    "claimed_by": self.worker_id,
                    "heartbeat_at": now,
                    "updated_at": now,
                },
                synchronize_session=False
            )
        )
        db.commit()

        if rows_affected > 0:
            candidate.status = "PROCESSING"
            candidate.claimed_at = now
            candidate.claimed_by = self.worker_id
            candidate.heartbeat_at = now
            candidate.updated_at = now
            logger.info(f"Worker '{self.worker_id}' successfully claimed job '{candidate.job_code}' (ID {candidate.id}).")
            return candidate

        return None

    def recover_stale_jobs(self, db: Session) -> int:
        """
        Detects abandoned or crashed 'PROCESSING' jobs whose worker heartbeat has expired.
        Safely cleans up partial changes and re-queues them if within retry limits,
        or marks them as FAILED if max retries are exceeded.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=self.stale_timeout_seconds)

        stale_candidates = (
            db.query(ImportJob)
            .filter(
                ImportJob.status.in_(["PROCESSING", "VALIDATED"]),
                (ImportJob.heartbeat_at.is_(None) | (ImportJob.heartbeat_at < cutoff))
            )
            .all()
        )

        recovered_count = 0
        service = HMISImportService(db)

        for job in stale_candidates:
            logger.warning(
                f"Detected stale import job '{job.job_code}' (last heartbeat: {job.heartbeat_at}, claimed_by: {job.claimed_by})."
            )

            # Revert any partial observation writes to preserve provenance and database integrity
            service.cleanup_partial_import(job)

            if job.retry_count < job.max_retries:
                job.retry_count += 1
                job.status = "QUEUED"
                job.claimed_by = None
                job.claimed_at = None
                job.heartbeat_at = None
                job.updated_at = datetime.now(timezone.utc)
                job.error_summary = (
                    f"Job automatically recovered from inactive worker after timeout; "
                    f"queued for retry {job.retry_count}/{job.max_retries}."
                )
                logger.info(f"Re-queued stale job '{job.job_code}' for retry attempt {job.retry_count}/{job.max_retries}.")
            else:
                job.status = "FAILED"
                job.completed_at = datetime.now(timezone.utc)
                job.updated_at = datetime.now(timezone.utc)
                job.error_summary = f"Job processing timed out and exceeded maximum allowed retries ({job.max_retries})."

                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    error_code="STALE_WORKER_TIMEOUT_EXCEEDED",
                    severity="CRITICAL",
                    message=f"Processing timed out without worker heartbeat and exceeded {job.max_retries} retries."
                )
                db.add(err_log)
                logger.error(f"Permanently failed stale job '{job.job_code}' due to retry exhaustion.")

            db.commit()
            recovered_count += 1

        return recovered_count

    def process_job_by_id(self, job_id: int) -> Optional[ImportJob]:
        """
        Claims and executes processing for a specific job ID.
        """
        db = SessionLocal()
        try:
            job = self.claim_job(db, job_id=job_id)
            if not job:
                # Job may already be claimed or completed
                return db.query(ImportJob).filter(ImportJob.id == job_id).first()

            service = HMISImportService(db)
            processed_job = service.process_import_job(job.id, worker_id=self.worker_id)
            return processed_job
        except Exception as e:
            logger.exception(f"Unexpected exception in process_job_by_id for job ID {job_id}: {e}")
            return None
        finally:
            db.close()

    def process_next_job(self) -> bool:
        """
        Claims and processes the next eligible QUEUED job.
        Returns True if a job was claimed and processed, False if queue was empty.
        """
        db = SessionLocal()
        try:
            # First check for any stale jobs needing recovery
            self.recover_stale_jobs(db)

            # Claim next queued job
            job = self.claim_job(db)
            if not job:
                return False

            service = HMISImportService(db)
            service.process_import_job(job.id, worker_id=self.worker_id)
            return True
        except Exception as e:
            logger.exception(f"Error in process_next_job for worker '{self.worker_id}': {e}")
            return False
        finally:
            db.close()


class HMISImportWorkerThread(threading.Thread):
    """
    In-process daemon worker thread that continuously polls for QUEUED import jobs
    and processes them asynchronously.
    """

    def __init__(self, poll_interval: float = 2.0):
        super().__init__(name="HMISImportWorkerThread", daemon=True)
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()
        self._notify_event = threading.Event()
        self.worker = HMISImportWorker()

    def run(self):
        logger.info(f"HMIS Background Import Worker thread started (ID: {self.worker.worker_id}, interval: {self.poll_interval}s).")
        while not self._stop_event.is_set():
            try:
                processed_any = self.worker.process_next_job()
                if not processed_any:
                    # Wait for next poll interval or until woken up by notify()
                    self._notify_event.wait(timeout=self.poll_interval)
                    self._notify_event.clear()
            except Exception as e:
                logger.exception(f"Unhandled error in import worker thread: {e}")
                self._stop_event.wait(timeout=self.poll_interval)

        logger.info("HMIS Background Import Worker thread cleanly stopped.")

    def notify(self):
        """Wakes up the worker immediately when a new job is queued."""
        self._notify_event.set()

    def stop(self):
        """Signals the worker thread to stop."""
        self._stop_event.set()
        self._notify_event.set()


# Module-level thread singleton
_worker_thread: Optional[HMISImportWorkerThread] = None
_worker_lock = threading.Lock()


def get_worker_instance() -> Optional[HMISImportWorkerThread]:
    global _worker_thread
    return _worker_thread


def start_in_process_worker() -> Optional[HMISImportWorkerThread]:
    """
    Safely starts the in-process worker thread if enabled in settings and not already running.
    Guarded against duplicate spawns on reload.
    """
    global _worker_thread
    if not settings.ENABLE_IMPORT_WORKER:
        logger.info("Background import worker is disabled by configuration (ENABLE_IMPORT_WORKER=False).")
        return None

    with _worker_lock:
        if _worker_thread is not None and _worker_thread.is_alive():
            return _worker_thread

        _worker_thread = HMISImportWorkerThread(poll_interval=settings.WORKER_POLL_INTERVAL)
        _worker_thread.start()
        return _worker_thread


def stop_in_process_worker():
    """
    Gracefully stops the in-process worker thread.
    """
    global _worker_thread
    with _worker_lock:
        if _worker_thread is not None:
            _worker_thread.stop()
            _worker_thread.join(timeout=5.0)
            _worker_thread = None


def notify_worker():
    """
    Notifies the running worker thread to process queued jobs immediately.
    """
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        _worker_thread.notify()
