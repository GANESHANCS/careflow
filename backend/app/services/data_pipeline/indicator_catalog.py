import re
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class IndicatorMetadata(BaseModel):
    code: str = Field(..., description="Stable internal identifier code")
    name: str = Field(..., description="Standardized English display name")
    category: str = Field(..., description="Healthcare operational domain")
    unit: str = Field(default="count", description="Measurement unit")
    aliases: List[str] = Field(default_factory=list, description="Common aliases/headers in HMIS reports")
    regex_patterns: List[str] = Field(default_factory=list, description="Regex patterns for matching raw header names")


STANDARD_INDICATORS: Dict[str, IndicatorMetadata] = {
    "opd_attendance": IndicatorMetadata(
        code="opd_attendance",
        name="Outpatient Department (OPD) Attendance",
        category="Outpatient Services",
        unit="visits",
        aliases=["opd_attendance", "total_opd", "opd_count", "outpatient_attendance", "opd_total"],
        regex_patterns=[r".*opd.*attend.*", r".*outpatient.*", r"^opd_total$"]
    ),
    "inpatient_admissions": IndicatorMetadata(
        code="inpatient_admissions",
        name="Inpatient Admissions (IPD)",
        category="Inpatient Services",
        unit="admissions",
        aliases=["inpatient_admissions", "ipd_attendance", "ipd_total", "inpatient_admit"],
        regex_patterns=[r".*inpatient.*", r".*ipd.*attend.*", r"^ipd_total$"]
    ),
    "institutional_deliveries": IndicatorMetadata(
        code="institutional_deliveries",
        name="Institutional Deliveries",
        category="Maternal Health",
        unit="deliveries",
        aliases=["institutional_deliveries", "inst_deliveries", "facility_deliveries", "deliveries_total"],
        regex_patterns=[r".*inst.*deliver.*", r".*facility.*deliver.*"]
    ),
    "antenatal_visits": IndicatorMetadata(
        code="antenatal_visits",
        name="Antenatal Care (ANC) Registered Visits",
        category="Maternal Health",
        unit="visits",
        aliases=["anc_visits", "antenatal_visits", "anc_registered", "total_anc"],
        regex_patterns=[r".*anc.*visit.*", r".*antenatal.*", r"^anc_total$"]
    ),
    "postnatal_visits": IndicatorMetadata(
        code="postnatal_visits",
        name="Postnatal Care (PNC) Visits",
        category="Maternal Health",
        unit="visits",
        aliases=["pnc_visits", "postnatal_visits", "pnc_registered", "total_pnc"],
        regex_patterns=[r".*pnc.*visit.*", r".*postnatal.*", r"^pnc_total$"]
    ),
    "immunisation": IndicatorMetadata(
        code="immunisation",
        name="Full Immunisation Coverage / Doses",
        category="Child Health",
        unit="children",
        aliases=["immunisation", "full_immunisation", "child_immunisation", "vac_doses"],
        regex_patterns=[r".*immunis.*", r".*vaccin.*", r"^immunization_total$"]
    )
}


class IndicatorCatalog:
    """
    Registry for HMIS operational metrics. Supports dynamic lookup and regex mapping.
    """

    def __init__(self, catalog_override: Optional[Dict[str, IndicatorMetadata]] = None):
        self._catalog = catalog_override or STANDARD_INDICATORS

    def get_indicator(self, code: str) -> Optional[IndicatorMetadata]:
        return self._catalog.get(code.lower())

    def match_column_name(self, raw_col_name: str) -> Optional[str]:
        cleaned = raw_col_name.lower().strip().replace(" ", "_").replace("-", "_")
        
        # 1. Exact alias match
        for code, meta in self._catalog.items():
            if cleaned == code or cleaned in [a.lower() for a in meta.aliases]:
                return code

        # 2. Regex pattern match
        for code, meta in self._catalog.items():
            for pattern in meta.regex_patterns:
                if re.search(pattern, cleaned, re.IGNORECASE):
                    return code

        return None

    def list_indicators(self) -> List[IndicatorMetadata]:
        return list(self._catalog.values())
