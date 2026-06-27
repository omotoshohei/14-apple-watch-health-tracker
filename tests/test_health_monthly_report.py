from pathlib import Path

import pandas as pd
import pytest

from health_report import (
    aggregate_daily_metrics,
    build_stats_summary,
    calculate_stats,
    clean_and_prefix_svg,
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
    assert stats.minimum == 4000
    assert stats.valid_days == 2
    assert stats.missing_days == 1
    assert stats.achieved_days == 1
    assert stats.achievement_rate == 50


def test_build_stats_summary_formats_display_values() -> None:
    series = pd.Series([8000.0, pd.NA, 4000.0], dtype="Float64")

    stats = calculate_stats(series, 8000)
    summary = build_stats_summary(stats, "steps")

    assert [(item.label, item.value, item.unit) for item in summary] == [
        ("Average", "6000.0", "steps"),
        ("Maximum", "8000.0", "steps"),
        ("Minimum", "4000.0", "steps"),
        ("Goal Achieved Rate", "50.0", "%"),
    ]


def test_build_stats_summary_handles_no_valid_days() -> None:
    series = pd.Series([pd.NA, pd.NA], dtype="Float64")

    stats = calculate_stats(series, 8000)
    summary = build_stats_summary(stats, "steps")

    assert [(item.label, item.value, item.unit) for item in summary] == [
        ("Average", "N/A", "steps"),
        ("Maximum", "N/A", "steps"),
        ("Minimum", "N/A", "steps"),
        ("Goal Achieved Rate", "N/A", "%"),
    ]


def test_render_html_report_writes_five_slide_report(tmp_path: Path) -> None:
    slides = [
        {
            "name": f"Metric {index}",
            "chart_svg": f"<svg id='dummy_{index}'>...</svg>",
            "stats_summary": [
                {"label": "Average", "value": "1.0", "unit": "unit"},
                {"label": "Maximum", "value": "2.0", "unit": "unit"},
                {"label": "Minimum", "value": "0.5", "unit": "unit"},
                {"label": "Goal Achieved Rate", "value": "50.0", "unit": "%"},
            ],
            "target_value": "1",
            "unit": "unit",
        }
        for index in range(5)
    ]

    output = render_html_report(slides, tmp_path / "report.html", 2026, 2)

    html = output.read_text(encoding="utf-8")
    assert html.count('<section class="slide">') == 5
    assert "Monthly Stats" in html
    assert "Goal Achieved Rate" in html
    assert "Gemini Insight" not in html
    assert "1920px" in html
    assert "1080px" in html


def test_validate_inputs_requires_xml_only(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"

    with pytest.raises(FileNotFoundError):
        validate_inputs(xml_path)

    xml_path.write_text("<HealthData />", encoding="utf-8")
    assert validate_inputs(xml_path) is None


def test_generate_report_outputs_stats_without_api_key(tmp_path: Path) -> None:
    xml_path = tmp_path / "export.xml"
    write_sample_export(xml_path)

    output = generate_report(xml_path, 2026, 2, tmp_path / "output")

    html = output.read_text(encoding="utf-8")
    assert output.name == "apple_watch_health_monthly_report_2026_02.html"
    assert "Average" in html
    assert "Maximum" in html
    assert "Minimum" in html
    assert "Goal Achieved Rate" in html
    assert "Gemini Insight" not in html
    assert '<svg id="sleep_duration_svg" class="matplotlib-svg"' in html
    assert not (tmp_path / "output" / "assets").exists()


def test_clean_and_prefix_svg() -> None:
    raw_svg = """<?xml version="1.0" encoding="utf-8" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg id="old-root-id" class="old-root-class"
     xmlns:xlink="http://www.w3.org/1999/xlink" width="10" height="10">
  <defs>
    <style type="text/css">*{stroke: red}</style>
  </defs>
  <g id="figure_1">
    <path id="path_1" clip-path="url(#clip_1)" xlink:href="#sym_1" href="#sym_2"/>
  </g>
</svg>"""

    processed = clean_and_prefix_svg(raw_svg, "test-metric@foo")
    # Verify prefix sanitization
    assert 'id="test-metric_foo_svg"' in processed
    assert 'class="matplotlib-svg"' in processed
    assert 'id="test-metric_foo_figure_1"' in processed
    assert 'id="test-metric_foo_path_1"' in processed
    assert 'clip-path="url(#test-metric_foo_clip_1)"' in processed
    assert 'xlink:href="#test-metric_foo_sym_1"' in processed
    assert 'href="#test-metric_foo_sym_2"' in processed
    assert "#test-metric_foo_svg *{stroke: red}" in processed
    assert "<?xml" not in processed
    assert "<!DOCTYPE" not in processed
