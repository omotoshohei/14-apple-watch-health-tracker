from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_report import generate_weekly_report


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an Apple Watch health weekly trend HTML report."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=Path("data/preprocess/health_metrics_weekly.csv"),
        help="Path to the aggregated weekly health metrics CSV.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="Report output directory.",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point for weekly trend report generation."""
    args = parse_args()
    start_time = time.time()

    print(f"Generating weekly trend report from CSV: {args.csv}...")
    try:
        output_path = generate_weekly_report(args.csv, args.output_dir)
        elapsed = time.time() - start_time
        print(
            f"Weekly trend report successfully generated: {output_path} "
            f"(took {elapsed:.2f} seconds)"
        )
    except (FileNotFoundError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: An unexpected error occurred: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
