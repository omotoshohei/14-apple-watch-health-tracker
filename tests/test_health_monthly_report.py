from pathlib import Path

import pandas as pd
import pytest

from health_monthly_report import (
    INSIGHT_FALLBACK,
    aggregate_daily_metrics,
    build_insight_prompt,
    calculate_stats,
    generate_report,
    parse_health_records,
    render_html_report,
    validate_inputs,
)


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


def test_parse_health_records_filters_target_month(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    write_sample_export(xml_path)

    records = parse_health_records(xml_path, 2026, 2)

    assert len(records) == 8
    assert {record.metric_key for record in records} == {
        "sleep_duration",
        "steps",
        "active_energy",
        "exercise_time",
        "stand_hours",
    }


def test_aggregate_daily_metrics_preserves_missing_days(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    write_sample_export(xml_path)
    records = parse_health_records(xml_path, 2026, 2)

    daily = aggregate_daily_metrics(records, 2026, 2)

    assert float(daily["steps"].loc[pd.Timestamp("2026-02-01").date()]) == 3500
    assert pd.isna(daily["steps"].loc[pd.Timestamp("2026-02-02").date()])
    assert float(daily["stand_hours"].loc[pd.Timestamp("2026-02-01").date()]) == 2
    assert float(daily["sleep_duration"].loc[pd.Timestamp("2026-02-01").date()]) == 1
    assert float(daily["sleep_duration"].loc[pd.Timestamp("2026-02-02").date()]) == 6.5


def test_calculate_stats_excludes_missing_days() -> None:
    series = pd.Series([8000.0, pd.NA, 4000.0], dtype="Float64")

    stats = calculate_stats(series, 8000)

    assert stats.average == 6000
    assert stats.maximum == 8000
    assert stats.valid_days == 2
    assert stats.missing_days == 1
    assert stats.achieved_days == 1
    assert stats.achievement_rate == 50


def test_build_insight_prompt_marks_missing_values(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    write_sample_export(xml_path)
    records = parse_health_records(xml_path, 2026, 2)
    daily = aggregate_daily_metrics(records, 2026, 2)
    from health_monthly_report import METRIC_DEFINITIONS

    metric = METRIC_DEFINITIONS["steps"]
    stats = calculate_stats(daily["steps"], metric.target_value)

    prompt = build_insight_prompt(metric, daily["steps"], stats, 2026, 2)

    assert "2026-02-01: 3500.0" in prompt
    assert "2026-02-02: N/A" in prompt
    assert "Missing Days" in prompt


def test_render_html_report_writes_five_slide_report(tmp_path: Path) -> None:
    slides = [
        {
            "name": f"Metric {index}",
            "image_path": f"assets/metric_{index}.png",
            "insight": "A short insight.",
            "target_value": "1",
            "unit": "unit",
        }
        for index in range(5)
    ]

    output = render_html_report(slides, tmp_path / "report.html", 2026, 2)

    html = output.read_text(encoding="utf-8")
    assert html.count('<section class="slide">') == 5
    assert "1920px" in html
    assert "1080px" in html


def test_validate_inputs_requires_xml_and_api_key(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"

    with pytest.raises(FileNotFoundError):
        validate_inputs(xml_path, "key")

    xml_path.write_text("<HealthData />", encoding="utf-8")
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        validate_inputs(xml_path, None)


def test_generate_report_uses_fallback_when_gemini_fails(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    xml_path = tmp_path / "export.xml"
    write_sample_export(xml_path)

    def fail_insight(*args: object, **kwargs: object) -> str:
        raise RuntimeError(INSIGHT_FALLBACK)

    monkeypatch.setattr("health_monthly_report.get_gemini_insight", fail_insight)

    output = generate_report(xml_path, 2026, 2, tmp_path / "output", api_key="dummy")

    html = output.read_text(encoding="utf-8")
    assert output.name == "apple_watch_health_monthly_report_2026_02.html"
    assert html.count(INSIGHT_FALLBACK) == 5
    assert (tmp_path / "output" / "assets" / "sleep_duration.png").exists()
