import re
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session

from backend.app.db.models.district_observation import DistrictObservation, classify_subgroup_total
from backend.app.db.models.import_job import ImportJob
from backend.app.db.models.import_observation_record import ImportObservationRecord
from backend.app.db.models.import_error_log import ImportErrorLog
from backend.app.db.models.indicator import Indicator
from backend.app.services.imports.schema_profiles import (
    DistrictMonthlyTabularV1Profile,
    SchemaValidationResult,
)


class DistrictHMISAdapter:
    """
    Ingestion and transformation adapter for District-Level HMIS monthly performance datasets.
    Converts wide fiscal-year monthly spreadsheets (April-March) into normalized, durable
    DistrictObservation entities with strict preservation of zeroes, missing values,
    disaggregation slices, and arithmetic reversibility.
    """

    MONTH_ORDER = [
        "April", "May", "June", "July", "August", "September",
        "October", "November", "December", "January", "February", "March"
    ]

    # Canonical crosswalk mapping from MoHFW S.No. to CAREFlow core indicators
    CORE_INDICATOR_CROSSWALK = {
        "14.12.1": "IND_opd_attendance",       # OPD attendance (All)
        "14.10.1.c": "IND_inpatient_admissions", # Total IPD admissions (male + female)
        "2.2": "IND_institutional_deliveries",  # Deliveries conducted at Public Institutions
        "2.3": "IND_institutional_deliveries",  # Deliveries conducted at Private Institutions
        "1.1": "IND_antenatal_visits",          # Total pregnant women registered for ANC
        "6.1": "IND_postnatal_visits",          # Post partum check-up within 48 hours
        "6.2": "IND_postnatal_visits",          # Post partum check-up between 48 hrs & 14 days
        "10.1.13.c": "IND_immunisation",        # Total children fully immunised
    }

    # Non-additive infrastructure / capacity metrics where summing across months is invalid
    NON_ADDITIVE_SNO_ITEMS = {
        "9.12", "14.01", "14.02", "14.03", "14.04", "14.06", "14.08", "14.09"
    }

    @classmethod
    def validate_headers(cls, headers: List[str]) -> SchemaValidationResult:
        """Validates column headers against the DistrictMonthlyTabularV1Profile."""
        return DistrictMonthlyTabularV1Profile.validate_headers(headers)

    @classmethod
    def get_fiscal_month_mapping(cls, financial_year: str = "2015-16") -> Dict[str, Tuple[str, str]]:
        """
        Validates the Indian financial year string (e.g. '2015-16') and returns
        a mapping from month names ('April'..'March') to ('YYYY-MM', 'YYYY-MM-01').
        """
        clean_fy = str(financial_year).strip()
        match = re.match(r"^(\d{4})-(\d{2})$", clean_fy)
        if not match:
            raise ValueError(
                f"Invalid financial year format '{financial_year}'. Expected format 'YYYY-YY' (e.g. '2015-16')."
            )

        start_year = int(match.group(1))
        # Determine 4-digit end year from 2-digit suffix (e.g., '16' -> 2016)
        century = (start_year // 100) * 100
        end_year_short = int(match.group(2))
        end_year = century + end_year_short
        if end_year != start_year + 1:
            raise ValueError(
                f"Financial year mismatch in '{financial_year}': end year {end_year} must be start year {start_year} + 1."
            )

        mapping: Dict[str, Tuple[str, str]] = {}
        for idx, month_name in enumerate(cls.MONTH_ORDER, start=1):
            if idx <= 9:
                # April (04) to December (12) belong to start_year
                m_num = idx + 3
                month_str = f"{start_year}-{m_num:02d}"
            else:
                # January (01) to March (03) belong to end_year
                m_num = idx - 9
                month_str = f"{end_year}-{m_num:02d}"

            mapping[month_name] = (month_str, f"{month_str}-01")

        return mapping

    @classmethod
    def parse_cell_value(cls, val: Any) -> Tuple[Optional[float], str]:
        """
        Parses a cell value while strictly preserving zeroes vs missing tokens.
        Returns: (numeric_value, value_type)
        """
        if pd.isna(val) or val is None:
            return None, "MISSING"

        if isinstance(val, (int, float, np.integer, np.floating)):
            if np.isnan(val):
                return None, "MISSING"
            f_val = float(val)
            if f_val == 0.0:
                return 0.0, "ZERO"
            return f_val, "VALID"

        val_str = str(val).strip()
        if not val_str or val_str.lower() in ("", "na", "n/a", "null", "none", "nan", "-", "--", "nil", "?"):
            return None, "MISSING"

        clean_str = re.sub(r'[,"]', "", val_str)
        try:
            num = float(clean_str)
            if num == 0.0:
                return 0.0, "ZERO"
            return num, "VALID"
        except ValueError:
            return None, "INVALID"

    @classmethod
    def map_indicator_code(cls, s_no: str, parameter_name: str) -> Optional[str]:
        """Maps source S.No. and description to a canonical CAREFlow indicator ID."""
        clean_sno = str(s_no).strip().lower()
        if clean_sno in cls.CORE_INDICATOR_CROSSWALK:
            return cls.CORE_INDICATOR_CROSSWALK[clean_sno]
        return None

    @classmethod
    def generate_observation_id(
        cls,
        state: str,
        district: str,
        s_no: str,
        subgroup_type: str,
        reporting_month: str
    ) -> str:
        """
        Generates a deterministic primary key for DistrictObservation.
        Format: DOBS_{clean_state}_{clean_district}_{clean_sno}_{clean_type}_{reporting_month}
        """
        def clean_token(s: str) -> str:
            cleaned = re.sub(r"[^a-zA-Z0-9_.]", "_", str(s).strip())
            return re.sub(r"_+", "_", cleaned).strip("_")

        c_state = clean_token(state)
        c_dist = clean_token(district)
        c_sno = clean_token(s_no)
        c_type = clean_token(subgroup_type)
        return f"DOBS_{c_state}_{c_dist}_{c_sno}_{c_type}_{reporting_month}"

    @classmethod
    def extract_long_records(
        cls,
        df: pd.DataFrame,
        financial_year: str = "2015-16",
        state: str = "Tamil Nadu",
        source_file: str = "hmis-item-rpt-tn-for-2015-16.csv"
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Converts wide-format district HMIS DataFrame into normalized long-format records.
        Returns: (long_records, errors)
        """
        month_mapping = cls.get_fiscal_month_mapping(financial_year)
        ingested_at = datetime.now(timezone.utc).isoformat()

        long_records: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        seen_keys: set = set()

        # Map column names in case of case/whitespace differences
        col_lookup = {col.strip().lower(): col for col in df.columns}
        dist_col = col_lookup.get("district", "District")
        sno_col = col_lookup.get("s.no.", col_lookup.get("s_no", "S.No."))
        param_col = col_lookup.get("parameters", col_lookup.get("parameter", "Parameters"))
        type_col = col_lookup.get("type", "Type")
        total_col = col_lookup.get("total", "Total")

        month_cols = {}
        for m in cls.MONTH_ORDER:
            m_lower = m.lower()
            if m_lower in col_lookup:
                month_cols[m] = col_lookup[m_lower]
            else:
                errors.append({
                    "row": None,
                    "code": "MISSING_MONTH_COLUMN",
                    "message": f"Required month column '{m}' was not found in dataset."
                })

        for row_idx, row in df.iterrows():
            raw_dist = str(row.get(dist_col, "")).strip()
            raw_sno = str(row.get(sno_col, "")).strip()
            raw_param = str(row.get(param_col, "")).strip()
            raw_type = str(row.get(type_col, "TOTAL")).strip() or "TOTAL"
            raw_total = row.get(total_col, None)

            if not raw_dist or not raw_sno:
                errors.append({
                    "row": row_idx + 1,
                    "code": "EMPTY_ESSENTIAL_FIELD",
                    "message": f"Row {row_idx + 1} is missing District or S.No."
                })
                continue

            parsed_total, _ = cls.parse_cell_value(raw_total)
            is_sub_total = classify_subgroup_total(raw_type)
            ind_id = cls.map_indicator_code(raw_sno, raw_param)

            for m_name, (m_period, m_date) in month_mapping.items():
                m_col_actual = month_cols.get(m_name)
                val_raw = row.get(m_col_actual) if m_col_actual else None
                num_val, val_type = cls.parse_cell_value(val_raw)

                natural_key = (raw_dist, raw_sno, raw_type, m_period)
                if natural_key in seen_keys:
                    errors.append({
                        "row": row_idx + 1,
                        "code": "DUPLICATE_NATURAL_KEY",
                        "message": f"Duplicate natural key detected: District='{raw_dist}', S.No='{raw_sno}', Type='{raw_type}', Month='{m_period}'"
                    })
                    continue
                seen_keys.add(natural_key)

                obs_id = cls.generate_observation_id(state, raw_dist, raw_sno, raw_type, m_period)

                record = {
                    "id": obs_id,
                    "state": state,
                    "district": raw_dist,
                    "s_no": raw_sno,
                    "parameter_name": raw_param,
                    "subgroup_type": raw_type,
                    "is_subgroup_total": is_sub_total,
                    "indicator_id": ind_id,
                    "financial_year": financial_year,
                    "reporting_month": m_period,
                    "observation_date": m_date,
                    "value": num_val,
                    "value_type": val_type,
                    "validation_status": "VALIDATED",
                    "reported_annual_total": parsed_total,
                    "source_file": source_file,
                    "source_row": row_idx + 1,
                    "ingested_at": ingested_at,
                    "transformation_version": "1.0.0",
                }
                long_records.append(record)

        return long_records, errors

    @classmethod
    def to_wide_dataframe(cls, long_records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Reverses the wide-to-long transformation by re-pivoting long records back into
        the canonical 17-column format (District, S.No., Parameters, Type, April..March, Total).
        Guarantees 100% round-trip reversibility.
        """
        if not long_records:
            return pd.DataFrame(columns=["District", "S.No.", "Parameters", "Type"] + cls.MONTH_ORDER + ["Total"])

        df_long = pd.DataFrame(long_records)
        period_to_month = {
            m_period: m_name
            for m_name, (m_period, _) in cls.get_fiscal_month_mapping(
                df_long["financial_year"].iloc[0] if "financial_year" in df_long.columns else "2015-16"
            ).items()
        }
        df_long["month_name"] = df_long["reporting_month"].map(period_to_month)

        pivoted = df_long.pivot(
            index=["district", "s_no", "parameter_name", "subgroup_type", "reported_annual_total"],
            columns="month_name",
            values="value"
        ).reset_index()

        pivoted = pivoted.rename(columns={
            "district": "District",
            "s_no": "S.No.",
            "parameter_name": "Parameters",
            "subgroup_type": "Type",
            "reported_annual_total": "Total",
        })

        cols_order = ["District", "S.No.", "Parameters", "Type"] + [m for m in cls.MONTH_ORDER if m in pivoted.columns] + ["Total"]
        return pivoted[cols_order]

    @classmethod
    def dry_run(
        cls,
        file_path_or_df: Union[Path, str, pd.DataFrame],
        financial_year: str = "2015-16",
        state: str = "Tamil Nadu"
    ) -> Dict[str, Any]:
        """
        Performs a non-destructive dry-run analysis of a district HMIS dataset,
        generating comprehensive data quality, missing value, arithmetic, and
        disaggregation diagnostics without touching the database.
        """
        if isinstance(file_path_or_df, (str, Path)):
            p = Path(file_path_or_df)
            df = pd.read_csv(p, low_memory=False)
            filename = p.name
        else:
            df = file_path_or_df.copy()
            filename = "in_memory_dataframe.csv"

        long_records, errors = cls.extract_long_records(
            df=df,
            financial_year=financial_year,
            state=state,
            source_file=filename
        )

        val_types = {"VALID": 0, "ZERO": 0, "MISSING": 0, "INVALID": 0}
        subgroup_totals = 0
        subgroup_slices = 0

        for r in long_records:
            vt = r.get("value_type", "MISSING")
            val_types[vt] = val_types.get(vt, 0) + 1
            if r.get("is_subgroup_total", True):
                subgroup_totals += 1
            else:
                subgroup_slices += 1

        # Arithmetic sum verification on wide rows
        months_num = [m for m in cls.MONTH_ORDER if m in df.columns]
        df_num = df.copy()
        for m in months_num + ["Total"]:
            if m in df_num.columns:
                df_num[m] = pd.to_numeric(df_num[m], errors="coerce")

        calc_sum = df_num[months_num].sum(axis=1, min_count=1)
        reported_tot = df_num["Total"] if "Total" in df_num.columns else pd.Series(np.nan, index=df_num.index)

        has_both = calc_sum.notna() & reported_tot.notna()
        matches = (np.isclose(calc_sum[has_both], reported_tot[has_both], atol=1e-3)).sum() if has_both.any() else 0
        mismatches = int(has_both.sum() - matches)

        sno_col = next((c for c in df.columns if c.strip().lower() in ["s.no.", "s_no"]), "S.No.")
        stock_metrics_count = int(df[sno_col].astype(str).str.strip().isin(cls.NON_ADDITIVE_SNO_ITEMS).sum())

        return {
            "source_filename": filename,
            "financial_year": financial_year,
            "state": state,
            "total_source_rows": len(df),
            "total_monthly_records": len(long_records),
            "records_by_value_type": val_types,
            "subgroup_totals_count": subgroup_totals,
            "subgroup_slices_count": subgroup_slices,
            "districts_count": df["District"].nunique() if "District" in df.columns else 0,
            "parameters_count": df[sno_col].nunique() if sno_col in df.columns else 0,
            "arithmetic_sum_matches": int(matches),
            "arithmetic_sum_mismatches": mismatches,
            "non_additive_stock_rows": stock_metrics_count,
            "validation_errors_count": len(errors),
            "validation_errors": errors[:20],
        }

    @classmethod
    def ingest_dataset(
        cls,
        db: Session,
        file_path_or_df: Union[Path, str, pd.DataFrame],
        job: Optional[ImportJob] = None,
        financial_year: str = "2015-16",
        state: str = "Tamil Nadu",
        batch_size: int = 500
    ) -> Dict[str, Any]:
        """
        Parses and persists a district HMIS dataset into the district_observations table
        with transactional boundaries, cancellation support, and change record tracking.
        """
        if isinstance(file_path_or_df, (str, Path)):
            p = Path(file_path_or_df)
            df = pd.read_csv(p, low_memory=False)
            filename = p.name
        else:
            df = file_path_or_df.copy()
            filename = "in_memory_dataframe.csv"

        long_records, errors = cls.extract_long_records(
            df=df,
            financial_year=financial_year,
            state=state,
            source_file=filename
        )

        job_id = job.id if job else None

        # Log any pre-flight extraction errors
        if job:
            for err in errors:
                err_log = ImportErrorLog(
                    import_job_id=job.id,
                    source_row=err.get("row"),
                    error_code=err.get("code", "PARSE_ERROR"),
                    severity="ERROR",
                    message=err.get("message", "Error parsing row")
                )
                db.add(err_log)
            db.flush()

        imported_count = 0
        total_count = len(long_records)

        # Chunked persistence loop
        for i in range(0, total_count, batch_size):
            chunk = long_records[i : i + batch_size]

            for rec in chunk:
                obs_pk = rec["id"]
                val = rec["value"]
                val_type = rec["value_type"]
                existing_obs = db.query(DistrictObservation).filter(DistrictObservation.id == obs_pk).first()

                if existing_obs:
                    will_update = (val is not None or existing_obs.value is None)
                    is_different = will_update and ((existing_obs.value != val) or (existing_obs.value_type != val_type))
                    action = "UPDATE" if is_different else "UNCHANGED"

                    if job_id:
                        change_rec = ImportObservationRecord(
                            import_job_id=job_id,
                            observation_id=obs_pk,
                            action=action,
                            previous_value=existing_obs.value,
                            previous_value_type=existing_obs.value_type,
                            previous_validation_status=existing_obs.validation_status,
                            previous_source_file=existing_obs.source_file,
                            previous_source_sheet=None,
                            previous_source_row=existing_obs.source_row,
                            previous_ingested_at=existing_obs.ingested_at,
                            previous_transformation_version=existing_obs.transformation_version,
                            previous_import_job_id=existing_obs.last_import_job_id,
                            new_value=val,
                            new_value_type=val_type,
                        )
                        db.add(change_rec)

                    if is_different:
                        existing_obs.value = val
                        existing_obs.value_type = val_type
                        existing_obs.validation_status = rec["validation_status"]
                        existing_obs.reported_annual_total = rec["reported_annual_total"]
                        existing_obs.source_file = rec["source_file"]
                        existing_obs.source_row = rec["source_row"]
                        existing_obs.ingested_at = rec["ingested_at"]
                        existing_obs.last_import_job_id = job_id
                else:
                    obs_entity = DistrictObservation(
                        id=obs_pk,
                        state=rec["state"],
                        district=rec["district"],
                        s_no=rec["s_no"],
                        parameter_name=rec["parameter_name"],
                        subgroup_type=rec["subgroup_type"],
                        is_subgroup_total=rec["is_subgroup_total"],
                        indicator_id=rec["indicator_id"],
                        financial_year=rec["financial_year"],
                        reporting_month=rec["reporting_month"],
                        observation_date=rec["observation_date"],
                        value=val,
                        value_type=val_type,
                        validation_status=rec["validation_status"],
                        reported_annual_total=rec["reported_annual_total"],
                        source_file=rec["source_file"],
                        source_row=rec["source_row"],
                        ingested_at=rec["ingested_at"],
                        transformation_version=rec["transformation_version"],
                        last_import_job_id=job_id
                    )
                    db.add(obs_entity)

                    if job_id:
                        change_rec = ImportObservationRecord(
                            import_job_id=job_id,
                            observation_id=obs_pk,
                            action="INSERT",
                            previous_value=None,
                            previous_value_type=None,
                            previous_validation_status=None,
                            previous_source_file=None,
                            previous_source_sheet=None,
                            previous_source_row=None,
                            previous_ingested_at=None,
                            previous_transformation_version=None,
                            previous_import_job_id=None,
                            new_value=val,
                            new_value_type=val_type,
                        )
                        db.add(change_rec)

                imported_count += 1

            db.flush()

            if job:
                now = datetime.now(timezone.utc)
                job.processed_records = imported_count
                job.records_imported = imported_count
                job.heartbeat_at = now
                job.updated_at = now
                db.commit()

        if job:
            now = datetime.now(timezone.utc)
            job.total_records = total_count
            job.processed_records = total_count
            job.records_imported = imported_count
            job.records_rejected = len(errors)
            job.status = "COMPLETED_WITH_WARNINGS" if len(errors) > 0 else "COMPLETED"
            job.completed_at = now
            job.updated_at = now
            db.commit()

        return {
            "total_records": total_count,
            "records_imported": imported_count,
            "records_rejected": len(errors),
            "status": "COMPLETED_WITH_WARNINGS" if len(errors) > 0 else "COMPLETED"
        }
