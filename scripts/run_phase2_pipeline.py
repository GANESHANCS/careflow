import sys
import json
from pathlib import Path

# Add project root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.services.data_pipeline.pipeline_runner import HMISPipelineRunner


def main():
    print("=" * 70)
    print("  CAREFLOW INDIA — HMIS DATA INGESTION & QUALITY PIPELINE (PHASE 2)")
    print("=" * 70)

    runner = HMISPipelineRunner(
        raw_dir="data/raw",
        interim_dir="data/interim",
        processed_dir="data/processed"
    )

    result = runner.run_pipeline()

    if result["status"] == "NO_SOURCE_FILES":
        print(f"\n[NOTICE] {result['message']}\n")
        print("REAL HMIS FILES FOUND: NO")
        print("Framework readiness: 100% operational (awaiting raw files).\n")
        return

    print("\n[SUCCESS] Pipeline Execution Summary:")
    print(f"  Status                  : {result['status']}")
    print(f"  Files Processed         : {result['files_processed']}")
    print(f"  Observations Ingested   : {result['total_observations_ingested']}")
    print(f"  Deduplicated Records    : {result['deduplicated_observations']}")
    print(f"  Facilities Standardized : {result['facilities_standardized']}")
    print(f"  Overall Quality Score   : {result['quality_score']} / 100.0")
    print("\n  Generated Output Artifacts:")
    for name, path_str in result.get("output_paths", {}).items():
        print(f"    - {name}: {path_str}")

    print("\nREAL HMIS FILES FOUND: YES")
    print("=" * 70)


if __name__ == "__main__":
    main()
