import pytest
from pathlib import Path
from sqlalchemy.orm import Session

from backend.app.services.data_loader_service import ProcessedDataLoaderService
from backend.app.db.models.facility import Facility
from backend.app.db.models.observation import Observation
from backend.app.services.data_pipeline.pipeline_runner import HMISPipelineRunner

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures" / "synthetic_hmis"


def test_data_loader_missing_files(db_session: Session, tmp_path):
    loader = ProcessedDataLoaderService(processed_dir=str(tmp_path / "nonexistent"))
    result = loader.load_processed_data(db_session)
    assert result["status"] == "ERROR"
    assert "Processed dataset files not found" in result["message"]


def test_data_loader_idempotent_ingestion(db_session: Session, tmp_path):
    # 1. Run pipeline on synthetic fixtures to generate processed Parquet datasets
    processed_dir = tmp_path / "processed"
    interim_dir = tmp_path / "interim"

    runner = HMISPipelineRunner(
        raw_dir=str(FIXTURES_DIR),
        interim_dir=str(interim_dir),
        processed_dir=str(processed_dir)
    )
    pipe_res = runner.run_pipeline()
    assert pipe_res["status"] == "SUCCESS"

    # 2. Run loader first time
    loader = ProcessedDataLoaderService(processed_dir=str(processed_dir))
    res1 = loader.load_processed_data(db_session)

    assert res1["status"] == "SUCCESS"
    assert res1["summary"]["facilities_created"] > 0
    assert res1["summary"]["observations_created"] > 0

    initial_fac_count = db_session.query(Facility).count()
    initial_obs_count = db_session.query(Observation).count()

    # 3. Run loader second time (verify idempotency)
    res2 = loader.load_processed_data(db_session)
    assert res2["status"] == "SUCCESS"
    assert res2["summary"]["facilities_created"] == 0
    assert res2["summary"]["observations_created"] == 0

    assert db_session.query(Facility).count() == initial_fac_count
    assert db_session.query(Observation).count() == initial_obs_count
