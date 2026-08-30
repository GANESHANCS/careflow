import re
from typing import Any, Optional, Tuple, Dict
import pandas as pd
import numpy as np
from datetime import datetime


class ValueClassification:
    MISSING = "MISSING"
    ZERO = "ZERO"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    VALID = "VALID"
    INVALID = "INVALID"


class HMISSchemaNormalizer:
    """
    Normalizes column headers, raw strings, date fields, missing value tokens,
    and converts numeric counts while preserving value semantics.
    """

    MISSING_TOKENS = {
        "", "na", "n/a", "null", "none", "nan", "-", "--", "nil", 
        "not available", "not_available", "missing", "unknown", "?"
    }

    NOT_APPLICABLE_TOKENS = {
        "not applicable", "not_applicable", "n/a (not applicable)", "not_avail"
    }

    @staticmethod
    def normalize_column_name(col_name: Any) -> str:
        if not col_name:
            return "unnamed_column"
        col_str = str(col_name).strip()
        # Convert spaces/hyphens to underscore, drop special chars
        col_str = re.sub(r'[\s\-\/\.]+', '_', col_str)
        col_str = re.sub(r'[^a-zA-Z0-9_]', '', col_str)
        col_str = col_str.lower()
        col_str = re.sub(r'_+', '_', col_str).strip('_')
        return col_str if col_str else "unnamed_column"

    @classmethod
    def normalize_value(cls, val: Any) -> Tuple[Optional[float], str]:
        """
        Parses a raw observation cell value.
        Returns: (numeric_value, classification)
        """
        if pd.isna(val) or val is None:
            return None, ValueClassification.MISSING

        if isinstance(val, (int, float, np.integer, np.floating)):
            if np.isnan(val):
                return None, ValueClassification.MISSING
            val_float = float(val)
            if val_float == 0.0:
                return 0.0, ValueClassification.ZERO
            return val_float, ValueClassification.VALID

        val_str = str(val).strip().lower()

        if val_str in cls.NOT_APPLICABLE_TOKENS:
            return None, ValueClassification.NOT_APPLICABLE

        if val_str in cls.MISSING_TOKENS:
            return None, ValueClassification.MISSING

        # Try parsing numeric
        try:
            # Strip commas or quotes in numeric strings like "1,250"
            clean_num_str = re.sub(r'[,"]', '', val_str)
            num_val = float(clean_num_str)
            if num_val == 0.0:
                return 0.0, ValueClassification.ZERO
            return num_val, ValueClassification.VALID
        except ValueError:
            return None, ValueClassification.INVALID

    @staticmethod
    def normalize_date(val: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Normalizes reporting month to 'YYYY-MM' format and 'YYYY-MM-01' ISO string.
        """
        if pd.isna(val) or val is None:
            return None, None

        if isinstance(val, (datetime, pd.Timestamp)):
            month_str = val.strftime("%Y-%m")
            iso_date = f"{month_str}-01"
            return month_str, iso_date

        val_str = str(val).strip()
        
        # Supported format matching (e.g. "2024-04", "04/2024", "Apr 2024", "2024-04-15")
        for fmt in [
            "%Y-%m", "%Y/%m", "%m/%Y", "%m-%Y",
            "%b %Y", "%B %Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"
        ]:
            try:
                dt = datetime.strptime(val_str, fmt)
                month_str = dt.strftime("%Y-%m")
                iso_date = f"{month_str}-01"
                return month_str, iso_date
            except ValueError:
                continue

        # Regex fallback for YYYY-MM in string
        match = re.search(r'(\d{4})[\-\/](0[1-9]|1[0-2])', val_str)
        if match:
            year, month = match.group(1), match.group(2)
            return f"{year}-{month}", f"{year}-{month}-01"

        return None, None
