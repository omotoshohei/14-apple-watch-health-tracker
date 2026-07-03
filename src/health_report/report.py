from __future__ import annotations

import calendar
import html
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")

import io
import re

import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Template
from matplotlib.ticker import FuncFormatter


def clean_and_prefix_svg(svg_content: str, prefix: str) -> str:
    """Preprocess Matplotlib SVG to prevent ID collision in a single HTML document."""
    # 1. Sanitize prefix
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", prefix)

    # 2. Extract starting from <svg
    svg_idx = svg_content.find("<svg")
    if svg_idx == -1:
        raise ValueError("Input SVG content does not contain '<svg' tag.")
    svg = svg_content[svg_idx:]

    # 3. Replace existing ID definitions
    svg = re.sub(r'\bid=(["\'])([^"\'>\s]+)\1', rf"id=\1{safe_prefix}_\2\1", svg)

    # 4. Replace references
    svg = re.sub(r'url\((["\']?)#([^)\'"]+)\1\)', rf"url(\1#{safe_prefix}_\2\1)", svg)
    svg = re.sub(r'\b(xlink:)?href=(["\']?)#([^"\'>\s]+)\2', rf"\1href=\2#{safe_prefix}_\3\2", svg)

    # 5. Clean and add id/class to the root <svg ...> tag
    def clean_root_svg(match: re.Match) -> str:
        tag_content = match.group(0)
        # Remove any existing id="..." or class="..." inside this tag
        tag_content = re.sub(r'\bid=(["\']?)[^"\'>\s]+\1', "", tag_content)
        tag_content = re.sub(r'\bclass=(["\']?)[^"\'>\s]+\1', "", tag_content)
        # Insert new id and class
        tag_content = re.sub(
            r"^<svg", f'<svg id="{safe_prefix}_svg" class="matplotlib-svg"', tag_content
        )
        tag_content = re.sub(r"\s+", " ", tag_content)
        return tag_content

    svg = re.sub(r"^<svg[^>]*>", clean_root_svg, svg, count=1)

    # 6. Style tag scoping
    svg = re.sub(
        r"(<style[^>]*>)(.*?)(</style>)",
        lambda m: (
            m.group(1) + re.sub(r"\*\s*\{", f"#{safe_prefix}_svg *{{", m.group(2)) + m.group(3)
        ),
        svg,
        flags=re.DOTALL,
    )

    return svg


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    name: str
    record_type: str
    unit: str
    target_value: float
    aggregation: str
    color: str
    lower_is_better: bool = False


@dataclass(frozen=True)
class HealthRecord:
    metric_key: str
    start: datetime
    end: datetime
    value: float | str | None


@dataclass(frozen=True)
class MetricStats:
    average: float | None
    maximum: float | None
    minimum: float | None
    achieved_days: int
    valid_days: int
    missing_days: int
    achievement_rate: float | None


@dataclass(frozen=True)
class StatSummaryItem:
    label: str
    value: str
    unit: str


METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "sleep_duration": MetricDefinition(
        key="sleep_duration",
        name="Sleep Duration",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="hours",
        target_value=6.5,
        aggregation="duration_hours",
        color="#38bdf8",
    ),
    "steps": MetricDefinition(
        key="steps",
        name="Steps",
        record_type="HKQuantityTypeIdentifierStepCount",
        unit="steps",
        target_value=15000.0,
        aggregation="sum",
        color="#34d399",
    ),
    "active_energy": MetricDefinition(
        key="active_energy",
        name="Active Energy Burned",
        record_type="HKQuantityTypeIdentifierActiveEnergyBurned",
        unit="kcal",
        target_value=500.0,
        aggregation="sum",
        color="#f59e0b",
    ),
    "exercise_time": MetricDefinition(
        key="exercise_time",
        name="Exercise Time",
        record_type="HKQuantityTypeIdentifierAppleExerciseTime",
        unit="minutes",
        target_value=30.0,
        aggregation="sum",
        color="#a78bfa",
    ),
    "stand_hours": MetricDefinition(
        key="stand_hours",
        name="Stand Hours",
        record_type="HKCategoryTypeIdentifierAppleStandHour",
        unit="hours",
        target_value=12.0,
        aggregation="unique_hours",
        color="#fb7185",
    ),
    "sleep_onset": MetricDefinition(
        key="sleep_onset",
        name="Sleep Onset Time",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="hours",
        target_value=25.5,
        aggregation="sleep_onset",
        color="#818cf8",
        lower_is_better=True,
    ),
    "wake_time": MetricDefinition(
        key="wake_time",
        name="Wake Time",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="hours",
        target_value=32.5,
        aggregation="wake_time",
        color="#14b8a6",
        lower_is_better=True,
    ),
    "awake_count": MetricDefinition(
        key="awake_count",
        name="Awake Count",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="times",
        target_value=1.0,
        aggregation="awake_count",
        color="#f97316",
        lower_is_better=True,
    ),
    "awake_duration": MetricDefinition(
        key="awake_duration",
        name="Awake Duration",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="minutes",
        target_value=5.0,
        aggregation="awake_duration",
        color="#ef4444",
        lower_is_better=True,
    ),
    "longest_awake_duration": MetricDefinition(
        key="longest_awake_duration",
        name="Longest Awake Duration",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="minutes",
        target_value=5.0,
        aggregation="longest_awake_duration",
        color="#dc2626",
        lower_is_better=True,
    ),
    "first_morning_awake_time": MetricDefinition(
        key="first_morning_awake_time",
        name="First Morning Awake Time",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="hours",
        target_value=31.0,
        aggregation="first_morning_awake_time",
        color="#06b6d4",
        lower_is_better=False,
    ),
}

RECORD_TYPE_TO_METRICS: dict[str, list[MetricDefinition]] = {}
for metric in METRIC_DEFINITIONS.values():
    RECORD_TYPE_TO_METRICS.setdefault(metric.record_type, []).append(metric)
ASLEEP_PREFIX = "HKCategoryValueSleepAnalysisAsleep"
STOOD_VALUE = "HKCategoryValueAppleStandHourStood"


def parse_apple_datetime(value: str) -> datetime:
    """Parse Apple Health timestamps while preserving the embedded offset."""
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S %z")


def target_month_bounds(year: int, month: int) -> tuple[datetime, datetime]:
    """Return inclusive/exclusive naive date bounds for target month comparisons."""
    start = datetime.combine(date(year, month, 1), time.min)
    if month == 12:
        end = datetime.combine(date(year + 1, 1, 1), time.min)
    else:
        end = datetime.combine(date(year, month + 1, 1), time.min)
    return start, end


def month_dates(year: int, month: int) -> list[date]:
    """Return all local dates in a target month."""
    _, days = calendar.monthrange(year, month)
    return [date(year, month, day) for day in range(1, days + 1)]


def overlaps_target_month(start: datetime, end: datetime, year: int, month: int) -> bool:
    """Return whether a record interval overlaps the target month in local date terms."""
    month_start, month_end = target_month_bounds(year, month)
    local_start = start.replace(tzinfo=None)
    local_end = end.replace(tzinfo=None)
    return local_start < month_end and local_end > month_start


