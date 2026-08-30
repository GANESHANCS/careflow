import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.db.session import SessionLocal
from backend.app.db.seed import seed_standard_indicators


def main():
    print("=" * 60)
    print("  CAREFLOW INDIA — HMIS INDICATOR DATABASE SEEDER")
    print("=" * 60)

    db = SessionLocal()
    try:
        indicators = seed_standard_indicators(db)
        print(f"\n[SUCCESS] Successfully seeded/verified {len(indicators)} standard HMIS indicators:")
        for ind in indicators:
            print(f"  - [{ind.code}] {ind.name} (Category: {ind.category}, Unit: {ind.unit})")
    finally:
        db.close()
    print("=" * 60)


if __name__ == "__main__":
    main()
