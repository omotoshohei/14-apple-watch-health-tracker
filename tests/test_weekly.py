from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from health_report.weekly import (
    WEEKLY_COLUMNS,
    aggregate_daily_csv_to_weekly_csv,
    generate_weekly_report,
    generate_weekly_trend_charts,
    load_weekly_trend_data,
)

DAILY_COLUMNS = [
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


def write_daily_csv(path: Path) -> None:
    rows = []
    for day in pd.date_range("2026-06-03", "2026-06-24", freq="D"):
        if day == pd.Timestamp("2026-06-10"):
            continue
        rows.append(
            {
                "date": day.date().isoformat(),
                "sleep_duration": 7.0,
                "steps": pd.NA if day == pd.Timestamp("2026-06-09") else 16000,
                "active_energy": 600,
                "exercise_time": 40,
                "stand_hours": 13,
                "sleep_onset": 24.5,
                "wake_time": 31.5,
                "awake_count": 0,
                "awake_duration": 3,
                "longest_awake_duration": 3,
                "first_morning_awake_time": 31.5,
            }
        )
    pd.DataFrame(rows, columns=DAILY_COLUMNS).to_csv(path, index=False, na_rep="NA")


def test_aggregate_daily_csv_to_weekly_csv_generates_complete_monday_weeks(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily.csv"
    output_csv = tmp_path / "weekly.csv"
    write_daily_csv(input_csv)

    output = aggregate_daily_csv_to_weekly_csv(input_csv, output_csv)

    assert output == output_csv
    df = pd.read_csv(output_csv, keep_default_na=False, na_values=["NA"])
    assert list(df.columns) == WEEKLY_COLUMNS
    assert df["week"].unique().tolist() == ["2026-W24", "2026-W25"]
    assert df["week_start"].unique().tolist() == ["2026-06-08", "2026-06-15"]
    assert df["week_end"].unique().tolist() == ["2026-06-14", "2026-06-21"]


def test_weekly_aggregation_counts_missing_rows_and_values(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily.csv"
    output_csv = tmp_path / "weekly.csv"
    write_daily_csv(input_csv)

    aggregate_daily_csv_to_weekly_csv(input_csv, output_csv)
    df = pd.read_csv(output_csv, keep_default_na=False, na_values=["NA"])
    steps = df[(df["week"] == "2026-W24") & (df["metric"] == "steps")].iloc[0]

    assert steps["valid_days"] == 5
    assert steps["missing_days"] == 2
    assert steps["achieved_days"] == 5
    assert steps["achievement_rate"] == 100


def test_weekly_aggregation_lower_is_better_metric(tmp_path: Path) -> None:
    input_csv = tmp_path / "daily.csv"
    output_csv = tmp_path / "weekly.csv"
    write_daily_csv(input_csv)

    aggregate_daily_csv_to_weekly_csv(input_csv, output_csv)
    df = pd.read_csv(output_csv, keep_default_na=False, na_values=["NA"])
    onset = df[(df["week"] == "2026-W25") & (df["metric"] == "sleep_onset")].iloc[0]

    assert onset["valid_days"] == 7
    assert onset["achieved_days"] == 7


def test_weekly_aggregation_requires_complete_week(tmp_path: Path) -> None:
    input_csv = tmp_path / "short.csv"
    output_csv = tmp_path / "weekly.csv"
    pd.DataFrame(
        [{"date": "2026-06-03", **{col: 1 for col in DAILY_COLUMNS if col != "date"}}]
    ).to_csv(input_csv, index=False)

    with pytest.raises(ValueError, match="complete Monday-start weeks"):
        aggregate_daily_csv_to_weekly_csv(input_csv, output_csv)


def test_load_weekly_trend_data_missing_column(tmp_path: Path) -> None:
    csv_path = tmp_path / "weekly.csv"
    csv_path.write_text(
        "week,week_start,week_end,metric,maximum,minimum,achieved_days,valid_days\n"
        "2026-W24,2026-06-08,2026-06-14,steps,1,1,1,1\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Missing required column"):
        load_weekly_trend_data(csv_path)


def test_generate_weekly_report_with_missing_metric_slide(tmp_path: Path) -> None:
    csv_path = tmp_path / "weekly.csv"
    csv_path.write_text(
        "\n".join(
            [
                ",".join(WEEKLY_COLUMNS),
                (
                    "2026-W24,2026-06-08,2026-06-14,sleep_duration,Sleep Duration,"
                    "hours,6.5,False,7.0,8.0,6.0,7,7,0,100.0"
                ),
            ]
        ),
        encoding="utf-8",
    )

    df = load_weekly_trend_data(csv_path)
    charts = generate_weekly_trend_charts(df)
    assert "steps" in charts
    assert "No weekly data" in charts["steps"]

    output = generate_weekly_report(csv_path, tmp_path / "output")
    html = output.read_text(encoding="utf-8")

    assert output.name == "apple_watch_health_weekly_report.html"
    assert "Sleep Duration Weekly Trend" in html
    assert "Steps Weekly Trend" in html
    assert "2026-06-08 ~ 2026-06-14" in html
    assert "No weekly data" in html


def test_generate_weekly_report_limits_visuals_to_recent_ten_weeks(tmp_path: Path) -> None:
    csv_path = tmp_path / "weekly.csv"
    rows = [",".join(WEEKLY_COLUMNS)]
    for week_start in pd.date_range("2026-04-06", periods=11, freq="W-MON"):
        week_end = week_start + pd.Timedelta(days=6)
        iso = week_start.isocalendar()
        rows.append(
            ",".join(
                [
                    f"{iso.year}-W{iso.week:02d}",
                    week_start.date().isoformat(),
                    week_end.date().isoformat(),
                    "sleep_duration",
                    "Sleep Duration",
                    "hours",
                    "6.5",
                    "False",
                    "7.0",
                    "8.0",
                    "6.0",
                    "7",
                    "7",
                    "0",
                    "100.0",
                ]
            )
        )
    csv_path.write_text("\n".join(rows), encoding="utf-8")

    output = generate_weekly_report(csv_path, tmp_path / "output")
    html = output.read_text(encoding="utf-8")

    assert "2026-04-13 ~ 2026-06-21" in html
    assert "2026-W15" not in html
    assert "2026-04-06 - 2026-04-12" not in html
    assert "2026-W16" in html
    assert "2026-W25" in html
