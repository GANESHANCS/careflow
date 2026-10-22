"""
Tests for Phase 15B: Multi-Year HMIS Ingestion Pipeline and Financial Year Normalization.
All test insertions execute in isolated temporary SQLite databases to guarantee zero dev DB pollution.
"""

import os
import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.db.models.base import Base
from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.imports.district_adapter import DistrictHMISAdapter


def test_detect_financial_year():
    """Verifies automatic detection of Indian financial year from various filename patterns."""
    assert DistrictHMISAdapter.detect_financial_year("hmis-item-rpt-tn-for-2015-16.csv") == "2015-16"
    assert DistrictHMISAdapter.detect_financial_year("hmis-item-rpt-tn-for-2016-17.csv") == "2016-17"
    assert DistrictHMISAdapter.detect_financial_year("tn_district_hmis_2017-18.csv") == "2017-18"
    assert DistrictHMISAdapter.detect_financial_year("data_2018_19_upload.csv") == "2018-19"
    assert DistrictHMISAdapter.detect_financial_year("unknown_file.csv") == "2015-16"


def test_multi_year_fiscal_month_mapping():
    """Verifies fiscal month sequence generation for FY 2016-17."""
    mapping = DistrictHMISAdapter.get_fiscal_month_mapping("2016-17")
    assert len(mapping) == 12
    assert mapping["April"] == ("2016-04", "2016-04-01")
    assert mapping["December"] == ("2016-12", "2016-12-01")
    assert mapping["January"] == ("2017-01", "2017-01-01")
    assert mapping["March"] == ("2017-03", "2017-03-01")


def test_multi_year_extraction_and_isolated_ingestion():
    """
    Tests extraction and idempotent ingestion of synthetic multi-year HMIS data
    in an isolated in-memory SQLite database, guaranteeing zero mutation of real dev DB.
    """
    # 1. Create synthetic wide DataFrame representing FY 2016-17 for 2 districts
    raw_data = {
        "District": ["Ariyalur", "Chennai"],
        "S.No.": ["1.1", "1.1"],
        "Parameters": ["Total number of pregnant women registered for ANC", "Total number of pregnant women registered for ANC"],
        "Type": ["TOTAL", "TOTAL"],
        "April": [120, 450],
        "May": [130, 460],
        "June": [125, 455],
        "July": [140, 470],
        "August": [135, 465],
        "September": [150, 480],
        "October": [145, 475],
        "November": [160, 490],
        "December": [155, 485],
        "January": [170, 500],
        "February": [165, 495],
        "March": [180, 510],
        "Total": [1770, 5740],
    }
    df = pd.DataFrame(raw_data)

    # 2. Extract long records for FY 2016-17
    records, errors = DistrictHMISAdapter.extract_long_records(
        df=df,
        financial_year="2016-17",
        state="Tamil Nadu",
        source_file="hmis-item-rpt-tn-for-2016-17.csv"
    )

    assert len(errors) == 0
    assert len(records) == 24  # 2 districts * 12 months

    # Verify normalization
    sample = records[0]
    assert sample["financial_year"] == "2016-17"
    assert sample["reporting_month"] == "2016-04"
    assert sample["observation_date"] == "2016-04-01"
    assert sample["value"] == 120.0
    assert sample["value_type"] == "VALID"
    assert sample["id"] == "DOBS_Tamil_Nadu_Ariyalur_1.1_TOTAL_2016-04"

    jan_sample = next(r for r in records if r["district"] == "Ariyalur" and r["reporting_month"] == "2017-01")
    assert jan_sample["value"] == 170.0
    assert jan_sample["observation_date"] == "2017-01-01"

    # 3. Test isolated in-memory database ingestion
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionTest = sessionmaker(bind=engine)
    session = SessionTest()

    # Insert records
    for r in records:
        obs = DistrictObservation(**r)
        session.add(obs)
    session.commit()

    count = session.query(DistrictObservation).count()
    assert count == 24

    # Test idempotency (repeated insert should be handled or natural key unique constraint triggers)
    dup_sample = DistrictObservation(**records[0])
    session.add(dup_sample)
    with pytest.raises(Exception):
        session.commit()
    session.rollback()

    session.close()
