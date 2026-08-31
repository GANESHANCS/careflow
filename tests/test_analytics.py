import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.data_quality import DataQualityLog
from backend.app.services.analytics.change_calc import calculate_mom_change, calculate_yoy_change
from backend.app.services.analytics.summary import ExecutiveSummaryService
from backend.app.services.analytics.trends import TimeSeriesTrendsService
from backend.app.services.analytics.regional import RegionalAnalyticsService
from backend.app.services.analytics.facility import FacilityAnalyticsService
from backend.app.services.analytics.comparison import FacilityComparisonService
from backend.app.services.analytics.data_quality import DataQualityAnalyticsService


def test_change_calculations():
    # Valid positive growth
    assert calculate_mom_change(120.0, 100.0) == 20.0
    # Valid negative growth
    assert calculate_mom_change(80.0, 100.0) == -20.0
    # Zero denominator safe check (returns None, not ZeroDivisionError!)
    assert calculate_mom_change(50.0, 0.0) is None
    # Missing values
    assert calculate_mom_change(None, 100.0) is None
    assert calculate_mom_change(100.0, None) is None


def test_executive_summary_service(db_session: Session):
    fac1 = Facility(id="FC_S1", facility_code="S1", facility_name="DH S1", facility_type="DH", state="StateX", district="DistY", raw_facility_name="DH S1")
    fac2 = Facility(id="FC_S2", facility_code="S2", facility_name="PHC S2", facility_type="PHC", state="StateX", district="DistY", raw_facility_name="PHC S2")
    ind = Indicator(id="IND_opd", code="opd_attendance", name="OPD Attendance", category="General", unit="visits")
    db_session.add_all([fac1, fac2, ind])
    db_session.commit()

    obs1 = Observation(id="O1", facility_id="FC_S1", indicator_id="IND_opd", observation_date="2024-04-01", reporting_month="2024-04", value=500.0, value_type="VALID", source_file="s.csv", ingested_at="t")
    obs2 = Observation(id="O2", facility_id="FC_S2", indicator_id="IND_opd", observation_date="2024-04-01", reporting_month="2024-04", value=300.0, value_type="VALID", source_file="s.csv", ingested_at="t")
    db_session.add_all([obs1, obs2])
    db_session.commit()

    service = ExecutiveSummaryService(db_session)
    summary = service.get_summary(state="StateX")

    assert summary["total_facilities"] == 2
    assert summary["reporting_facilities"] == 2
    assert summary["reporting_completeness_pct"] == 100.0
    assert summary["latest_period"] == "2024-04"
    assert summary["totals_by_indicator"]["opd_attendance"] == 800.0


def test_monthly_trends_service(db_session: Session):
    fac = Facility(id="FC_T1", facility_code="T1", facility_name="DH T1", facility_type="DH", state="StateT", district="DistT", raw_facility_name="DH T1")
    ind = Indicator(id="IND_ipd", code="inpatient_admissions", name="IPD", category="General", unit="admissions")
    db_session.add_all([fac, ind])
    db_session.commit()

    o1 = Observation(id="OT1", facility_id="FC_T1", indicator_id="IND_ipd", observation_date="2024-01-01", reporting_month="2024-01", value=50.0, value_type="VALID", source_file="f", ingested_at="t")
    o2 = Observation(id="OT2", facility_id="FC_T1", indicator_id="IND_ipd", observation_date="2024-02-01", reporting_month="2024-02", value=75.0, value_type="VALID", source_file="f", ingested_at="t")
    db_session.add_all([o1, o2])
    db_session.commit()

    service = TimeSeriesTrendsService(db_session)
    trends = service.get_monthly_trends(indicator_code="inpatient_admissions")

    assert trends["total_facilities"] == 1
    assert len(trends["series"]) == 2
    assert trends["series"][0]["reporting_month"] == "2024-01"
    assert trends["series"][0]["total_value"] == 50.0
    assert trends["series"][1]["reporting_month"] == "2024-02"
    assert trends["series"][1]["total_value"] == 75.0


def test_regional_analytics_service(db_session: Session):
    f1 = Facility(id="FR1", facility_code="R1", facility_name="F1", facility_type="DH", state="StateR", district="DistA", raw_facility_name="F1")
    f2 = Facility(id="FR2", facility_code="R2", facility_name="F2", facility_type="PHC", state="StateR", district="DistB", raw_facility_name="F2")
    ind = Indicator(id="IND_del", code="institutional_deliveries", name="Deliveries", category="Maternal", unit="deliveries")
    db_session.add_all([f1, f2, ind])
    db_session.commit()

    o1 = Observation(id="OR1", facility_id="FR1", indicator_id="IND_del", observation_date="2024-03-01", reporting_month="2024-03", value=100.0, value_type="VALID", source_file="f", ingested_at="t")
    o2 = Observation(id="OR2", facility_id="FR2", indicator_id="IND_del", observation_date="2024-03-01", reporting_month="2024-03", value=40.0, value_type="VALID", source_file="f", ingested_at="t")
    db_session.add_all([o1, o2])
    db_session.commit()

    service = RegionalAnalyticsService(db_session)
    res = service.get_regional_analytics(level="district", indicator_code="institutional_deliveries")

    assert res["level"] == "district"
    assert len(res["regions"]) == 2
    top_region = res["regions"][0]
    assert top_region["region_name"] == "DistA"
    assert top_region["total_utilization"] == 100.0


