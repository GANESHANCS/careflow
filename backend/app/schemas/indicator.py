from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class IndicatorResponse(BaseModel):
    id: str
    code: str
    name: str
    description: Optional[str] = None
    category: str
    unit: str
    source_system: str
    active: bool

    model_config = ConfigDict(from_attributes=True)


class IndicatorListResponse(BaseModel):
    items: List[IndicatorResponse]
    total: int
