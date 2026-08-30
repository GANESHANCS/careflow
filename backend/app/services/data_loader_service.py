import json
from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
from sqlalchemy.orm import Session

from backend.app.db.models.facility import Facility
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.observation import Observation
from backend.app.db.models.data_quality import DataQualityLog
from backend.app.db.seed import seed_standard_indicators


class ProcessedDataLoaderService:
    """
    Service for ingesting processed Parquet datasets from data/processed/
    into the PostgreSQL/relational database idempotently.
    """

    def __init__(self, processed_dir: str = "data/processed"):
        self.processed_dir = Path(processed_dir)

    def load_processed_data(self, db: Session) -> Dict[str, Any]:
        fac_path = self.processed_dir / "facilities.parquet"
        ind_path = self.processed_dir / "indicators.parquet"
        obs_path = self.processed_dir / "observations.parquet"
        qual_path = self.processed_dir / "data_quality_report.json"

        # 1. Validate file existence
        missing_files = []
        for p, label in [(fac_path, "facilities.parquet"), (ind_path, "indicators.parquet"), (obs_path, "observations.parquet")]:
            if not p.exists():
                missing_files.append(label)

        if missing_files:
            return {
                "status": "ERROR",
                "message": f"Processed dataset files not found: {', '.join(missing_files)}. Run Phase 2 pipeline first.",
                "facilities_loaded": 0,
                "indicators_loaded": 0,
                "observations_loaded": 0
            }

        # 2. Seed baseline indicators
        seed_standard_indicators(db)

        summary = {
            "facilities_created": 0,
            "facilities_existing": 0,
            "indicators_created": 0,
            "indicators_existing": 0,
            "observations_created": 0,
            "observations_skipped": 0,
            "quality_logs_created": 0
        }

        # 3. Ingest Indicators Parquet
        try:
            df_ind = pd.read_parquet(ind_path)
            for _, row in df_ind.iterrows():
                code = str(row.get("code")).strip()
                ind_id = f"IND_{code}"
                existing = db.query(Indicator).filter(Indicator.id == ind_id).first()
                if not existing:
                    ind = Indicator(
                        id=ind_id,
                        code=code,
                        name=str(row.get("name")),
                        category=str(row.get("category", "General")),
                        unit=str(row.get("unit", "count")),
                        source_system="HMIS",
                        active=True
                    )
                    db.add(ind)
                    summary["indicators_created"] += 1
                else:
                    summary["indicators_existing"] += 1
            db.commit()
        except Exception as e:
            db.rollback()
            return {"status": "ERROR", "message": f"Error loading indicators.parquet: {str(e)}"}

        # 4. Ingest Facilities Parquet
        try:
            df_fac = pd.read_parquet(fac_path)
            for _, row in df_fac.iterrows():
                fac_id = str(row.get("facility_id")).strip()
                existing = db.query(Facility).filter(Facility.id == fac_id).first()
                if not existing:
                    fac_code = str(row.get("facility_code")) if row.get("facility_code") and not pd.isna(row.get("facility_code")) else None
                    fac = Facility(
                        id=fac_id,
                        facility_code=fac_code,
                        facility_name=str(row.get("facility_name")),
                        facility_type=str(row.get("facility_type", "UNKNOWN")),
                        state=str(row.get("state", "India")),
                        district=str(row.get("district", "Unknown District")),
                        sub_district=str(row.get("sub_district")) if row.get("sub_district") and not pd.isna(row.get("sub_district")) else None,
                        raw_facility_name=str(row.get("raw_facility_name", row.get("facility_name"))),
                        raw_district_name=str(row.get("raw_district_name")) if row.get("raw_district_name") and not pd.isna(row.get("raw_district_name")) else None
                    )
                    db.add(fac)
                    summary["facilities_created"] += 1
                else:
                    summary["facilities_existing"] += 1
            db.commit()
        except Exception as e:
            db.rollback()
            return {"status": "ERROR", "message": f"Error loading facilities.parquet: {str(e)}"}

        # 5. Ingest Observations Parquet
        try:
            df_obs = pd.read_parquet(obs_path)
            
            # Map indicators code -> indicator_id
            indicator_map = {ind.code: ind.id for ind in db.query(Indicator).all()}

            for _, row in df_obs.iterrows():
                fac_id = str(row.get("facility_id")).strip()
                ind_code = str(row.get("indicator_code")).strip()
                ind_id = indicator_map.get(ind_code, f"IND_{ind_code}")

                # Ensure dynamic indicator exists
                if ind_id not in indicator_map.values():
                    dynamic_ind = Indicator(
                        id=ind_id,
                        code=ind_code,
                        name=ind_code.replace("_", " ").title(),
                        category="Dynamic HMIS",
                        unit="count",
                        source_system="HMIS",
                        active=True
                    )
                    db.add(dynamic_ind)
                    db.commit()
                    indicator_map[ind_code] = ind_id

                obs_date = str(row.get("observation_date", "YYYY-MM-01")).strip()
                rep_month = str(row.get("reporting_month", "YYYY-MM")).strip()

                # Check uniqueness by (facility_id, indicator_id, observation_date)
                existing = db.query(Observation).filter(
                    Observation.facility_id == fac_id,
                    Observation.indicator_id == ind_id,
                    Observation.observation_date == obs_date
                ).first()

                if not existing:
                    raw_val = row.get("value")
                    val_float = float(raw_val) if raw_val is not None and not pd.isna(raw_val) else None
                    
                    obs = Observation(
                        id=str(row.get("obs_id", f"OBS_{fac_id}_{ind_code}_{obs_date}")),
                        facility_id=fac_id,
                        indicator_id=ind_id,
                        observation_date=obs_date,
                        reporting_month=rep_month,
                        value=val_float,
                        value_type=str(row.get("value_type", "VALID")),
                        validation_status="VALIDATED",
                        source_file=str(row.get("source_file", "unknown")),
                        source_sheet=str(row.get("source_sheet")) if row.get("source_sheet") and not pd.isna(row.get("source_sheet")) else None,
                        source_row=int(row.get("raw_row_number")) if row.get("raw_row_number") and not pd.isna(row.get("raw_row_number")) else None,
                        ingested_at=str(row.get("ingested_at", "N/A")),
                        transformation_version=str(row.get("transformation_version", "2.0.0"))
                    )
                    db.add(obs)
                    summary["observations_created"] += 1
                else:
                    summary["observations_skipped"] += 1
            db.commit()
        except Exception as e:
            db.rollback()
            return {"status": "ERROR", "message": f"Error loading observations.parquet: {str(e)}"}

        # 6. Ingest Data Quality Report JSON
        if qual_path.exists():
            try:
                with open(qual_path, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                score = q_data.get("quality_score", {}).get("overall_score", 100.0)
                issues = q_data.get("issues", [])
                
                for idx, issue in enumerate(issues):
                    q_log = DataQualityLog(
                        id=f"DQ_{idx}_{issue.get('check_id')}",
                        audit_timestamp=q_data.get("execution_timestamp", "N/A"),
                        quality_score=score,
                        issue_category=issue.get("check_name", "General"),
                        severity=issue.get("severity", "INFO"),
                        affected_record_count=issue.get("affected_count", 0),
                        description=issue.get("description", ""),
                        source_file="data_quality_report.json"
                    )
                    db.add(q_log)
                    summary["quality_logs_created"] += 1
                db.commit()
            except Exception:
                db.rollback()

        return {
            "status": "SUCCESS",
            "message": "Processed Parquet datasets loaded into database successfully.",
            "summary": summary
        }
