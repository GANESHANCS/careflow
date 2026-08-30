import pytest
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.repositories.facility_repository import FacilityRepository
from backend.app.repositories.indicator_repository import IndicatorRepository
from backend.app.repositories.observation_repository import ObservationRepository


def test_facility_repository_filtering_and_pagination(db_session: Session):
    repo = FacilityRepository(db_session)

    fac1 = Facility(id="F1", facility_code="101", facility_name="DH Alpha", facility_type="DH", state="State_A", district="District_X", raw_facility_name="DH Alpha")
    fac2 = Facility(id="F2", facility_code="102", facility_name="PHC Beta", facility_type="PHC", state="State_A", district="District_Y", raw_facility_name="PHC Beta")
    fac3 = Facility(id="F3", facility_code="103", facility_name="CHC Gamma", facility_type="CHC", state="State_B", district="District_Z", raw_facility_name="CHC Gamma")
    db_session.add_all([fac1, fac2, fac3])
    db_session.commit()

    # Test filtering by State
    items_a, total_a = repo.list_facilities(state="State_A")
    assert total_a == 2
    assert len(items_a) == 2

    # Test filtering by District
    items_y, total_y = repo.list_facilities(district="District_Y")
    assert total_y == 1
    assert items_y[0].facility_name == "PHC Beta"

    # Test pagination limit
    items_p, total_p = repo.list_facilities(limit=1)
    assert len(items_p) == 1
    assert total_p == 3


def test_observation_repository_by_facility(db_session: Session):
    fac_repo = FacilityRepository(db_session)
    obs_repo = ObservationRepository(db_session)

    fac = Facility(id="F10", facility_code="110", facility_name="PHC Delta", facility_type="PHC", state="S", district="D", raw_facility_name="PHC Delta")
    ind = Indicator(id="IND_opd", code="opd_attendance", name="OPD", category="General", unit="count")
    db_session.add_all([fac, ind])
    db_session.commit()

    obs1 = Observation(id="O1", facility_id="F10", indicator_id="IND_opd", observation_date="2024-01-01", reporting_month="2024-01", value=100.0, value_type="VALID", source_file="f.csv", ingested_at="t")
    obs2 = Observation(id="O2", facility_id="F10", indicator_id="IND_opd", observation_date="2024-02-01", reporting_month="2024-02", value=120.0, value_type="VALID", source_file="f.csv", ingested_at="t")
    db_session.add_all([obs1, obs2])
    db_session.commit()

    obs_list, count = obs_repo.list_by_facility(facility_id="F10", indicator_code="opd_attendance")
    assert count == 2
    assert obs_list[0].reporting_month == "2024-01"
    assert obs_list[1].reporting_month == "2024-02"
