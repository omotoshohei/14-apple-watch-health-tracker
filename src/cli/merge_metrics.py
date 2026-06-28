from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd


def merge_csv_files(input_dir: Path, output_file: Path) -> None:
    """Merge all health_metrics_YYYY_MM.csv files into a single CSV file.

    Args:
        input_dir (Path): Directory containing the monthly CSV files.
        output_file (Path): Target path for the merged output CSV file.
    """
    # Find all monthly health metrics CSV files (health_metrics_YYYY_MM.csv)
    # Exclude health_metrics_all.csv by specific pattern matching
    csv_files = sorted(input_dir.glob("health_metrics_[0-9][0-9][0-9][0-9]_[0-9][0-9].csv"))
    if not csv_files:
        print(f"Warning: No health_metrics_YYYY_MM.csv files found in {input_dir}")
        return

    print(f"Found {len(csv_files)} files to merge:")
    for f in csv_files:
        print(f"  - {f.name}")

    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            dfs.append(df)
        except Exception as e:
            print(f"Error reading {csv_file.name}: {e}")
            raise

    # Combine all DataFrames
    merged_df = pd.concat(dfs, ignore_index=True)

    # Standardize 'date' format, sort chronologically, and remove duplicates
    merged_df["date"] = pd.to_datetime(merged_df["date"])
    merged_df = merged_df.sort_values("date").drop_duplicates(subset=["date"])
    merged_df["date"] = merged_df["date"].dt.strftime("%Y-%m-%d")

    # Reindex columns to ensure standardized order
    cols = [
        "date",
        "sleep_duration",
        "steps",
        "active_energy",
        "exercise_time",
        "stand_hours",
        "sleep_onset",
        "wake_time",
        "awake_count",
        "awake_duration",
        "longest_awake_duration",
        "first_morning_awake_time",
    ]
    merged_df = merged_df.reindex(columns=cols)

    # Output directory creation
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Save to target file, representing missing values as 'NA'
    merged_df.to_csv(output_file, index=False, na_rep="NA")
    print(f"Successfully merged data and wrote to {output_file}")


def main() -> int:
    """CLI entry point for merging health metrics CSVs."""
    parser = argparse.ArgumentParser(
        description="Merge monthly health metrics CSVs into health_metrics_all.csv"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/preprocess"),
        help="Directory containing monthly CSV files.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/preprocess/health_metrics_all.csv"),
        help="Path to output merged CSV file.",
    )
    args = parser.parse_args()

    try:
        merge_csv_files(args.input_dir, args.output)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
