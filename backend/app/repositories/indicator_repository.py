from typing import List, Optional
from sqlalchemy.orm import Session
from backend.app.db.models.indicator import Indicator


class IndicatorRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, indicator_id: str) -> Optional[Indicator]:
        return self.db.query(Indicator).filter(Indicator.id == indicator_id).first()

    def get_by_code(self, code: str) -> Optional[Indicator]:
        return self.db.query(Indicator).filter(Indicator.code == code).first()

    def list_indicators(
        self,
        category: Optional[str] = None,
        active_only: bool = True
    ) -> List[Indicator]:
        query = self.db.query(Indicator)
        if active_only:
            query = query.filter(Indicator.active == True)
        if category:
            query = query.filter(Indicator.category.ilike(f"%{category}%"))
        return query.order_by(Indicator.code).all()
