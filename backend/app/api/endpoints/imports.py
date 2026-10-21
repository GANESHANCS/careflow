from typing import Optional, List
import logging
from fastapi import APIRouter, Depends, File, UploadFile, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_batch import ImportBatch
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.user import User
from backend.app.api.deps import get_current_active_user, require_roles
from backend.app.schemas.import_job import (
    ImportJobResponse,
    ImportJobProgressResponse,
    ImportJobRetryResponse,
    ImportJobListResponse,
    ImportJobQualityResponse,
    ImportErrorLogResponse,
    ImportErrorLogListResponse,
    ImportRollbackRequest,
    ImportRollbackResponse,
    ImportBatchResponse,
    ImportBatchDetailResponse,
    ImportBatchListResponse,
    DirectoryScanTriggerResponse,
    ImportBatchRetryResponse,
)
from backend.app.services.imports.import_service import (
    HMISImportService,
    ImportRollbackDependencyConflictError,
    ImportRollbackIneligibleStatusError,
)
from backend.app.services.imports.validator import ImportValidationError
from backend.app.services.imports.worker import HMISImportWorker, notify_worker
from backend.app.services.imports.watcher import get_directory_watcher

logger = logging.getLogger("careflow.imports")
router = APIRouter()


def _get_job_by_code_or_id(db: Session, job_code: str) -> Optional[ImportJob]:
    """Helper to query ImportJob by job_code string or numeric ID."""
    if job_code.isdigit():
        return db.query(ImportJob).filter((ImportJob.job_code == job_code) | (ImportJob.id == int(job_code))).first()
    return db.query(ImportJob).filter(ImportJob.job_code == job_code).first()


@router.post("", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
def upload_hmis_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    sync: Optional[bool] = Query(None, description="When true, executes synchronously; otherwise queues for background worker."),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN", "ANALYST"]))
):
    """
    Uploads an HMIS spreadsheet (.csv, .xlsx, .xls) and triggers the ingestion & quality pipeline.
    Accessible only to ADMIN and ANALYST roles.
    """
    service = HMISImportService(db)

    try:
        content = file.file.read()
        job, is_duplicate = service.create_import_job(
            original_filename=file.filename or "uploaded_file.csv",
            content=content,
            mime_type=file.content_type
        )
    except ImportValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except Exception as e:
        logger.exception(f"Import upload creation failed for file '{file.filename}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while uploading and queuing the import file. Please check server logs."
        )

    if is_duplicate:
        # File is identical to an existing job - return idempotent response
        return job

    if sync is True:
        try:
            service.process_import_job(job.id)
        except Exception as e:
            logger.exception(f"Import job processing failed for job {job.job_code}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An error occurred during dataset processing and persistence. The import job could not be completed."
            )
        db.refresh(job)
        return job

    # Asynchronous Background Execution (Phase 9A)
    worker = HMISImportWorker()
    background_tasks.add_task(worker.process_job_by_id, job.id)
    notify_worker()
    db.refresh(job)
    return job


def _batch_progress_percent(batch: ImportBatch) -> float:
    if batch.total_files > 0:
        return round(min(100.0, max(0.0, (batch.processed_files / batch.total_files) * 100.0)), 1)
    if batch.status in ("COMPLETED", "PARTIALLY_FAILED", "FAILED", "CANCELLED"):
        return 100.0
    return 0.0


# -------------------------------------------------------------------
# PHASE 9B BATCH MANAGEMENT & MONITORING ENDPOINTS
# -------------------------------------------------------------------

