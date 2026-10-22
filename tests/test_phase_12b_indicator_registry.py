import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus


@pytest.fixture
def seed_registry_test_data(db_session: Session):
    """Seeds a representative mix of verified, stock, and unmapped parameters."""
    obs = [
        # Verified clinical indicators
        DistrictObservation(
            id="DOBS_REG_1",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="1.1",
            parameter_name="Total number of pregnant women registered for ANC",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=120.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        DistrictObservation(
            id="DOBS_REG_2",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.12.1",
            parameter_name="Outpatient attendance - All",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=340.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        # Stock metric (unmapped clinical indicator, but recognized stock count)
        DistrictObservation(
            id="DOBS_REG_3",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="14.01",
            parameter_name="Sub Centres functional in Government buildings",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=15.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
        # Pure unmapped raw HMIS parameter
        DistrictObservation(
            id="DOBS_REG_4",
            state="Tamil Nadu",
            district="Ariyalur",
            s_no="99.99.1",
            parameter_name="Ad-hoc Administrative Census Item",
            subgroup_type="TOTAL",
            is_subgroup_total=True,
            financial_year="2015-16",
            reporting_month="2015-04",
            observation_date="2015-04-01",
            value=5.0,
            value_type="VALID",
            validation_status="VALIDATED",
            source_file="test.csv",
            ingested_at="2026-10-21T00:00:00Z"
        ),
    ]
    db_session.add_all(obs)
    db_session.commit()


# ---------------------------------------------------------------------------
# Unit Tests: IndicatorMappingRegistry Logic
# ---------------------------------------------------------------------------

def test_registry_verified_clinical_mappings():
    # Test ANC registration (1.1)
    anc = IndicatorMappingRegistry.get_mapping("1.1", "Total pregnant women registered for ANC")
    assert anc.status == MappingStatus.VERIFIED
    assert anc.canonical_id == "IND_antenatal_visits"
    assert "ANC" in anc.canonical_name
    assert "Maternal Health" in anc.category
    assert anc.unit == "visits"
    assert "1.1" in anc.rationale
    assert anc.clinical_definition is not None
    assert "MoHFW" in anc.provenance
    assert anc.is_stock_metric is False

    # Test OPD attendance (14.12.1)
    opd = IndicatorMappingRegistry.get_mapping("14.12.1")
    assert opd.status == MappingStatus.VERIFIED
    assert opd.canonical_id == "IND_opd_attendance"
    assert opd.is_stock_metric is False

    # Test IPD admissions (14.10.1.c) - classified as AMBIGUOUS due to demographic slice partitioning
    ipd = IndicatorMappingRegistry.get_mapping("14.10.1.c")
    assert ipd.status == MappingStatus.AMBIGUOUS
    assert ipd.canonical_id == "IND_inpatient_admissions"
    assert "AMBIGUOUS" in ipd.rationale
    assert ipd.unit == "admissions"

    # Test Immunisation (10.1.13.c)
    imm = IndicatorMappingRegistry.get_mapping("10.1.13.c")
    assert imm.status == MappingStatus.VERIFIED
    assert imm.canonical_id == "IND_immunisation"
    assert "Universal Immunization Programme" in imm.provenance


def test_registry_stock_metric_classification():
    stock = IndicatorMappingRegistry.get_mapping("14.01", "Sub Centres functional")
    assert stock.is_stock_metric is True
    # Stock metric without clinical indicator mapping remains UNMAPPED
    assert stock.status == MappingStatus.UNMAPPED
    assert stock.canonical_id is None


def test_registry_unmapped_parameter_handling():
    unmapped = IndicatorMappingRegistry.get_mapping("88.88.88", "Custom Local Program Counter")
    assert unmapped.status == MappingStatus.UNMAPPED
    assert unmapped.canonical_id is None
    assert unmapped.canonical_name is None
    assert "No validated canonical CAREFlow clinical crosswalk" in unmapped.rationale


# ---------------------------------------------------------------------------
# API Tests: Indicator Registry & Audit Endpoints
# ---------------------------------------------------------------------------

def test_registry_endpoints_unauthenticated(client: TestClient, seed_registry_test_data):
    res_reg = client.get("/api/analytics/district/indicators/registry")
    assert res_reg.status_code == 401

    res_aud = client.get("/api/analytics/district/indicators/audit")
    assert res_aud.status_code == 401


def test_indicator_registry_endpoint(client: TestClient, auth_headers: dict, seed_registry_test_data):
    res = client.get("/api/analytics/district/indicators/registry", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_items"] == 4
    assert data["verified_count"] == 2  # 1.1 and 14.12.1
    assert data["unmapped_count"] == 2  # 14.01 and 99.99.1

    # Filter by VERIFIED
    res_verified = client.get("/api/analytics/district/indicators/registry?status=VERIFIED", headers=auth_headers)
    assert res_verified.status_code == 200
    v_data = res_verified.json()
    assert len(v_data["items"]) == 2
    assert all(item["status"] == "VERIFIED" for item in v_data["items"])

    # Filter by UNMAPPED
    res_unmapped = client.get("/api/analytics/district/indicators/registry?status=UNMAPPED", headers=auth_headers)
    assert res_unmapped.status_code == 200
    u_data = res_unmapped.json()
    assert len(u_data["items"]) == 2
    assert all(item["status"] == "UNMAPPED" for item in u_data["items"])


def test_indicator_audit_report_endpoint(client: TestClient, auth_headers: dict, seed_registry_test_data):
    res = client.get("/api/analytics/district/indicators/audit", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_parameters_observed"] == 4
    assert data["verified_mappings_count"] == 2
    assert data["unmapped_parameters_count"] == 2
    assert data["verified_percentage"] == 50.0
    assert data["unmapped_percentage"] == 50.0
    assert data["stock_metrics_count"] == 1  # 14.01
    assert len(data["verified_mappings"]) == 2
    assert "strict non-fabrication" in data["governance_note"]
    assert "audit_timestamp" in data
