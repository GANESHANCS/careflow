from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import openpyxl


class HMISFileInspector:
    """
    Utility for inspecting raw HMIS Excel and CSV reporting files.
    Identifies column layouts, sheet structures, header irregularities,
    and infers potential spatial, temporal, and indicator fields.
    """

    def __init__(self, raw_dir: str = "data/raw"):
        self.raw_dir = Path(raw_dir)

    def discover_raw_files(self) -> List[Path]:
        if not self.raw_dir.exists():
            return []
        supported_extensions = {".csv", ".xlsx", ".xls"}
        files = [
            f for f in self.raw_dir.glob("*") 
            if f.is_file() and f.suffix.lower() in supported_extensions and not f.name.startswith(".")
        ]
        return sorted(files)

    def inspect_file(self, file_path: Path) -> Dict[str, Any]:
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        file_size_bytes = file_path.stat().st_size
        extension = file_path.suffix.lower()

        inspection_report: Dict[str, Any] = {
            "filename": file_path.name,
            "filepath": str(file_path),
            "extension": extension,
            "size_bytes": file_size_bytes,
            "size_kb": round(file_size_bytes / 1024, 2),
            "sheets": [],
            "issues": []
        }

        if extension in [".xlsx", ".xls"]:
            self._inspect_excel(file_path, inspection_report)
        elif extension == ".csv":
            self._inspect_csv(file_path, inspection_report)
        else:
            inspection_report["issues"].append(f"Unsupported file format: {extension}")

        return inspection_report

    def _inspect_excel(self, file_path: Path, report: Dict[str, Any]):
        try:
            excel_file = pd.ExcelFile(file_path)
            report["sheet_names"] = excel_file.sheet_names

            for sheet_name in excel_file.sheet_names:
                df_raw = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)
                sheet_info = self._analyze_dataframe(df_raw, sheet_name=sheet_name)
                report["sheets"].append(sheet_info)
        except Exception as e:
            report["issues"].append(f"Error reading Excel file: {str(e)}")

    def _inspect_csv(self, file_path: Path, report: Dict[str, Any]):
        try:
            report["sheet_names"] = ["CSV_Main"]
            # Try reading raw without assuming header row index
            df_raw = pd.read_csv(file_path, header=None, low_memory=False)
            sheet_info = self._analyze_dataframe(df_raw, sheet_name="CSV_Main")
            report["sheets"].append(sheet_info)
        except Exception as e:
            report["issues"].append(f"Error reading CSV file: {str(e)}")

    def _analyze_dataframe(self, df_raw: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        if df_raw.empty:
            return {
                "sheet_name": sheet_name,
                "row_count": 0,
                "col_count": 0,
                "header_row_index": 0,
                "columns": [],
                "issues": ["Sheet is completely empty"]
            }

        # Detect likely header row (first row with multiple non-null string values)
        header_row_idx = 0
        for idx in range(min(10, len(df_raw))):
            row_vals = df_raw.iloc[idx].dropna().tolist()
            string_vals = [v for v in row_vals if isinstance(v, str) and len(v.strip()) > 1]
            if len(string_vals) >= max(2, int(df_raw.shape[1] * 0.3)):
                header_row_idx = idx
                break

        # Extract headers and data
        header = df_raw.iloc[header_row_idx].fillna("").astype(str).str.strip().tolist()
        df_data = df_raw.iloc[header_row_idx + 1:].copy()
        df_data.columns = [h if h else f"Unnamed_{i}" for i, h in enumerate(header)]

        col_names = list(df_data.columns)
        
        # Analyze potential entity / spatial / date / indicator columns
        potential_dates = [c for c in col_names if any(k in c.lower() for k in ["date", "month", "year", "period"])]
        potential_facilities = [c for c in col_names if any(k in c.lower() for k in ["facility", "hospital", "phc", "chc", "dh", "code"])]
        potential_districts = [c for c in col_names if any(k in c.lower() for k in ["district", "state", "block", "subdistrict"])]
        potential_indicators = [c for c in col_names if any(k in c.lower() for k in ["opd", "ipd", "delivery", "admission", "visit", "count", "immunisation", "total"])]

        # Missing value statistics
        missing_stats = df_data.isnull().sum().to_dict()
        missing_pcts = {k: round((v / max(1, len(df_data))) * 100, 2) for k, v in missing_stats.items()}

        return {
            "sheet_name": sheet_name,
            "row_count": len(df_data),
            "col_count": len(col_names),
            "header_row_index": header_row_idx,
            "columns": col_names,
            "inferred_date_cols": potential_dates,
            "inferred_facility_cols": potential_facilities,
            "inferred_district_cols": potential_districts,
            "inferred_indicator_cols": potential_indicators,
            "missing_percentages": missing_pcts,
            "sample_head": df_data.head(3).to_dict(orient="records")
        }
