import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.session import SessionLocal
from backend.app.services.data_loader_service import ProcessedDataLoaderService


def main():
    print("=" * 70)
    print("  CAREFLOW INDIA — PROCESSED DATA PARQUET -> DATABASE LOADER")
    print("=" * 70)

    service = ProcessedDataLoaderService(processed_dir="data/processed")
    db = SessionLocal()
    
    try:
        result = service.load_processed_data(db)
        if result["status"] == "ERROR":
            print(f"\n[ERROR] {result['message']}\n")
        else:
            print(f"\n[SUCCESS] {result['message']}")
            print("  Ingestion Summary:")
            print(json.dumps(result["summary"], indent=4))
    finally:
        db.close()

    print("=" * 70)


if __name__ == "__main__":
    main()
