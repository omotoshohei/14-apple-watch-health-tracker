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
    preprocess_xml_to_csv,
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

    assert len(records) == 10
    assert {record.metric_key for record in records} == {
        "sleep_duration",
        "steps",
        "active_energy",
        "exercise_time",
        "stand_hours",
        "sleep_onset",
        "wake_time",
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
    assert float(daily["sleep_onset"].loc[pd.Timestamp("2026-02-01").date()]) == 23.0
    assert float(daily["wake_time"].loc[pd.Timestamp("2026-02-01").date()]) == 30.5
    assert float(daily["awake_count"].loc[pd.Timestamp("2026-02-01").date()]) == 0.0
    assert float(daily["awake_duration"].loc[pd.Timestamp("2026-02-01").date()]) == 0.0
    assert float(daily["longest_awake_duration"].loc[pd.Timestamp("2026-02-01").date()]) == 0.0
    assert pd.isna(daily["first_morning_awake_time"].loc[pd.Timestamp("2026-02-01").date()])
    assert pd.isna(daily["wake_time"].loc[pd.Timestamp("2026-02-02").date()])


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

    from health_report import METRIC_DEFINITIONS

    stats = calculate_stats(series, 8000)
    summary = build_stats_summary(stats, METRIC_DEFINITIONS["steps"])

    assert [(item.label, item.value, item.unit) for item in summary] == [
        ("Average", "6000.0", "steps"),
        ("Maximum", "8000.0", "steps"),
        ("Minimum", "4000.0", "steps"),
        ("Goal Achieved Rate", "50.0", "%"),
    ]


def test_build_stats_summary_handles_no_valid_days() -> None:
    series = pd.Series([pd.NA, pd.NA], dtype="Float64")

    from health_report import METRIC_DEFINITIONS

    stats = calculate_stats(series, 8000)
    summary = build_stats_summary(stats, METRIC_DEFINITIONS["steps"])

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
            "goal_text": f"Goal {index}",
        }
        for index in range(6)
    ]

    output = render_html_report(slides, tmp_path / "report.html", 2026, 2)

    html = output.read_text(encoding="utf-8")
    assert html.count('<section class="slide">') == 6
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
    csv_path = tmp_path / "health_metrics_2026_02.csv"
    write_sample_export(xml_path)
    preprocess_xml_to_csv(xml_path, 2026, 2, csv_path)

    output = generate_report(csv_path, 2026, 2, tmp_path / "output")

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


def test_format_to_time_str() -> None:
    from health_report import format_to_time_str

    assert format_to_time_str(None) == "N/A"
    assert format_to_time_str(23.5) == "23:30"
    assert format_to_time_str(25.25) == "01:15"
    assert format_to_time_str(24.0) == "00:00"
    assert format_to_time_str(18.75) == "18:45"


def test_calculate_stats_lower_is_better() -> None:
    series = pd.Series([23.5, 25.0, 24.0, pd.NA], dtype="Float64")
    # Target value is 24.0, lower is better. 23.5 and 24.0 achieve the goal, 25.0 does not.
    stats = calculate_stats(series, 24.0, lower_is_better=True)
    assert stats.achieved_days == 2
    assert stats.valid_days == 3
    assert stats.missing_days == 1
    assert stats.achievement_rate == pytest.approx(2 / 3 * 100)


def test_sleep_onset_midnight_crossing_and_end_of_month(tmp_path: Path) -> None:

    # We want to test sleep onset timezone and boundary conditions:
    # 1. Midnight crossing (e.g. 01:30 next morning) -> assigned to previous date with 25.5 value.
    # 2. Month-end boundary: A sleep session starting on the morning of March 1st (e.g., 02:00)
    #    should be processed as sleep_onset of Feb 28th.
    records_xml_str = [
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-02-15 01:30:00 +0900",  # Onset of Feb 14th
            "2026-02-15 07:00:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-02-28 23:30:00 +0900",  # Onset of Feb 28th
            "2026-03-01 06:30:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            # Onset of Feb 28th (after 18:00 but before next day 18:00,
            # actually on March 1st 02:00).
            "2026-03-01 02:00:00 +0900",
            # Wait, 2026-03-01 02:00:00 is between Feb 28 18:00 and Mar 1 18:00.
            # However, Feb 28 23:30 was earlier in start time.
            "2026-03-01 07:00:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-03-01 03:00:00 +0900",  # Onset of Feb 28th (if 23:30 record did not exist)
            "2026-03-01 08:00:00 +0900",
        ),
    ]
    xml_path = tmp_path / "export_sleep.xml"
    xml_path.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<HealthData>",
                *records_xml_str,
                "</HealthData>",
            ]
        ),
        encoding="utf-8",
    )

    # We parse for target month Feb (month 2).
    # Since March 1st 03:00:00 is before March 1st 18:00, it should be
    # parsed as Feb 28th sleep onset!
    records = parse_health_records(xml_path, 2026, 2)
    daily = aggregate_daily_metrics(records, 2026, 2)

    # Feb 14th sleep onset should be 25.5
    assert float(daily["sleep_onset"].loc[pd.Timestamp("2026-02-14").date()]) == 25.5

    # Feb 28th sleep onset should select the earliest session starting
    # between Feb 28 18:00 and Mar 1 18:00:
    # We had:
    # - 2026-02-28 23:30 (onset: 23.5)
    # - 2026-03-01 02:00 (onset: 26.0)
    # - 2026-03-01 03:00 (onset: 27.0)
    # The earliest starting session is 2026-02-28 23:30, which is 23.5.
    assert float(daily["sleep_onset"].loc[pd.Timestamp("2026-02-28").date()]) == 23.5

    # Let's verify if we ONLY have the March 1st 03:00:00 session, it parses properly as Feb 28th:
    xml_path_single = tmp_path / "export_single.xml"
    xml_path_single.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<HealthData>",
                record_xml(
                    "HKCategoryTypeIdentifierSleepAnalysis",
                    "HKCategoryValueSleepAnalysisAsleepCore",
                    "2026-03-01 03:00:00 +0900",
                    "2026-03-01 08:00:00 +0900",
                ),
                "</HealthData>",
            ]
        ),
        encoding="utf-8",
    )
    records_single = parse_health_records(xml_path_single, 2026, 2)
    daily_single = aggregate_daily_metrics(records_single, 2026, 2)
    assert float(daily_single["sleep_onset"].loc[pd.Timestamp("2026-02-28").date()]) == 27.0


