import os
import io
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models.base import Base
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.district_observation import DistrictObservation, classify_subgroup_total
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_observation_record import ImportObservationRecord
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.data_quality import DataQualityLog

from backend.app.services.imports.schema_profiles import (
    SchemaProfileRegistry,
    DistrictMonthlyTabularV1Profile,
)
from backend.app.services.imports.district_adapter import DistrictHMISAdapter
from backend.app.services.imports.import_service import (
    HMISImportService,
    ImportRollbackIneligibleStatusError,
    ImportRollbackDependencyConflictError,
)


@pytest.fixture
def sample_wide_dataframe():
    """Returns a synthetic, minimal wide district HMIS dataframe."""
    return pd.DataFrame([
        {
            "District": "Ariyalur",
            "S.No.": "14.12.1",
            "Parameters": "Outpatient attendance - All",
            "Type": "TOTAL",
            "April": 100, "May": 150, "June": 200, "July": 250, "August": 300, "September": 350,
            "October": 400, "November": 450, "December": 500, "January": 550, "February": 600, "March": 650,
            "Total": 4550,
        },
        {
            "District": "Ariyalur",
            "S.No.": "1.1",
            "Parameters": "Total number of pregnant women registered for ANC",
            "Type": "4. Total",
            "April": 50, "May": 60, "June": 0, "July": None, "August": "NA", "September": 70,
            "October": 80, "November": 90, "December": 100, "January": 110, "February": 120, "March": 130,
            "Total": 810,
        },
        {
            "District": "Ariyalur",
            "S.No.": "14.01",
            "Parameters": "Sub Centres functioning in Government Buildings",
            "Type": "TOTAL",
            "April": 15, "May": 15, "June": 15, "July": 15, "August": 15, "September": 15,
            "October": 15, "November": 15, "December": 15, "January": 15, "February": 15, "March": 15,
            "Total": None,  # Stock metric total is non-additive and None
        },
        {
            "District": "Chennai",
            "S.No.": "1.1",
            "Parameters": "Total number of pregnant women registered for ANC",
            "Type": "1. Children",
            "April": 10, "May": 20, "June": 30, "July": 40, "August": 50, "September": 60,
            "October": 70, "November": 80, "December": 90, "January": 100, "February": 110, "March": 120,
            "Total": 780,
        },
    ])


# ---------------------------------------------------------------------------
# Unit Tests: Schema Profile & Fiscal-Year Mapping
# ---------------------------------------------------------------------------

def test_fiscal_year_month_mapping():
    mapping = DistrictHMISAdapter.get_fiscal_month_mapping("2015-16")
    assert len(mapping) == 12
    assert mapping["April"] == ("2015-04", "2015-04-01")
    assert mapping["December"] == ("2015-12", "2015-12-01")
    assert mapping["January"] == ("2016-01", "2016-01-01")
    assert mapping["March"] == ("2016-03", "2016-03-01")

    # Invalid financial year format
    with pytest.raises(ValueError, match="Invalid financial year format"):
        DistrictHMISAdapter.get_fiscal_month_mapping("2015-2016")

    # Mismatched century/consecutive year
    with pytest.raises(ValueError, match="Financial year mismatch"):
        DistrictHMISAdapter.get_fiscal_month_mapping("2015-17")


def test_schema_profile_detection_and_validation():
    valid_cols = ["District", "S.No.", "Parameters", "Type", "April", "May", "June", "July",
                  "August", "September", "October", "November", "December", "January", "February", "March", "Total"]
    profile = SchemaProfileRegistry.detect_profile(valid_cols)
    assert profile.profile_id == "district_monthly_tabular_v1"

    val_res = profile.validate_headers(valid_cols)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # Missing mandatory column
    invalid_cols = ["District", "S.No.", "Type", "April"]
    val_res_inv = DistrictMonthlyTabularV1Profile.validate_headers(invalid_cols)
    assert val_res_inv.is_valid is False
    assert any("Parameter" in err for err in val_res_inv.errors)


# ---------------------------------------------------------------------------
# Unit Tests: Cell Parsing, Zero vs Missing, Subgroup Semantics
# ---------------------------------------------------------------------------

def test_cell_parsing_zeros_vs_missing():
    # Numeric zero
    assert DistrictHMISAdapter.parse_cell_value(0) == (0.0, "ZERO")
    assert DistrictHMISAdapter.parse_cell_value("0") == (0.0, "ZERO")
    assert DistrictHMISAdapter.parse_cell_value(0.0) == (0.0, "ZERO")

    # Missing tokens
    assert DistrictHMISAdapter.parse_cell_value(None) == (None, "MISSING")
    assert DistrictHMISAdapter.parse_cell_value(np.nan) == (None, "MISSING")
    assert DistrictHMISAdapter.parse_cell_value("") == (None, "MISSING")
    assert DistrictHMISAdapter.parse_cell_value("NA") == (None, "MISSING")
    assert DistrictHMISAdapter.parse_cell_value("-") == (None, "MISSING")
    assert DistrictHMISAdapter.parse_cell_value("nil") == (None, "MISSING")

    # Valid positive numbers
    assert DistrictHMISAdapter.parse_cell_value(42) == (42.0, "VALID")
    assert DistrictHMISAdapter.parse_cell_value("1,250") == (1250.0, "VALID")

    # Invalid non-numeric string
    assert DistrictHMISAdapter.parse_cell_value("corrupted_text") == (None, "INVALID")


