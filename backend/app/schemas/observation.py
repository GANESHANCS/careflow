from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class ObservationResponse(BaseModel):
    id: str
    facility_id: str
    indicator_id: str
    observation_date: str
    reporting_month: str
    value: Optional[float] = None
    value_type: str
    validation_status: str
    source_file: str

    model_config = ConfigDict(from_attributes=True)


class ObservationListResponse(BaseModel):
    facility_id: str
    items: List[ObservationResponse]
    total: int
    skip: int
    limit: int
