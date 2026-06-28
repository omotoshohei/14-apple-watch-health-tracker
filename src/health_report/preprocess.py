from __future__ import annotations

from pathlib import Path

import pandas as pd

from .report import aggregate_daily_metrics, parse_health_records


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

    columns = [
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
    for col in columns:
        df[col] = daily_metrics[col]

    df_reset = df.reset_index()
    # Write to CSV, representing missing values as 'NA'.
    df_reset.to_csv(output_csv_path, index=False, na_rep="NA")
    return output_csv_path
