import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.health_monthly_report import main


def test_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    # Running --help should exit with status 0
    monkeypatch.setattr(sys, "argv", ["health_monthly_report.py", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0


def test_cli_missing_args(monkeypatch: pytest.MonkeyPatch) -> None:
    # Running without mandatory args should exit with non-zero
    monkeypatch.setattr(sys, "argv", ["health_monthly_report.py"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0


def test_cli_execution_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    xml_path.write_text("<HealthData />", encoding="utf-8")

    with (
        patch("cli.health_monthly_report.validate_inputs") as mock_val,
        patch("cli.health_monthly_report.generate_report") as mock_gen,
    ):
        mock_val.return_value = None
        mock_gen.return_value = tmp_path / "report.html"

        monkeypatch.setattr(
            sys,
            "argv",
            [
                "health_monthly_report.py",
                "--year",
                "2026",
                "--month",
                "6",
                "--xml",
                str(xml_path),
                "--output-dir",
                str(tmp_path / "output"),
            ],
        )

        code = main()
        assert code == 0
        mock_val.assert_called_once_with(xml_path)
        mock_gen.assert_called_once_with(xml_path, 2026, 6, tmp_path / "output")
