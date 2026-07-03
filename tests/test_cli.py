import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from cli.aggregate_weekly_metrics import main as aggregate_weekly_main
from cli.health_monthly_report import main
from cli.health_weekly_report import main as health_weekly_main


def test_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["health_monthly_report.py", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0


def test_cli_missing_args(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["health_monthly_report.py"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code != 0


def test_cli_xml_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    xml_path.write_text("<HealthData />", encoding="utf-8")
    output_dir = tmp_path / "output"
    expected_csv = Path("data/preprocess") / "health_metrics_2026_06.csv"

    with (
        patch("cli.health_monthly_report.validate_inputs") as mock_val,
        patch("cli.health_monthly_report.preprocess_xml_to_csv") as mock_pre,
        patch("cli.health_monthly_report.generate_report") as mock_gen,
    ):
        mock_val.return_value = None
        mock_pre.return_value = expected_csv
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
                str(output_dir),
            ],
        )

        code = main()
        assert code == 0
        mock_val.assert_called_once_with(xml_path)
        mock_pre.assert_called_once_with(xml_path, 2026, 6, expected_csv)
        mock_gen.assert_called_once_with(expected_csv, 2026, 6, output_dir)


def test_cli_csv_flow(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    csv_path = tmp_path / "health_metrics.csv"
    csv_path.write_text(
        "date,sleep_duration,steps,active_energy,exercise_time,stand_hours", encoding="utf-8"
    )
    output_dir = tmp_path / "output"

    with (
        patch("cli.health_monthly_report.validate_inputs") as mock_val,
        patch("cli.health_monthly_report.preprocess_xml_to_csv") as mock_pre,
        patch("cli.health_monthly_report.generate_report") as mock_gen,
    ):
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
                "--csv",
                str(csv_path),
                "--output-dir",
                str(output_dir),
            ],
        )

        code = main()
        assert code == 0
        mock_val.assert_not_called()
        mock_pre.assert_not_called()
        mock_gen.assert_called_once_with(csv_path, 2026, 6, output_dir)


def test_cli_preprocess_only(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    xml_path.write_text("<HealthData />", encoding="utf-8")
    output_dir = tmp_path / "output"
    expected_csv = Path("data/preprocess") / "health_metrics_2026_06.csv"

    with (
        patch("cli.health_monthly_report.validate_inputs") as mock_val,
        patch("cli.health_monthly_report.preprocess_xml_to_csv") as mock_pre,
        patch("cli.health_monthly_report.generate_report") as mock_gen,
    ):
        mock_val.return_value = None
        mock_pre.return_value = expected_csv

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
                "--preprocess-only",
                "--output-dir",
                str(output_dir),
            ],
        )

        code = main()
        assert code == 0
        mock_val.assert_called_once_with(xml_path)
        mock_pre.assert_called_once_with(xml_path, 2026, 6, expected_csv)
        mock_gen.assert_not_called()


def test_cli_mutually_exclusive_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
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
            "export.xml",
            "--csv",
            "metrics.csv",
        ],
    )
    code = main()
    assert code != 0


def test_aggregate_weekly_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["aggregate_weekly_metrics.py", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        aggregate_weekly_main()
    assert excinfo.value.code == 0


def test_health_weekly_cli_help(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["health_weekly_report.py", "--help"])
    with pytest.raises(SystemExit) as excinfo:
        health_weekly_main()
    assert excinfo.value.code == 0


def test_aggregate_weekly_cli_missing_input(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "aggregate_weekly_metrics.py",
            "--input",
            str(tmp_path / "missing.csv"),
            "--output",
            str(tmp_path / "weekly.csv"),
        ],
    )
    assert aggregate_weekly_main() == 1


def test_health_weekly_cli_missing_input(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["health_weekly_report.py", "--csv", str(tmp_path / "missing.csv")],
    )
    assert health_weekly_main() == 1
