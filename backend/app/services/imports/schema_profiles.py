from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Set, Any
import re
from backend.app.services.data_pipeline.schema_normalizer import HMISSchemaNormalizer


@dataclass
class SchemaValidationResult:
    is_valid: bool
    profile_id: str
    matched_columns: List[str]
    missing_required: List[str]
    detected_entity_cols: Dict[str, str]
    detected_date_col: Optional[str]
    detected_indicator_cols: List[str]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaseSchemaProfile:
    """
    Abstract base specification for an HMIS dataset schema profile.
    Provides pre-flight structural validation of column headers, entity associations,
    and temporal identifiers before any row processing begins.
    """
    profile_id: str = "base"
    name: str = "Base Profile"
    version: str = "1.0.0"
    description: str = "Base schema profile"
    is_synthetic_baseline: bool = True

    required_column_groups: List[Tuple[str, List[str]]] = []
    known_indicator_columns: Set[str] = set()

    @classmethod
    def validate_headers(cls, raw_headers: List[str]) -> SchemaValidationResult:
        normalized = [HMISSchemaNormalizer.normalize_column_name(h) for h in raw_headers]
        norm_set = set(normalized)

        errors: List[str] = []
        warnings: List[str] = []
        missing_required: List[str] = []

        # 1. Check required column groups
        for group_name, candidates in cls.required_column_groups:
            matched = any(c in norm_set for c in candidates)
            if not matched:
                missing_required.append(f"{group_name} (any of: {', '.join(candidates)})")
                errors.append(
                    f"Profile '{cls.profile_id}': Missing required {group_name} column. "
                    f"Expected one of: [{', '.join(candidates)}]."
                )

        # 2. Identify entity columns
        entity_map: Dict[str, str] = {}
        for c in normalized:
            if any(k in c for k in ["facility_code", "facility_id"]):
                entity_map["facility_code"] = c
            elif any(k in c for k in ["facility_name", "hospital_name", "clinic_name", "centre_name"]):
                entity_map["facility_name"] = c
            elif any(k in c for k in ["district", "dist_name"]):
                entity_map["district"] = c
            elif any(k in c for k in ["state", "state_name"]):
                entity_map["state"] = c

        # 3. Identify date column
        date_col = next((c for c in normalized if any(k in c for k in ["reporting_month", "date", "month", "period", "year"])), None)
        if not date_col:
            errors.append("No identifiable temporal column (e.g., 'reporting_month', 'date', 'month') was found in headers.")

        # 4. Identify indicator columns
        indicator_cols = [
            c for c in normalized
            if c not in entity_map.values()
            and c != date_col
            and not c.startswith("unnamed")
            and not any(k in c for k in ["state", "district", "sub_district", "block", "facility", "code", "type"])
        ]
        if not indicator_cols:
            warnings.append("No potential clinical or operational indicator columns were detected.")

        is_valid = len(errors) == 0
        return SchemaValidationResult(
            is_valid=is_valid,
            profile_id=cls.profile_id,
            matched_columns=normalized,
            missing_required=missing_required,
            detected_entity_cols=entity_map,
            detected_date_col=date_col,
            detected_indicator_cols=indicator_cols,
            errors=errors,
            warnings=warnings,
        )


class MOHFWStandardV2Profile(BaseSchemaProfile):
    """
    Standard MoHFW HMIS Tabular Ingestion Profile (v2.0).
    Matches the canonical Ministry of Health & Family Welfare reporting layout:
    - Entity columns: State, District, Facility Code, Facility Name
    - Temporal column: Reporting Month (YYYY-MM)
    - Indicators: OPD Attendance, Inpatient Admissions, Institutional Deliveries, Antenatal Visits, etc.
    """
    profile_id = "mohfw_standard_v2"
    name = "MoHFW Standard Tabular HMIS Profile"
    version = "2.0.0"
    description = (
        "Standard multi-facility monthly reporting profile supporting MoHFW tabular formats. "
        "Verified against integration test contracts; unvalidated against unindexed external spreadsheets."
    )
    is_synthetic_baseline = False

    required_column_groups = [
        ("Temporal Period", ["reporting_month", "month", "observation_date", "date", "period"]),
        ("Facility Identifier", ["facility_code", "facility_name", "facility", "facility_id", "code"]),
        ("Spatial District/State", ["district", "state", "district_name", "state_name"]),
    ]


class FacilityMonthlyTabularV1Profile(BaseSchemaProfile):
    """
    Simplified Facility Monthly Tabular Profile (v1.0).
    Permits single-district or facility-centric files with minimal metadata columns.
    """
    profile_id = "facility_monthly_tabular_v1"
    name = "Facility Monthly Tabular Profile"
    version = "1.0.0"
    description = "Simplified tabular monthly reporting profile requiring facility and date columns."
    is_synthetic_baseline = True

    required_column_groups = [
        ("Temporal Period", ["reporting_month", "month", "date", "period"]),
        ("Facility Identifier", ["facility_code", "facility_name", "facility", "facility_id"]),
    ]


class SchemaProfileRegistry:
    """
    Registry for discovering, selecting, and applying schema validation profiles.
    """
    _PROFILES: Dict[str, type[BaseSchemaProfile]] = {
        MOHFWStandardV2Profile.profile_id: MOHFWStandardV2Profile,
        FacilityMonthlyTabularV1Profile.profile_id: FacilityMonthlyTabularV1Profile,
    }
    _DEFAULT_PROFILE = MOHFWStandardV2Profile

    @classmethod
    def get_profile(cls, profile_id: Optional[str]) -> type[BaseSchemaProfile]:
        if not profile_id:
            return cls._DEFAULT_PROFILE
        return cls._PROFILES.get(profile_id, cls._DEFAULT_PROFILE)

    @classmethod
    def detect_profile(cls, raw_headers: List[str]) -> type[BaseSchemaProfile]:
        """
        Infers the most appropriate profile by testing header compatibility.
        Falls back to MOHFWStandardV2Profile if ambiguous.
        """
        for profile in [MOHFWStandardV2Profile, FacilityMonthlyTabularV1Profile]:
            result = profile.validate_headers(raw_headers)
            if result.is_valid:
                return profile
        return cls._DEFAULT_PROFILE

    @classmethod
    def list_profiles(cls) -> List[Dict[str, Any]]:
        return [
            {
                "profile_id": p.profile_id,
                "name": p.name,
                "version": p.version,
                "description": p.description,
                "is_synthetic_baseline": p.is_synthetic_baseline,
            }
            for p in cls._PROFILES.values()
        ]
