from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.db.models.facility import Facility


class FacilityRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, facility_id: str) -> Optional[Facility]:
        return self.db.query(Facility).filter(Facility.id == facility_id).first()

    def get_by_code(self, facility_code: str) -> Optional[Facility]:
        return self.db.query(Facility).filter(Facility.facility_code == facility_code).first()

    def list_facilities(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        facility_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Tuple[List[Facility], int]:
        query = self.db.query(Facility)

        if state:
            query = query.filter(Facility.state.ilike(f"%{state}%"))
        if district:
            query = query.filter(Facility.district.ilike(f"%{district}%"))
        if facility_type:
            query = query.filter(Facility.facility_type == facility_type)

        total = query.count()
        facilities = query.offset(skip).limit(limit).all()
        return facilities, total
