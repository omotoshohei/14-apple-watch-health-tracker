from pathlib import Path
from unittest.mock import patch

import pytest

from cli.html_to_pdf import (
    DEFAULT_INPUT_DIR,
    output_pdf_path,
    resolve_html_inputs,
    run_conversion,
    should_skip_output,
)


def test_resolve_html_inputs_defaults_to_output(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    output_dir = tmp_path / DEFAULT_INPUT_DIR
    output_dir.mkdir(parents=True)
    second = output_dir / "b.html"
    first = output_dir / "a.html"
    ignored = output_dir / "notes.txt"
    second.write_text("<html></html>", encoding="utf-8")
    first.write_text("<html></html>", encoding="utf-8")
    ignored.write_text("ignored", encoding="utf-8")

    monkeypatch.chdir(tmp_path)

    assert resolve_html_inputs(None, None) == [
        DEFAULT_INPUT_DIR / first.name,
        DEFAULT_INPUT_DIR / second.name,
    ]


def test_resolve_html_inputs_accepts_single_file(tmp_path: Path) -> None:
    html_path = tmp_path / "report.html"
    html_path.write_text("<html></html>", encoding="utf-8")

    assert resolve_html_inputs(html_path, None) == [html_path]


def test_resolve_html_inputs_accepts_input_dir(tmp_path: Path) -> None:
    html_dir = tmp_path / "reports"
    html_dir.mkdir()
    html_path = html_dir / "report.html"
    html_path.write_text("<html></html>", encoding="utf-8")

    assert resolve_html_inputs(None, html_dir) == [html_path]


def test_resolve_html_inputs_rejects_input_and_input_dir(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Cannot specify both --input and --input-dir"):
        resolve_html_inputs(tmp_path / "report.html", tmp_path)


def test_resolve_html_inputs_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="HTML input file not found"):
        resolve_html_inputs(tmp_path / "missing.html", None)


def test_resolve_html_inputs_rejects_non_html_file(tmp_path: Path) -> None:
    text_path = tmp_path / "report.txt"
    text_path.write_text("not html", encoding="utf-8")

    with pytest.raises(ValueError, match="must have a .html extension"):
        resolve_html_inputs(text_path, None)


def test_resolve_html_inputs_rejects_empty_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="No HTML files found"):
        resolve_html_inputs(None, tmp_path)


def test_output_pdf_path_uses_html_stem(tmp_path: Path) -> None:
    html_path = tmp_path / "apple_watch_health_weekly_report.html"
    output_dir = tmp_path / "pdf"

    assert output_pdf_path(html_path, output_dir) == (
        output_dir / "apple_watch_health_weekly_report.pdf"
    )


def test_should_skip_output_requires_flag_and_existing_file(tmp_path: Path) -> None:
    pdf_path = tmp_path / "report.pdf"

    assert not should_skip_output(pdf_path, skip_existing=True)
    pdf_path.write_bytes(b"%PDF")
    assert not should_skip_output(pdf_path, skip_existing=False)
    assert should_skip_output(pdf_path, skip_existing=True)


def test_run_conversion_skips_existing_pdf(tmp_path: Path) -> None:
    html_path = tmp_path / "report.html"
    output_dir = tmp_path / "pdf"
    pdf_path = output_dir / "report.pdf"
    html_path.write_text("<html></html>", encoding="utf-8")
    output_dir.mkdir()
    pdf_path.write_bytes(b"%PDF")

    with patch("cli.html_to_pdf.convert_html_to_pdf") as convert:
        converted, skipped = run_conversion([html_path], output_dir, skip_existing=True)

    assert converted == 0
    assert skipped == 1
    convert.assert_not_called()


def test_run_conversion_converts_html(tmp_path: Path) -> None:
    html_path = tmp_path / "report.html"
    output_dir = tmp_path / "pdf"
    html_path.write_text("<html></html>", encoding="utf-8")

    with patch("cli.html_to_pdf.convert_html_to_pdf") as convert:
        converted, skipped = run_conversion([html_path], output_dir)

    assert converted == 1
    assert skipped == 0
    convert.assert_called_once_with(html_path, output_dir / "report.pdf")
