from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class FacilityResponse(BaseModel):
    id: str
    facility_code: Optional[str] = None
    facility_name: str
    facility_type: str
    state: str
    district: str
    sub_district: Optional[str] = None
    raw_facility_name: str
    raw_district_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class FacilityListResponse(BaseModel):
    items: List[FacilityResponse]
    total: int
    skip: int
    limit: int
