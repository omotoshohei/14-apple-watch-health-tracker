from pathlib import Path

import pandas as pd
import pytest

from health_report.preprocess import preprocess_xml_to_csv
from health_report.report import generate_report, load_daily_metrics_from_csv


def record_xml(record_type: str, value: str, start: str, end: str, unit: str | None = None) -> str:
    unit_attr = "" if unit is None else f' unit="{unit}"'
    return (
        f'  <Record type="{record_type}" value="{value}"{unit_attr} '
        f'startDate="{start}" endDate="{end}"/>'
    )


def write_sample_export(path: Path) -> None:
    records = [
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-02-01 23:00:00 +0900",
            "2026-02-02 06:30:00 +0900",
        ),
        record_xml(
            "HKQuantityTypeIdentifierStepCount",
            "1000",
            "2026-02-01 10:00:00 +0900",
            "2026-02-01 10:05:00 +0900",
            "count",
        ),
        record_xml(
            "HKQuantityTypeIdentifierStepCount",
            "2500",
            "2026-02-01 11:00:00 +0900",
            "2026-02-01 11:05:00 +0900",
            "count",
        ),
        record_xml(
            "HKQuantityTypeIdentifierActiveEnergyBurned",
            "520",
            "2026-02-01 12:00:00 +0900",
            "2026-02-01 12:10:00 +0900",
            "kcal",
        ),
        record_xml(
            "HKQuantityTypeIdentifierAppleExerciseTime",
            "35",
            "2026-02-01 18:00:00 +0900",
            "2026-02-01 18:35:00 +0900",
            "min",
        ),
        record_xml(
            "HKCategoryTypeIdentifierAppleStandHour",
            "HKCategoryValueAppleStandHourStood",
            "2026-02-01 09:00:00 +0900",
            "2026-02-01 09:05:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierAppleStandHour",
            "HKCategoryValueAppleStandHourStood",
            "2026-02-01 09:30:00 +0900",
            "2026-02-01 09:35:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierAppleStandHour",
            "HKCategoryValueAppleStandHourStood",
            "2026-02-01 10:00:00 +0900",
            "2026-02-01 10:05:00 +0900",
        ),
        record_xml(
            "HKQuantityTypeIdentifierStepCount",
            "9999",
            "2026-03-01 10:00:00 +0900",
            "2026-03-01 10:05:00 +0900",
            "count",
        ),
    ]
    path.write_text(
        "\n".join(
            ['<?xml version="1.0" encoding="UTF-8"?>', "<HealthData>", *records, "</HealthData>"]
        ),
        encoding="utf-8",
    )


def test_load_daily_metrics_from_csv_success(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    csv_path = tmp_path / "health_metrics_2026_02.csv"
    write_sample_export(xml_path)
    preprocess_xml_to_csv(xml_path, 2026, 2, csv_path)

    metrics = load_daily_metrics_from_csv(csv_path, 2026, 2)
    assert len(metrics) == 11
    assert "steps" in metrics
    assert "sleep_onset" in metrics
    assert "wake_time" in metrics
    assert len(metrics["steps"]) == 28
    assert metrics["steps"].loc[pd.Timestamp("2026-02-01").date()] == 3500
    assert pd.isna(metrics["steps"].loc[pd.Timestamp("2026-02-02").date()])


def test_load_daily_metrics_from_csv_missing_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "corrupt.csv"
    # missing steps column
    csv_path.write_text(
        "date,sleep_duration,active_energy,exercise_time,stand_hours,sleep_onset,"
        "wake_time,awake_count,awake_duration,longest_awake_duration,first_morning_awake_time\n"
        "2026-02-01,7.0,500.0,30.0,12.0,24.0,31.0,0.0,0.0,0.0,NA\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required column in CSV"):
        load_daily_metrics_from_csv(csv_path, 2026, 2)


def test_load_daily_metrics_from_csv_date_outside_month(tmp_path: Path) -> None:
    csv_path = tmp_path / "outside.csv"
    # March 1st in February report
    content = (
        "date,sleep_duration,steps,active_energy,exercise_time,stand_hours,sleep_onset,"
        "wake_time,awake_count,awake_duration,longest_awake_duration,first_morning_awake_time\n"
        "2026-02-01,7.0,1000,500.0,30.0,12.0,23.5,31.0,0.0,0.0,0.0,NA\n"
        "2026-03-01,7.0,1000,500.0,30.0,12.0,23.5,31.0,0.0,0.0,0.0,NA\n"
    )
    csv_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="contains dates outside target month"):
        load_daily_metrics_from_csv(csv_path, 2026, 2)


def test_load_daily_metrics_from_csv_missing_dates(tmp_path: Path) -> None:
    csv_path = tmp_path / "missing_dates.csv"
    # Only 1 day provided for February
    content = (
        "date,sleep_duration,steps,active_energy,exercise_time,stand_hours,sleep_onset,"
        "wake_time,awake_count,awake_duration,longest_awake_duration,first_morning_awake_time\n"
        "2026-02-01,7.0,1000,500.0,30.0,12.0,23.5,31.0,0.0,0.0,0.0,NA\n"
    )
    csv_path.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError, match="is missing dates for the target month"):
        load_daily_metrics_from_csv(csv_path, 2026, 2)


def test_generate_report_from_csv_success(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    csv_path = tmp_path / "health_metrics_2026_02.csv"
    write_sample_export(xml_path)
    preprocess_xml_to_csv(xml_path, 2026, 2, csv_path)

    output_dir = tmp_path / "output"
    report_path = generate_report(csv_path, 2026, 2, output_dir)
    assert report_path.exists()
    assert report_path.name == "apple_watch_health_monthly_report_2026_02.html"

    html = report_path.read_text(encoding="utf-8")
    assert "Average" in html
    assert "Maximum" in html
