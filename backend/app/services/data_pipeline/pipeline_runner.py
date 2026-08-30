import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from backend.app.services.data_pipeline.file_inspector import HMISFileInspector
from backend.app.services.data_pipeline.schema_normalizer import HMISSchemaNormalizer, ValueClassification
from backend.app.services.data_pipeline.indicator_catalog import IndicatorCatalog
from backend.app.services.data_pipeline.entity_standardizer import HMISEntityStandardizer, FacilityEntity
from backend.app.services.data_pipeline.deduplication import DeduplicationEngine
from backend.app.services.data_pipeline.quality_engine import HMISQualityEngine, DataQualityReport


class HMISPipelineRunner:
    """
    Main orchestration engine for the HMIS Ingestion & Quality Pipeline.
    Reads raw HMIS Excel/CSV files, normalizes schema and indicators,
    standardizes entities, deduplicates observations, evaluates data quality,
    and exports Parquet datasets and quality reports.
    """

    TRANSFORMATION_VERSION = "2.0.0"

    def __init__(
        self, 
        raw_dir: str = "data/raw", 
        interim_dir: str = "data/interim", 
        processed_dir: str = "data/processed"
    ):
        self.raw_dir = Path(raw_dir)
        self.interim_dir = Path(interim_dir)
        self.processed_dir = Path(processed_dir)
        self.catalog = IndicatorCatalog()
        self.inspector = HMISFileInspector(raw_dir=str(self.raw_dir))

    def run_pipeline(self) -> Dict[str, Any]:
        """
        Executes full ingestion pipeline.
        Returns execution summary.
        """
        self.interim_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        raw_files = self.inspector.discover_raw_files()
        
        if not raw_files:
            return {
                "status": "NO_SOURCE_FILES",
                "message": "No HMIS source files found under data/raw/. Ingestion framework is ready; add HMIS files and rerun.",
                "files_processed": 0,
                "real_hmis_files_found": False,
                "execution_timestamp": datetime.now(timezone.utc).isoformat()
            }

        all_observations: List[Dict[str, Any]] = []
        all_facilities: Dict[str, FacilityEntity] = {}
        file_inspection_reports: List[Dict[str, Any]] = []

        # Process each raw file
        for file_path in raw_files:
            inspection = self.inspector.inspect_file(file_path)
            file_inspection_reports.append(inspection)

            file_obs, file_facs = self._process_single_file(file_path, inspection)
            all_observations.extend(file_obs)
            for fac in file_facs:
                all_facilities[fac.facility_id] = fac

        if not all_observations:
            return {
                "status": "EMPTY_DATASET",
                "message": "Source files were inspected but contained 0 valid observations.",
                "files_processed": len(raw_files),
                "real_hmis_files_found": True,
                "file_inspection": file_inspection_reports,
                "execution_timestamp": datetime.now(timezone.utc).isoformat()
            }

        # Step 6: Deduplication
        dedup_obs, dedup_diag = DeduplicationEngine.deduplicate_observations(all_observations)

        # Step 8 & 9: Quality Engine Audit & Scoring
        facilities_list = [f.model_dump() for f in all_facilities.values()]
        quality_report: DataQualityReport = HMISQualityEngine.evaluate_dataset(
            observations=dedup_obs,
            facilities=facilities_list,
            dedup_diagnostics=dedup_diag
        )

        # Step 11: Export Processed Datasets
        output_paths = self._export_artifacts(dedup_obs, facilities_list, quality_report)

        return {
            "status": "SUCCESS",
            "message": "HMIS Ingestion and Data Quality Pipeline executed successfully.",
            "files_processed": len(raw_files),
            "real_hmis_files_found": True,
            "total_observations_ingested": len(all_observations),
            "deduplicated_observations": len(dedup_obs),
            "facilities_standardized": len(all_facilities),
            "quality_score": quality_report.quality_score.overall_score,
            "quality_report_summary": quality_report.model_dump(),
            "output_paths": output_paths,
            "execution_timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _process_single_file(self, file_path: Path, inspection: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[FacilityEntity]]:
        ext = file_path.suffix.lower()
        observations: List[Dict[str, Any]] = []
        facilities: List[FacilityEntity] = []

        ingested_at = datetime.now(timezone.utc).isoformat()

        sheets_to_process = inspection.get("sheets", [])
        for sheet in sheets_to_process:
            sheet_name = sheet.get("sheet_name", "Sheet1")
            header_idx = sheet.get("header_row_index", 0)

            try:
                if ext in [".xlsx", ".xls"]:
                    df_raw = pd.read_excel(file_path, sheet_name=sheet_name, skiprows=header_idx)
                else:
                    df_raw = pd.read_csv(file_path, skiprows=header_idx, low_memory=False)
            except Exception:
                continue

            if df_raw.empty:
                continue

            # Normalize column headers
            orig_cols = list(df_raw.columns)
            norm_cols = [HMISSchemaNormalizer.normalize_column_name(c) for c in orig_cols]
            df_raw.columns = norm_cols

            # Find date / period column
            date_col = next((c for c in norm_cols if any(k in c for k in ["date", "month", "period", "year"])), None)
            
            # Map indicator columns vs entity metadata columns
            entity_col_keys = {"state", "district", "sub_district", "block", "facility", "facility_name", "facility_code", "code", "facility_type"}
            
            for row_idx, row in df_raw.iterrows():
                row_dict = row.to_dict()
                
                # Standardize Facility Entity
                facility_entity = HMISEntityStandardizer.process_row(row_dict)
                facilities.append(facility_entity)

                # Determine reporting month
                month_str, iso_date = HMISSchemaNormalizer.normalize_date(row_dict.get(date_col) if date_col else None)

                # Iterate columns for indicator values
                for col_name in norm_cols:
                    if col_name in entity_col_keys or col_name == date_col or col_name.startswith("unnamed"):
                        continue

                    indicator_code = self.catalog.match_column_name(col_name)
                    if not indicator_code:
                        # Fallback for dynamic indicators not yet in standard catalog
                        indicator_code = f"ind_{col_name}"

                    raw_val = row_dict.get(col_name)
                    norm_num, val_class = HMISSchemaNormalizer.normalize_value(raw_val)

                    obs_record = {
                        "obs_id": f"OBS_{file_path.stem}_{sheet_name}_{row_idx}_{col_name}",
                        "facility_id": facility_entity.facility_id,
                        "facility_code": facility_entity.facility_code,
                        "facility_name": facility_entity.facility_name,
                        "district": facility_entity.district,
                        "state": facility_entity.state,
                        "indicator_code": indicator_code,
                        "raw_column_name": col_name,
                        "reporting_month": month_str or "UNKNOWN",
                        "observation_date": iso_date,
                        "value": norm_num,
                        "value_type": val_class,
                        "raw_value_str": str(raw_val) if raw_val is not None else None,
                        "source_file": file_path.name,
                        "source_sheet": sheet_name,
                        "raw_row_number": row_idx + header_idx + 1,
                        "ingested_at": ingested_at,
                        "transformation_version": self.TRANSFORMATION_VERSION
                    }
                    observations.append(obs_record)

        return observations, facilities

    def _export_artifacts(
        self, 
        observations: List[Dict[str, Any]], 
        facilities: List[Dict[str, Any]], 
        quality_report: DataQualityReport
    ) -> Dict[str, str]:
        
        # 1. Export Facilities Parquet
        df_facilities = pd.DataFrame(facilities).drop_duplicates(subset=["facility_id"])
        fac_path = self.processed_dir / "facilities.parquet"
        df_facilities.to_parquet(fac_path, index=False)

        # 2. Export Observations Parquet
        df_obs = pd.DataFrame(observations)
        obs_path = self.processed_dir / "observations.parquet"
        df_obs.to_parquet(obs_path, index=False)

        # 3. Export Indicators Parquet
        indicators_data = [i.model_dump() for i in self.catalog.list_indicators()]
        df_indicators = pd.DataFrame(indicators_data)
        ind_path = self.processed_dir / "indicators.parquet"
        df_indicators.to_parquet(ind_path, index=False)

        # 4. Export Data Quality Report JSON
        report_path = self.processed_dir / "data_quality_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(quality_report.model_dump(), f, indent=2)

        # 5. Export Interim Normalized Staging
        interim_path = self.interim_dir / "normalized_staging.parquet"
        df_obs.to_parquet(interim_path, index=False)

        return {
            "facilities_parquet": str(fac_path),
            "observations_parquet": str(obs_path),
            "indicators_parquet": str(ind_path),
            "quality_report_json": str(report_path),
            "interim_staging_parquet": str(interim_path)
        }