def test_subgroup_total_classification():
    # True totals
    assert classify_subgroup_total("TOTAL") is True
    assert classify_subgroup_total("Total") is True
    assert classify_subgroup_total("4. Total") is True
    assert classify_subgroup_total("3. Total") is True

    # Slices containing 'total' or non-totals
    assert classify_subgroup_total("5. Total Stock") is False
    assert classify_subgroup_total("1. Children") is False
    assert classify_subgroup_total("2. Adults") is False
    assert classify_subgroup_total("1. 6-14 yrs") is False
    assert classify_subgroup_total("1. Number tested") is False


# ---------------------------------------------------------------------------
# Unit Tests: Wide-to-Long Transformation & Reversibility
# ---------------------------------------------------------------------------

def test_wide_to_long_and_reversible(sample_wide_dataframe):
    long_records, errors = DistrictHMISAdapter.extract_long_records(sample_wide_dataframe)
    assert len(errors) == 0
    # 4 rows * 12 months = 48 records
    assert len(long_records) == 48

    # Check zero preservation
    anc_june = next(r for r in long_records if r["s_no"] == "1.1" and r["reporting_month"] == "2015-06" and r["subgroup_type"] == "4. Total")
    assert anc_june["value"] == 0.0
    assert anc_june["value_type"] == "ZERO"

    # Check missing preservation
    anc_july = next(r for r in long_records if r["s_no"] == "1.1" and r["reporting_month"] == "2015-07" and r["subgroup_type"] == "4. Total")
    assert anc_july["value"] is None
    assert anc_july["value_type"] == "MISSING"

    # Check stock metric non-additive preservation
    stock_rec = next(r for r in long_records if r["s_no"] == "14.01")
    assert stock_rec["reported_annual_total"] is None

    # Check reversibility
    df_restored = DistrictHMISAdapter.to_wide_dataframe(long_records)
    assert len(df_restored) == len(sample_wide_dataframe)
    # Check April column matches when sorted by natural keys
    orig_sorted = sample_wide_dataframe.sort_values(by=["District", "S.No.", "Type"]).reset_index(drop=True)
    rest_sorted = df_restored.sort_values(by=["District", "S.No.", "Type"]).reset_index(drop=True)
    assert list(rest_sorted["April"]) == list(orig_sorted["April"].astype(float))


def test_duplicate_natural_key_detection():
    dup_df = pd.DataFrame([
        {
            "District": "Ariyalur", "S.No.": "1.1", "Parameters": "ANC", "Type": "TOTAL",
            "April": 10, "May": 10, "June": 10, "July": 10, "August": 10, "September": 10,
            "October": 10, "November": 10, "December": 10, "January": 10, "February": 10, "March": 10, "Total": 120
        },
        {
            "District": "Ariyalur", "S.No.": "1.1", "Parameters": "ANC Duplicate", "Type": "TOTAL",
            "April": 15, "May": 15, "June": 15, "July": 15, "August": 15, "September": 15,
            "October": 15, "November": 15, "December": 15, "January": 15, "February": 15, "March": 15, "Total": 180
        }
    ])
    long_records, errors = DistrictHMISAdapter.extract_long_records(dup_df)
    assert len(long_records) == 12  # First row ingested
    assert len(errors) == 12  # Second row flagged as DUPLICATE_NATURAL_KEY for all 12 months
    assert all(e["code"] == "DUPLICATE_NATURAL_KEY" for e in errors)


def test_deterministic_observation_id():
    id1 = DistrictHMISAdapter.generate_observation_id("Tamil Nadu", "Ariyalur", "14.12.1", "TOTAL", "2015-04")
    id2 = DistrictHMISAdapter.generate_observation_id("Tamil Nadu", "Ariyalur", "14.12.1", "TOTAL", "2015-04")
    assert id1 == id2
    assert id1 == "DOBS_Tamil_Nadu_Ariyalur_14.12.1_TOTAL_2015-04"


# ---------------------------------------------------------------------------
# Integration Tests: Persistence, Idempotency, Rollback & Coexistence
# ---------------------------------------------------------------------------

def test_ingest_and_idempotent_reimport(db_session, sample_wide_dataframe):
    res1 = DistrictHMISAdapter.ingest_dataset(
        db=db_session,
        file_path_or_df=sample_wide_dataframe,
        batch_size=20
    )
    assert res1["records_imported"] == 48

    count_after_first = db_session.query(DistrictObservation).count()
    assert count_after_first == 48

    # Re-import identical dataframe: should be completely idempotent (0 duplicate row explosion)
    res2 = DistrictHMISAdapter.ingest_dataset(
        db=db_session,
        file_path_or_df=sample_wide_dataframe,
        batch_size=20
    )
    assert res2["records_imported"] == 48
    count_after_second = db_session.query(DistrictObservation).count()
    assert count_after_second == 48


