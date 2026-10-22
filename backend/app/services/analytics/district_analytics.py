import statistics
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException, status

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.indicator import Indicator
from backend.app.db.models.import_job import ImportJob
from backend.app.services.imports.district_adapter import DistrictHMISAdapter
from backend.app.services.analytics.indicator_registry import IndicatorMappingRegistry, MappingStatus
from backend.app.schemas.district_analytics import (
    DistrictCatalogResponse,
    DistrictIndicatorItem,
    DistrictIndicatorCatalogResponse,
    DistrictTrendObservation,
    DistrictMonthlyTrendsResponse,
    DistrictComparisonItem,
    DistrictComparisonResponse,
    DistrictCoverageItem,
    DistrictDataQualitySummaryResponse,
    IndicatorMappingItem,
    IndicatorRegistryResponse,
    IndicatorAuditReportResponse,
)


class DistrictAnalyticsService:
    """
    Read-only analytics service for District-Level HMIS monthly performance datasets.
    Provides catalog discovery, temporal monthly trends, district cross-comparison,
    and data quality summaries while strictly preserving data separation from facility observations.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_catalog_and_coverage(self) -> DistrictCatalogResponse:
        """Returns district names, reporting periods, and explicit coverage metadata."""
        districts = [
            r[0] for r in self.db.query(DistrictObservation.district).distinct().order_by(DistrictObservation.district.asc()).all()
            if r[0]
        ]
        periods = [
            r[0] for r in self.db.query(DistrictObservation.reporting_month).distinct().order_by(DistrictObservation.reporting_month.asc()).all()
            if r[0]
        ]
        years = [
            r[0] for r in self.db.query(DistrictObservation.financial_year).distinct().order_by(DistrictObservation.financial_year.asc()).all()
            if r[0]
        ]
        subgroups = [
            r[0] for r in self.db.query(DistrictObservation.subgroup_type).distinct().order_by(DistrictObservation.subgroup_type.asc()).all()
            if r[0]
        ]
        total_obs = self.db.query(func.count(DistrictObservation.id)).scalar() or 0

        limitations = [
            "Official administrative dataset: MoHFW / NHM Tamil Nadu State Performance Report (FY 2015-16).",
            "Observed temporal range is strictly bounded from April 2015 (2015-04) to March 2016 (2016-03).",
            "Macro district records are isolated from micro facility observations; they must never be summed together.",
            "Non-additive infrastructure and stock metrics (e.g. S.No. 14.01) cannot be summed across months.",
            "Missing cells are recorded with MISSING status and must not be interpreted as zero healthcare activity."
        ]

        return DistrictCatalogResponse(
            districts=districts,
            reporting_periods=periods,
            financial_years=years,
            subgroup_types=subgroups,
            total_observed_records=total_obs,
            source_name="MoHFW / NHM District Item Performance Report (Tamil Nadu)",
            geographic_level="District Level (32 Districts of Tamil Nadu)",
            limitations=limitations
        )

    def get_indicator_catalog(self) -> DistrictIndicatorCatalogResponse:
        """Returns list of distinct source parameters, available subgroups, and verified crosswalks."""
        params = (
            self.db.query(DistrictObservation.s_no, DistrictObservation.parameter_name)
            .distinct()
            .order_by(DistrictObservation.s_no.asc())
            .all()
        )

        indicator_cache = {
            ind.id: ind.name for ind in self.db.query(Indicator).all()
        }

        # Pre-fetch all subgroups grouped by s_no
        subgroups_query = (
            self.db.query(DistrictObservation.s_no, DistrictObservation.subgroup_type)
            .distinct()
            .all()
        )
        subgroup_map: Dict[str, List[str]] = {}
        for s_no, sg in subgroups_query:
            if s_no not in subgroup_map:
                subgroup_map[s_no] = []
            subgroup_map[s_no].append(sg)

        items: List[DistrictIndicatorItem] = []
        mapped_count = 0
        unmapped_count = 0

        for s_no, param_name in params:
            mapping = IndicatorMappingRegistry.get_mapping(s_no, param_name)
            is_mapped = mapping.status.value == "VERIFIED"

            if is_mapped:
                mapped_count += 1
            else:
                unmapped_count += 1

            items.append(
                DistrictIndicatorItem(
                    s_no=s_no,
                    parameter_name=param_name,
                    available_subgroups=sorted(subgroup_map.get(s_no, ["TOTAL"])),
                    is_stock_metric=mapping.is_stock_metric,
                    is_mapped=is_mapped,
                    canonical_indicator_id=mapping.canonical_id,
                    canonical_indicator_name=mapping.canonical_name,
                    mapping_status=mapping.status.value
                )
            )

        return DistrictIndicatorCatalogResponse(
            total_indicators=len(items),
            mapped_count=mapped_count,
            unmapped_count=unmapped_count,
            indicators=items
        )

    def get_monthly_trends(
        self,
        district: str,
        s_no: str,
        subgroup_type: Optional[str] = None,
        start_month: Optional[str] = None,
        end_month: Optional[str] = None,
        financial_year: Optional[str] = None,
    ) -> DistrictMonthlyTrendsResponse:
        """Fetches chronological monthly observations for a single district and indicator."""
        # Validate district exists
        district_exists = self.db.query(DistrictObservation.id).filter(
            DistrictObservation.district.ilike(district)
        ).first()
        if not district_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"District '{district}' not found in official district observations."
            )

        # Validate S.No. exists
        param_row = self.db.query(DistrictObservation.parameter_name).filter(
            DistrictObservation.s_no == s_no
        ).first()
        if not param_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator S.No. '{s_no}' not found in district dataset."
            )
        parameter_name = param_row[0]

        # Determine subgroup if not specified
        if not subgroup_type:
            # Prefer TOTAL, 4. Total, 3. Total, or first available
            available_subgroups = [
                r[0] for r in self.db.query(DistrictObservation.subgroup_type)
                .filter(DistrictObservation.district.ilike(district), DistrictObservation.s_no == s_no)
                .distinct().all()
            ]
            if not available_subgroups:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No subgroup records found for district '{district}' and indicator '{s_no}'."
                )
            for preferred in ["TOTAL", "Total", "4. Total", "3. Total"]:
                if preferred in available_subgroups:
                    subgroup_type = preferred
                    break
            if not subgroup_type:
                subgroup_type = available_subgroups[0]

        query = self.db.query(DistrictObservation).filter(
            DistrictObservation.district.ilike(district),
            DistrictObservation.s_no == s_no,
            DistrictObservation.subgroup_type == subgroup_type
        )

        if start_month:
            query = query.filter(DistrictObservation.reporting_month >= start_month)
        if end_month:
            query = query.filter(DistrictObservation.reporting_month <= end_month)
        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year.strip())

        records = query.order_by(DistrictObservation.reporting_month.asc()).all()

        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No observations found for district '{district}', S.No. '{s_no}', subgroup '{subgroup_type}'."
            )

        obs_items: List[DistrictTrendObservation] = []
        valid_cnt = 0
        zero_cnt = 0
        missing_cnt = 0
        valid_values: List[float] = []
        reported_annual_tot: Optional[float] = None

        for r in records:
            if r.value_type == "VALID" and r.value is not None:
                valid_cnt += 1
                valid_values.append(r.value)
            elif r.value_type == "ZERO":
                zero_cnt += 1
                valid_values.append(0.0)
            elif r.value_type == "MISSING":
                missing_cnt += 1

            if r.reported_annual_total is not None and reported_annual_tot is None:
                reported_annual_tot = r.reported_annual_total

            obs_items.append(
                DistrictTrendObservation(
                    id=r.id,
                    reporting_month=r.reporting_month,
                    observation_date=r.observation_date,
                    value=r.value,
                    value_type=r.value_type,
                    subgroup_type=r.subgroup_type,
                    is_subgroup_total=r.is_subgroup_total,
                    reported_annual_total=r.reported_annual_total,
                    source_file=r.source_file,
                    source_row=r.source_row,
                    transformation_version=r.transformation_version,
                    last_import_job_id=r.last_import_job_id
                )
            )

        is_stock = s_no in DistrictHMISAdapter.NON_ADDITIVE_SNO_ITEMS
        calc_sum = sum(valid_values) if (not is_stock and (valid_cnt > 0 or zero_cnt > 0)) else None

        canonical_id = DistrictHMISAdapter.CORE_INDICATOR_CROSSWALK.get(s_no.lower())
        canonical_name = None
        if canonical_id:
            ind = self.db.query(Indicator).filter(Indicator.id == canonical_id).first()
            canonical_name = ind.name if ind else None

        return DistrictMonthlyTrendsResponse(
            district=records[0].district,
            s_no=s_no,
            parameter_name=parameter_name,
            subgroup_type=subgroup_type,
            is_subgroup_total=records[0].is_subgroup_total,
            is_stock_metric=is_stock,
            canonical_indicator_id=canonical_id,
            canonical_indicator_name=canonical_name,
            annual_total_reported=reported_annual_tot,
            calculated_sum=calc_sum,
            valid_months_count=valid_cnt,
            zero_months_count=zero_cnt,
            missing_months_count=missing_cnt,
            total_months_count=len(records),
            observations=obs_items
        )

    def get_district_comparison(
        self,
        s_no: str,
        reporting_month: str,
        subgroup_type: Optional[str] = None,
        districts: Optional[List[str]] = None,
        financial_year: Optional[str] = None,
    ) -> DistrictComparisonResponse:
        """Cross-district comparison for a specified indicator and period."""
        # Validate S.No.
        param_row = self.db.query(DistrictObservation.parameter_name).filter(
            DistrictObservation.s_no == s_no
        ).first()
        if not param_row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Indicator S.No. '{s_no}' not found in district dataset."
            )
        parameter_name = param_row[0]

        # Determine subgroup
        if not subgroup_type:
            avail = [
                r[0] for r in self.db.query(DistrictObservation.subgroup_type)
                .filter(DistrictObservation.s_no == s_no, DistrictObservation.reporting_month == reporting_month)
                .distinct().all()
            ]
            if not avail:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"No records found for S.No. '{s_no}' in period '{reporting_month}'."
                )
            for preferred in ["TOTAL", "Total", "4. Total", "3. Total"]:
                if preferred in avail:
                    subgroup_type = preferred
                    break
            if not subgroup_type:
                subgroup_type = avail[0]

        query = self.db.query(DistrictObservation).filter(
            DistrictObservation.s_no == s_no,
            DistrictObservation.reporting_month == reporting_month,
            DistrictObservation.subgroup_type == subgroup_type
        )

        if financial_year:
            query = query.filter(DistrictObservation.financial_year == financial_year.strip())

        if districts:
            query = query.filter(DistrictObservation.district.in_(districts))

        records = query.order_by(DistrictObservation.district.asc()).all()
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No district records matched criteria for period '{reporting_month}' and subgroup '{subgroup_type}'."
            )

        is_stock = s_no in DistrictHMISAdapter.NON_ADDITIVE_SNO_ITEMS
        is_sub_tot = records[0].is_subgroup_total

        # Rank items by value (handling missing values at the end)
        sorted_for_rank = sorted(
            records,
            key=lambda x: (x.value is not None, x.value if x.value is not None else -float("inf")),
            reverse=True
        )
        rank_map = {}
        current_rank = 1
        for rec in sorted_for_rank:
            if rec.value is not None:
                rank_map[rec.id] = current_rank
                current_rank += 1
            else:
                rank_map[rec.id] = None

        items: List[DistrictComparisonItem] = []
        numeric_vals: List[float] = []

        for r in records:
            if r.value is not None:
                numeric_vals.append(r.value)
            items.append(
                DistrictComparisonItem(
                    district=r.district,
                    value=r.value,
                    value_type=r.value_type,
                    reported_annual_total=r.reported_annual_total,
                    rank=rank_map.get(r.id)
                )
            )

        state_mean = round(statistics.mean(numeric_vals), 2) if numeric_vals else None
        state_median = round(statistics.median(numeric_vals), 2) if numeric_vals else None
        state_tot = round(sum(numeric_vals), 2) if (not is_stock and numeric_vals) else None

        return DistrictComparisonResponse(
            s_no=s_no,
            parameter_name=parameter_name,
            reporting_month=reporting_month,
            subgroup_type=subgroup_type,
            is_subgroup_total=is_sub_tot,
            is_stock_metric=is_stock,
            total_districts=len(items),
            reporting_districts=len(numeric_vals),
            state_mean=state_mean,
            state_median=state_median,
            state_total=state_tot,
            items=items
        )

    def get_data_quality_summary(self) -> DistrictDataQualitySummaryResponse:
        """Generates comprehensive data quality and coverage diagnostics for district observations."""
        total_obs = self.db.query(func.count(DistrictObservation.id)).scalar() or 0

        # Value counts
        val_rows = (
            self.db.query(DistrictObservation.value_type, func.count(DistrictObservation.id))
            .group_by(DistrictObservation.value_type)
            .all()
        )
        val_counts = {vt: cnt for vt, cnt in val_rows}

        subgroup_totals = self.db.query(func.count(DistrictObservation.id)).filter(
            DistrictObservation.is_subgroup_total == True
        ).scalar() or 0
        subgroup_slices = total_obs - subgroup_totals

        # Distinct counts
        dist_count = self.db.query(func.count(func.distinct(DistrictObservation.district))).scalar() or 0
        param_count = self.db.query(func.count(func.distinct(DistrictObservation.s_no))).scalar() or 0

        # Stock metrics count
        stock_rows = self.db.query(func.count(DistrictObservation.id)).filter(
            DistrictObservation.s_no.in_(DistrictHMISAdapter.NON_ADDITIVE_SNO_ITEMS)
        ).scalar() or 0
        stock_metrics_wide_count = stock_rows // 12 if total_obs > 0 else 0

        # District-level breakdown
        dist_breakdown_rows = (
            self.db.query(
                DistrictObservation.district,
                DistrictObservation.value_type,
                func.count(DistrictObservation.id)
            )
            .group_by(DistrictObservation.district, DistrictObservation.value_type)
            .all()
        )
        dist_map: Dict[str, Dict[str, int]] = {}
        for d, vt, cnt in dist_breakdown_rows:
            if d not in dist_map:
                dist_map[d] = {"VALID": 0, "ZERO": 0, "MISSING": 0, "INVALID": 0}
            dist_map[d][vt] = cnt

        coverage_list: List[DistrictCoverageItem] = []
        for d in sorted(dist_map.keys()):
            d_vals = dist_map[d]
            d_total = sum(d_vals.values())
            non_missing = d_vals.get("VALID", 0) + d_vals.get("ZERO", 0)
            comp_pct = round((non_missing / d_total * 100), 2) if d_total > 0 else 0.0
            coverage_list.append(
                DistrictCoverageItem(
                    district=d,
                    total_records=d_total,
                    valid_records=d_vals.get("VALID", 0),
                    zero_records=d_vals.get("ZERO", 0),
                    missing_records=d_vals.get("MISSING", 0),
                    completeness_pct=comp_pct
                )
            )

        # Retrieve latest import job metadata
        latest_job = (
            self.db.query(ImportJob)
            .filter(ImportJob.schema_profile == "district_monthly_tabular_v1")
            .order_by(ImportJob.id.desc())
            .first()
        )
        job_dict = None
        if latest_job:
            job_dict = {
                "id": latest_job.id,
                "job_code": latest_job.job_code,
                "original_filename": latest_job.original_filename,
                "status": latest_job.status,
                "total_records": latest_job.total_records,
                "records_imported": latest_job.records_imported,
                "records_rejected": latest_job.records_rejected,
                "completed_at": latest_job.completed_at.isoformat() if latest_job.completed_at else None,
                "schema_profile": latest_job.schema_profile,
            }

        return DistrictDataQualitySummaryResponse(
            total_records=total_obs,
            value_counts=val_counts,
            subgroup_totals_count=subgroup_totals,
            subgroup_slices_count=subgroup_slices,
            non_additive_stock_rows=stock_metrics_wide_count,
            districts_count=dist_count,
            parameters_count=param_count,
            import_job=job_dict,
            district_coverage=coverage_list,
            audit_timestamp=datetime.now(timezone.utc).isoformat()
        )

    def get_indicator_registry(self, status_filter: Optional[str] = None) -> IndicatorRegistryResponse:
        """Fetches all observed indicators from the verified mapping registry with audit metadata."""
        records = IndicatorMappingRegistry.get_all_mappings(self.db, status_filter=status_filter)
        verified = sum(1 for r in records if r.status == MappingStatus.VERIFIED)
        unmapped = sum(1 for r in records if r.status == MappingStatus.UNMAPPED)
        return IndicatorRegistryResponse(
            total_items=len(records),
            verified_count=verified,
            unmapped_count=unmapped,
            items=[IndicatorMappingItem(**r.to_dict()) for r in records]
        )

    def get_indicator_audit_report(self) -> IndicatorAuditReportResponse:
        """Generates a formal indicator mapping audit report with clinical definitions and provenance."""
        summary = IndicatorMappingRegistry.get_audit_summary(self.db)
        return IndicatorAuditReportResponse(
            total_parameters_observed=summary["total_parameters_observed"],
            verified_mappings_count=summary["verified_mappings_count"],
            ambiguous_mappings_count=summary.get("ambiguous_mappings_count", 0),
            provisional_mappings_count=summary["provisional_mappings_count"],
            unmapped_parameters_count=summary["unmapped_parameters_count"],
            verified_percentage=summary["verified_percentage"],
            unmapped_percentage=summary["unmapped_percentage"],
            stock_metrics_count=summary["stock_metrics_count"],
            verified_mappings=[IndicatorMappingItem(**vm) for vm in summary["verified_mappings"]],
            ambiguous_mappings=[IndicatorMappingItem(**am) for am in summary.get("ambiguous_mappings", [])],
            unmapped_indicators_sample=summary["unmapped_indicators_sample"],
            governance_note=summary["governance_note"],
            audit_timestamp=summary["audit_timestamp"]
        )
