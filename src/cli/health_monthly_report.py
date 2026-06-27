from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

# Ensure we can load from src directory if run directly or dynamically.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_report import generate_report, validate_inputs


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an Apple Watch health monthly HTML report."
    )
    parser.add_argument("--year", type=int, required=True, help="Target year, for example 2026.")
    parser.add_argument(
        "--month", type=int, required=True, choices=range(1, 13), help="Target month 1-12."
    )
    parser.add_argument(
        "--xml", type=Path, default=Path("export.xml"), help="Path to Apple Health export.xml."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output"), help="Report output directory."
    )
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    load_dotenv()
    args = parse_args()
    try:
        validate_inputs(args.xml)
        output_path = generate_report(args.xml, args.year, args.month, args.output_dir)
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1
    print(f"Report generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
