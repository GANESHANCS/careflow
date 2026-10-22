import os
import json
import logging
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_batch import ImportBatch
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.import_observation_record import ImportObservationRecord
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.data_quality import DataQualityLog

from backend.app.services.data_pipeline.file_inspector import HMISFileInspector
from backend.app.services.data_pipeline.schema_normalizer import HMISSchemaNormalizer, ValueClassification
from backend.app.core.config import settings
from backend.app.services.data_pipeline.indicator_catalog import IndicatorCatalog
from backend.app.services.data_pipeline.entity_standardizer import HMISEntityStandardizer
from backend.app.services.data_pipeline.deduplication import DeduplicationEngine
from backend.app.services.data_pipeline.quality_engine import HMISQualityEngine, DataQualityReport

from backend.app.services.imports.storage import ImportStorageService
from backend.app.services.imports.validator import ImportValidationError, ImportValidatorService
from backend.app.services.imports.schema_profiles import SchemaProfileRegistry
from backend.app.services.imports.district_adapter import DistrictHMISAdapter

logger = logging.getLogger("careflow.imports")


class ImportRollbackDependencyConflictError(Exception):
    """Raised when a rollback would overwrite or delete observations modified by subsequent active imports."""
    def __init__(self, message: str, conflicting_job_codes: List[str], conflicting_observations: List[str]):
        super().__init__(message)
        self.message = message
        self.conflicting_job_codes = conflicting_job_codes
        self.conflicting_observations = conflicting_observations


class ImportRollbackIneligibleStatusError(Exception):
    """Raised when attempting to roll back an import that is not in an eligible completed state."""
    def __init__(self, message: str, current_status: str):
        super().__init__(message)
        self.message = message
        self.current_status = current_status


VALID_IMPORT_STATUS_TRANSITIONS: Dict[str, set] = {
    "QUEUED": {"PROCESSING", "FAILED", "CANCELLED"},
    "PROCESSING": {"VALIDATED", "FAILED", "QUEUED", "CANCELLED"},
    "VALIDATED": {"COMPLETED", "COMPLETED_WITH_WARNINGS", "FAILED", "CANCELLED", "QUEUED"},
    "COMPLETED": {"ROLLED_BACK"},
    "COMPLETED_WITH_WARNINGS": {"ROLLED_BACK"},
    "ROLLED_BACK": set(),
    "FAILED": {"QUEUED"},
    "CANCELLED": set(),
}


def validate_status_transition(current_status: str, target_status: str) -> bool:
    """Centralized lifecycle transition validator for HMIS import jobs."""
    allowed = VALID_IMPORT_STATUS_TRANSITIONS.get(current_status.upper(), set())
    if target_status.upper() not in allowed:
        raise ValueError(
            f"Invalid import status transition: '{current_status}' -> '{target_status}'. Allowed transitions: {sorted(list(allowed))}"
        )
    return True


