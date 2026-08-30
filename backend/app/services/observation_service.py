from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from backend.app.repositories.observation_repository import ObservationRepository
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.db.models.observation import Observation


class ObservationService:
    def __init__(self, db: Session):
        self.obs_repo = ObservationRepository(db)
        self.fac_repo = FacilityRepository(db)

    def get_facility_observations(
        self,
        facility_id: str,
        indicator_code: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Optional[Tuple[List[Observation], int]]:
        # Check facility existence first
        fac = self.fac_repo.get_by_id(facility_id)
        if not fac:
            return None
        return self.obs_repo.list_by_facility(
            facility_id=facility_id,
            indicator_code=indicator_code,
            start_month=start_month,
            end_month=end_month,
            skip=skip,
            limit=limit
        )
