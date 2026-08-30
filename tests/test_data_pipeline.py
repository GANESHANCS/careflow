from pathlib import Path
import pytest
import pandas as pd

from backend.app.services.data_pipeline.file_inspector import HMISFileInspector
from backend.app.services.data_pipeline.schema_normalizer import HMISSchemaNormalizer, ValueClassification
from backend.app.services.data_pipeline.indicator_catalog import IndicatorCatalog
from backend.app.services.data_pipeline.entity_standardizer import HMISEntityStandardizer
from backend.app.services.data_pipeline.temporal_validator import TemporalValidator
from backend.app.services.data_pipeline.deduplication import DeduplicationEngine
from backend.app.services.data_pipeline.quality_engine import HMISQualityEngine
from backend.app.services.data_pipeline.pipeline_runner import HMISPipelineRunner

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "synthetic_hmis"
CSV_FIXTURE = FIXTURES_DIR / "synthetic_test_hmis_report_2024.csv"
XLSX_FIXTURE = FIXTURES_DIR / "synthetic_test_hmis_report_2024.xlsx"


def test_schema_normalizer_column_names():
    assert HMISSchemaNormalizer.normalize_column_name(" Facility Code ") == "facility_code"
    assert HMISSchemaNormalizer.normalize_column_name("OPD Attendance (Total)") == "opd_attendance_total"
    assert HMISSchemaNormalizer.normalize_column_name("ANC-Registered/2024") == "anc_registered_2024"
    assert HMISSchemaNormalizer.normalize_column_name("") == "unnamed_column"


def test_schema_normalizer_values():
    # Valid positive count
    val, vtype = HMISSchemaNormalizer.normalize_value("1,250")
    assert val == 1250.0
    assert vtype == ValueClassification.VALID

    # Zero count
    val_z, vtype_z = HMISSchemaNormalizer.normalize_value("0")
    assert val_z == 0.0
    assert vtype_z == ValueClassification.ZERO

    # Missing value tokens
    val_m1, vtype_m1 = HMISSchemaNormalizer.normalize_value("NA")
    assert val_m1 is None
    assert vtype_m1 == ValueClassification.MISSING

    val_m2, vtype_m2 = HMISSchemaNormalizer.normalize_value("-")
    assert val_m2 is None
    assert vtype_m2 == ValueClassification.MISSING

    # Not Applicable
    val_na, vtype_na = HMISSchemaNormalizer.normalize_value("Not Applicable")
    assert val_na is None
    assert vtype_na == ValueClassification.NOT_APPLICABLE


def test_schema_normalizer_date():
    m1, iso1 = HMISSchemaNormalizer.normalize_date("2024-04")
    assert m1 == "2024-04"
    assert iso1 == "2024-04-01"

    m2, iso2 = HMISSchemaNormalizer.normalize_date("Apr 2024")
    assert m2 == "2024-04"
    assert iso2 == "2024-04-01"

    m_invalid, iso_invalid = HMISSchemaNormalizer.normalize_date("InvalidDate")
    assert m_invalid is None
    assert iso_invalid is None


def test_indicator_catalog():
    catalog = IndicatorCatalog()
    assert catalog.match_column_name("opd_attendance") == "opd_attendance"
    assert catalog.match_column_name("Total OPD Attendance Count") == "opd_attendance"
    assert catalog.match_column_name("Institutional Deliveries") == "institutional_deliveries"
    assert catalog.match_column_name("anc_visits") == "antenatal_visits"
    assert catalog.match_column_name("pnc_visits") == "postnatal_visits"
    assert catalog.match_column_name("immunisation_coverage") == "immunisation"


def test_entity_standardizer():
    row_with_code = {
        "state": "State_A", "district": "District_X",
        "facility_name": "District Hospital Alpha", "facility_code": "1001"
    }
    entity1 = HMISEntityStandardizer.process_row(row_with_code)
    assert entity1.facility_id == "FC_1001"
    assert entity1.facility_type == "DH"

    row_no_code = {
        "state": "State_A", "district": "District_X",
        "facility_name": "Primary Health Centre Beta", "facility_code": ""
    }
    entity2 = HMISEntityStandardizer.process_row(row_no_code)
    assert entity2.facility_id.startswith("FKEY_")
    assert entity2.facility_type == "PHC"


def test_deduplication_engine():
    obs = [
        {"facility_id": "FC_1001", "indicator_code": "opd_attendance", "reporting_month": "2024-04", "value": 100},
        {"facility_id": "FC_1001", "indicator_code": "opd_attendance", "reporting_month": "2024-04", "value": 100},
        {"facility_id": "FC_1002", "indicator_code": "opd_attendance", "reporting_month": "2024-04", "value": 200}
    ]
    deduped, diag = DeduplicationEngine.deduplicate_observations(obs)
    assert len(deduped) == 2
    assert diag["duplicates_found"] == 1


def test_temporal_validator():
    comp = TemporalValidator.evaluate_facility_completeness(
        facility_id="FC_1001",
        reported_months=["2024-01", "2024-02", "2024-04"], # 2024-03 missing
        global_start_month="2024-01",
        global_end_month="2024-04"
    )
    assert comp["total_expected"] == 4
    assert comp["total_reported"] == 3
    assert comp["completeness_pct"] == 75.0
    assert comp["missing_months"] == ["2024-03"]


def test_file_inspector_synthetic_csv():
    inspector = HMISFileInspector(raw_dir=str(FIXTURES_DIR))
    report = inspector.inspect_file(CSV_FIXTURE)
    assert report["extension"] == ".csv"
    assert len(report["sheets"]) == 1
    sheet = report["sheets"][0]
    assert sheet["row_count"] == 4
    assert "opd attendance" in [c.lower() for c in sheet["columns"]]


def test_pipeline_runner_synthetic_fixtures(tmp_path):
    interim_dir = tmp_path / "interim"
    processed_dir = tmp_path / "processed"

    runner = HMISPipelineRunner(
        raw_dir=str(FIXTURES_DIR),
        interim_dir=str(interim_dir),
        processed_dir=str(processed_dir)
    )
    res = runner.run_pipeline()

    assert res["status"] == "SUCCESS"
    assert res["files_processed"] == 2 # CSV and XLSX synthetic fixtures
    assert res["deduplicated_observations"] > 0
    assert res["quality_score"] > 0.0

    # Verify exported Parquet artifacts
    assert (processed_dir / "facilities.parquet").exists()
    assert (processed_dir / "observations.parquet").exists()
    assert (processed_dir / "indicators.parquet").exists()
    assert (processed_dir / "data_quality_report.json").exists()


def test_pipeline_runner_empty_raw_directory(tmp_path):
    empty_raw = tmp_path / "empty_raw"
    empty_raw.mkdir()

    runner = HMISPipelineRunner(
        raw_dir=str(empty_raw),
        interim_dir=str(tmp_path / "interim"),
        processed_dir=str(tmp_path / "processed")
    )
    res = runner.run_pipeline()

    assert res["status"] == "NO_SOURCE_FILES"
    assert res["real_hmis_files_found"] is False
    assert "No HMIS source files found" in res["message"]
