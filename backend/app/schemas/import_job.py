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
    records_imported: int
    records_rejected: int
    quality_score: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

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
