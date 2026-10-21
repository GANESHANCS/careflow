from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class ImportErrorLogResponse(BaseModel):
    id: int
    import_job_id: int
    source_row: Optional[int] = None
    source_sheet: Optional[str] = None
    error_code: str
    severity: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ImportErrorLogListResponse(BaseModel):
    total: int
    items: List[ImportErrorLogResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class ImportJobResponse(BaseModel):
    id: int
    job_code: str
    original_filename: str
    file_size_bytes: Optional[int] = None
    mime_type: Optional[str] = None
    file_hash: Optional[str] = None
    status: str
    total_records: int
    processed_records: int = 0
    records_imported: int
    records_rejected: int
    quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    claimed_at: Optional[datetime] = None
    claimed_by: Optional[str] = None
    heartbeat_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_summary: Optional[str] = None
    schema_profile: Optional[str] = "mohfw_standard_v2"
    batch_id: Optional[int] = None
    rolled_back_at: Optional[datetime] = None
    rolled_back_by: Optional[str] = None
    rollback_reason: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_records <= 0:
            return 100.0 if self.status in ("COMPLETED", "COMPLETED_WITH_WARNINGS") else 0.0
        pct = (self.processed_records / self.total_records) * 100.0
        return round(min(100.0, max(0.0, pct)), 1)

    model_config = ConfigDict(from_attributes=True)


class ImportBatchResponse(BaseModel):
    id: int
    batch_code: str
    source: str
    status: str
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    total_records: int
    imported_records: int
    rejected_records: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    initiated_by: Optional[str] = None
    error_summary: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        if self.total_files <= 0:
            return 100.0 if self.status in ("COMPLETED", "PARTIALLY_FAILED", "FAILED") else 0.0
        pct = (self.processed_files / self.total_files) * 100.0
        return round(min(100.0, max(0.0, pct)), 1)

    model_config = ConfigDict(from_attributes=True)


class ImportBatchDetailResponse(ImportBatchResponse):
    items: List[ImportJobResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ImportBatchListResponse(BaseModel):
    total: int
    items: List[ImportBatchResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class DirectoryScanTriggerResponse(BaseModel):
    scanned_files: int
    enqueued_files: int
    quarantined_files: int
    duplicate_files: int
    batch_code: Optional[str] = None
    message: str


class ImportJobProgressResponse(BaseModel):
    job_code: str
    status: str
    total_records: int
    processed_records: int
    records_imported: int
    records_rejected: int
    progress_percent: float
    heartbeat_at: Optional[datetime] = None
    error_summary: Optional[str] = None
    schema_profile: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ImportJobRetryResponse(BaseModel):
    job_code: str
    status: str
    retry_count: int
    message: str

    model_config = ConfigDict(from_attributes=True)


class ImportRollbackRequest(BaseModel):
    reason: Optional[str] = None


class ImportRollbackResponse(BaseModel):
    job_code: str
    status: str
    records_deleted: int
    records_restored: int
    records_unchanged: int
    rolled_back_at: datetime
    rolled_back_by: Optional[str] = None
    message: str

    model_config = ConfigDict(from_attributes=True)


class ImportJobListResponse(BaseModel):
    total: int
    items: List[ImportJobResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class QualitySeverityCounts(BaseModel):
    CRITICAL: int = 0
    WARNING: int = 0
    INFO: int = 0


class QualityCategoryBreakdown(BaseModel):
    completeness: float = 100.0
    validity: float = 100.0
    consistency: float = 100.0
    timeliness: float = 100.0
    accuracy: float = 100.0


class ImportJobQualityResponse(BaseModel):
    job_code: str
    overall_quality_score: float
    total_issues: int
    severity_counts: Dict[str, int]
    category_scores: Dict[str, float]
    findings: List[Dict[str, Any]]


class ImportBatchResponse(BaseModel):
    id: int
    batch_code: str
    source: str
    status: str
    total_files: int
    processed_files: int
    successful_files: int
    failed_files: int
    total_records: int
    imported_records: int
    rejected_records: int
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    initiated_by: Optional[str] = None
    error_summary: Optional[str] = None
    progress_percent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class ImportBatchDetailResponse(ImportBatchResponse):
    import_jobs: List[ImportJobResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ImportBatchListResponse(BaseModel):
    total: int
    items: List[ImportBatchResponse]
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


class DirectoryScanTriggerResponse(BaseModel):
    files_discovered: int
    jobs_created: int
    batch_code: Optional[str] = None
    message: str


class ImportBatchRetryResponse(BaseModel):
    batch_code: str
    status: str
    retried_jobs: int
    message: str