def test_wake_and_awake_metrics_aggregation(tmp_path: Path) -> None:
    records_xml_str = [
        # Sleep session: 2026-02-15 00:00 to 07:30 (bedtime date: 2026-02-14)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-02-15 00:00:00 +0900",
            "2026-02-15 02:00:00 +0900",
        ),
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAsleepCore",
            "2026-02-15 03:00:00 +0900",
            "2026-02-15 07:30:00 +0900",
        ),
        # Awake records:
        # 1. Before sleep session (outside)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-14 23:30:00 +0900",
            "2026-02-14 23:45:00 +0900",
        ),
        # 2. During first sleep interval (inside, duration = 15m)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-15 01:00:00 +0900",
            "2026-02-15 01:15:00 +0900",
        ),
        # 3. Between sleep intervals (inside, duration = 40m)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-15 02:30:00 +0900",
            "2026-02-15 03:10:00 +0900",
        ),
        # 4. Spanning sleep session end (inside part: 07:15 to 07:30 = 15m)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-15 07:15:00 +0900",
            "2026-02-15 07:45:00 +0900",
        ),
        # 5. After sleep session end (outside)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-15 08:00:00 +0900",
            "2026-02-15 08:30:00 +0900",
        ),
        # 6. Morning awake record (inside morning 5-12 bounds, duration = 10m)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisAwake",
            "2026-02-15 06:00:00 +0900",
            "2026-02-15 06:10:00 +0900",
        ),
        # InBed record (should be ignored)
        record_xml(
            "HKCategoryTypeIdentifierSleepAnalysis",
            "HKCategoryValueSleepAnalysisInBed",
            "2026-02-15 00:00:00 +0900",
            "2026-02-15 07:30:00 +0900",
        ),
    ]

    xml_path = tmp_path / "export_awake.xml"
    xml_path.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<HealthData>",
                *records_xml_str,
                "</HealthData>",
            ]
        ),
        encoding="utf-8",
    )

    records = parse_health_records(xml_path, 2026, 2)
    daily = aggregate_daily_metrics(records, 2026, 2)

    target_date = pd.Timestamp("2026-02-14").date()

    # wake_time: 07:30 next morning -> 31.5
    assert float(daily["wake_time"].loc[target_date]) == 31.5

    # awake_count: records 2, 3, 4, 6 (4 overlapping records)
    assert float(daily["awake_count"].loc[target_date]) == 4.0

    # awake_duration: 15 (rec 2) + 40 (rec 3) + 15 (rec 4 clipped) + 10 (rec 6) = 80.0 minutes
    assert float(daily["awake_duration"].loc[target_date]) == 80.0

    # longest_awake_duration: rec 3 (40 minutes)
    assert float(daily["longest_awake_duration"].loc[target_date]) == 40.0

    # first_morning_awake_time: rec 6 starts at 06:00 next morning -> 30.0
    assert float(daily["first_morning_awake_time"].loc[target_date]) == 30.0

    # Test day with sleep but NO awake records
    xml_path_no_awake = tmp_path / "export_no_awake.xml"
    xml_path_no_awake.write_text(
        "\n".join(
            [
                '<?xml version="1.0" encoding="UTF-8"?>',
                "<HealthData>",
                record_xml(
                    "HKCategoryTypeIdentifierSleepAnalysis",
                    "HKCategoryValueSleepAnalysisAsleepCore",
                    "2026-02-15 00:00:00 +0900",
                    "2026-02-15 07:30:00 +0900",
                ),
                "</HealthData>",
            ]
        ),
        encoding="utf-8",
    )
    records_no_awake = parse_health_records(xml_path_no_awake, 2026, 2)
    daily_no_awake = aggregate_daily_metrics(records_no_awake, 2026, 2)

    assert float(daily_no_awake["wake_time"].loc[target_date]) == 31.5
    assert float(daily_no_awake["awake_count"].loc[target_date]) == 0.0
    assert float(daily_no_awake["awake_duration"].loc[target_date]) == 0.0
    assert float(daily_no_awake["longest_awake_duration"].loc[target_date]) == 0.0
    assert pd.isna(daily_no_awake["first_morning_awake_time"].loc[target_date])
