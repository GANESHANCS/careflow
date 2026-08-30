from typing import List, Dict, Any, Tuple
import pandas as pd


class DeduplicationEngine:
    """
    Identifies and resolves duplicate HMIS observation records.
    Logical composite key: facility_id + indicator_code + reporting_month.
    Reconciles duplicate records deterministically while logging diagnostics.
    """

    @classmethod
    def deduplicate_observations(
        cls, 
        observations: List[Dict[str, Any]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Deduplicates a list of observation dictionaries.
        Returns: (deduplicated_observations, diagnostics_dict)
        """
        if not observations:
            return [], {
                "total_input_records": 0,
                "deduplicated_records": 0,
                "duplicates_found": 0,
                "duplicate_keys": [],
                "retained_count": 0,
                "discarded_count": 0
            }

        df = pd.DataFrame(observations)

        composite_cols = ["facility_id", "indicator_code", "reporting_month"]
        for col in composite_cols:
            if col not in df.columns:
                df[col] = "UNKNOWN"

        total_input = len(df)
        
        # Group by key to identify duplicates
        duplicates_mask = df.duplicated(subset=composite_cols, keep=False)
        duplicate_df = df[duplicates_mask]
        
        duplicate_keys = []
        if not duplicate_df.empty:
            dup_grouped = duplicate_df.groupby(composite_cols).size().reset_index(name='count')
            duplicate_keys = dup_grouped.to_dict(orient="records")

        # Deterministic sorting strategy:
        # Prefer non-null numeric value, then newest ingestion timestamp
        sort_cols = []
        ascending = []
        
        if "value" in df.columns:
            df["is_null"] = df["value"].isnull()
            sort_cols.append("is_null")
            ascending.append(True)
            
        if "ingested_at" in df.columns:
            sort_cols.append("ingested_at")
            ascending.append(False)

        if sort_cols:
            df = df.sort_values(by=sort_cols, ascending=ascending)

        # Drop duplicates keeping top record
        df_clean = df.drop_duplicates(subset=composite_cols, keep="first").copy()
        
        if "is_null" in df_clean.columns:
            df_clean = df_clean.drop(columns=["is_null"])

        dedup_records = df_clean.to_dict(orient="records")
        discarded_count = total_input - len(dedup_records)

        diagnostics = {
            "total_input_records": total_input,
            "deduplicated_records": len(dedup_records),
            "duplicates_found": discarded_count,
            "duplicate_keys_count": len(duplicate_keys),
            "duplicate_keys_sample": duplicate_keys[:10],
            "retained_count": len(dedup_records),
            "discarded_count": discarded_count
        }

        return dedup_records, diagnostics
