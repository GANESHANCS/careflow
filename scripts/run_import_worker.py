#!/usr/bin/env python3
"""
CAREFlow India — Asynchronous HMIS Batch Import Worker CLI
Runs the background worker loop as a standalone process or one-shot execution.

Usage:
    # Run continuously polling for QUEUED jobs:
    python scripts/run_import_worker.py --interval 2.0

    # Run once to process currently queued jobs and exit:
    python scripts/run_import_worker.py --once
"""

import sys
import time
import argparse
import logging
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app.core.logging import setup_logging
from backend.app.services.imports.worker import HMISImportWorker

setup_logging()
logger = logging.getLogger("careflow.worker.cli")


def parse_args():
    parser = argparse.ArgumentParser(description="CAREFlow HMIS Background Import Worker")
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Process currently queued jobs once and exit",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    worker = HMISImportWorker()
    logger.info(f"Starting standalone HMIS Import Worker (ID: {worker.worker_id}, once={args.once}).")

    if args.once:
        processed_total = 0
        while True:
            did_work = worker.process_next_job()
            if did_work:
                processed_total += 1
            else:
                break
        logger.info(f"Worker finished one-shot execution. Total jobs processed: {processed_total}.")
        sys.exit(0)

    try:
        while True:
            did_work = worker.process_next_job()
            if not did_work:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        logger.info("Worker received interrupt signal; exiting cleanly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
