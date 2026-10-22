import csv
import io
from typing import Generator, Optional, List, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import func
import statistics

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.services.analytics.district_analytics import DistrictAnalyticsService

MAX_EXPORT_ROWS = 10000


def sanitize_csv_cell(val: Any) -> str:
    """
    Sanitizes values against formula injection (OWASP CSV Injection).
    If a string value starts with =, +, -, @, tab, or carriage return,
    prepends a single quote (') so spreadsheet applications evaluate it
    as literal text rather than executable macro/formula expressions.
    """
    if val is None:
        return ""
    if isinstance(val, bool):
        return "true" if val else "false"
    if isinstance(val, (int, float)):
        return str(val)

    s = str(val)
    if not s:
        return ""
    if s[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{s}"
    stripped = s.strip()
    if stripped and stripped[0] in ("=", "+", "-", "@", "\t", "\r"):
        return f"'{stripped}"
    return stripped



class DistrictExportService:
    def __init__(self, db: Session):
        self.db = db

    def export_trends_csv(
        self,
        district: str,
        s_no: str,
        subgroup_type: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        financial_year: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Streams filtered monthly observations as RFC 4180 compliant CSV.
        Strictly preserves zero vs missing values and sanitizes against formula injection.
        """
        # Metadata / provenance banner comments
        yield f"# CAREFlow India — District HMIS Observations Export\n"
        yield f"# Source: MoHFW / NHM Tamil Nadu State Performance Report Archives\n"
        yield f"# District: {district} | Indicator S.No: {s_no}\n"
        yield f"# Integrity Rule: Missing values are represented as empty cells; numeric zero is represented as '0'.\n"

        headers = [
            "district",
            "s_no",
            "parameter_name",
            "reporting_month",
            "financial_year",
            "observation_date",
            "value",
            "value_type",
            "subgroup_type",
            "is_subgroup_total",
            "reported_annual_total",
            "source_file",
            "source_row",
            "last_import_job_id",
            "transformation_version",
        ]

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        query = self.db.query(DistrictObservation).filter(
            func.lower(DistrictObservation.district) == district.lower().strip(),
            func.lower(DistrictObservation.s_no) == s_no.lower().strip(),
        )

        if subgroup_type:
            query = query.filter(
                func.lower(DistrictObservation.subgroup_type) == subgroup_type.lower().strip()
            )
        if start_month:
            query = query.filter(DistrictObservation.reporting_month >= start_month)
        if end_month:
            query = query.filter(DistrictObservation.reporting_month <= end_month)
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year.strip())

        query = query.order_by(
            DistrictObservation.reporting_month.asc(),
            DistrictObservation.subgroup_type.asc(),
        ).limit(MAX_EXPORT_ROWS)

        records = query.all()

        for obs in records:
            # Missing value represented as empty string; zero represented as "0"
            val_str = "" if obs.value is None else str(obs.value)
            ann_total_str = "" if obs.reported_annual_total is None else str(obs.reported_annual_total)

            row = [
                sanitize_csv_cell(obs.district),
                sanitize_csv_cell(obs.s_no),
                sanitize_csv_cell(obs.parameter_name),
                sanitize_csv_cell(obs.reporting_month),
                sanitize_csv_cell(obs.financial_year),
                sanitize_csv_cell(obs.observation_date.isoformat() if hasattr(obs.observation_date, "isoformat") else (str(obs.observation_date) if obs.observation_date else "")),
                val_str,
                sanitize_csv_cell(obs.value_type),
                sanitize_csv_cell(obs.subgroup_type),
                "true" if obs.is_subgroup_total else "false",
                ann_total_str,
                sanitize_csv_cell(obs.source_file),
                str(obs.source_row) if obs.source_row is not None else "",
                str(obs.last_import_job_id) if obs.last_import_job_id is not None else "",
                sanitize_csv_cell(obs.transformation_version),
            ]
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)

    def export_comparison_csv(
        self,
        s_no: str,
        reporting_month: str,
        subgroup_type: Optional[str] = None,
        districts: Optional[List[str]] = None,
        financial_year: Optional[str] = None,
    ) -> Generator[str, None, None]:
        """
        Streams cross-district comparison observations as RFC 4180 compliant CSV.
        Includes state mean, median, and district rankings.
        """
        # Resolve subgroup_type if not specified to prevent mixed-subgroup duplicate ranking
        if not subgroup_type:
            avail = [
                r[0] for r in self.db.query(DistrictObservation.subgroup_type)
                .filter(
                    func.lower(DistrictObservation.s_no) == s_no.lower().strip(),
                    DistrictObservation.reporting_month == reporting_month.strip()
                )
                .distinct().all()
            ]
            if avail:
                for preferred in ["TOTAL", "Total", "4. Total", "3. Total"]:
                    if preferred in avail:
                        subgroup_type = preferred
                        break
                if not subgroup_type:
                    subgroup_type = avail[0]

        resolved_sg = subgroup_type or "All"
        yield f"# CAREFlow India — Cross-District HMIS Comparison Export\n"
        yield f"# Indicator S.No: {s_no} | Reporting Period: {reporting_month} | Subgroup: {resolved_sg}\n"
        yield f"# Note: Cross-district comparisons display raw counts; variations reflect geographic scale and population size.\n"

        headers = [
            "district",
            "s_no",
            "parameter_name",
            "reporting_month",
            "financial_year",
            "value",
            "value_type",
            "rank",
            "reported_annual_total",
            "state_mean",
            "state_median",
            "state_total",
        ]

        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(headers)
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)

        query = self.db.query(DistrictObservation).filter(
            func.lower(DistrictObservation.s_no) == s_no.lower().strip(),
            DistrictObservation.reporting_month == reporting_month.strip(),
        )

        if subgroup_type:
            query = query.filter(
                func.lower(DistrictObservation.subgroup_type) == subgroup_type.lower().strip()
            )
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year.strip())
        if districts and len(districts) > 0:
            clean_dists = [d.lower().strip() for d in districts]
            query = query.filter(func.lower(DistrictObservation.district).in_(clean_dists))

        query = query.order_by(DistrictObservation.district.asc()).limit(MAX_EXPORT_ROWS)
        records = query.all()

        # Compute summary stats across valid observations
        numeric_vals = [r.value for r in records if r.value is not None]
        state_mean = round(statistics.mean(numeric_vals), 2) if numeric_vals else None
        state_median = round(statistics.median(numeric_vals), 2) if numeric_vals else None
        state_total = round(sum(numeric_vals), 2) if numeric_vals else None

        # Determine ranks (highest value = rank 1, missing = no rank)
        ranked_records = sorted(
            [r for r in records if r.value is not None],
            key=lambda x: (x.value if x.value is not None else -1),
            reverse=True,
        )
        rank_map: Dict[str, int] = {
            r.district: idx + 1 for idx, r in enumerate(ranked_records)
        }

        for obs in records:
            val_str = "" if obs.value is None else str(obs.value)
            rank_str = str(rank_map[obs.district]) if obs.district in rank_map else ""
            ann_total_str = "" if obs.reported_annual_total is None else str(obs.reported_annual_total)

            row = [
                sanitize_csv_cell(obs.district),
                sanitize_csv_cell(obs.s_no),
                sanitize_csv_cell(obs.parameter_name),
                sanitize_csv_cell(obs.reporting_month),
                sanitize_csv_cell(obs.financial_year),
                val_str,
                sanitize_csv_cell(obs.value_type),
                rank_str,
                ann_total_str,
                str(state_mean) if state_mean is not None else "",
                str(state_median) if state_median is not None else "",
                str(state_total) if state_total is not None else "",
            ]
            writer.writerow(row)
            yield output.getvalue()
            output.seek(0)
            output.truncate(0)
