import re
import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class FacilityEntity(BaseModel):
    facility_id: str = Field(..., description="Standardized internal primary key")
    facility_code: Optional[str] = Field(None, description="Official HMIS facility code")
    facility_name: str = Field(..., description="Normalized facility name")
    facility_type: str = Field(default="UNKNOWN", description="Standardized facility type (PHC, CHC, DH, SC, etc.)")
    state: str = Field(default="UNKNOWN", description="Standardized state name")
    district: str = Field(default="UNKNOWN", description="Standardized district name")
    sub_district: Optional[str] = Field(None, description="Sub-district / Block name")
    raw_facility_name: str = Field(..., description="Original raw facility name for provenance")
    raw_district_name: Optional[str] = Field(None, description="Original raw district name")


class HMISEntityStandardizer:
    """
    Standardizes state, district, and facility entities.
    Prioritizes official HMIS facility codes.
    Generates deterministic fallback keys for un-coded entities.
    """

    FACILITY_TYPE_RULES = [
        (r".*\b(district hospital|dh)\b.*", "DH"),
        (r".*\b(community health centre|chc)\b.*", "CHC"),
        (r".*\b(primary health centre|phc)\b.*", "PHC"),
        (r".*\b(sub centre|sub-center|sc)\b.*", "SC"),
        (r".*\b(medical college|mc|teaching hospital)\b.*", "MEDICAL_COLLEGE"),
        (r".*\b(sub divisional hospital|sdh|area hospital)\b.*", "SDH"),
        (r".*\b(urban primary health centre|uphc)\b.*", "UPHC"),
        (r".*\b(private hospital|nursing home)\b.*", "PRIVATE"),
    ]

    @classmethod
    def standardize_facility_type(cls, raw_name: str) -> str:
        clean = raw_name.lower().strip()
        for pattern, type_code in cls.FACILITY_TYPE_RULES:
            if re.search(pattern, clean):
                return type_code
        return "OTHER"

    @classmethod
    def clean_text(cls, text: Optional[str]) -> str:
        if not text or pd_isna(text):
            return "UNKNOWN"
        t = str(text).strip()
        t = re.sub(r'\s+', ' ', t)
        return t.title()

    @classmethod
    def process_row(cls, row: Dict[str, Any]) -> FacilityEntity:
        raw_name = str(row.get("facility_name", row.get("facility", "Unknown Facility"))).strip()
        raw_code = row.get("facility_code", row.get("code", None))
        
        facility_code = str(raw_code).strip() if raw_code and not pd_isna(raw_code) else None
        state = cls.clean_text(row.get("state", "India"))
        district = cls.clean_text(row.get("district", "Unknown District"))
        sub_district = cls.clean_text(row.get("block", row.get("sub_district", None)))
        
        clean_name = cls.clean_text(raw_name)
        facility_type = str(row.get("facility_type", ""))
        if not facility_type or facility_type == "UNKNOWN":
            facility_type = cls.standardize_facility_type(clean_name)

        # Generate primary key ID
        if facility_code and facility_code.lower() not in ["none", "nan", "null", "0", ""]:
            facility_id = f"FC_{facility_code}"
        else:
            # Deterministic composite hash key
            composite_str = f"{state.lower()}_{district.lower()}_{clean_name.lower()}"
            hash_str = hashlib.md5(composite_str.encode('utf-8')).hexdigest()[:10]
            facility_id = f"FKEY_{hash_str}"

        return FacilityEntity(
            facility_id=facility_id,
            facility_code=facility_code,
            facility_name=clean_name,
            facility_type=facility_type,
            state=state,
            district=district,
            sub_district=sub_district if sub_district != "Unknown" else None,
            raw_facility_name=raw_name,
            raw_district_name=str(row.get("district", "")) if row.get("district") else None
        )


def pd_isna(val: Any) -> bool:
    return val is None or str(val).lower() in ["nan", "none", "null", ""]