class HMISImportService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = ImportStorageService()
        self.catalog = IndicatorCatalog()

    def _is_job_cancelled(self, job_id: int) -> bool:
        """
        Directly queries the database row status for cancellation,
        bypassing SQLAlchemy's session identity map cache.
        """
        status = (
            self.db.query(ImportJob.status)
            .filter(ImportJob.id == job_id)
            .execution_options(populate_existing=True)
            .scalar()
        )
        return status == "CANCELLED"

    def create_import_batch(
        self,
        batch_code: Optional[str] = None,
        source: str = "DIRECTORY_WATCHER",
        initiated_by: Optional[str] = None,
        total_files: int = 0
    ) -> ImportBatch:
        batch_code = batch_code or f"BATCH_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6].upper()}"
        batch = ImportBatch(
            batch_code=batch_code,
            source=source,
            status="QUEUED",
            total_files=total_files,
            processed_files=0,
            successful_files=0,
            failed_files=0,
            total_records=0,
            imported_records=0,
            rejected_records=0,
            initiated_by=initiated_by,
        )
        self.db.add(batch)
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def update_batch_metrics(self, batch_id: int) -> Optional[ImportBatch]:
        """
        Recalculates aggregated lifecycle status and metrics for an ImportBatch
        from its constituent ImportJobs.
        """
        batch = self.db.query(ImportBatch).filter(ImportBatch.id == batch_id).first()
        if not batch:
            return None

        jobs = self.db.query(ImportJob).filter(ImportJob.batch_id == batch_id).all()
        if not jobs:
            return batch

        batch.total_files = len(jobs)
        batch.total_records = sum(j.total_records or 0 for j in jobs)
        batch.imported_records = sum(j.records_imported or 0 for j in jobs)
        batch.rejected_records = sum(j.records_rejected or 0 for j in jobs)

        successful = sum(1 for j in jobs if j.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS"))
        failed = sum(1 for j in jobs if j.status == "FAILED")
        cancelled = sum(1 for j in jobs if j.status == "CANCELLED")
        in_progress = sum(1 for j in jobs if j.status in ("QUEUED", "PROCESSING", "VALIDATED"))

        batch.processed_files = successful + failed + cancelled
        batch.successful_files = successful
        batch.failed_files = failed

        now = datetime.now(timezone.utc)
        if in_progress > 0:
            if batch.processed_files > 0 or any(j.status in ("PROCESSING", "VALIDATED") for j in jobs):
                batch.status = "PROCESSING"
            else:
                batch.status = "QUEUED"
        else:
            if failed == 0 and cancelled == 0:
                batch.status = "COMPLETED"
                batch.completed_at = batch.completed_at or now
            elif successful > 0 and (failed > 0 or cancelled > 0):
                batch.status = "PARTIALLY_FAILED"
                batch.completed_at = batch.completed_at or now
            elif failed > 0:
                batch.status = "FAILED"
                batch.completed_at = batch.completed_at or now
            elif cancelled > 0:
                batch.status = "CANCELLED"
                batch.completed_at = batch.completed_at or now

        # Summarize errors if any
        failed_jobs = [j for j in jobs if j.status == "FAILED" and j.error_summary]
        if failed_jobs:
            batch.error_summary = f"{len(failed_jobs)} file(s) failed: " + "; ".join(
                f"{j.original_filename}: {j.error_summary}" for j in failed_jobs[:3]
            )
            if len(failed_jobs) > 3:
                batch.error_summary += f" (+{len(failed_jobs) - 3} more)"
            batch.error_summary = batch.error_summary[:512]

        batch.updated_at = now
        self.db.commit()
        self.db.refresh(batch)
        return batch

    def create_import_job(
        self,
        original_filename: str,
        content: bytes,
        mime_type: Optional[str] = None,
        batch_id: Optional[int] = None
    ) -> Tuple[ImportJob, bool]:
        ImportValidatorService.validate_file_constraints(original_filename, content, mime_type)

        file_hash = self.storage.calculate_file_hash(content)
        existing_job = ImportValidatorService.check_idempotency(self.db, file_hash)
        if existing_job:
            if batch_id and existing_job.batch_id is None:
                existing_job.batch_id = batch_id
                self.db.commit()
                self.db.refresh(existing_job)
            return existing_job, True

        job_code = self.storage.generate_job_code()
        rel_path, abs_path = self.storage.save_upload_file(job_code, original_filename, content)

        job = ImportJob(
            job_code=job_code,
            original_filename=original_filename,
            file_size_bytes=len(content),
            mime_type=mime_type or "application/octet-stream",
            storage_path=abs_path,
            file_hash=file_hash,
            status="QUEUED",
            total_records=0,
            records_imported=0,
            records_rejected=0,
            batch_id=batch_id
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job, False

    def process_import_job(self, job_id: int, worker_id: Optional[str] = None) -> ImportJob:
        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise ValueError(f"ImportJob with id {job_id} not found.")

        if job.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS", "CANCELLED"):
            return job

        job.status = "PROCESSING"
        now = datetime.now(timezone.utc)
        if worker_id:
            job.claimed_by = worker_id
        job.claimed_at = job.claimed_at or now
        job.heartbeat_at = now
        job.updated_at = now
        self.db.commit()
        if job.batch_id:
            self.update_batch_metrics(job.batch_id)

        file_path = Path(job.storage_path)
        if not file_path.exists():
            return self._fail_job(job, "FILE_NOT_FOUND", f"Stored file at '{job.storage_path}' could not be located.")

        try:
            inspector = HMISFileInspector(raw_dir=str(file_path.parent))
            inspection = inspector.inspect_file(file_path)

            if inspection.get("issues") and not inspection.get("sheets"):
                return self._fail_job(job, "UNSUPPORTED_FORMAT", "; ".join(inspection["issues"]))

            # Pre-flight Schema Profile Validation
            sheets = inspection.get("sheets", [])
            first_sheet_cols = sheets[0].get("columns", []) if sheets else []
            detected_profile = SchemaProfileRegistry.detect_profile(first_sheet_cols)
            job.schema_profile = detected_profile.profile_id
            profile_val = detected_profile.validate_headers(first_sheet_cols)

            if not profile_val.is_valid:
                for err in profile_val.errors:
                    err_log = ImportErrorLog(
                        import_job_id=job.id,
                        error_code="SCHEMA_VALIDATION_ERROR",
                        severity="ERROR",
                        message=f"[{detected_profile.name}] {err}"
                    )
                    self.db.add(err_log)
                return self._fail_job(job, "SCHEMA_VALIDATION_ERROR", "; ".join(profile_val.errors))

            for warn in profile_val.warnings:
                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    error_code="SCHEMA_VALIDATION_WARNING",
                    severity="WARNING",
                    message=f"[{detected_profile.name}] {warn}"
                )
                self.db.add(err_log)

            if detected_profile.profile_id == "district_monthly_tabular_v1":
                return self._process_district_import_job(job, file_path, detected_profile)

            raw_obs, raw_facs, parse_errors = self._extract_observations_and_facilities(file_path, inspection)

            job.total_records = len(raw_obs) + len(parse_errors)
            job.processed_records = len(parse_errors)
            job.records_rejected = len(parse_errors)
            
            for err in parse_errors:
                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    source_row=err.get("row"),
                    source_sheet=err.get("sheet"),
                    error_code=err.get("code", "PARSE_ERROR"),
                    severity="ERROR",
                    message=err.get("message", "Error parsing row")
                )
                self.db.add(err_log)

            if not raw_obs:
                return self._fail_job(job, "EMPTY_DATASET", "File contained no parseable observation records.")

            if self._is_job_cancelled(job.id):
                logger.info(f"Import job '{job.job_code}' was cancelled prior to validation. Halting.")
                self.db.rollback()
                self.cleanup_partial_import(job)
                self.db.refresh(job)
                return job

            job.status = "VALIDATED"
            job.heartbeat_at = datetime.now(timezone.utc)
            self.db.commit()

            dedup_obs, dedup_diag = DeduplicationEngine.deduplicate_observations(raw_obs)
            duplicates_count = dedup_diag.get("duplicate_count", 0)

            fac_dicts = [f.model_dump() for f in raw_facs.values()]
            quality_report: DataQualityReport = HMISQualityEngine.evaluate_dataset(
                observations=dedup_obs,
                facilities=fac_dicts,
                dedup_diagnostics=dedup_diag
            )

            job.quality_score = quality_report.quality_score.overall_score

            for issue in quality_report.issues:
                log_sev = "WARNING" if issue.severity == "WARNING" else ("ERROR" if issue.severity in ("ERROR", "CRITICAL") else "INFO")
                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    error_code=f"CHECK_{issue.check_id}",
                    severity=log_sev,
                    message=f"[{issue.check_name}] {issue.description}"
                )
                self.db.add(err_log)

            for ind_data in self.catalog.list_indicators():
                existing_ind = self.db.query(Indicator).filter(Indicator.code == ind_data.code).first()
                if not existing_ind:
                    ind_obj = Indicator(
                        id=f"IND_{ind_data.code}",
                        code=ind_data.code,
                        name=ind_data.name,
                        category=ind_data.category,
                        unit=ind_data.unit,
                        active=True
                    )
                    self.db.add(ind_obj)

            self.db.flush()

            for fac in raw_facs.values():
                filter_cond = (Facility.id == fac.facility_id)
                if fac.facility_code:
                    filter_cond = filter_cond | (Facility.facility_code == fac.facility_code)
                existing_fac = self.db.query(Facility).filter(filter_cond).first()
                if not existing_fac:
                    fac_obj = Facility(
                        id=fac.facility_id,
                        facility_code=fac.facility_code,
                        facility_name=fac.facility_name,
                        facility_type=fac.facility_type,
                        state=fac.state,
                        district=fac.district,
                        raw_facility_name=fac.raw_facility_name
                    )
                    self.db.add(fac_obj)

            self.db.flush()

            imported_count = 0
            rejected_count = len(parse_errors)
            indicator_map = {i.code: i.id for i in self.db.query(Indicator).all()}

            # Chunked observation persistence with live progress tracking
            chunk_size = getattr(settings, "IMPORT_CHUNK_SIZE", 500)
            total_obs_count = len(dedup_obs)


            for chunk_start in range(0, total_obs_count, chunk_size):
                # Refresh job status to detect cancellation before processing chunk
                if self._is_job_cancelled(job.id):
                    logger.info(
                        f"Import job '{job.job_code}' detected cancellation before processing chunk at offset {chunk_start}. "
                        f"Halting further processing and cleaning up partial state."
                    )
                    self.db.rollback()
                    self.cleanup_partial_import(job)
                    self.db.refresh(job)
                    return job

                chunk = dedup_obs[chunk_start:chunk_start + chunk_size]

                for obs_data in chunk:
                    raw_v = obs_data.get("value")
                    val = None if (raw_v is None or pd.isna(raw_v)) else float(raw_v)
                    val_type = obs_data.get("value_type", ValueClassification.VALID)
                    ind_code = obs_data.get("indicator_code")
                    fac_id = obs_data.get("facility_id")
                    month_str = obs_data.get("reporting_month")
                    iso_date = obs_data.get("observation_date")

                    if not iso_date or month_str == "UNKNOWN":
                        rejected_count += 1
                        err_log = ImportErrorLog(
                            import_job_id=job.id,
                            source_row=obs_data.get("raw_row_number"),
                            source_sheet=obs_data.get("source_sheet"),
                            error_code="INVALID_TEMPORAL_PERIOD",
                            severity="ERROR",
                            message=f"Invalid reporting date/month: '{month_str}'"
                        )
                        self.db.add(err_log)
                        continue

                    ind_id = indicator_map.get(ind_code)
                    if not ind_id:
                        ind_id = f"IND_{ind_code}"
                        existing_by_id = self.db.query(Indicator).filter(Indicator.id == ind_id).first()
                        if not existing_by_id:
                            new_ind = Indicator(id=ind_id, code=ind_code, name=ind_code.replace('_', ' ').title(), category="Imported", unit="count", active=True)
                            self.db.add(new_ind)
                            self.db.flush()
                        indicator_map[ind_code] = ind_id

                    obs_pk = f"OBS_{fac_id}_{ind_code}_{month_str}"
                    existing_obs = self.db.query(Observation).filter(Observation.id == obs_pk).first()

                    if existing_obs:
                        will_update = (val is not None or existing_obs.value is None)
                        is_different = will_update and ((existing_obs.value != val) or (existing_obs.value_type != val_type))

                        if is_different:
                            change_rec = ImportObservationRecord(
                                import_job_id=job.id,
                                observation_id=obs_pk,
                                action="UPDATE",
                                previous_value=existing_obs.value,
                                previous_value_type=existing_obs.value_type,
                                previous_validation_status=existing_obs.validation_status,
                                previous_source_file=existing_obs.source_file,
                                previous_source_sheet=existing_obs.source_sheet,
                                previous_source_row=existing_obs.source_row,
                                previous_ingested_at=existing_obs.ingested_at,
                                previous_transformation_version=existing_obs.transformation_version,
                                previous_import_job_id=existing_obs.last_import_job_id,
                                new_value=val,
                                new_value_type=val_type,
                            )
                            self.db.add(change_rec)
                            existing_obs.value = val
                            existing_obs.value_type = val_type
                            existing_obs.source_file = job.original_filename
                            existing_obs.source_sheet = obs_data.get("source_sheet")
                            existing_obs.source_row = obs_data.get("raw_row_number")
                            existing_obs.ingested_at = datetime.now(timezone.utc).isoformat()
                            existing_obs.last_import_job_id = job.id
                        else:
                            change_rec = ImportObservationRecord(
                                import_job_id=job.id,
                                observation_id=obs_pk,
                                action="UNCHANGED",
                                previous_value=existing_obs.value,
                                previous_value_type=existing_obs.value_type,
                                previous_validation_status=existing_obs.validation_status,
                                previous_source_file=existing_obs.source_file,
                                previous_source_sheet=existing_obs.source_sheet,
                                previous_source_row=existing_obs.source_row,
                                previous_ingested_at=existing_obs.ingested_at,
                                previous_transformation_version=existing_obs.transformation_version,
                                previous_import_job_id=existing_obs.last_import_job_id,
                                new_value=existing_obs.value,
                                new_value_type=existing_obs.value_type,
                            )
                            self.db.add(change_rec)
                    else:
                        new_obs = Observation(
                            id=obs_pk,
                            facility_id=fac_id,
                            indicator_id=ind_id,
                            observation_date=iso_date,
                            reporting_month=month_str,
                            value=val,
                            value_type=val_type,
                            source_file=job.original_filename,
                            source_sheet=obs_data.get("source_sheet"),
                            source_row=obs_data.get("raw_row_number"),
                            ingested_at=datetime.now(timezone.utc).isoformat(),
                            transformation_version="2.0.0",
                            last_import_job_id=job.id,
                        )
                        self.db.add(new_obs)
                        change_rec = ImportObservationRecord(
                            import_job_id=job.id,
                            observation_id=obs_pk,
                            action="INSERT",
                            previous_value=None,
                            previous_value_type=None,
                            previous_validation_status=None,
                            previous_source_file=None,
                            previous_source_sheet=None,
                            previous_source_row=None,
                            previous_ingested_at=None,
                            previous_transformation_version=None,
                            previous_import_job_id=None,
                            new_value=val,
                            new_value_type=val_type,
                        )
                        self.db.add(change_rec)

                    imported_count += 1

                # Check cancellation right before committing the chunk
                if self._is_job_cancelled(job.id):
                    logger.info(
                        f"Import job '{job.job_code}' detected cancellation before committing chunk at offset {chunk_start}. "
                        f"Rolling back uncommitted chunk and cleaning up partial state."
                    )
                    self.db.rollback()
                    self.cleanup_partial_import(job)
                    self.db.refresh(job)
                    if job.batch_id:
                        self.update_batch_metrics(job.batch_id)
                    return job

                # Update incremental progress and worker heartbeat per chunk
                now = datetime.now(timezone.utc)
                job.processed_records = min(job.total_records, len(parse_errors) + chunk_start + len(chunk))
                job.records_imported = imported_count
                job.records_rejected = rejected_count
                job.heartbeat_at = now
                job.updated_at = now
                self.db.commit()

            # Check cancellation after completing the chunk loop before finalizing completion
            if self._is_job_cancelled(job.id):
                logger.info(
                    f"Import job '{job.job_code}' detected cancellation after chunk loop. "
                    f"Halting completion and cleaning up partial state."
                )
                self.db.rollback()
                self.cleanup_partial_import(job)
                self.db.refresh(job)
                if job.batch_id:
                    self.update_batch_metrics(job.batch_id)
                return job

            dq_log = DataQualityLog(
                id=f"DQ_{job.job_code}",
                audit_timestamp=datetime.now(timezone.utc).isoformat(),
                quality_score=quality_report.quality_score.overall_score,
                issue_category="Import Evaluation",
                severity="WARNING" if len(quality_report.issues) > 0 else "INFO",
                affected_record_count=len(quality_report.issues),
                description=f"Import job '{job.job_code}' evaluation score: {quality_report.quality_score.overall_score}%",
                source_file=job.original_filename
            )
            self.db.add(dq_log)

            job.processed_records = job.total_records
            job.records_imported = imported_count
            job.records_rejected = rejected_count
            has_errors = (rejected_count > 0 or any(l.severity == "ERROR" for l in job.error_logs))
            job.status = "COMPLETED_WITH_WARNINGS" if has_errors else "COMPLETED"
            now = datetime.now(timezone.utc)
            job.completed_at = now
            job.updated_at = now
            job.heartbeat_at = now

            self.db.commit()
            self.db.refresh(job)
            if job.batch_id:
                self.update_batch_metrics(job.batch_id)
            logger.info(f"Import job {job.job_code} completed successfully with status {job.status}.")
            return job

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Import job {job.job_code} encountered uncaught processing exception: {str(e)}")
            self.cleanup_partial_import(job)
            if self._is_job_cancelled(job.id):
                self.db.refresh(job)
                if job.batch_id:
                    self.update_batch_metrics(job.batch_id)
                return job
            return self._fail_job(job, "IMPORT_PROCESSING_FAILED", f"Processing error: {str(e)}")

    def _process_district_import_job(
        self, job: ImportJob, file_path: Path, detected_profile: Any
    ) -> ImportJob:
        """
        Specialized ingestion pipeline for district-level monthly tabular HMIS datasets.
        Preserves original district names, S.No. codes, descriptions, sub-group slices,
        and arithmetic totals in dedicated DistrictObservation entities.
        """
        try:
            df = pd.read_csv(file_path, low_memory=False)
            detected_fy = DistrictHMISAdapter.detect_financial_year(job.original_filename)
            long_records, parse_errors = DistrictHMISAdapter.extract_long_records(
                df=df,
                financial_year=detected_fy,
                state="Tamil Nadu",
                source_file=job.original_filename
            )

            job.total_records = len(long_records) + len(parse_errors)
            job.processed_records = len(parse_errors)
            job.records_rejected = len(parse_errors)

            for err in parse_errors:
                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    source_row=err.get("row"),
                    error_code=err.get("code", "PARSE_ERROR"),
                    severity="ERROR",
                    message=err.get("message", "Error parsing row")
                )
                self.db.add(err_log)

            if not long_records:
                return self._fail_job(job, "EMPTY_DATASET", "File contained no parseable district observation records.")

            if self._is_job_cancelled(job.id):
                logger.info(f"Import job '{job.job_code}' was cancelled prior to validation. Halting.")
                self.db.rollback()
                self.cleanup_partial_import(job)
                self.db.refresh(job)
                return job

            job.status = "VALIDATED"
            job.heartbeat_at = datetime.now(timezone.utc)
            self.db.commit()

            # Ensure canonical crosswalk indicators exist
            seen_ind_ids = set()
            for rec in long_records:
                ind_id = rec.get("indicator_id")
                if ind_id and ind_id not in seen_ind_ids:
                    seen_ind_ids.add(ind_id)
                    existing_ind = self.db.query(Indicator).filter(Indicator.id == ind_id).first()
                    if not existing_ind:
                        code = ind_id.replace("IND_", "")
                        ind_obj = Indicator(
                            id=ind_id,
                            code=code,
                            name=rec.get("parameter_name", code).replace('_', ' ').title()[:255],
                            category="District HMIS",
                            unit="count",
                            active=True
                        )
                        self.db.add(ind_obj)
            self.db.flush()

            imported_count = 0
            rejected_count = len(parse_errors)
            chunk_size = getattr(settings, "IMPORT_CHUNK_SIZE", 500)
            total_records_count = len(long_records)

            for chunk_start in range(0, total_records_count, chunk_size):
                if self._is_job_cancelled(job.id):
                    logger.info(
                        f"Import job '{job.job_code}' detected cancellation before processing chunk at offset {chunk_start}. "
                        f"Halting further processing and cleaning up partial state."
                    )
                    self.db.rollback()
                    self.cleanup_partial_import(job)
                    self.db.refresh(job)
                    if job.batch_id:
                        self.update_batch_metrics(job.batch_id)
                    return job

                chunk = long_records[chunk_start : chunk_start + chunk_size]
                chunk_ids = [r["id"] for r in chunk]
                existing_map = {
                    obs.id: obs for obs in self.db.query(DistrictObservation).filter(DistrictObservation.id.in_(chunk_ids)).all()
                }

                for rec in chunk:
                    obs_pk = rec["id"]
                    val = rec["value"]
                    val_type = rec["value_type"]

                    existing_obs = existing_map.get(obs_pk)

                    if existing_obs:
                        will_update = (val is not None or existing_obs.value is None)
                        is_different = will_update and ((existing_obs.value != val) or (existing_obs.value_type != val_type))

                        if is_different:
                            change_rec = ImportObservationRecord(
                                import_job_id=job.id,
                                observation_id=obs_pk,
                                action="UPDATE",
                                previous_value=existing_obs.value,
                                previous_value_type=existing_obs.value_type,
                                previous_validation_status=existing_obs.validation_status,
                                previous_source_file=existing_obs.source_file,
                                previous_source_sheet=None,
                                previous_source_row=existing_obs.source_row,
                                previous_ingested_at=existing_obs.ingested_at,
                                previous_transformation_version=existing_obs.transformation_version,
                                previous_import_job_id=existing_obs.last_import_job_id,
                                new_value=val,
                                new_value_type=val_type,
                            )
                            self.db.add(change_rec)
                            existing_obs.value = val
                            existing_obs.value_type = val_type
                            existing_obs.validation_status = rec["validation_status"]
                            existing_obs.reported_annual_total = rec["reported_annual_total"]
                            existing_obs.source_file = job.original_filename
                            existing_obs.source_row = rec["source_row"]
                            existing_obs.ingested_at = datetime.now(timezone.utc).isoformat()
                            existing_obs.last_import_job_id = job.id
                        else:
                            change_rec = ImportObservationRecord(
                                import_job_id=job.id,
                                observation_id=obs_pk,
                                action="UNCHANGED",
                                previous_value=existing_obs.value,
                                previous_value_type=existing_obs.value_type,
                                previous_validation_status=existing_obs.validation_status,
                                previous_source_file=existing_obs.source_file,
                                previous_source_sheet=None,
                                previous_source_row=existing_obs.source_row,
                                previous_ingested_at=existing_obs.ingested_at,
                                previous_transformation_version=existing_obs.transformation_version,
                                previous_import_job_id=existing_obs.last_import_job_id,
                                new_value=existing_obs.value,
                                new_value_type=existing_obs.value_type,
                            )
                            self.db.add(change_rec)
                    else:
                        new_obs = DistrictObservation(
                            id=obs_pk,
                            state=rec["state"],
                            district=rec["district"],
                            s_no=rec["s_no"],
                            parameter_name=rec["parameter_name"],
                            subgroup_type=rec["subgroup_type"],
                            is_subgroup_total=rec["is_subgroup_total"],
                            indicator_id=rec["indicator_id"],
                            financial_year=rec["financial_year"],
                            reporting_month=rec["reporting_month"],
                            observation_date=rec["observation_date"],
                            value=val,
                            value_type=val_type,
                            validation_status=rec["validation_status"],
                            reported_annual_total=rec["reported_annual_total"],
                            source_file=job.original_filename,
                            source_row=rec["source_row"],
                            ingested_at=datetime.now(timezone.utc).isoformat(),
                            transformation_version=rec["transformation_version"],
                            last_import_job_id=job.id,
                        )
                        self.db.add(new_obs)
                        change_rec = ImportObservationRecord(
                            import_job_id=job.id,
                            observation_id=obs_pk,
                            action="INSERT",
                            previous_value=None,
                            previous_value_type=None,
                            previous_validation_status=None,
                            previous_source_file=None,
                            previous_source_sheet=None,
                            previous_source_row=None,
                            previous_ingested_at=None,
                            previous_transformation_version=None,
                            previous_import_job_id=None,
                            new_value=val,
                            new_value_type=val_type,
                        )
                        self.db.add(change_rec)

                    imported_count += 1

                if self._is_job_cancelled(job.id):
                    logger.info(
                        f"Import job '{job.job_code}' detected cancellation before committing chunk at offset {chunk_start}. "
                        f"Rolling back uncommitted chunk and cleaning up partial state."
                    )
                    self.db.rollback()
                    self.cleanup_partial_import(job)
                    self.db.refresh(job)
                    if job.batch_id:
                        self.update_batch_metrics(job.batch_id)
                    return job

                now = datetime.now(timezone.utc)
                job.processed_records = min(job.total_records, len(parse_errors) + chunk_start + len(chunk))
                job.records_imported = imported_count
                job.records_rejected = rejected_count
                job.heartbeat_at = now
                job.updated_at = now
                self.db.commit()

            if self._is_job_cancelled(job.id):
                logger.info(
                    f"Import job '{job.job_code}' detected cancellation after chunk loop. "
                    f"Halting completion and cleaning up partial state."
                )
                self.db.rollback()
                self.cleanup_partial_import(job)
                self.db.refresh(job)
                if job.batch_id:
                    self.update_batch_metrics(job.batch_id)
                return job

            dq_log = DataQualityLog(
                id=f"DQ_{job.job_code}",
                audit_timestamp=datetime.now(timezone.utc).isoformat(),
                quality_score=100.0 if rejected_count == 0 else max(0.0, round(100.0 - (rejected_count / max(1, job.total_records) * 100), 2)),
                issue_category="District Import Evaluation",
                severity="WARNING" if rejected_count > 0 else "INFO",
                affected_record_count=rejected_count,
                description=f"District import job '{job.job_code}' processed {imported_count} records with {rejected_count} rejections.",
                source_file=job.original_filename
            )
            self.db.add(dq_log)

            job.processed_records = job.total_records
            job.records_imported = imported_count
            job.records_rejected = rejected_count
            has_errors = (rejected_count > 0 or any(l.severity == "ERROR" for l in job.error_logs))
            job.status = "COMPLETED_WITH_WARNINGS" if has_errors else "COMPLETED"
            now = datetime.now(timezone.utc)
            job.completed_at = now
            job.updated_at = now
            job.heartbeat_at = now

            self.db.commit()
            self.db.refresh(job)
            if job.batch_id:
                self.update_batch_metrics(job.batch_id)
            logger.info(f"District import job {job.job_code} completed successfully with status {job.status}.")
            return job

        except Exception as e:
            self.db.rollback()
            logger.exception(f"District import job {job.job_code} encountered uncaught processing exception: {str(e)}")
            self.cleanup_partial_import(job)
            if self._is_job_cancelled(job.id):
                self.db.refresh(job)
                if job.batch_id:
                    self.update_batch_metrics(job.batch_id)
                return job
            return self._fail_job(job, "IMPORT_PROCESSING_FAILED", f"Processing error: {str(e)}")

    def _fail_job(self, job: ImportJob, error_code: str, message: str) -> ImportJob:
        if self._is_job_cancelled(job.id):
            self.db.refresh(job)
            if job.batch_id:
                self.update_batch_metrics(job.batch_id)
            return job

        job.status = "FAILED"
        job.error_summary = message[:512] if message else "Processing failed."
        now = datetime.now(timezone.utc)
        job.completed_at = now
        job.updated_at = now
        job.heartbeat_at = now

        err_log = ImportErrorLog(
            import_job_id=job.id,
            error_code=error_code,
            severity="CRITICAL",
            message=message
        )
        self.db.add(err_log)
        self.db.commit()
        self.db.refresh(job)
        if job.batch_id:
            self.update_batch_metrics(job.batch_id)
        return job

    def cleanup_partial_import(self, job: ImportJob) -> None:
        """
        Reverses any partial observation insertions or updates committed by this import job,
        restoring the database to its exact prior state.
        Ensures that interrupted or failed jobs do not leave orphaned observations or corrupted before-images.
        """
        try:
            change_records = (
                self.db.query(ImportObservationRecord)
                .filter(ImportObservationRecord.import_job_id == job.id)
                .order_by(ImportObservationRecord.id.desc())
                .all()
            )
            for rec in change_records:
                obs = self.db.query(Observation).filter(Observation.id == rec.observation_id).first()
                if obs:
                    if rec.action == "INSERT":
                        if obs.last_import_job_id == job.id:
                            self.db.delete(obs)
                    elif rec.action == "UPDATE":
                        if obs.last_import_job_id == job.id:
                            obs.value = rec.previous_value
                            obs.value_type = rec.previous_value_type or "VALID"
                            obs.validation_status = rec.previous_validation_status or "VALIDATED"
                            obs.source_file = rec.previous_source_file or ""
                            obs.source_sheet = rec.previous_source_sheet
                            obs.source_row = rec.previous_source_row
                            obs.ingested_at = rec.previous_ingested_at or obs.ingested_at
                            obs.transformation_version = rec.previous_transformation_version or obs.transformation_version
                            obs.last_import_job_id = rec.previous_import_job_id
                else:
                    dist_obs = self.db.query(DistrictObservation).filter(DistrictObservation.id == rec.observation_id).first()
                    if dist_obs:
                        if rec.action == "INSERT":
                            if dist_obs.last_import_job_id == job.id:
                                self.db.delete(dist_obs)
                        elif rec.action == "UPDATE":
                            if dist_obs.last_import_job_id == job.id:
                                dist_obs.value = rec.previous_value
                                dist_obs.value_type = rec.previous_value_type or "VALID"
                                dist_obs.validation_status = rec.previous_validation_status or "VALIDATED"
                                dist_obs.source_file = rec.previous_source_file or ""
                                dist_obs.source_sheet = rec.previous_source_sheet
                                dist_obs.source_row = rec.previous_source_row
                                dist_obs.ingested_at = rec.previous_ingested_at or dist_obs.ingested_at
                                dist_obs.transformation_version = rec.previous_transformation_version or dist_obs.transformation_version
                                dist_obs.last_import_job_id = rec.previous_import_job_id

            # Remove change records associated with the partial execution
            self.db.query(ImportObservationRecord).filter(ImportObservationRecord.import_job_id == job.id).delete()
            # Remove any DQ log for this job code
            self.db.query(DataQualityLog).filter(DataQualityLog.id == f"DQ_{job.job_code}").delete()
            self.db.commit()
            logger.info(f"Cleaned up partial database modifications for import job '{job.job_code}'.")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Error during partial import cleanup for job '{job.job_code}': {e}")

    def retry_import_job(self, job_identifier: Any, requested_by: str) -> ImportJob:
        """
        Resets an eligible failed import job to QUEUED state for worker re-execution.
        """
        query = self.db.query(ImportJob)
        if isinstance(job_identifier, int) or (isinstance(job_identifier, str) and str(job_identifier).isdigit()):
            query = query.filter((ImportJob.id == int(job_identifier)) | (ImportJob.job_code == str(job_identifier)))
        else:
            query = query.filter(ImportJob.job_code == str(job_identifier))

        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            query = query.with_for_update()

        job = query.first()
        if not job:
            raise ValueError(f"Import job '{job_identifier}' not found.")

        if job.status not in ("FAILED", "PROCESSING", "VALIDATED"):
            raise ValueError(f"Only FAILED or stalled jobs can be retried. Job '{job.job_code}' has status '{job.status}'.")

        validate_status_transition(job.status, "QUEUED")

        # Clean up any partial state before retry
        self.cleanup_partial_import(job)

        job.status = "QUEUED"
        job.claimed_by = None
        job.claimed_at = None
        job.heartbeat_at = None
        job.error_summary = None
        job.processed_records = 0
        job.records_imported = 0
        job.records_rejected = 0
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(job)
        if job.batch_id:
            self.update_batch_metrics(job.batch_id)

        logger.info(f"Import job '{job.job_code}' reset to QUEUED for retry by '{requested_by}'.")
        return job

    def cancel_import_job(self, job_identifier: Any, cancelled_by: str, reason: Optional[str] = None) -> ImportJob:
        """
        Cancels an in-flight import job prior to completion (QUEUED, PROCESSING, or VALIDATED).
        """
        query = self.db.query(ImportJob)
        if isinstance(job_identifier, int) or (isinstance(job_identifier, str) and str(job_identifier).isdigit()):
            query = query.filter((ImportJob.id == int(job_identifier)) | (ImportJob.job_code == str(job_identifier)))
        else:
            query = query.filter(ImportJob.job_code == str(job_identifier))

        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            query = query.with_for_update()

        job = query.first()
        if not job:
            raise ValueError(f"Import job '{job_identifier}' not found.")

        # Idempotent check
        if job.status == "CANCELLED":
            return job

        if job.status not in ("QUEUED", "PROCESSING", "VALIDATED"):
            raise ValueError(f"Only QUEUED, PROCESSING, or VALIDATED jobs can be cancelled. Job '{job.job_code}' has status '{job.status}'.")

        validate_status_transition(job.status, "CANCELLED")

        job.status = "CANCELLED"
        job.error_summary = f"Cancelled by {cancelled_by}. Reason: {reason or 'No reason provided.'}"
        now = datetime.now(timezone.utc)
        job.completed_at = now
        job.updated_at = now
        self.db.commit()
        self.db.refresh(job)

        # Clean up any partial modifications recorded so far
        self.cleanup_partial_import(job)
        if job.batch_id:
            self.update_batch_metrics(job.batch_id)

        logger.info(f"Import job '{job.job_code}' was cancelled by '{cancelled_by}'.")
        return job

    def retry_import_batch(self, batch_code: str, requested_by: str) -> Tuple[ImportBatch, int]:
        """
        Retries all eligible failed jobs within a batch, resetting their status to QUEUED
        and updating the batch status.
        """
        batch = self.db.query(ImportBatch).filter(ImportBatch.batch_code == batch_code).first()
        if not batch:
            raise ValueError(f"ImportBatch '{batch_code}' not found.")

        jobs = self.db.query(ImportJob).filter(ImportJob.batch_id == batch.id).all()
        retried_count = 0
        for job in jobs:
            if job.status in ("FAILED", "PROCESSING", "VALIDATED"):
                self.retry_import_job(job.id, requested_by=requested_by)
                retried_count += 1

        batch.status = "QUEUED"
        batch.completed_at = None
        batch.error_summary = None
        batch.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.update_batch_metrics(batch.id)
        self.db.refresh(batch)
        return batch, retried_count

    def cancel_import_batch(self, batch_code: str, cancelled_by: str, reason: Optional[str] = None) -> ImportBatch:
        """
        Cancels all in-flight jobs in a batch.
        """
        batch = self.db.query(ImportBatch).filter(ImportBatch.batch_code == batch_code).first()
        if not batch:
            raise ValueError(f"ImportBatch '{batch_code}' not found.")

        jobs = self.db.query(ImportJob).filter(ImportJob.batch_id == batch.id).all()
        for job in jobs:
            if job.status in ("QUEUED", "PROCESSING", "VALIDATED"):
                try:
                    self.cancel_import_job(job.id, cancelled_by=cancelled_by, reason=reason)
                except Exception as exc:
                    logger.warning(
                        f"Job '{job.job_code}' could not be cancelled during batch cancellation "
                        f"(status may have changed concurrently): {exc}"
                    )

        batch.status = "CANCELLED"
        batch.completed_at = datetime.now(timezone.utc)
        batch.error_summary = f"Cancelled by {cancelled_by}. Reason: {reason or 'No reason provided.'}"[:512]
        batch.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.update_batch_metrics(batch.id)
        self.db.refresh(batch)
        return batch

    def rollback_import_job(
        self,
        job_identifier: Any,
        rolled_back_by: str,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Safely, atomically, and auditably rolls back a completed HMIS import job.

        Reverses observation insertions and updates tracked by this import job:
        - Deletes created observations if no subsequent active import modified them.
        - Restores before-images for updated observations.
        - Leaves unchanged observations untouched.
        - Safely rejects rollback with ImportRollbackDependencyConflictError if any subsequent
          active import modified the same observations.
        - Idempotently succeeds if already rolled back.
        - Preserves the original file on disk and ImportErrorLogs.
        - Deletes associated DataQualityLog so analytics accurately reflect the reversal.
        """
        query = self.db.query(ImportJob)
        if isinstance(job_identifier, int) or (isinstance(job_identifier, str) and str(job_identifier).isdigit()):
            query = query.filter((ImportJob.id == int(job_identifier)) | (ImportJob.job_code == str(job_identifier)))
        else:
            query = query.filter(ImportJob.job_code == str(job_identifier))

        if self.db.bind and self.db.bind.dialect.name == "postgresql":
            query = query.with_for_update()

        job = query.first()
        if not job:
            raise ValueError(f"Import job '{job_identifier}' not found.")

        # Idempotency check: if already rolled back, return existing state safely
        if job.status == "ROLLED_BACK":
            return {
                "job_code": job.job_code,
                "status": "ROLLED_BACK",
                "records_deleted": 0,
                "records_restored": 0,
                "records_unchanged": 0,
                "rolled_back_at": job.rolled_back_at or datetime.now(timezone.utc),
                "rolled_back_by": job.rolled_back_by,
                "message": f"Import job '{job.job_code}' has already been rolled back."
            }

        # Validate status eligibility
        if job.status not in ("COMPLETED", "COMPLETED_WITH_WARNINGS"):
            raise ImportRollbackIneligibleStatusError(
                f"Cannot roll back import job '{job.job_code}' with status '{job.status}'. Only completed imports can be rolled back.",
                current_status=job.status
            )

        validate_status_transition(job.status, "ROLLED_BACK")

        # Retrieve change records for this import
        change_records = (
            self.db.query(ImportObservationRecord)
            .filter(ImportObservationRecord.import_job_id == job.id)
            .order_by(ImportObservationRecord.id.desc())
            .all()
        )

        # Identify all observation IDs modified or created by this job
        touched_obs_ids = {
            r.observation_id for r in change_records if r.action in ("INSERT", "UPDATE")
        }

        # Check for subsequent active dependent imports that modified any of the same observations
        if touched_obs_ids:
            conflicts = (
                self.db.query(ImportObservationRecord, ImportJob)
                .join(ImportJob, ImportObservationRecord.import_job_id == ImportJob.id)
                .filter(
                    ImportObservationRecord.observation_id.in_(touched_obs_ids),
                    ImportJob.id > job.id,
                    ImportJob.status.in_(["COMPLETED", "COMPLETED_WITH_WARNINGS"]),
                    ImportObservationRecord.action.in_(["INSERT", "UPDATE"])
                )
                .all()
            )

            if conflicts:
                conflicting_job_codes = sorted(list({job_obj.job_code for _, job_obj in conflicts}))
                conflicting_obs_ids = sorted(list({rec.observation_id for rec, _ in conflicts}))
                raise ImportRollbackDependencyConflictError(
                    f"Cannot roll back import job '{job.job_code}' because subsequent active import job(s) "
                    f"[{', '.join(conflicting_job_codes)}] modified the same observation(s). "
                    f"Roll back subsequent dependent imports first.",
                    conflicting_job_codes=conflicting_job_codes,
                    conflicting_observations=conflicting_obs_ids
                )

        try:
            records_deleted = 0
            records_restored = 0
            records_unchanged = 0

            for rec in change_records:
                if rec.action == "INSERT":
                    obs = self.db.query(Observation).filter(Observation.id == rec.observation_id).first()
                    if obs:
                        self.db.delete(obs)
                        records_deleted += 1
                    else:
                        dist_obs = self.db.query(DistrictObservation).filter(DistrictObservation.id == rec.observation_id).first()
                        if dist_obs:
                            self.db.delete(dist_obs)
                            records_deleted += 1
                elif rec.action == "UPDATE":
                    obs = self.db.query(Observation).filter(Observation.id == rec.observation_id).first()
                    if obs:
                        obs.value = rec.previous_value
                        obs.value_type = rec.previous_value_type or "VALID"
                        obs.validation_status = rec.previous_validation_status or "VALIDATED"
                        obs.source_file = rec.previous_source_file or ""
                        obs.source_sheet = rec.previous_source_sheet
                        obs.source_row = rec.previous_source_row
                        obs.ingested_at = rec.previous_ingested_at or obs.ingested_at
                        obs.transformation_version = rec.previous_transformation_version or obs.transformation_version
                        obs.last_import_job_id = rec.previous_import_job_id
                        records_restored += 1
                    else:
                        dist_obs = self.db.query(DistrictObservation).filter(DistrictObservation.id == rec.observation_id).first()
                        if dist_obs:
                            dist_obs.value = rec.previous_value
                            dist_obs.value_type = rec.previous_value_type or "VALID"
                            dist_obs.validation_status = rec.previous_validation_status or "VALIDATED"
                            dist_obs.source_file = rec.previous_source_file or ""
                            dist_obs.source_sheet = rec.previous_source_sheet
                            dist_obs.source_row = rec.previous_source_row
                            dist_obs.ingested_at = rec.previous_ingested_at or dist_obs.ingested_at
                            dist_obs.transformation_version = rec.previous_transformation_version or dist_obs.transformation_version
                            dist_obs.last_import_job_id = rec.previous_import_job_id
                            records_restored += 1
                elif rec.action == "UNCHANGED":
                    records_unchanged += 1

            # Delete corresponding DataQualityLog so analytics accurately reflect the reversal
            dq_log = self.db.query(DataQualityLog).filter(DataQualityLog.id == f"DQ_{job.job_code}").first()
            if dq_log:
                self.db.delete(dq_log)

            # Update job status and audit trail
            now = datetime.now(timezone.utc)
            job.status = "ROLLED_BACK"
            job.rolled_back_at = now
            job.rolled_back_by = rolled_back_by
            job.rollback_reason = reason
            job.updated_at = now

            self.db.commit()
            self.db.refresh(job)

            logger.info(
                f"Import job {job.job_code} rolled back successfully by {rolled_back_by}: "
                f"{records_deleted} deleted, {records_restored} restored, {records_unchanged} unchanged."
            )

            return {
                "job_code": job.job_code,
                "status": "ROLLED_BACK",
                "records_deleted": records_deleted,
                "records_restored": records_restored,
                "records_unchanged": records_unchanged,
                "rolled_back_at": now,
                "rolled_back_by": rolled_back_by,
                "message": (
                    f"Successfully rolled back import job '{job.job_code}'. "
                    f"Reverted {records_deleted} inserted and {records_restored} updated observation records."
                )
            }

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Rollback failed for import job {job.job_code}: {e}")
            raise

    def _extract_observations_and_facilities(
        self, file_path: Path, inspection: Dict[str, Any]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], List[Dict[str, Any]]]:
        ext = file_path.suffix.lower()
        observations: List[Dict[str, Any]] = []
        facilities: Dict[str, Any] = {}
        errors: List[Dict[str, Any]] = []

        ingested_at = datetime.now(timezone.utc).isoformat()
        sheets = inspection.get("sheets", [])

        entity_col_keys = {"state", "district", "sub_district", "block", "facility", "facility_name", "facility_code", "code", "facility_type"}

        for sheet in sheets:
            sheet_name = sheet.get("sheet_name", "Sheet1")
            header_idx = sheet.get("header_row_index", 0)

            try:
                if ext in [".xlsx", ".xls"]:
                    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_idx)
                else:
                    df_raw = pd.read_csv(file_path, skiprows=header_idx, low_memory=False)
            except Exception as e:
                errors.append({
                    "sheet": sheet_name,
                    "row": None,
                    "code": "CORRUPT_SHEET",
                    "message": f"Could not read sheet '{sheet_name}': {str(e)}"
                })
                continue

            if df_raw.empty:
                continue

            orig_cols = list(df_raw.columns)
            norm_cols = [HMISSchemaNormalizer.normalize_column_name(c) for c in orig_cols]
            df_raw.columns = norm_cols

            date_col = next((c for c in norm_cols if any(k in c for k in ["date", "month", "period", "year"])), None)

            for row_idx, row in df_raw.iterrows():
                row_dict = row.to_dict()
                fac_entity = HMISEntityStandardizer.process_row(row_dict)
                facilities[fac_entity.facility_id] = fac_entity

                month_str, iso_date = HMISSchemaNormalizer.normalize_date(row_dict.get(date_col) if date_col else None)

                for col_name in norm_cols:
                    if col_name in entity_col_keys or col_name == date_col or col_name.startswith("unnamed"):
                        continue

                    indicator_code = self.catalog.match_column_name(col_name) or f"ind_{col_name}"
                    raw_val = row_dict.get(col_name)
                    norm_num, val_class = HMISSchemaNormalizer.normalize_value(raw_val)

                    obs_record = {
                        "facility_id": fac_entity.facility_id,
                        "facility_code": fac_entity.facility_code,
                        "facility_name": fac_entity.facility_name,
                        "district": fac_entity.district,
                        "state": fac_entity.state,
                        "indicator_code": indicator_code,
                        "reporting_month": month_str or "UNKNOWN",
                        "observation_date": iso_date,
                        "value": norm_num,
                        "value_type": val_class,
                        "raw_row_number": row_idx + header_idx + 1,
                        "source_sheet": sheet_name,
                        "source_file": file_path.name,
                        "ingested_at": ingested_at
                    }
                    observations.append(obs_record)

        return observations, facilities, errors