def test_import_service_district_job_lifecycle(db_session, tmp_path, sample_wide_dataframe):
    # Write sample dataset to disk
    csv_file = tmp_path / "test_district_hmis.csv"
    sample_wide_dataframe.to_csv(csv_file, index=False)

    service = HMISImportService(db_session)
    job = ImportJob(
        job_code="JOB_DIST_TEST_001",
        original_filename="test_district_hmis.csv",
        storage_path=str(csv_file),
        file_hash="test_hash_001",
        file_size_bytes=csv_file.stat().st_size,
        status="QUEUED"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # Process job via service
    completed_job = service.process_import_job(job.id)
    assert completed_job.status == "COMPLETED"
    assert completed_job.records_imported == 48
    assert completed_job.schema_profile == "district_monthly_tabular_v1"

    # Verify change records tracked
    change_recs = db_session.query(ImportObservationRecord).filter(ImportObservationRecord.import_job_id == job.id).all()
    assert len(change_recs) == 48
    assert all(r.action == "INSERT" for r in change_recs)

    # Verify rollback
    rollback_res = service.rollback_import_job(job.id, rolled_back_by="admin_test")
    assert rollback_res["status"] == "ROLLED_BACK"
    assert rollback_res["records_deleted"] == 48

    # Database state after rollback: 0 district observations
    assert db_session.query(DistrictObservation).count() == 0


def test_cancellation_during_chunk_loop(db_session, tmp_path, sample_wide_dataframe):
    csv_file = tmp_path / "test_district_cancel.csv"
    sample_wide_dataframe.to_csv(csv_file, index=False)

    service = HMISImportService(db_session)
    job = ImportJob(
        job_code="JOB_DIST_CANCEL_001",
        original_filename="test_district_cancel.csv",
        storage_path=str(csv_file),
        file_hash="test_hash_cancel",
        file_size_bytes=csv_file.stat().st_size,
        status="QUEUED"
    )
    db_session.add(job)
    db_session.commit()
    db_session.refresh(job)

    # Mark as CANCELLED before processing starts
    job.status = "CANCELLED"
    db_session.commit()

    res = service.process_import_job(job.id)
    assert res.status == "CANCELLED"
    assert db_session.query(DistrictObservation).count() == 0


def test_coexistence_with_facility_observations(db_session, tmp_path, sample_wide_dataframe):
    """
    Verifies that facility observations and district observations exist in separate tables,
    and rolling back a district job has zero impact on facility observations.
    """
    # 1. Insert a facility observation
    fac = Facility(id="FAC_TEST_01", facility_code="FC01", facility_name="Test PHC", raw_facility_name="Test PHC", state="TN", district="Ariyalur")
    ind = Indicator(id="IND_opd_attendance", code="opd_attendance", name="OPD", category="OPD", unit="count", active=True)
    db_session.add_all([fac, ind])
    db_session.flush()

    fac_obs = Observation(
        id="OBS_FAC_TEST_01_opd_attendance_2015-04",
        facility_id="FAC_TEST_01",
        indicator_id="IND_opd_attendance",
        observation_date="2015-04-01",
        reporting_month="2015-04",
        value=123.0,
        value_type="VALID",
        source_file="facility_report.csv",
        ingested_at="2026-10-21T00:00:00Z",
        transformation_version="2.0.0"
    )
    db_session.add(fac_obs)
    db_session.commit()

    # 2. Ingest district dataset via ImportJob
    csv_file = tmp_path / "test_coexistence.csv"
    sample_wide_dataframe.to_csv(csv_file, index=False)

    service = HMISImportService(db_session)
    job = ImportJob(
        job_code="JOB_DIST_COEXIST",
        original_filename="test_coexistence.csv",
        storage_path=str(csv_file),
        file_hash="test_hash_coexist",
        file_size_bytes=csv_file.stat().st_size,
        status="QUEUED"
    )
    db_session.add(job)
    db_session.commit()

    service.process_import_job(job.id)

    # Verify both exist
    assert db_session.query(Observation).count() == 1
    assert db_session.query(DistrictObservation).count() == 48

    # 3. Rollback the district import job
    service.rollback_import_job(job.id, rolled_back_by="admin_test")

    # Facility observation remains completely untouched
    assert db_session.query(Observation).count() == 1
    remaining_fac_obs = db_session.query(Observation).first()
    assert remaining_fac_obs.id == "OBS_FAC_TEST_01_opd_attendance_2015-04"
    assert remaining_fac_obs.value == 123.0

    # District observations completely cleaned up
    assert db_session.query(DistrictObservation).count() == 0