def parse_health_records(xml_path: Path, target_year: int, target_month: int) -> list[HealthRecord]:
    """Stream Apple Health XML and return relevant records overlapping the target month."""
    records: list[HealthRecord] = []
    try:
        context = ElementTree.iterparse(xml_path, events=("end",))
        for _, elem in context:
            if elem.tag != "Record":
                elem.clear()
                continue

            record_type = elem.attrib.get("type")
            metrics = RECORD_TYPE_TO_METRICS.get(record_type or "")
            if not metrics:
                elem.clear()
                continue

            raw_value = elem.attrib.get("value")
            start = parse_apple_datetime(elem.attrib["startDate"])
            end = parse_apple_datetime(elem.attrib["endDate"])

            for metric in metrics:
                if metric.key in ("sleep_duration", "sleep_onset", "wake_time") and not (
                    raw_value or ""
                ).startswith(ASLEEP_PREFIX):
                    continue
                if (
                    metric.key
                    in (
                        "awake_count",
                        "awake_duration",
                        "longest_awake_duration",
                        "first_morning_awake_time",
                    )
                    and raw_value != "HKCategoryValueSleepAnalysisAwake"
                ):
                    continue
                if metric.key == "stand_hours" and raw_value != STOOD_VALUE:
                    continue

                if metric.key in (
                    "sleep_onset",
                    "wake_time",
                    "awake_count",
                    "awake_duration",
                    "longest_awake_duration",
                    "first_morning_awake_time",
                ):
                    onset_start_bound = datetime(target_year, target_month, 1, 18, 0, 0)
                    if target_month == 12:
                        onset_end_bound = datetime(target_year + 1, 1, 1, 18, 0, 0)
                    else:
                        onset_end_bound = datetime(target_year, target_month + 1, 1, 18, 0, 0)

                    local_start = start.replace(tzinfo=None)
                    if not (onset_start_bound <= local_start < onset_end_bound):
                        continue
                else:
                    if not overlaps_target_month(start, end, target_year, target_month):
                        continue

                parsed_value: float | str | None
                if metric.aggregation == "sum":
                    parsed_value = float(raw_value or 0)
                else:
                    parsed_value = raw_value

                records.append(
                    HealthRecord(metric_key=metric.key, start=start, end=end, value=parsed_value)
                )
            elem.clear()
    except ElementTree.ParseError as exc:
        raise ValueError("Error: Failed to parse XML file. The file may be corrupted.") from exc
    return records


def split_duration_by_day(
    start: datetime, end: datetime, year: int, month: int
) -> dict[date, float]:
    """Split an interval into per-day hour durations clipped to the target month."""
    month_start, month_end = target_month_bounds(year, month)
    current = max(start.replace(tzinfo=None), month_start)
    clipped_end = min(end.replace(tzinfo=None), month_end)
    durations: dict[date, float] = {}
    while current < clipped_end:
        next_midnight = datetime.combine(current.date() + timedelta(days=1), time.min)
        segment_end = min(next_midnight, clipped_end)
        durations[current.date()] = (
            durations.get(current.date(), 0.0) + (segment_end - current).total_seconds() / 3600
        )
        current = segment_end
    return durations