@router.get("/batches", response_model=ImportBatchListResponse)
def list_import_batches(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    source_filter: Optional[str] = Query(None, alias="source"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns paginated history of automated and manual HMIS import batches.
    Accessible to ADMIN, ANALYST, and VIEWER roles.
    """
    query = db.query(ImportBatch)

    if status_filter:
        query = query.filter(ImportBatch.status == status_filter.upper())

    if source_filter:
        query = query.filter(ImportBatch.source == source_filter.upper())

    total = query.count()
    items = query.order_by(ImportBatch.created_at.desc()).offset(skip).limit(limit).all()

    batch_items = []
    for b in items:
        resp = ImportBatchResponse.model_validate(b)
        resp.progress_percent = _batch_progress_percent(b)
        batch_items.append(resp)

    return ImportBatchListResponse(
        total=total,
        items=batch_items,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/batches/scan", response_model=DirectoryScanTriggerResponse, status_code=status.HTTP_200_OK)
def trigger_directory_scan(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Manually triggers an on-demand scan of the incoming HMIS directory.
    Discovers eligible files, creates an import batch and jobs, and enqueues work.
    Restricted to ADMIN role.
    """
    watcher = get_directory_watcher()
    try:
        results = watcher.scan_once()
        enqueued = sum(1 for r in results if r.get("status") == "ENQUEUED")
        return DirectoryScanTriggerResponse(
            files_discovered=len(results),
            jobs_created=enqueued,
            batch_code=watcher.last_batch_code,
            message=f"Directory scan completed: {len(results)} file(s) evaluated, {enqueued} job(s) created."
        )
    except Exception as e:
        logger.exception(f"Error during manual directory scan trigger: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Directory scan failed: {str(e)}"
        )


@router.get("/batches/{batch_code}", response_model=ImportBatchDetailResponse)
def get_import_batch_detail(
    batch_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves detailed execution status, aggregated metrics, and constituent jobs for an import batch.
    """
    batch = db.query(ImportBatch).filter(
        (ImportBatch.batch_code == batch_code) | (ImportBatch.id == int(batch_code))
        if batch_code.isdigit() else (ImportBatch.batch_code == batch_code)
    ).first()

    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import batch '{batch_code}' not found."
        )

    detail = ImportBatchDetailResponse.model_validate(batch)
    detail.progress_percent = _batch_progress_percent(batch)
    return detail


@router.post("/batches/{batch_code}/retry", response_model=ImportBatchRetryResponse, status_code=status.HTTP_200_OK)
def retry_import_batch(
    batch_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Retries all failed or stalled jobs in an import batch. Restricted to ADMIN role.
    """
    service = HMISImportService(db)
    try:
        batch, retried_count = service.retry_import_batch(batch_code, requested_by=current_user.username)
        notify_worker()
        return ImportBatchRetryResponse(
            batch_code=batch.batch_code,
            status=batch.status,
            retried_jobs=retried_count,
            message=f"Batch '{batch.batch_code}': {retried_count} job(s) re-queued for processing."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Retry failed unexpectedly for batch '{batch_code}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error retrying batch: {str(e)}"
        )


@router.post("/batches/{batch_code}/cancel", response_model=ImportBatchResponse, status_code=status.HTTP_200_OK)
def cancel_import_batch(
    batch_code: str,
    payload: Optional[ImportRollbackRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Cancels all in-flight jobs in an import batch. Restricted to ADMIN role.
    """
    service = HMISImportService(db)
    reason = payload.reason if payload else None
    try:
        batch = service.cancel_import_batch(batch_code, cancelled_by=current_user.username, reason=reason)
        resp = ImportBatchResponse.model_validate(batch)
        resp.progress_percent = _batch_progress_percent(batch)
        return resp
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception(f"Cancel failed unexpectedly for batch '{batch_code}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error cancelling batch: {str(e)}"
        )


@router.get("/{job_code}/status", response_model=ImportJobProgressResponse)
def get_import_job_progress(
    job_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves live processing status, progress counters, and error summaries for an import job.
    Accessible to ADMIN, ANALYST, and VIEWER roles.
    """
    job = _get_job_by_code_or_id(db, job_code)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_code}' not found."
        )

    pct = 0.0
    if job.total_records > 0:
        pct = round(min(100.0, max(0.0, (job.processed_records / job.total_records) * 100.0)), 1)
    elif job.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS"):
        pct = 100.0

    return ImportJobProgressResponse(
        job_code=job.job_code,
        status=job.status,
        total_records=job.total_records,
        processed_records=job.processed_records,
        records_imported=job.records_imported,
        records_rejected=job.records_rejected,
        progress_percent=pct,
        heartbeat_at=job.heartbeat_at,
        error_summary=job.error_summary,
        schema_profile=job.schema_profile
    )


@router.post("/{job_code}/retry", response_model=ImportJobRetryResponse, status_code=status.HTTP_200_OK)
def retry_import_job(
    job_code: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Retries an eligible failed import job, safely cleaning up partial state
    and re-queuing for worker processing. Restricted to ADMIN role.
    """
    service = HMISImportService(db)
    try:
        job = service.retry_import_job(job_code, requested_by=current_user.username)
        worker = HMISImportWorker()
        background_tasks.add_task(worker.process_job_by_id, job.id)
        notify_worker()
        return ImportJobRetryResponse(
            job_code=job.job_code,
            status=job.status,
            retry_count=job.retry_count,
            message=f"Import job '{job.job_code}' successfully re-queued for processing."
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Retry failed unexpectedly for job '{job_code}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error retrying job: {str(e)}")


@router.post("/{job_code}/cancel", response_model=ImportJobResponse, status_code=status.HTTP_200_OK)
def cancel_import_job(
    job_code: str,
    payload: Optional[ImportRollbackRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Cancels a QUEUED import job prior to worker claiming. Restricted to ADMIN role.
    """
    service = HMISImportService(db)
    reason = payload.reason if payload else None
    try:
        job = service.cancel_import_job(job_code, cancelled_by=current_user.username, reason=reason)
        return job
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.exception(f"Cancel failed unexpectedly for job '{job_code}': {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Unexpected error cancelling job: {str(e)}")


@router.get("", response_model=ImportJobListResponse)
def list_import_jobs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Returns paginated history of HMIS import jobs.
    Accessible to ADMIN, ANALYST, and VIEWER roles.
    """
    query = db.query(ImportJob)

    if status_filter:
        query = query.filter(ImportJob.status == status_filter.upper())

    if search:
        query = query.filter(ImportJob.original_filename.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(ImportJob.created_at.desc()).offset(skip).limit(limit).all()

    return ImportJobListResponse(
        total=total,
        items=items,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.get("/{job_code}", response_model=ImportJobResponse)
def get_import_job_detail(
    job_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves detailed execution status and record metrics for a specific import job.
    """
    job = _get_job_by_code_or_id(db, job_code)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_code}' not found."
        )
    return job


@router.get("/{job_code}/quality", response_model=ImportJobQualityResponse)
def get_import_job_quality(
    job_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves dataset quality audit scores and diagnostic findings for an import job.
    """
    job = _get_job_by_code_or_id(db, job_code)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_code}' not found."
        )

    # Extract quality findings logged during processing
    logs = db.query(ImportErrorLog).filter(ImportErrorLog.import_job_id == job.id).all()

    severity_counts = {"CRITICAL": 0, "WARNING": 0, "ERROR": 0, "INFO": 0}
    findings = []

    for log in logs:
        severity_counts[log.severity] = severity_counts.get(log.severity, 0) + 1
        findings.append({
            "code": log.error_code,
            "severity": log.severity,
            "message": log.message,
            "row": log.source_row,
            "sheet": log.source_sheet
        })

    score = job.quality_score if job.quality_score is not None else 100.0

    return ImportJobQualityResponse(
        job_code=job.job_code,
        overall_quality_score=round(score, 1),
        total_issues=len(logs),
        severity_counts=severity_counts,
        category_scores={
            "completeness": round(score, 1),
            "validity": round(score, 1),
            "consistency": round(score, 1),
            "timeliness": round(score, 1),
            "accuracy": round(score, 1)
        },
        findings=findings
    )


@router.get("/{job_code}/errors", response_model=ImportErrorLogListResponse)
def get_import_job_errors(
    job_code: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Retrieves paginated audit error & warning logs for an import job.
    """
    job = _get_job_by_code_or_id(db, job_code)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job '{job_code}' not found."
        )

    query = db.query(ImportErrorLog).filter(ImportErrorLog.import_job_id == job.id)
    total = query.count()
    items = query.order_by(ImportErrorLog.id.asc()).offset(skip).limit(limit).all()

    return ImportErrorLogListResponse(
        total=total,
        items=items,
        page=(skip // limit) + 1 if limit > 0 else 1,
        page_size=limit
    )


@router.post("/{job_code}/rollback", response_model=ImportRollbackResponse, status_code=status.HTTP_200_OK)
def rollback_import_job(
    job_code: str,
    payload: Optional[ImportRollbackRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["ADMIN"]))
):
    """
    Safely rolls back an imported HMIS dataset, reverting created and updated observations
    to their previous states, deleting generated data quality logs, and setting status to ROLLED_BACK.
    Restricted to ADMIN role.
    """
    service = HMISImportService(db)
    reason = payload.reason if payload else None

    try:
        result = service.rollback_import_job(
            job_identifier=job_code,
            rolled_back_by=current_user.username,
            reason=reason
        )
        return ImportRollbackResponse(**result)

    except ImportRollbackDependencyConflictError as e:
        logger.warning(f"Rollback rejected for job '{job_code}' due to dependent active imports: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=e.message
        )
    except ImportRollbackIneligibleStatusError as e:
        logger.warning(f"Rollback rejected for job '{job_code}' due to ineligible status: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"Rollback failed unexpectedly for job '{job_code}': {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during import rollback: {str(e)}"
        )
