from typing import Optional, List
import logging
from fastapi import APIRouter, Depends, File, UploadFile, Query, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.user import User
from backend.app.api.deps import get_current_active_user, require_roles
from backend.app.schemas.import_job import (
    ImportJobResponse,
    ImportJobListResponse,
    ImportJobQualityResponse,
    ImportErrorLogResponse,
    ImportErrorLogListResponse,
)
from backend.app.services.imports.import_service import HMISImportService
from backend.app.services.imports.validator import ImportValidationError

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
        logger.exception(f"Import upload creation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import upload failure: {str(e)}"
        )

    if is_duplicate:
        # File is identical to an existing job - return idempotent response
        return job

    # Process job (execute synchronously)
    try:
        service.process_import_job(job.id)
    except Exception as e:
        logger.exception(f"Import job processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import processing failure: {str(e)}"
        )

    # Refresh job from DB to return completed status
    db.refresh(job)
    return job


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