def aggregate_daily_metrics(
    records: list[HealthRecord], target_year: int, target_month: int
) -> dict[str, pd.Series]:
    """Aggregate parsed health records into daily series with missing days as NA."""
    index = pd.Index(month_dates(target_year, target_month), name="date")
    results: dict[str, pd.Series] = {}

    # Pre-calculate sleep sessions and awake records grouped by bedtime date
    asleep_by_date: dict[date, list[tuple[datetime, datetime]]] = {}
    awake_by_date: dict[date, list[tuple[datetime, datetime]]] = {}

    for record in records:
        if record.metric_key == "sleep_onset":
            start_hour = record.start.hour
            if start_hour >= 18:
                bedtime_date = record.start.date()
            else:
                bedtime_date = record.start.date() - timedelta(days=1)
            if bedtime_date in index:
                asleep_by_date.setdefault(bedtime_date, []).append((record.start, record.end))
        elif record.metric_key == "awake_count":
            start_hour = record.start.hour
            if start_hour >= 18:
                bedtime_date = record.start.date()
            else:
                bedtime_date = record.start.date() - timedelta(days=1)
            if bedtime_date in index:
                awake_by_date.setdefault(bedtime_date, []).append((record.start, record.end))

    # Determine sleep session boundaries [session_start, session_end] per day D
    session_bounds: dict[date, tuple[datetime, datetime]] = {}
    for day, intervals in asleep_by_date.items():
        if intervals:
            session_start = min(i[0] for i in intervals)
            session_end = max(i[1] for i in intervals)
            session_bounds[day] = (session_start, session_end)

    for metric in METRIC_DEFINITIONS.values():
        values: dict[date, float] = {}
        seen_dates: set[date] = set()
        stand_hours: dict[date, set[int]] = {}
        earliest_starts: dict[date, datetime] = {}

        if metric.aggregation == "wake_time":
            for day, bounds in session_bounds.items():
                session_end = bounds[1]
                val = session_end.hour + session_end.minute / 60.0 + session_end.second / 3600.0
                if session_end.hour < 18:
                    val += 24.0
                values[day] = val
                seen_dates.add(day)

        elif metric.aggregation == "awake_count":
            for day, bounds in session_bounds.items():
                session_start, session_end = bounds
                day_awakes = awake_by_date.get(day, [])
                overlap_count = 0
                for start_dt, end_dt in day_awakes:
                    if start_dt < session_end and end_dt > session_start:
                        overlap_count += 1
                values[day] = float(overlap_count)
                seen_dates.add(day)

        elif metric.aggregation == "awake_duration":
            for day, bounds in session_bounds.items():
                session_start, session_end = bounds
                day_awakes = awake_by_date.get(day, [])
                total_duration = 0.0
                for start_dt, end_dt in day_awakes:
                    if start_dt < session_end and end_dt > session_start:
                        overlap_start = max(start_dt, session_start)
                        overlap_end = min(end_dt, session_end)
                        duration = (overlap_end - overlap_start).total_seconds() / 60.0
                        total_duration += duration
                values[day] = total_duration
                seen_dates.add(day)

        elif metric.aggregation == "longest_awake_duration":
            for day, bounds in session_bounds.items():
                session_start, session_end = bounds
                day_awakes = awake_by_date.get(day, [])
                max_duration = 0.0
                for start_dt, end_dt in day_awakes:
                    if start_dt < session_end and end_dt > session_start:
                        overlap_start = max(start_dt, session_start)
                        overlap_end = min(end_dt, session_end)
                        duration = (overlap_end - overlap_start).total_seconds() / 60.0
                        if duration > max_duration:
                            max_duration = duration
                values[day] = max_duration
                seen_dates.add(day)

        elif metric.aggregation == "first_morning_awake_time":
            for day, bounds in session_bounds.items():
                session_start, session_end = bounds
                day_awakes = awake_by_date.get(day, [])
                next_day = day + timedelta(days=1)
                morning_start = datetime.combine(next_day, time(5, 0))
                morning_end = datetime.combine(next_day, time(12, 0))

                earliest_awake_start = None
                for start_dt, end_dt in day_awakes:
                    if start_dt < session_end and end_dt > session_start:
                        local_start = start_dt.replace(tzinfo=None)
                        if morning_start <= local_start < morning_end:
                            if earliest_awake_start is None or start_dt < earliest_awake_start:
                                earliest_awake_start = start_dt

                if earliest_awake_start is not None:
                    val = (
                        earliest_awake_start.hour
                        + earliest_awake_start.minute / 60.0
                        + earliest_awake_start.second / 3600.0
                    )
                    if earliest_awake_start.hour < 18:
                        val += 24.0
                    values[day] = val
                    seen_dates.add(day)

        else:
            for record in records:
                if record.metric_key != metric.key:
                    continue
                if metric.aggregation == "duration_hours":
                    for day, hours in split_duration_by_day(
                        record.start, record.end, target_year, target_month
                    ).items():
                        values[day] = values.get(day, 0.0) + hours
                        seen_dates.add(day)
                elif metric.aggregation == "unique_hours":
                    local_day = record.start.date()
                    if local_day in index:
                        stand_hours.setdefault(local_day, set()).add(record.start.hour)
                        seen_dates.add(local_day)
                elif metric.aggregation == "sleep_onset":
                    start_hour = record.start.hour
                    if start_hour >= 18:
                        bedtime_date = record.start.date()
                    else:
                        bedtime_date = record.start.date() - timedelta(days=1)

                    if bedtime_date in index:
                        existing_start = earliest_starts.get(bedtime_date)
                        if existing_start is None or record.start < existing_start:
                            earliest_starts[bedtime_date] = record.start
                            seen_dates.add(bedtime_date)
                else:
                    local_day = record.start.date()
                    if local_day in index:
                        values[local_day] = values.get(local_day, 0.0) + float(record.value or 0)
                        seen_dates.add(local_day)

            if metric.aggregation == "unique_hours":
                values = {day: float(len(hours)) for day, hours in stand_hours.items()}
            elif metric.aggregation == "sleep_onset":
                values = {}
                for day, start_dt in earliest_starts.items():
                    val = start_dt.hour + start_dt.minute / 60.0
                    if start_dt.hour < 18:
                        val += 24.0
                    values[day] = val

        series = pd.Series(pd.NA, index=index, dtype="Float64")
        for day in seen_dates:
            series.loc[day] = values.get(day, 0.0)
        results[metric.key] = series

    return results


