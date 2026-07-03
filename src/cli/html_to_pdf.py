from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

DEFAULT_INPUT_DIR = Path("output")
DEFAULT_OUTPUT_DIR = Path("output/pdf")

PRINT_CSS = """
@page {
  size: 20in 11.25in;
  margin: 0;
}

html,
body {
  width: 1920px !important;
  margin: 0 !important;
  padding: 0 !important;
  background: #ffffff !important;
  overflow: visible !important;
}

.slide-wrapper {
  width: 1920px !important;
  height: 1080px !important;
  min-width: 1920px !important;
  min-height: 1080px !important;
  max-width: 1920px !important;
  max-height: 1080px !important;
  margin: 0 !important;
  padding: 0 !important;
  display: block !important;
  overflow: hidden !important;
  page-break-after: always !important;
  break-after: page !important;
  scroll-snap-align: none !important;
  box-sizing: border-box !important;
}

.slide-wrapper:last-child {
  page-break-after: auto !important;
  break-after: auto !important;
}

.slide {
  width: 1920px !important;
  height: 1080px !important;
  min-width: 1920px !important;
  min-height: 1080px !important;
  max-width: 1920px !important;
  max-height: 1080px !important;
  margin: 0 !important;
  transform: none !important;
  transform-origin: top left !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  box-sizing: border-box !important;
}
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert generated Apple Watch health HTML reports to 16:9 PDFs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Path to a single HTML report file.",
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        help="Directory containing HTML report files. Non-recursive.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where PDF files will be written.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip conversion when the output PDF already exists.",
    )
    return parser.parse_args()


def resolve_html_inputs(input_path: Path | None, input_dir: Path | None) -> list[Path]:
    if input_path is not None and input_dir is not None:
        raise ValueError("Cannot specify both --input and --input-dir.")

    if input_path is not None:
        if not input_path.exists():
            raise FileNotFoundError(f"HTML input file not found: {input_path}")
        if not input_path.is_file():
            raise ValueError(f"HTML input path is not a file: {input_path}")
        if input_path.suffix.lower() != ".html":
            raise ValueError(f"HTML input file must have a .html extension: {input_path}")
        return [input_path]

    search_dir = input_dir or DEFAULT_INPUT_DIR
    if not search_dir.exists():
        raise FileNotFoundError(f"HTML input directory not found: {search_dir}")
    if not search_dir.is_dir():
        raise ValueError(f"HTML input directory path is not a directory: {search_dir}")

    html_files = sorted(path for path in search_dir.glob("*.html") if path.is_file())
    if not html_files:
        raise FileNotFoundError(f"No HTML files found in input directory: {search_dir}")
    return html_files


def output_pdf_path(html_path: Path, output_dir: Path) -> Path:
    return output_dir / f"{html_path.stem}.pdf"


def should_skip_output(pdf_path: Path, skip_existing: bool) -> bool:
    return skip_existing and pdf_path.exists()


def convert_html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    try:
        from playwright.sync_api import Error as PlaywrightError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError(
            "Playwright is not installed. Install dependencies, then run: "
            "uv run playwright install chromium"
        ) from exc

    pdf_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1920, "height": 1080})
                page.goto(html_path.resolve().as_uri(), wait_until="load")
                page.emulate_media(media="print")
                page.add_style_tag(content=PRINT_CSS)
                page.pdf(
                    path=str(pdf_path),
                    print_background=True,
                    prefer_css_page_size=True,
                )
            finally:
                browser.close()
    except PlaywrightError as exc:
        raise RuntimeError(
            f"Playwright failed while converting {html_path}. "
            "If Chromium is not installed, run: uv run playwright install chromium"
        ) from exc


def run_conversion(
    html_files: list[Path],
    output_dir: Path,
    *,
    skip_existing: bool = False,
) -> tuple[int, int]:
    converted = 0
    skipped = 0
    output_dir.mkdir(parents=True, exist_ok=True)

    for html_path in html_files:
        pdf_path = output_pdf_path(html_path, output_dir)
        if should_skip_output(pdf_path, skip_existing):
            print(f"Skipped existing PDF: {pdf_path}")
            skipped += 1
            continue

        print(f"Converting {html_path} -> {pdf_path}")
        convert_html_to_pdf(html_path, pdf_path)
        converted += 1

    return converted, skipped


def main() -> int:
    args = parse_args()
    start_time = time.time()

    try:
        html_files = resolve_html_inputs(args.input, args.input_dir)
        converted, skipped = run_conversion(
            html_files,
            args.output_dir,
            skip_existing=args.skip_existing,
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: An unexpected error occurred: {exc}", file=sys.stderr)
        return 1

    elapsed = time.time() - start_time
    print(
        f"PDF conversion complete: {converted} converted, {skipped} skipped "
        f"(took {elapsed:.2f} seconds)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
