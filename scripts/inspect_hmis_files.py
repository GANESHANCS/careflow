import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.data_pipeline.file_inspector import HMISFileInspector


def main():
    print("=" * 60)
    print("  CAREFLOW HMIS RAW FILE INSPECTION UTILITY")
    print("=" * 60)

    inspector = HMISFileInspector(raw_dir="data/raw")
    raw_files = inspector.discover_raw_files()

    if not raw_files:
        print("\n[INFO] No HMIS source files (.csv, .xlsx, .xls) found under 'data/raw/'.")
        print("Inspection tool is ready to inspect raw HMIS files when placed in data/raw/.\n")
        return

    print(f"\nDiscovered {len(raw_files)} raw file(s) in data/raw/:\n")
    for idx, file_path in enumerate(raw_files, 1):
        print(f"[{idx}] {file_path.name}")
        report = inspector.inspect_file(file_path)
        print(json.dumps(report, indent=2))
        print("-" * 60)


if __name__ == "__main__":
    main()
