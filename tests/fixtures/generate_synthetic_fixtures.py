from pathlib import Path
import pandas as pd

FIXTURE_DIR = Path(__file__).resolve().parent / "synthetic_hmis"
FIXTURE_DIR.mkdir(parents=True, exist_ok=True)

# Synthetic test data representing varied HMIS reporting edge cases
# (e.g. missing codes, "NA", negative counts, whitespace, unmapped columns, duplicates)
data = [
    {
        "State": "SYNTHETIC_State_A",
        "District": "SYNTHETIC_District_X",
        "Block": "SYNTHETIC_Block_1",
        "Facility Code": "1001",
        "Facility Name": "SYNTHETIC District Hospital Alpha",
        "Facility Type": "District Hospital",
        "Reporting Month": "2024-04",
        "OPD Attendance": "1250",
        "Inpatient Admissions": "340",
        "Institutional Deliveries": "85",
        "ANC Visits": "210",
        "PNC Visits": "180",
        "Immunisation Coverage": "195"
    },
    # Edge case: "NA", string spaces, missing facility code
    {
        "State": "SYNTHETIC_State_A",
        "District": "SYNTHETIC_District_X",
        "Block": "SYNTHETIC_Block_1",
        "Facility Code": "",
        "Facility Name": "  SYNTHETIC Primary Health Centre Beta  ",
        "Facility Type": "PHC",
        "Reporting Month": "2024-04",
        "OPD Attendance": "480",
        "Inpatient Admissions": "NA",
        "Institutional Deliveries": "15",
        "ANC Visits": "90",
        "PNC Visits": "-",
        "Immunisation Coverage": "88"
    },
    # Edge case: Negative count, duplicate month, invalid date, zero count
    {
        "State": "SYNTHETIC_State_A",
        "District": "SYNTHETIC_District_Y",
        "Block": "SYNTHETIC_Block_2",
        "Facility Code": "1003",
        "Facility Name": "SYNTHETIC Community Health Centre Gamma",
        "Facility Type": "CHC",
        "Reporting Month": "2024-04",
        "OPD Attendance": "-50", # Negative count edge case
        "Inpatient Admissions": "0",
        "Institutional Deliveries": "45",
        "ANC Visits": "120",
        "PNC Visits": "110",
        "Immunisation Coverage": "115"
    },
    # Duplicate record of facility 1001 for 2024-04 (for deduplication testing)
    {
        "State": "SYNTHETIC_State_A",
        "District": "SYNTHETIC_District_X",
        "Block": "SYNTHETIC_Block_1",
        "Facility Code": "1001",
        "Facility Name": "SYNTHETIC District Hospital Alpha",
        "Facility Type": "District Hospital",
        "Reporting Month": "2024-04",
        "OPD Attendance": "1250",
        "Inpatient Admissions": "340",
        "Institutional Deliveries": "85",
        "ANC Visits": "210",
        "PNC Visits": "180",
        "Immunisation Coverage": "195"
    }
]

df_synthetic = pd.DataFrame(data)

# Export CSV fixture
csv_path = FIXTURE_DIR / "synthetic_test_hmis_report_2024.csv"
df_synthetic.to_csv(csv_path, index=False)

# Export Excel fixture
xlsx_path = FIXTURE_DIR / "synthetic_test_hmis_report_2024.xlsx"
df_synthetic.to_excel(xlsx_path, index=False, sheet_name="SYNTHETIC_HMIS_DATA")

print(f"Generated synthetic test fixtures:\n  - {csv_path}\n  - {xlsx_path}")
