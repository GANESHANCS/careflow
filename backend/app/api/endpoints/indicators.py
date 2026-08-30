from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.indicator_service import IndicatorService
from backend.app.schemas.indicator import IndicatorListResponse

router = APIRouter()


@router.get("/indicators", response_model=IndicatorListResponse)
def list_indicators(
    category: Optional[str] = Query(None, description="Filter indicators by operational category"),
    db: Session = Depends(get_db)
):
    """
    List registered HMIS indicators.
    """
    service = IndicatorService(db)
    items = service.list_indicators(category=category)
    return IndicatorListResponse(items=items, total=len(items))
