from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.db.models.district_observation import DistrictObservation


class DistrictObservationRepository:
    """
    Data access repository for DistrictObservation entities.
    Provides querying, filtering, and aggregation across district-level HMIS datasets.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, obs_id: str) -> Optional[DistrictObservation]:
        """Fetch a district observation by its primary key ID."""
        return self.db.query(DistrictObservation).filter(DistrictObservation.id == obs_id).first()

    def get_by_natural_key(
        self,
        district: str,
        s_no: str,
        subgroup_type: str,
        reporting_month: str
    ) -> Optional[DistrictObservation]:
        """Fetch a district observation by its unique natural key."""
        return self.db.query(DistrictObservation).filter(
            DistrictObservation.district == district,
            DistrictObservation.s_no == s_no,
            DistrictObservation.subgroup_type == subgroup_type,
            DistrictObservation.reporting_month == reporting_month
        ).first()

    def list_observations(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        s_no: Optional[str] = None,
        indicator_id: Optional[str] = None,
        subgroup_type: Optional[str] = None,
        is_subgroup_total: Optional[bool] = None,
        financial_year: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[DistrictObservation], int]:
        """
        Query district observations with dynamic filtering and pagination.
        """
        query = self.db.query(DistrictObservation)

        if state:
            query = query.filter(DistrictObservation.state.ilike(f"%{state}%"))
        if district:
            query = query.filter(DistrictObservation.district.ilike(f"%{district}%"))
        if s_no:
            query = query.filter(DistrictObservation.s_no == s_no)
        if indicator_id:
            query = query.filter(DistrictObservation.indicator_id == indicator_id)
        if subgroup_type:
            query = query.filter(DistrictObservation.subgroup_type == subgroup_type)
        if is_subgroup_total is not None:
            query = query.filter(DistrictObservation.is_subgroup_total == is_subgroup_total)
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year)
        if start_month:
            query = query.filter(DistrictObservation.reporting_month >= start_month)
        if end_month:
            query = query.filter(DistrictObservation.reporting_month <= end_month)

        total = query.count()
        items = query.order_by(
            DistrictObservation.reporting_month.asc(),
            DistrictObservation.district.asc(),
            DistrictObservation.s_no.asc()
        ).offset(skip).limit(limit).all()

        return items, total

    def list_distinct_districts(self, state: Optional[str] = None) -> List[str]:
        """Return sorted list of distinct district names."""
        query = self.db.query(DistrictObservation.district).distinct()
        if state:
            query = query.filter(DistrictObservation.state.ilike(f"%{state}%"))
        return sorted([r[0] for r in query.all() if r[0]])

    def list_distinct_parameters(self) -> List[Dict[str, str]]:
        """Return list of distinct parameters (s_no and parameter_name)."""
        rows = (
            self.db.query(DistrictObservation.s_no, DistrictObservation.parameter_name)
            .distinct()
            .order_by(DistrictObservation.s_no.asc())
            .all()
        )
        return [{"s_no": r[0], "parameter_name": r[1]} for r in rows]

    def add(self, obs: DistrictObservation) -> DistrictObservation:
        """Add and flush a single district observation."""
        self.db.add(obs)
        self.db.flush()
        return obs

    def bulk_add(self, obs_list: List[DistrictObservation]) -> int:
        """Bulk add a list of district observations."""
        self.db.add_all(obs_list)
        self.db.flush()
        return len(obs_list)
