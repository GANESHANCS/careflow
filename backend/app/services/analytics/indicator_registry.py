from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.db.models.district_observation import DistrictObservation
from backend.app.db.models.indicator import Indicator


class MappingStatus(str, Enum):
    VERIFIED = "VERIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    UNVERIFIED = "UNVERIFIED"
    PROVISIONAL = "PROVISIONAL"
    UNMAPPED = "UNMAPPED"


class IndicatorMappingRecord:
    def __init__(
        self,
        s_no: str,
        parameter_name: str,
        canonical_id: Optional[str] = None,
        canonical_name: Optional[str] = None,
        category: Optional[str] = None,
        unit: Optional[str] = None,
        status: MappingStatus = MappingStatus.UNMAPPED,
        rationale: str = "",
        clinical_definition: Optional[str] = None,
        provenance: str = "MoHFW / NHM Tamil Nadu State Performance Report (FY 2015-16)",
        is_stock_metric: bool = False,
        reviewed_at: str = "2026-10-21T00:00:00Z",
    ):
        self.s_no = s_no
        self.parameter_name = parameter_name
        self.canonical_id = canonical_id
        self.canonical_name = canonical_name
        self.category = category
        self.unit = unit
        self.status = status
        self.rationale = rationale
        self.clinical_definition = clinical_definition
        self.provenance = provenance
        self.is_stock_metric = is_stock_metric
        self.reviewed_at = reviewed_at

    def to_dict(self) -> Dict[str, Any]:
        return {
            "s_no": self.s_no,
            "parameter_name": self.parameter_name,
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "category": self.category,
            "unit": self.unit,
            "status": self.status.value,
            "rationale": self.rationale,
            "clinical_definition": self.clinical_definition,
            "provenance": self.provenance,
            "is_stock_metric": self.is_stock_metric,
            "reviewed_at": self.reviewed_at,
        }


