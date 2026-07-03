from __future__ import annotations

from pathlib import Path

import pandas as pd

from .report import (
    METRIC_DEFINITIONS,
    aggregate_daily_metrics,
    calculate_stats,
    month_dates,
    parse_health_records,
)

DAILY_METRIC_COLUMNS = [
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


def preprocess_xml_to_csv(
    xml_path: Path,
    target_year: int,
    target_month: int,
    output_csv_path: Path,
) -> Path:
    """Preprocess Apple Health XML data and output a day-by-day CSV for the target month.

    Args:
        xml_path: Path to the Apple Health export.xml.
        target_year: The target year (e.g. 2026).
        target_month: The target month (1-12).
        output_csv_path: The path where the CSV should be saved.

    Returns:
        The path of the generated CSV file.
    """
    records = parse_health_records(xml_path, target_year, target_month)
    daily_metrics = aggregate_daily_metrics(records, target_year, target_month)

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)

    # All series share the same index of datetime.date objects representing the month's days.
    # We construct the DataFrame using these dates.
    dates = list(daily_metrics.values())[0].index
    df = pd.DataFrame(index=dates)
    df.index.name = "date"

    for col in DAILY_METRIC_COLUMNS:
        df[col] = daily_metrics[col]

    df_reset = df.reset_index()
    # Write to CSV, representing missing values as 'NA'.
    df_reset.to_csv(output_csv_path, index=False, na_rep="NA")
    return output_csv_path


def aggregate_daily_csv_to_monthly_csv(input_csv_path: Path, output_csv_path: Path) -> Path:
    """Aggregate a day-by-day health metrics CSV into month-level metric statistics.

    The output uses one row per (month, metric), so trend reports can consume a
    single monthly CSV without re-reading daily data.
    """
    if not input_csv_path.exists():
        raise FileNotFoundError(f"Error: CSV file not found: {input_csv_path}")

    dtypes = {col: "Float64" for col in DAILY_METRIC_COLUMNS}
    df = pd.read_csv(input_csv_path, dtype=dtypes, keep_default_na=False, na_values=["NA"])

    required_cols = ["date", *DAILY_METRIC_COLUMNS]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Error: Missing required column in CSV: {missing_cols[0]}")

    try:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    except Exception as exc:
        raise ValueError("Error: Failed to parse dates in CSV.") from exc

    df = df.sort_values("date").drop_duplicates(subset=["date"], keep="last")
    df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")

    rows: list[dict[str, object]] = []
    for month, month_df in df.groupby("month", sort=True):
        year, month_num = (int(part) for part in month.split("-"))
        month_df = month_df.set_index("date").reindex(month_dates(year, month_num))

        for metric in METRIC_DEFINITIONS.values():
            series = month_df[metric.key]
            stats = calculate_stats(
                series,
                metric.target_value,
                lower_is_better=metric.lower_is_better,
            )
            rows.append(
                {
                    "month": month,
                    "metric": metric.key,
                    "metric_name": metric.name,
                    "unit": metric.unit,
                    "target_value": metric.target_value,
                    "lower_is_better": metric.lower_is_better,
                    "average": stats.average,
                    "maximum": stats.maximum,
                    "minimum": stats.minimum,
                    "achieved_days": stats.achieved_days,
                    "valid_days": stats.valid_days,
                    "missing_days": stats.missing_days,
                    "achievement_rate": stats.achievement_rate,
                }
            )

    output_csv_path.parent.mkdir(parents=True, exist_ok=True)
    monthly_df = pd.DataFrame(rows)
    monthly_df.to_csv(output_csv_path, index=False, na_rep="NA")
    return output_csv_path
