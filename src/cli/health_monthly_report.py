from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure we can load from src directory if run directly or dynamically.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_report import generate_report, preprocess_xml_to_csv, validate_inputs


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an Apple Watch health monthly HTML report."
    )
    parser.add_argument("--year", type=int, required=True, help="Target year, for example 2026.")
    parser.add_argument(
        "--month", type=int, required=True, choices=range(1, 13), help="Target month 1-12."
    )
    parser.add_argument("--xml", type=Path, default=None, help="Path to Apple Health export.xml.")
    parser.add_argument(
        "--csv", type=Path, default=None, help="Path to preprocessed health metrics CSV."
    )
    parser.add_argument(
        "--preprocess-only",
        action="store_true",
        help="Generate CSV only, do not generate HTML report.",
    )
    parser.add_argument(
        "--csv-output", type=Path, default=None, help="Output path for the generated CSV."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output"), help="Report output directory."
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    load_dotenv()
    args = parse_args()

    # Mutually exclusive validations
    if args.xml is not None and args.csv is not None:
        print("Error: Cannot specify both --xml and --csv.")
        return 1

    if args.csv is not None and args.preprocess_only:
        print("Error: Cannot specify --preprocess-only when reading from --csv.")
        return 1

    # Determine execution mode and inputs
    is_xml_input = True
    input_xml = args.xml
    input_csv = args.csv

    if input_csv is not None:
        is_xml_input = False
    else:
        # Default to export.xml if neither xml nor csv is specified
        if input_xml is None:
            input_xml = Path("export.xml")

    # Resolve CSV path
    if is_xml_input:
        if args.csv_output is not None:
            csv_path = args.csv_output
        else:
            csv_path = Path("data/preprocess") / f"health_metrics_{args.year}_{args.month:02d}.csv"
    else:
        csv_path = input_csv

    try:
        if is_xml_input:
            validate_inputs(input_xml)
            print(f"Preprocessing XML data from {input_xml}...")
            preprocess_xml_to_csv(input_xml, args.year, args.month, csv_path)
            print(f"CSV generated: {csv_path}")

        if not args.preprocess_only:
            print(f"Generating HTML report from CSV: {csv_path}...")
            output_path = generate_report(csv_path, args.year, args.month, args.output_dir)
            print(f"Report generated: {output_path}")

    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
