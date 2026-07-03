from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure we can load from src directory when run directly.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_report import aggregate_daily_csv_to_monthly_csv


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Aggregate daily health metrics into monthly metric statistics."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/preprocess/health_metrics_all.csv"),
        help="Path to the merged daily health metrics CSV.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/preprocess/health_metrics_monthly.csv"),
        help="Path to output the monthly metrics CSV.",
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point for monthly metric aggregation."""
    args = parse_args()
    try:
        output_path = aggregate_daily_csv_to_monthly_csv(args.input, args.output)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1

    print(f"Monthly metrics CSV generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
