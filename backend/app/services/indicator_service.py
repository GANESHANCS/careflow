from typing import Optional, List
from sqlalchemy.orm import Session
from backend.app.repositories.indicator_repository import IndicatorRepository
from backend.app.db.models.indicator import Indicator


class IndicatorService:
    def __init__(self, db: Session):
        self.repo = IndicatorRepository(db)

    def list_indicators(self, category: Optional[str] = None) -> List[Indicator]:
        return self.repo.list_indicators(category=category)
