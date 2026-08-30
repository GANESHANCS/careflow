import sys
import uuid
import math
import random
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.session import SessionLocal, engine
from backend.app.db.models.base import Base
from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.seed import seed_standard_indicators


def seed_synthetic_forecasting_data():
    """
    Seeds 36 months (2022-01 to 2024-12) of realistic synthetic monthly observations
    for synthetic healthcare facilities to enable time-series forecasting training.
    """
    print("Initializing DB tables...")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Seed standard indicators first
        seed_standard_indicators(db)

        # Create synthetic facilities
        facilities_data = [
            {
                "id": "fac_synth_dh_alpha",
                "facility_code": "SYNTH_DH_1001",
                "facility_name": "SYNTHETIC District Hospital Alpha",
                "facility_type": "District Hospital",
                "state": "SYNTHETIC_State_A",
                "district": "SYNTHETIC_District_X",
                "sub_district": "SYNTHETIC_Block_1",
                "raw_facility_name": "SYNTHETIC District Hospital Alpha",
                "raw_district_name": "SYNTHETIC_District_X"
            },
            {
                "id": "fac_synth_phc_beta",
                "facility_code": "SYNTH_PHC_1002",
                "facility_name": "SYNTHETIC Primary Health Centre Beta",
                "facility_type": "PHC",
                "state": "SYNTHETIC_State_A",
                "district": "SYNTHETIC_District_X",
                "sub_district": "SYNTHETIC_Block_1",
                "raw_facility_name": "SYNTHETIC Primary Health Centre Beta",
                "raw_district_name": "SYNTHETIC_District_X"
            },
            {
                "id": "fac_synth_chc_gamma",
                "facility_code": "SYNTH_CHC_1003",
                "facility_name": "SYNTHETIC Community Health Centre Gamma",
                "facility_type": "CHC",
                "state": "SYNTHETIC_State_A",
                "district": "SYNTHETIC_District_Y",
                "sub_district": "SYNTHETIC_Block_2",
                "raw_facility_name": "SYNTHETIC Community Health Centre Gamma",
                "raw_district_name": "SYNTHETIC_District_Y"
            }
        ]

        for f_data in facilities_data:
            existing = db.query(Facility).filter(Facility.id == f_data["id"]).first()
            if not existing:
                fac = Facility(**f_data)
                db.add(fac)
        db.commit()

        # Fetch indicators using case-insensitive matching
        opd_ind = db.query(Indicator).filter((Indicator.code == "opd_attendance") | (Indicator.code == "OPD_ATTENDANCE")).first()
        ipd_ind = db.query(Indicator).filter((Indicator.code == "inpatient_admissions") | (Indicator.code == "INPATIENT_ADM")).first()
        del_ind = db.query(Indicator).filter((Indicator.code == "institutional_deliveries") | (Indicator.code == "INST_DELIVERIES")).first()

        indicators_map = {
            "opd_attendance": (opd_ind, 1200.0, 300.0, 0.15),
            "inpatient_admissions": (ipd_ind, 350.0, 80.0, 0.10),
            "institutional_deliveries": (del_ind, 85.0, 20.0, 0.08)
        }


        # Generate 36 months (2022-01 to 2024-12)
        months = []
        for year in range(2022, 2025):
            for month in range(1, 13):
                months.append((f"{year:04d}-{month:02d}", f"{year:04d}-{month:02d}-01", month, year - 2022))

        random.seed(42)
        obs_created = 0

        for f_data in facilities_data:
            fac_id = f_data["id"]
            fac_multiplier = 1.2 if "DH" in f_data["facility_code"] else (0.5 if "PHC" in f_data["facility_code"] else 0.8)

            for ind_code, (ind_obj, base_val, val_std, trend_factor) in indicators_map.items():
                if not ind_obj:
                    continue

                for m_str, d_str, month_num, year_idx in months:
                    # Idempotency check
                    existing_obs = db.query(Observation).filter(
                        Observation.facility_id == fac_id,
                        Observation.indicator_id == ind_obj.id,
                        Observation.observation_date == d_str
                    ).first()

                    if existing_obs:
                        continue

                    # Synthetic seasonal pattern (Monsoon peak Jul-Sep: month_num 7, 8, 9)
                    season_wave = 1.0 + 0.25 * math.sin(2.0 * math.pi * (month_num - 3) / 12.0)
                    trend_wave = 1.0 + (year_idx * trend_factor)
                    noise = random.gauss(0, val_std * 0.1)

                    val = max(10.0, (base_val * fac_multiplier * season_wave * trend_wave) + noise)
                    val = round(val, 1)

                    obs_id = f"obs_{fac_id}_{ind_obj.id}_{d_str}"
                    obs = Observation(
                        id=obs_id,
                        facility_id=fac_id,
                        indicator_id=ind_obj.id,
                        observation_date=d_str,
                        reporting_month=m_str,
                        value=val,
                        value_type="VALID",
                        validation_status="VALIDATED",
                        source_file="synthetic_fixture_36m.csv",
                        source_sheet="SYNTHETIC_DATA",
                        source_row=obs_created + 1,
                        ingested_at="2026-08-30T12:00:00Z",
                        transformation_version="2.0.0"
                    )
                    db.add(obs)
                    obs_created += 1

        db.commit()
        print(f"[SUCCESS] Seeded {obs_created} multi-year synthetic observations across {len(facilities_data)} facilities.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_synthetic_forecasting_data()
