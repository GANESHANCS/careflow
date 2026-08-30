from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.db.models.facility import Facility


class FacilityService:
    def __init__(self, db: Session):
        self.repo = FacilityRepository(db)

    def get_facility(self, facility_id: str) -> Optional[Facility]:
        return self.repo.get_by_id(facility_id)

    def list_facilities(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        facility_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Facility], int]:
        return self.repo.list_facilities(state=state, district=district, facility_type=facility_type, skip=skip, limit=limit)