def test_facility_analytics_service(db_session: Session):
    f = Facility(id="FF1", facility_code="F1", facility_name="Fac 1", facility_type="DH", state="S", district="D", raw_facility_name="Fac 1")
    ind = Indicator(id="IND_anc", code="antenatal_visits", name="ANC", category="Maternal", unit="visits")
    db_session.add_all([f, ind])
    db_session.commit()

    o1 = Observation(id="OF1", facility_id="FF1", indicator_id="IND_anc", observation_date="2024-01-01", reporting_month="2024-01", value=200.0, value_type="VALID", source_file="f", ingested_at="t")
    o2 = Observation(id="OF2", facility_id="FF1", indicator_id="IND_anc", observation_date="2024-03-01", reporting_month="2024-03", value=250.0, value_type="VALID", source_file="f", ingested_at="t")
    db_session.add_all([o1, o2])
    db_session.commit()

    service = FacilityAnalyticsService(db_session)
    res = service.get_facility_analytics(facility_id="FF1")

    assert res is not None
    assert res["facility_name"] == "Fac 1"
    # Month 2024-02 was skipped, so missing_months should detect it
    assert "2024-02" in res["missing_months"]


def test_facility_comparison_service(db_session: Session):
    f1 = Facility(id="FCMP1", facility_code="CMP1", facility_name="Fac CMP 1", facility_type="DH", state="S", district="D", raw_facility_name="Fac CMP 1")
    f2 = Facility(id="FCMP2", facility_code="CMP2", facility_name="Fac CMP 2", facility_type="PHC", state="S", district="D", raw_facility_name="Fac CMP 2")
    ind = Indicator(id="IND_pnc", code="postnatal_visits", name="PNC", category="Maternal", unit="visits")
    db_session.add_all([f1, f2, ind])
    db_session.commit()

    o1 = Observation(id="OCMP1", facility_id="FCMP1", indicator_id="IND_pnc", observation_date="2024-04-01", reporting_month="2024-04", value=300.0, value_type="VALID", source_file="f", ingested_at="t")
    o2 = Observation(id="OCMP2", facility_id="FCMP2", indicator_id="IND_pnc", observation_date="2024-04-01", reporting_month="2024-04", value=150.0, value_type="VALID", source_file="f", ingested_at="t")
    db_session.add_all([o1, o2])
    db_session.commit()

    service = FacilityComparisonService(db_session)
    res = service.compare_facilities(facility_ids=["FCMP1", "FCMP2"], indicator_code="postnatal_visits")

    assert len(res["facilities"]) == 2
    assert res["facilities"][0]["latest_value"] == 300.0
    assert res["facilities"][1]["latest_value"] == 150.0


def test_data_quality_analytics_service(db_session: Session):
    dq = DataQualityLog(id="DQ_TEST_1", audit_timestamp="2026-08-30T00:00:00Z", quality_score=85.0, issue_category="Outliers", severity="WARNING", affected_record_count=3, description="Extreme outlier", source_file="test.csv")
    db_session.add(dq)
    db_session.commit()

    service = DataQualityAnalyticsService(db_session)
    res = service.get_quality_analytics()

    assert res["overall_quality_score"] == 85.0
    assert res["total_issues"] == 1
    assert res["severity_counts"]["WARNING"] == 1


def test_analytics_api_endpoints(client: TestClient, db_session: Session, auth_headers: dict):
    f = Facility(id="F_API_1", facility_code="A1", facility_name="API Hospital", facility_type="DH", state="StateA", district="DistA", raw_facility_name="API Hospital")
    ind = Indicator(id="IND_imm", code="immunisation", name="Immunisation", category="Child", unit="children")
    db_session.add_all([f, ind])
    db_session.commit()

    o = Observation(id="O_API_1", facility_id="F_API_1", indicator_id="IND_imm", observation_date="2024-05-01", reporting_month="2024-05", value=400.0, value_type="VALID", source_file="f", ingested_at="t")
    db_session.add(o)
    db_session.commit()

    # Unauthenticated GET /api/analytics/summary -> 401
    res_unauth = client.get("/api/analytics/summary")
    assert res_unauth.status_code == 401

    # GET /api/analytics/summary with auth
    res_sum = client.get("/api/analytics/summary", headers=auth_headers)
    assert res_sum.status_code == 200
    assert res_sum.json()["total_facilities"] >= 1

    # GET /api/analytics/trends
    res_tr = client.get("/api/analytics/trends?indicator_code=immunisation", headers=auth_headers)
    assert res_tr.status_code == 200
    assert len(res_tr.json()["series"]) >= 1

    # GET /api/analytics/regional
    res_reg = client.get("/api/analytics/regional?level=district", headers=auth_headers)
    assert res_reg.status_code == 200

    # GET /api/analytics/facilities
    res_fac = client.get("/api/analytics/facilities?facility_id=F_API_1", headers=auth_headers)
    assert res_fac.status_code == 200
    assert res_fac.json()["facility_name"] == "API Hospital"

    # GET /api/analytics/compare
    res_cmp = client.get("/api/analytics/compare?facility_ids=F_API_1&indicator_code=immunisation", headers=auth_headers)
    assert res_cmp.status_code == 200

    # GET /api/analytics/data-quality
    res_dq = client.get("/api/analytics/data-quality", headers=auth_headers)
    assert res_dq.status_code == 200

    # Test invalid level error validation
    res_err = client.get("/api/analytics/regional?level=invalid_level", headers=auth_headers)
    assert res_err.status_code == 400
