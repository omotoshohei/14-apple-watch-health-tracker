from pathlib import Path

import pandas as pd

from health_report.preprocess import preprocess_xml_to_csv


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


def test_preprocess_xml_to_csv(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    csv_path = tmp_path / "health_metrics_2026_02.csv"
    write_sample_export(xml_path)

    res_path = preprocess_xml_to_csv(xml_path, 2026, 2, csv_path)
    assert res_path == csv_path
    assert csv_path.exists()

    # Read CSV and verify
    df = pd.read_csv(
        csv_path,
        dtype={
            "sleep_duration": "Float64",
            "steps": "Float64",
            "active_energy": "Float64",
            "exercise_time": "Float64",
            "stand_hours": "Float64",
            "sleep_onset": "Float64",
            "wake_time": "Float64",
            "awake_count": "Float64",
            "awake_duration": "Float64",
            "longest_awake_duration": "Float64",
            "first_morning_awake_time": "Float64",
        },
        keep_default_na=False,
        na_values=["NA"],
    )
    assert list(df.columns) == [
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
    assert len(df) == 28  # Feb 2026 has 28 days

    # 2026-02-01 values:
    row_1 = df[df["date"] == "2026-02-01"].iloc[0]
    assert float(row_1["steps"]) == 3500.0
    assert float(row_1["active_energy"]) == 520.0
    assert float(row_1["exercise_time"]) == 35.0
    assert float(row_1["stand_hours"]) == 2.0
    assert float(row_1["sleep_duration"]) == 1.0
    assert float(row_1["sleep_onset"]) == 23.0
    assert float(row_1["wake_time"]) == 30.5  # ends at 06:30 next morning -> 30.5
    assert float(row_1["awake_count"]) == 0.0
    assert float(row_1["awake_duration"]) == 0.0
    assert float(row_1["longest_awake_duration"]) == 0.0
    assert pd.isna(row_1["first_morning_awake_time"])

    # 2026-02-02 values:
    row_2 = df[df["date"] == "2026-02-02"].iloc[0]
    assert pd.isna(row_2["steps"])
    assert float(row_2["sleep_duration"]) == 6.5
    assert pd.isna(row_2["sleep_onset"])
    assert pd.isna(row_2["wake_time"])
    assert pd.isna(row_2["awake_count"])