def calculate_stats(
    series: pd.Series, target_value: float, lower_is_better: bool = False
) -> MetricStats:
    """Calculate statistics while excluding missing days."""
    valid = series.dropna().astype(float)
    if valid.empty:
        return MetricStats(None, None, None, 0, 0, int(series.isna().sum()), None)
    if lower_is_better:
        achieved_days = int((valid <= target_value).sum())
    else:
        achieved_days = int((valid >= target_value).sum())
    valid_days = int(valid.count())
    return MetricStats(
        average=float(valid.mean()),
        maximum=float(valid.max()),
        minimum=float(valid.min()),
        achieved_days=achieved_days,
        valid_days=valid_days,
        missing_days=int(series.isna().sum()),
        achievement_rate=achieved_days / valid_days * 100,
    )


def format_to_time_str(val: float | None) -> str:
    """Convert decimal hours (e.g. 25.25) to HH:MM format (e.g. '01:15')."""
    if val is None or pd.isna(val):
        return "N/A"
    total_minutes = int(round(val * 60))
    hours = (total_minutes // 60) % 24
    minutes = total_minutes % 60
    return f"{hours:02d}:{minutes:02d}"


def format_float(value: float | None) -> str:
    """Format an optional float for prompts and templates."""
    return "N/A" if value is None else f"{value:.1f}"


def build_stats_summary(stats: MetricStats, metric: MetricDefinition) -> list[StatSummaryItem]:
    """Build display-ready monthly statistics."""
    if metric.key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
        return [
            StatSummaryItem("Average", format_to_time_str(stats.average), ""),
            StatSummaryItem("Latest", format_to_time_str(stats.maximum), ""),
            StatSummaryItem("Earliest", format_to_time_str(stats.minimum), ""),
            StatSummaryItem("Goal Achieved Rate", format_float(stats.achievement_rate), "%"),
        ]
    else:
        return [
            StatSummaryItem("Average", format_float(stats.average), metric.unit),
            StatSummaryItem("Maximum", format_float(stats.maximum), metric.unit),
            StatSummaryItem("Minimum", format_float(stats.minimum), metric.unit),
            StatSummaryItem("Goal Achieved Rate", format_float(stats.achievement_rate), "%"),
        ]


def generate_chart(
    metric: MetricDefinition,
    series: pd.Series,
    target_year: int,
    target_month: int,
) -> str:
    """Generate a daily line chart SVG for one metric."""
    labels = [f"{day:%m/%d}" for day in series.index]
    values = [None if pd.isna(value) else float(value) for value in series]

    fig, ax = plt.subplots(figsize=(16.0, 5.8), dpi=150)
    fig.patch.set_facecolor("none")
    ax.set_facecolor("none")
    x_positions = list(range(len(labels)))

    valid_x = [x for x, value in zip(x_positions, values, strict=True) if value is not None]
    valid_values = [value for value in values if value is not None]

    ax.axhline(metric.target_value, color="#ef4444", linestyle="--", linewidth=1.8, alpha=0.82)

    if metric.key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
        ax.set_ylabel("Time", color="#475569", fontsize=16)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: format_to_time_str(x)))
        target_label = f" Target {format_to_time_str(metric.target_value)}"

        # Set Y-axis range dynamically focusing on values and target_value
        valid_vals = [v for v in values if v is not None]
        all_vals = valid_vals + [metric.target_value]
        ymin = min(all_vals) - 0.5
        ymax = max(all_vals) + 0.5
        if ymax - ymin < 4.0:
            center = (ymin + ymax) / 2.0
            ymin = center - 2.0
            ymax = center + 2.0
        ax.set_ylim(ymin, ymax)
        fill_bottom = ymin
    else:
        ax.set_ylabel(metric.unit, color="#475569", fontsize=16)
        target_label = f" Target {metric.target_value:g} {metric.unit}"
        fill_bottom = 0

    if valid_x:
        ax.plot(
            valid_x,
            valid_values,
            color=metric.color,
            linewidth=3.0,
            marker="o",
            markersize=8,
            markeredgecolor="white",
            markeredgewidth=1.5,
        )
        ax.fill_between(
            valid_x,
            valid_values,
            y2=fill_bottom,
            color=metric.color,
            alpha=0.15,
        )

    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", color="#475569", fontsize=12)
    ax.tick_params(axis="x", labelsize=12)
    ax.tick_params(axis="y", colors="#475569", labelsize=13)
    ax.grid(axis="y", color="#e2e8f0", alpha=0.7)
    for spine_name, spine in ax.spines.items():
        if spine_name in ["top", "right"]:
            spine.set_visible(False)
        else:
            spine.set_color("#cbd5e1")
    ax.text(
        0.995,
        metric.target_value,
        target_label,
        transform=ax.get_yaxis_transform(),
        color="#ef4444",
        ha="right",
        va="bottom",
        fontsize=13,
        fontweight="bold",
    )
    fig.tight_layout()
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    return buf.getvalue()


HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Apple Watch Health Monthly Report {{ year }}-{{ month }}</title>
  <style>
    html {
      scroll-snap-type: y mandatory;
      scroll-behavior: smooth;
    }
    body {
      margin: 0;
      background: #f8fafc;
      color: #0f172a;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      overflow-x: hidden;
    }
    .slide-wrapper {
      width: 100vw;
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      scroll-snap-align: start;
      box-sizing: border-box;
    }
    .slide {
      box-sizing: border-box;
      width: 1920px;
      height: 1080px;
      padding: 48px 64px;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      gap: 28px;
      border: 1px solid #e2e8f0;
      border-radius: 16px;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.08);
      transform-origin: center center;
      flex-shrink: 0;
    }
    .header {
      display: flex;
      align-items: flex-end;
      justify-content: space-between;
      border-bottom: 2px solid #f1f5f9;
      padding-bottom: 18px;
    }
    h1 {
      margin: 0;
      font-size: 64px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #0f172a;
    }
    .month {
      color: #64748b;
      font-size: 32px;
      font-weight: 600;
    }
    .content {
      display: flex;
      flex-direction: column;
      gap: 28px;
      min-height: 0;
      flex-grow: 1;
      justify-content: space-between;
    }
    .chart {
      width: 100%;
      background: none;
    }
    .chart svg {
      display: block;
      width: 100%;
      height: auto;
    }
    .stats-panel {
      display: grid;
      grid-template-columns: 300px 1fr;
      column-gap: 48px;
      row-gap: 12px;
      border-top: 2px solid #f1f5f9;
      padding-top: 24px;
    }
    .label {
      grid-column: 1;
      grid-row: 1;
      color: #0284c7;
      font-size: 26px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .stats-grid {
      grid-column: 2;
      grid-row: 1 / span 2;
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 18px;
      align-self: stretch;
    }
    .stat-card {
      min-width: 0;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #f8fafc;
      padding: 22px 24px;
    }
    .stat-label {
      color: #64748b;
      font-size: 20px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      margin-bottom: 12px;
    }
    .stat-value {
      color: #0f172a;
      font-size: 42px;
      font-weight: 800;
      line-height: 1.1;
      overflow-wrap: anywhere;
    }
    .stat-unit {
      color: #475569;
      font-size: 22px;
      font-weight: 600;
      margin-left: 6px;
    }
    .goal {
      grid-column: 1;
      grid-row: 2;
      color: #64748b;
      font-size: 22px;
      font-weight: 500;
      margin-top: 8px;
    }
  </style>
</head>
<body>
{% for slide in slides %}
  <div class="slide-wrapper">
    <section class="slide">
      <div class="header">
        <h1>{{ slide.name }}</h1>
        <div class="month">{{ year }}-{{ month }}</div>
      </div>
      <div class="content">
        <div class="chart">
          {{ slide.chart_svg | safe }}
        </div>
        <aside class="stats-panel">
          <div class="label">Monthly Stats</div>
          <div class="stats-grid">
            {% for item in slide.stats_summary %}
            <div class="stat-card">
              <div class="stat-label">{{ item.label }}</div>
              <div class="stat-value">
                {{ item.value }}
                {% if item.unit %}
                <span class="stat-unit">{{ item.unit }}</span>
                {% endif %}
              </div>
            </div>
            {% endfor %}
          </div>
          <div class="goal">{{ slide.goal_text }}</div>
        </aside>
      </div>
    </section>
  </div>
{% endfor %}

<script>
  function scaleSlides() {
    const targetWidth = 1920;
    const targetHeight = 1080;
    const slides = document.querySelectorAll('.slide');
    const winW = window.innerWidth;
    const winH = window.innerHeight;
    
    // Scale fitting calculation with small padding
    const scaleX = (winW - 40) / targetWidth;
    const scaleY = (winH - 40) / targetHeight;
    const scale = Math.min(scaleX, scaleY);
    
    slides.forEach(slide => {
      slide.style.transform = 'scale(' + scale + ')';
    });
  }

  window.addEventListener('resize', scaleSlides);
  window.addEventListener('DOMContentLoaded', scaleSlides);
  window.addEventListener('load', scaleSlides);

  // Navigation Logic
  let currentSlideIndex = 0;
  const wrappers = document.querySelectorAll('.slide-wrapper');
  
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {
      e.preventDefault();
      if (currentSlideIndex < wrappers.length - 1) {
        currentSlideIndex++;
        wrappers[currentSlideIndex].scrollIntoView({ behavior: 'smooth' });
      }
    } else if (e.key === 'ArrowUp' || e.key === 'ArrowLeft' || e.key === 'PageUp') {
      e.preventDefault();
      if (currentSlideIndex > 0) {
        currentSlideIndex--;
        wrappers[currentSlideIndex].scrollIntoView({ behavior: 'smooth' });
      }
    } else if (e.key === 'Home') {
      e.preventDefault();
      currentSlideIndex = 0;
      wrappers[currentSlideIndex].scrollIntoView({ behavior: 'smooth' });
    } else if (e.key === 'End') {
      e.preventDefault();
      currentSlideIndex = wrappers.length - 1;
      wrappers[currentSlideIndex].scrollIntoView({ behavior: 'smooth' });
    }
  });

  // Sync scroll positions
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.5
  };
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const index = Array.from(wrappers).indexOf(entry.target);
        if (index !== -1) {
          currentSlideIndex = index;
        }
      }
    });
  }, observerOptions);
  wrappers.forEach(w => observer.observe(w));