class IndicatorMappingRegistry:
    """
    Central, documented registry managing crosswalks between raw source HMIS indicator
    codes (MoHFW S.No.) and canonical CAREFlow clinical indicator definitions.
    Enforces strict auditability, non-conflation of clinically distinct concepts,
    and clear demarcation between verified, provisional, and unmapped parameters.
    """

    # Verified clinical crosswalk specifications with explicit clinical rationales
    _VERIFIED_REGISTRY: Dict[str, Dict[str, Any]] = {
        "1.1": {
            "canonical_id": "IND_antenatal_visits",
            "canonical_name": "Antenatal Care (ANC) Registered Visits",
            "category": "Maternal Health",
            "unit": "visits",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 1.1: Total pregnant women registered for ANC. "
                "Covers primary trimester registrations and routine antenatal surveillance."
            ),
            "clinical_definition": "Total count of pregnant women registered for antenatal monitoring during reporting period.",
            "provenance": "MoHFW HMIS Operational Guidelines (Maternal & Child Health Indicators Section 1.1)",
        },
        "2.2": {
            "canonical_id": "IND_institutional_deliveries",
            "canonical_name": "Institutional Deliveries",
            "category": "Maternal Health",
            "unit": "deliveries",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 2.2: Institutional deliveries conducted at Public Facilities "
                "(PHC, CHC, SDH, DH). Slices by facility tier must not be double counted."
            ),
            "clinical_definition": "Deliveries occurring in accredited public health sector facilities under skilled birth attendance.",
            "provenance": "MoHFW HMIS Operational Guidelines (Delivery Care Section 2.2)",
        },
        "2.3": {
            "canonical_id": "IND_institutional_deliveries",
            "canonical_name": "Institutional Deliveries",
            "category": "Maternal Health",
            "unit": "deliveries",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 2.3: Institutional deliveries conducted at Private Facilities. "
                "Captures private sector maternity returns."
            ),
            "clinical_definition": "Deliveries occurring in registered private medical institutions under skilled birth attendance.",
            "provenance": "MoHFW HMIS Operational Guidelines (Delivery Care Section 2.3)",
        },
        "6.1": {
            "canonical_id": "IND_postnatal_visits",
            "canonical_name": "Postnatal Care (PNC) Visits",
            "category": "Maternal Health",
            "unit": "visits",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 6.1: Post-partum check-up within 48 hours of delivery. "
                "High-priority early maternal mortality prevention window."
            ),
            "clinical_definition": "Postnatal evaluation of mother and newborn within first 48 hours postpartum.",
            "provenance": "MoHFW HMIS Operational Guidelines (Postnatal Care Section 6.1)",
        },
        "6.2": {
            "canonical_id": "IND_postnatal_visits",
            "canonical_name": "Postnatal Care (PNC) Visits",
            "category": "Maternal Health",
            "unit": "visits",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 6.2: Post-partum check-up between 48 hours and 14 days of delivery. "
                "Captures secondary PNC monitoring visits."
            ),
            "clinical_definition": "Subsequent postnatal check-up completed between 3 and 14 days following delivery.",
            "provenance": "MoHFW HMIS Operational Guidelines (Postnatal Care Section 6.2)",
        },
        "10.1.13.c": {
            "canonical_id": "IND_immunisation",
            "canonical_name": "Full Immunisation Coverage / Doses",
            "category": "Child Health",
            "unit": "children",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 10.1.13.c: Total children aged 9-11 months fully immunised "
                "(BCG, 3 DPT/Pentavalent, 3 OPV, Measles/MR). Slices by sex (10.1.13.a, 10.1.13.b) are distinct."
            ),
            "clinical_definition": "Children completing complete universal primary immunization schedule before first birthday.",
            "provenance": "Universal Immunization Programme (UIP) MoHFW HMIS Guidelines (Child Immunization Section 10.1.13)",
        },
        "14.10.1.c": {
            "canonical_id": "IND_inpatient_admissions",
            "canonical_name": "Inpatient Admissions (IPD) [Disaggregated Slices]",
            "category": "Inpatient Services",
            "unit": "admissions",
            "status": MappingStatus.AMBIGUOUS,
            "rationale": (
                "MoHFW Item 14.10.1.c represents total inpatient admissions (sum of items 14.10.1.a & 14.10.1.b), "
                "but in official state returns it is partitioned into demographic age slices ('1. Children' and '2. Adults') "
                "without an authoritative unified TOTAL row (is_subgroup_total=False). Unqualified mapping to canonical "
                "IND_inpatient_admissions is AMBIGUOUS because queries defaulting to first available subgroup capture only "
                "pediatric admissions and exclude adult patients."
            ),
            "clinical_definition": "Admissions requiring overnight hospitalization; classified as AMBIGUOUS due to absence of unified aggregate total in raw source returns.",
            "provenance": "MoHFW HMIS Operational Guidelines (Facility Services Section 14.10)",
        },
        "14.12.1": {
            "canonical_id": "IND_opd_attendance",
            "canonical_name": "Outpatient Department (OPD) Attendance",
            "category": "Outpatient Services",
            "unit": "visits",
            "status": MappingStatus.VERIFIED,
            "rationale": (
                "Direct clinical equivalent to MoHFW HMIS Item 14.12.1: Outpatient Department attendance (All services combined). "
                "Represents gross patient encounter volume."
            ),
            "clinical_definition": "Total clinical ambulatory consultations conducted across general and specialty outpatient clinics.",
            "provenance": "MoHFW HMIS Operational Guidelines (Facility Services Section 14.12)",
        },
    }

    # Non-additive infrastructure / equipment stock metrics
    _STOCK_METRICS = {
        "9.12", "14.01", "14.02", "14.03", "14.04", "14.06", "14.08", "14.09"
    }

    @classmethod
    def get_mapping(cls, s_no: str, parameter_name: str = "") -> IndicatorMappingRecord:
        """
        Retrieves registry specification for a given source S.No.
        If unmapped, returns a structured UNMAPPED record with verbatim tracking.
        """
        clean_sno = s_no.strip()
        is_stock = clean_sno in cls._STOCK_METRICS

        if clean_sno in cls._VERIFIED_REGISTRY:
            spec = cls._VERIFIED_REGISTRY[clean_sno]
            return IndicatorMappingRecord(
                s_no=clean_sno,
                parameter_name=parameter_name or clean_sno,
                canonical_id=spec["canonical_id"],
                canonical_name=spec["canonical_name"],
                category=spec["category"],
                unit=spec["unit"],
                status=spec["status"],
                rationale=spec["rationale"],
                clinical_definition=spec.get("clinical_definition"),
                provenance=spec["provenance"],
                is_stock_metric=is_stock,
            )

        # Unmapped indicator: return explicit unmapped status without fabricating clinical mappings
        return IndicatorMappingRecord(
            s_no=clean_sno,
            parameter_name=parameter_name or clean_sno,
            canonical_id=None,
            canonical_name=None,
            category=None,
            unit="Count",
            status=MappingStatus.UNMAPPED,
            rationale=(
                f"Source parameter '{clean_sno}' is retained verbatim. No validated canonical CAREFlow "
                "clinical crosswalk has been established under authoritative MoHFW clinical review."
            ),
            clinical_definition=None,
            provenance="MoHFW / NHM Tamil Nadu State Performance Report (FY 2015-16)",
            is_stock_metric=is_stock,
        )

    @classmethod
    def get_all_mappings(
        cls, db: Session, status_filter: Optional[str] = None
    ) -> List[IndicatorMappingRecord]:
        """
        Queries all distinct source parameters present in district observations
        and returns enriched registry records.
        """
        records = (
            db.query(DistrictObservation.s_no, DistrictObservation.parameter_name)
            .distinct()
            .order_by(DistrictObservation.s_no.asc())
            .all()
        )

        results: List[IndicatorMappingRecord] = []
        for s_no, param_name in records:
            rec = cls.get_mapping(s_no, param_name)
            if status_filter:
                filter_upper = status_filter.upper().strip()
                if rec.status.value != filter_upper:
                    continue
            results.append(rec)

        return results

    @classmethod
    def get_audit_summary(cls, db: Session) -> Dict[str, Any]:
        """
        Produces a comprehensive registry audit summary with verified, provisional,
        and unmapped counts, stock metric flags, and provenance references.
        """
        distinct_snos = [
            r[0] for r in db.query(DistrictObservation.s_no).distinct().all()
        ]
        total_parameters = len(distinct_snos)

        verified_records: List[Dict[str, Any]] = []
        ambiguous_records: List[Dict[str, Any]] = []
        unmapped_snos: List[str] = []
        stock_metric_snos: List[str] = []

        for s_no in distinct_snos:
            rec = cls.get_mapping(s_no)
            if rec.status == MappingStatus.VERIFIED:
                verified_records.append(rec.to_dict())
            elif rec.status == MappingStatus.AMBIGUOUS:
                ambiguous_records.append(rec.to_dict())
            else:
                unmapped_snos.append(s_no)

            if rec.is_stock_metric:
                stock_metric_snos.append(s_no)

        return {
            "total_parameters_observed": total_parameters,
            "verified_mappings_count": len(verified_records),
            "ambiguous_mappings_count": len(ambiguous_records),
            "provisional_mappings_count": 0,
            "unmapped_parameters_count": len(unmapped_snos),
            "verified_percentage": round((len(verified_records) / max(1, total_parameters)) * 100, 2),
            "unmapped_percentage": round((len(unmapped_snos) / max(1, total_parameters)) * 100, 2),
            "stock_metrics_count": len(stock_metric_snos),
            "verified_mappings": verified_records,
            "ambiguous_mappings": ambiguous_records,
            "unmapped_indicators_sample": unmapped_snos[:15],
            "governance_note": (
                "Indicator mappings follow strict non-fabrication safety rules. Indicators without direct "
                "authoritative equivalence in MoHFW standard definitions are preserved verbatim as unmapped, "
                "and indicators lacking a single aggregate total (such as 14.10.1.c) are classified as AMBIGUOUS."
            ),
            "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        }
