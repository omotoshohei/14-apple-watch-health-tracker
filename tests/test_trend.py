from __future__ import annotations

from pathlib import Path

import pytest

from health_report.trend import (
    generate_trend_charts,
    generate_trend_report,
    load_monthly_trend_data,
)


def write_dummy_monthly_csv(path: Path) -> None:
    """Create a mock health_metrics_monthly.csv file for testing."""
    rows = [
        "month,metric,metric_name,unit,target_value,lower_is_better,average,maximum,minimum,achieved_days,valid_days,missing_days,achievement_rate",
        # Sleep duration (normal metric)
        "2026-02,sleep_duration,Sleep Duration,hours,6.5,False,6.5,8.0,5.0,15,28,0,53.57",
        "2026-03,sleep_duration,Sleep Duration,hours,6.5,False,7.2,8.5,5.5,20,31,0,64.52",
        # Sleep onset (time metric)
        "2026-02,sleep_onset,Sleep Onset Time,hours,25.5,True,24.5,26.0,23.0,10,28,0,35.71",
        "2026-03,sleep_onset,Sleep Onset Time,hours,25.5,True,23.8,25.5,22.5,18,31,0,58.06",
    ]
    path.write_text("\n".join(rows), encoding="utf-8")


def test_load_monthly_trend_data(tmp_path: Path) -> None:
    csv_path = tmp_path / "health_metrics_monthly.csv"
    write_dummy_monthly_csv(csv_path)

    df = load_monthly_trend_data(csv_path)
    assert len(df) == 4
    assert list(df["month"].unique()) == ["2026-02", "2026-03"]
    assert "sleep_duration" in df["metric"].values
    assert "sleep_onset" in df["metric"].values


def test_load_monthly_trend_data_missing_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "corrupted_monthly.csv"
    # missing 'average' column
    rows = [
        "month,metric,metric_name,unit,target_value,lower_is_better,maximum,minimum,achieved_days,valid_days,missing_days,achievement_rate",
        "2026-02,sleep_duration,Sleep Duration,hours,6.5,False,8.0,5.0,15,28,0,53.57",
    ]
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    with pytest.raises(ValueError, match="Missing required column"):
        load_monthly_trend_data(csv_path)


def test_generate_trend_charts(tmp_path: Path) -> None:
    csv_path = tmp_path / "health_metrics_monthly.csv"
    write_dummy_monthly_csv(csv_path)
    df = load_monthly_trend_data(csv_path)

    charts = generate_trend_charts(df)
    # Check that SVGs are generated for the metrics present in METRIC_DEFINITIONS
    # (Since generate_trend_charts generates charts for all defined METRIC_DEFINITIONS)
    assert "sleep_duration" in charts
    assert "sleep_onset" in charts
    assert "<svg" in charts["sleep_duration"]
    assert "trend_sleep_duration_svg" in charts["sleep_duration"]  # Prefixed id


def test_generate_trend_report(tmp_path: Path) -> None:
    csv_path = tmp_path / "health_metrics_monthly.csv"
    write_dummy_monthly_csv(csv_path)

    output_dir = tmp_path / "output"
    output_html = generate_trend_report(csv_path, output_dir)

    assert output_html.exists()
    html_content = output_html.read_text(encoding="utf-8")
    assert "<!doctype html>" in html_content
    assert "Sleep Duration Trend" in html_content
    assert "Sleep Onset Time Trend" in html_content
    assert "2026-02 ~ 2026-03" in html_content  # Period string
    assert "trend_sleep_duration_svg" in html_content  # Chart SVG embedded
