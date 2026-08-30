from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.app.db.models.observation import Observation
from backend.app.db.models.indicator import Indicator


class ObservationRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_facility(
        self,
        facility_id: str,
        indicator_code: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Observation], int]:
        query = self.db.query(Observation).filter(Observation.facility_id == facility_id)

        if indicator_code:
            query = query.join(Indicator).filter(Indicator.code == indicator_code)

        if start_month:
            query = query.filter(Observation.reporting_month >= start_month)

        if end_month:
            query = query.filter(Observation.reporting_month <= end_month)

        total = query.count()
        observations = query.order_by(Observation.reporting_month.asc()).offset(skip).limit(limit).all()
        return observations, total
