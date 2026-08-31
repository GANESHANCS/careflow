import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.data_quality import DataQualityLog

from backend.app.services.data_pipeline.file_inspector import HMISFileInspector
from backend.app.services.data_pipeline.schema_normalizer import HMISSchemaNormalizer, ValueClassification
from backend.app.services.data_pipeline.indicator_catalog import IndicatorCatalog
from backend.app.services.data_pipeline.entity_standardizer import HMISEntityStandardizer
from backend.app.services.data_pipeline.deduplication import DeduplicationEngine
from backend.app.services.data_pipeline.quality_engine import HMISQualityEngine, DataQualityReport

from backend.app.services.imports.storage import ImportStorageService
from backend.app.services.imports.validator import ImportValidationError, ImportValidatorService

logger = logging.getLogger("careflow.imports")


class HMISImportService:
    def __init__(self, db: Session):
        self.db = db
        self.storage = ImportStorageService()
        self.catalog = IndicatorCatalog()

    def create_import_job(
        self,
        original_filename: str,
        content: bytes,
        mime_type: Optional[str] = None
    ) -> Tuple[ImportJob, bool]:
        ImportValidatorService.validate_file_constraints(original_filename, content, mime_type)

        file_hash = self.storage.calculate_file_hash(content)
        existing_job = ImportValidatorService.check_idempotency(self.db, file_hash)
        if existing_job:
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
            records_rejected=0
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        return job, False

    def process_import_job(self, job_id: int) -> ImportJob:
        job = self.db.query(ImportJob).filter(ImportJob.id == job_id).first()
        if not job:
            raise ValueError(f"ImportJob with id {job_id} not found.")

        if job.status == "COMPLETED":
            return job

        job.status = "PROCESSING"
        job.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        file_path = Path(job.storage_path)
        if not file_path.exists():
            return self._fail_job(job, "FILE_NOT_FOUND", f"Stored file at '{job.storage_path}' could not be located.")

        try:
            inspector = HMISFileInspector(raw_dir=str(file_path.parent))
            inspection = inspector.inspect_file(file_path)

            if inspection.get("issues") and not inspection.get("sheets"):
                return self._fail_job(job, "UNSUPPORTED_FORMAT", "; ".join(inspection["issues"]))

            raw_obs, raw_facs, parse_errors = self._extract_observations_and_facilities(file_path, inspection)

            job.total_records = len(raw_obs) + len(parse_errors)
            
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

            job.status = "VALIDATED"
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
                existing_fac = self.db.query(Facility).filter(Facility.id == fac.facility_id).first()
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

            for obs_data in dedup_obs:
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
                    if val is not None or existing_obs.value is None:
                        existing_obs.value = val
                        existing_obs.value_type = val_type
                        existing_obs.source_file = job.original_filename
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
                        ingested_at=datetime.now(timezone.utc).isoformat()
                    )
                    self.db.add(new_obs)

                imported_count += 1

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

            job.records_imported = imported_count
            job.records_rejected = rejected_count
            has_errors = (rejected_count > 0 or any(l.severity == "ERROR" for l in job.error_logs))
            job.status = "COMPLETED_WITH_WARNINGS" if has_errors else "COMPLETED"
            job.completed_at = datetime.now(timezone.utc)
            job.updated_at = datetime.now(timezone.utc)

            self.db.commit()
            self.db.refresh(job)
            logger.info(f"Import job {job.job_code} completed successfully with status {job.status}.")
            return job

        except Exception as e:
            self.db.rollback()
            logger.exception(f"Import job {job.job_code} encountered uncaught processing exception: {str(e)}")
            return self._fail_job(job, "IMPORT_PROCESSING_FAILED", f"Processing error: {str(e)}")

    def _fail_job(self, job: ImportJob, error_code: str, message: str) -> ImportJob:
        job.status = "FAILED"
        job.completed_at = datetime.now(timezone.utc)
        job.updated_at = datetime.now(timezone.utc)

        err_log = ImportErrorLog(
            import_job_id=job.id,
            error_code=error_code,
            severity="CRITICAL",
            message=message
        )
        self.db.add(err_log)
        self.db.commit()
        self.db.refresh(job)
        return job

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