</script>
</body>
</html>"""
)


def render_html_report(
    slides: list[dict[str, Any]], output_path: Path, year: int, month: int
) -> Path:
    """Render the final five-slide HTML report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    safe_slides = []
    for slide in slides:
        stats_summary = [
            {
                "label": html.escape(str(item["label"])),
                "value": html.escape(str(item["value"])),
                "unit": html.escape(str(item["unit"])),
            }
            for item in slide["stats_summary"]
        ]
        safe_slides.append(
            {
                **slide,
                "stats_summary": stats_summary,
            }
        )
    output_path.write_text(
        HTML_TEMPLATE.render(slides=safe_slides, year=year, month=f"{month:02d}"),
        encoding="utf-8",
    )
    return output_path


def load_daily_metrics_from_csv(
    csv_path: Path,
    target_year: int,
    target_month: int,
) -> dict[str, pd.Series]:
    """Load daily metrics from a CSV file, restoring the pandas Series for each metric.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If a required column is missing, dates are outside target month,
                    or dates for target month are missing.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Error: CSV file not found: {csv_path}")

    # Read CSV, parsing missing values represented as 'NA'
    dtypes = {
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
    }
    df = pd.read_csv(csv_path, dtype=dtypes, keep_default_na=False, na_values=["NA"])

    # Validate columns
    required_cols = [
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
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Error: Missing required column in CSV: {col}")

    # Parse and validate dates
    try:
        df["date"] = pd.to_datetime(df["date"]).dt.date
    except Exception as exc:
        raise ValueError("Error: Failed to parse dates in CSV.") from exc

    df.set_index("date", inplace=True)

    expected_dates = set(month_dates(target_year, target_month))
    actual_dates = set(df.index)

    outside_dates = actual_dates - expected_dates
    if outside_dates:
        raise ValueError(f"Error: CSV contains dates outside target month: {outside_dates}")

    missing_dates = expected_dates - actual_dates
    if missing_dates:
        raise ValueError(f"Error: CSV is missing dates for the target month: {missing_dates}")

    # Ensure correct sorting and index type (reindexing to list[date])
    df = df.reindex(month_dates(target_year, target_month))

    results = {}
    for col in [
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
    ]:
        results[col] = df[col]
    return results


def validate_inputs(xml_path: Path, api_key: str | None = None) -> None:
    """Validate required runtime inputs."""
    if not xml_path.exists():
        raise FileNotFoundError(
            "Error: export.xml not found. Please place the exported XML file "
            "in the project root directory."
        )


def generate_report(
    csv_path: Path,
    target_year: int,
    target_month: int,
    output_dir: Path,
    api_key: str | None = None,
    model: str | None = None,
) -> Path:
    """Run the full report generation workflow."""
    daily_series = load_daily_metrics_from_csv(csv_path, target_year, target_month)
    slides: list[dict[str, Any]] = []

    for metric in METRIC_DEFINITIONS.values():
        series = daily_series[metric.key]
        stats = calculate_stats(series, metric.target_value, lower_is_better=metric.lower_is_better)
        raw_svg = generate_chart(metric, series, target_year, target_month)
        prefixed_svg = clean_and_prefix_svg(raw_svg, metric.key)

        if metric.key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
            if metric.lower_is_better:
                goal_text = f"Goal: {format_to_time_str(metric.target_value)} or earlier"
            else:
                goal_text = f"Goal: {format_to_time_str(metric.target_value)} or later"
        else:
            if metric.lower_is_better:
                goal_text = f"Goal: {metric.target_value:g} {metric.unit} or less"
            else:
                goal_text = f"Goal: {metric.target_value:g} {metric.unit} or more"

        slides.append(
            {
                "name": metric.name,
                "chart_svg": prefixed_svg,
                "stats_summary": [item.__dict__ for item in build_stats_summary(stats, metric)],
                "target_value": f"{metric.target_value:g}",
                "unit": metric.unit,
                "goal_text": goal_text,
            }
        )

    html_path = (
        output_dir / f"apple_watch_health_daily_report_{target_year}_{target_month:02d}.html"
    )
    return render_html_report(slides, html_path, target_year, target_month)
