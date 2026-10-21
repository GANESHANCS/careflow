import os
import time
import shutil
import logging
import threading
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.db.session import SessionLocal
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_batch import ImportBatch
from backend.app.services.imports.import_service import HMISImportService, ImportValidationError
from backend.app.services.imports.validator import ImportValidatorService
from backend.app.services.imports.storage import ImportStorageService
from backend.app.services.imports.worker import notify_worker

logger = logging.getLogger("careflow.watcher")

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
IGNORED_EXTENSIONS = {".tmp", ".temp", ".part", ".crdownload"}


class HMISIncomingDirectoryWatcher:
    """
    Automated incoming-directory watcher for batch HMIS file ingestion.
    Monitors a configurable directory, validates file completion, creates database-backed
    import jobs and batches, moves processed files to a completed folder, and isolates invalid files in quarantine.
    """

    def __init__(
        self,
        incoming_dir: Optional[str] = None,
        stability_wait_seconds: float = 0.5,
        session_factory=None
    ):
        self.base_incoming_dir = Path(incoming_dir or settings.INCOMING_IMPORT_DIR).resolve()
        self.processed_dir = self.base_incoming_dir / "processed"
        self.quarantine_dir = self.base_incoming_dir / "quarantine"
        self.stability_wait_seconds = stability_wait_seconds
        self.session_factory = session_factory or SessionLocal
        self.last_batch_code: Optional[str] = None

        self._lock = threading.Lock()
        self._active_files: set = set()

        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Creates incoming, processed, and quarantine directories safely."""
        self.base_incoming_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)

    def is_file_stable(self, file_path: Path) -> bool:
        """
        Verifies that a file is not actively being written or copied by checking
        file size stability across a time delta and checking read exclusivity.
        """
        try:
            if not file_path.exists() or not file_path.is_file():
                return False

            size_before = file_path.stat().st_size
            time.sleep(self.stability_wait_seconds)
            size_after = file_path.stat().st_size

            if size_before != size_after:
                return False

            # Verify read accessibility
            with open(file_path, "rb") as f:
                _ = f.read(1024)
            return True
        except (PermissionError, OSError):
            return False

    def scan_once(self) -> List[Dict[str, Any]]:
        """
        Performs a single pass scan over the incoming directory.
        Discovers eligible files, creates an ImportBatch, enqueues ImportJobs,
        and moves files to processed or quarantine.
        """
        results = []
        if not self.base_incoming_dir.exists():
            return results

        candidates = []
        for item in sorted(self.base_incoming_dir.iterdir()):
            if item.is_dir() or item.name.startswith(".") or item.name.startswith("~"):
                continue

            ext = item.suffix.lower()
            if ext in IGNORED_EXTENSIONS:
                continue

            with self._lock:
                if item.name in self._active_files:
                    continue

            if ext not in SUPPORTED_EXTENSIONS:
                logger.warning(f"Rejecting unsupported file '{item.name}' from incoming directory. Moving to quarantine.")
                self._quarantine_file(item, reason=f"Unsupported file extension '{ext}'")
                results.append({"filename": item.name, "status": "QUARANTINED", "reason": f"Unsupported extension {ext}"})
                continue

            if not self.is_file_stable(item):
                logger.debug(f"File '{item.name}' is still being written or copied; skipping until next scan.")
                continue

            candidates.append(item)

        if not candidates:
            return results

        db = self.session_factory()
        batch = None
        try:
            service = HMISImportService(db)
            batch = service.create_import_batch(
                source="DIRECTORY_WATCHER",
                total_files=len(candidates)
            )
            self.last_batch_code = batch.batch_code

            for item in candidates:
                with self._lock:
                    self._active_files.add(item.name)
                try:
                    outcome = self._ingest_file(item, batch_id=batch.id, db=db, service=service)
                    outcome["batch_code"] = batch.batch_code
                    results.append(outcome)
                finally:
                    with self._lock:
                        self._active_files.discard(item.name)

            service.update_batch_metrics(batch.id)
        except Exception as e:
            logger.exception(f"Error during batch incoming directory scan: {e}")
            if batch:
                try:
                    batch.status = "FAILED"
                    batch.error_summary = str(e)[:512]
                    db.commit()
                except Exception:
                    pass
        finally:
            db.close()

        return results

    def _ingest_file(
        self,
        file_path: Path,
        batch_id: Optional[int] = None,
        db: Optional[Session] = None,
        service: Optional[HMISImportService] = None
    ) -> Dict[str, Any]:
        """
        Reads file content, verifies hash idempotency, creates an import job,
        and moves the original file to processed/ or quarantine/.
        """
        should_close = False
        if db is None:
            db = self.session_factory()
            service = HMISImportService(db)
            should_close = True
        elif service is None:
            service = HMISImportService(db)

        try:
            with open(file_path, "rb") as f:
                content = f.read()

            if len(content) == 0:
                self._quarantine_file(file_path, reason="Empty file (0 bytes)")
                return {"filename": file_path.name, "status": "QUARANTINED", "reason": "Empty file"}

            file_hash = service.storage.calculate_file_hash(content)

            # Idempotency check
            existing_job = ImportValidatorService.check_idempotency(db, file_hash)
            if existing_job:
                logger.info(
                    f"File '{file_path.name}' matches existing import job '{existing_job.job_code}'. Moving to processed without duplicating."
                )
                self._move_to_processed(file_path, suffix=f"duplicate_{existing_job.job_code}")
                return {
                    "filename": file_path.name,
                    "status": "DUPLICATE",
                    "job_code": existing_job.job_code,
                    "existing_status": existing_job.status
                }

            # Enqueue new import job
            mime_type = "text/csv" if file_path.suffix.lower() == ".csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            job, _ = service.create_import_job(
                original_filename=file_path.name,
                content=content,
                mime_type=mime_type,
                batch_id=batch_id
            )

            # Move source file to processed directory
            self._move_to_processed(file_path, suffix=job.job_code)

            # Trigger background worker
            notify_worker()

            logger.info(f"Incoming directory watcher enqueued job '{job.job_code}' for file '{file_path.name}'.")
            return {
                "filename": file_path.name,
                "status": "ENQUEUED",
                "job_code": job.job_code,
                "job_id": job.id
            }

        except ImportValidationError as e:
            logger.warning(f"Validation error for incoming file '{file_path.name}': {e.message}. Quarantining.")
            self._quarantine_file(file_path, reason=e.message)
            return {"filename": file_path.name, "status": "QUARANTINED", "reason": e.message}
        except Exception as e:
            logger.exception(f"Unexpected error processing incoming file '{file_path.name}': {e}. Quarantining.")
            self._quarantine_file(file_path, reason=str(e))
            return {"filename": file_path.name, "status": "QUARANTINED", "reason": str(e)}
        finally:
            if should_close:
                db.close()

    def _move_to_processed(self, file_path: Path, suffix: str = "") -> Path:
        """Moves processed file to processed/ with timestamp/job suffix to avoid collisions."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        stem = file_path.stem
        ext = file_path.suffix
        dest_name = f"{stem}_{suffix}_{timestamp}{ext}" if suffix else f"{stem}_{timestamp}{ext}"
        dest_path = self.processed_dir / dest_name
        shutil.move(str(file_path), str(dest_path))
        return dest_path

    def _quarantine_file(self, file_path: Path, reason: str = "") -> Path:
        """Moves invalid or corrupted file to quarantine/ directory with diagnostic info."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        dest_name = f"{file_path.stem}_quarantined_{timestamp}{file_path.suffix}"
        dest_path = self.quarantine_dir / dest_name
        shutil.move(str(file_path), str(dest_path))

        # Write error note alongside quarantined file
        note_path = self.quarantine_dir / f"{dest_name}.error.txt"
        try:
            with open(note_path, "w", encoding="utf-8") as nf:
                nf.write(
                    f"Quarantine Reason: {reason}\n"
                    f"Timestamp: {datetime.now(timezone.utc).isoformat()}\n"
                    f"Original Name: {file_path.name}\n"
                )
        except Exception:
            pass

        return dest_path


class HMISDirectoryWatcherThread(threading.Thread):
    """
    Background daemon thread that periodically triggers HMISIncomingDirectoryWatcher.
    """

    def __init__(self, watcher: HMISIncomingDirectoryWatcher, poll_interval: float = 10.0):
        super().__init__(daemon=True, name="HMISDirectoryWatcherThread")
        self.watcher = watcher
        self.poll_interval = poll_interval
        self._stop_event = threading.Event()

    def run(self):
        logger.info(f"HMIS Incoming Directory Watcher thread started (watching '{self.watcher.base_incoming_dir}', interval: {self.poll_interval}s).")
        while not self._stop_event.is_set():
            try:
                self.watcher.scan_once()
            except Exception as e:
                logger.error(f"Error during directory watcher scan: {e}")
            self._stop_event.wait(timeout=self.poll_interval)
        logger.info("HMIS Incoming Directory Watcher thread stopped.")

    def stop(self):
        self._stop_event.set()


_directory_watcher_instance: Optional[HMISIncomingDirectoryWatcher] = None
_directory_watcher_thread: Optional[HMISDirectoryWatcherThread] = None


def get_directory_watcher() -> HMISIncomingDirectoryWatcher:
    """Returns singleton instance of HMISIncomingDirectoryWatcher."""
    global _directory_watcher_instance
    if _directory_watcher_instance is None:
        _directory_watcher_instance = HMISIncomingDirectoryWatcher()
    return _directory_watcher_instance


def start_directory_watcher(poll_interval: Optional[float] = None) -> HMISDirectoryWatcherThread:
    """Starts the background directory watcher thread if not already running."""
    global _directory_watcher_thread
    watcher = get_directory_watcher()
    if _directory_watcher_thread is None or not _directory_watcher_thread.is_alive():
        interval = poll_interval or 10.0
        _directory_watcher_thread = HMISDirectoryWatcherThread(watcher, poll_interval=interval)
        _directory_watcher_thread.start()
    return _directory_watcher_thread


def stop_directory_watcher() -> None:
    """Stops the background directory watcher thread."""
    global _directory_watcher_thread
    if _directory_watcher_thread and _directory_watcher_thread.is_alive():
        _directory_watcher_thread.stop()
        _directory_watcher_thread.join(timeout=5.0)
        _directory_watcher_thread = None
