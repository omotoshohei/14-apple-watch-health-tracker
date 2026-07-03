from __future__ import annotations

# ruff: noqa: E501
import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Template
from matplotlib.ticker import FuncFormatter

from .preprocess import DAILY_METRIC_COLUMNS
from .report import (
    METRIC_DEFINITIONS,
    calculate_stats,
    clean_and_prefix_svg,
    format_float,
    format_to_time_str,
)

WEEKLY_COLUMNS = [
    "week",
    "week_start",
    "week_end",
    "metric",
    "metric_name",
    "unit",
    "target_value",
    "lower_is_better",
    "average",
    "maximum",
    "minimum",
    "achieved_days",
    "valid_days",
    "missing_days",
    "achievement_rate",
]

WEEKLY_REQUIRED_COLUMNS = [
    "week",
    "week_start",
    "week_end",
    "metric",
    "average",
    "maximum",
    "minimum",
    "achievement_rate",
    "achieved_days",
    "valid_days",
]

TIME_METRICS = {"sleep_onset", "wake_time", "first_morning_awake_time"}
WEEKLY_REPORT_MAX_WEEKS = 10


def load_daily_metrics_for_weekly(csv_path: Path) -> pd.DataFrame:
    """Load and validate merged daily metric CSV data."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Error: CSV file not found: {csv_path}")

    dtypes = {col: "Float64" for col in DAILY_METRIC_COLUMNS}
    df = pd.read_csv(csv_path, dtype=dtypes, keep_default_na=False, na_values=["NA"])

    required_cols = ["date", *DAILY_METRIC_COLUMNS]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Error: Missing required column in CSV: {missing_cols[0]}")

    try:
        df["date"] = pd.to_datetime(df["date"]).dt.normalize()
    except Exception as exc:
        raise ValueError("Error: Failed to parse dates in CSV.") from exc

    return df.sort_values("date").drop_duplicates(subset=["date"], keep="last")


def _complete_monday_weeks(df: pd.DataFrame) -> list[pd.Timestamp]:
    min_date = df["date"].min()
    max_date = df["date"].max()
    first_monday = min_date + pd.Timedelta(days=(7 - min_date.weekday()) % 7)
    last_monday = max_date - pd.Timedelta(days=max_date.weekday())
    if last_monday + pd.Timedelta(days=6) > max_date:
        last_monday -= pd.Timedelta(days=7)

    if first_monday > last_monday:
        raise ValueError("Error: complete Monday-start weeks are not found in daily CSV.")

    return list(pd.date_range(first_monday, last_monday, freq="W-MON"))


def aggregate_daily_csv_to_weekly_csv(input_csv_path: Path, output_csv_path: Path) -> Path:
    """Aggregate a day-by-day health metrics CSV into Monday-start weekly statistics."""
    df = load_daily_metrics_for_weekly(input_csv_path)
    week_starts = _complete_monday_weeks(df)

    rows: list[dict[str, object]] = []
    daily_by_date = df.set_index("date")
    for week_start in week_starts:
        week_end = week_start + pd.Timedelta(days=6)
        week_dates = pd.date_range(week_start, week_end, freq="D")
        week_df = daily_by_date.reindex(week_dates)
        iso = week_start.isocalendar()
        week_label = f"{iso.year}-W{iso.week:02d}"

        for metric in METRIC_DEFINITIONS.values():
            stats = calculate_stats(
                week_df[metric.key],
                metric.target_value,
                lower_is_better=metric.lower_is_better,
            )
            rows.append(
                {
                    "week": week_label,
                    "week_start": week_start.date().isoformat(),
                    "week_end": week_end.date().isoformat(),
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
    pd.DataFrame(rows, columns=WEEKLY_COLUMNS).to_csv(output_csv_path, index=False, na_rep="NA")
    return output_csv_path


def load_weekly_trend_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate weekly trend data from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Error: Weekly metrics CSV file not found: {csv_path}")

    dtypes = {
        "week": "str",
        "week_start": "str",
        "week_end": "str",
        "metric": "str",
        "metric_name": "str",
        "unit": "str",
        "target_value": "Float64",
        "lower_is_better": "boolean",
        "average": "Float64",
        "maximum": "Float64",
        "minimum": "Float64",
        "achieved_days": "Int64",
        "valid_days": "Int64",
        "missing_days": "Int64",
        "achievement_rate": "Float64",
    }
    df = pd.read_csv(csv_path, dtype=dtypes, keep_default_na=False, na_values=["NA"])
    missing_cols = [col for col in WEEKLY_REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Error: Missing required column in weekly CSV: {missing_cols[0]}")

    try:
        df["week_start"] = pd.to_datetime(df["week_start"]).dt.normalize()
        df["week_end"] = pd.to_datetime(df["week_end"]).dt.normalize()
    except Exception as exc:
        raise ValueError("Error: Failed to parse week_start or week_end in weekly CSV.") from exc

    if df.empty:
        raise ValueError("Error: complete Monday-start weeks are not found in weekly CSV.")

    return df.sort_values(["week_start", "metric"])


def _empty_weekly_chart(metric_key: str, weeks: list[str]) -> str:
    metric = METRIC_DEFINITIONS[metric_key]
    fig, ax = plt.subplots(figsize=(10.0, 5.8), dpi=150)
    fig.patch.set_facecolor("none")
    ax.set_facecolor("none")
    ax.set_xticks(list(range(len(weeks))))
    ax.set_xticklabels(weeks, rotation=35, ha="right", color="#475569", fontsize=10)
    ax.tick_params(axis="y", colors="#475569", labelsize=12)
    ax.grid(axis="y", color="#cbd5e1", alpha=0.7, linestyle=":")
    ax.text(
        0.5,
        0.5,
        "No weekly data",
        transform=ax.transAxes,
        ha="center",
        va="center",
        color="#64748b",
        fontsize=18,
    )
    for spine_name, spine in ax.spines.items():
        spine.set_visible(spine_name not in ["top", "right"])
        spine.set_color("#cbd5e1")
    if metric.key in TIME_METRICS:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: format_to_time_str(x)))
    fig.tight_layout()
    buf = io.StringIO()
    fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
    plt.close(fig)
    return clean_and_prefix_svg(buf.getvalue(), f"weekly_{metric_key}")


def generate_weekly_trend_charts(df: pd.DataFrame) -> dict[str, str]:
    """Generate inline SVG weekly trend line charts for all metrics."""
    charts: dict[str, str] = {}
    weeks_df = df[["week", "week_start"]].drop_duplicates().sort_values("week_start")
    weeks = weeks_df["week"].tolist()

    for metric_key, metric in METRIC_DEFINITIONS.items():
        metric_df = df[df["metric"] == metric_key]
        if metric_df.empty:
            charts[metric.key] = _empty_weekly_chart(metric_key, weeks)
            continue

        series_data = []
        for week in weeks:
            row = metric_df[metric_df["week"] == week]
            if not row.empty and not pd.isna(row.iloc[0]["average"]):
                series_data.append((week, float(row.iloc[0]["average"])))
            else:
                series_data.append((week, None))

        fig, ax = plt.subplots(figsize=(10.0, 5.8), dpi=150)
        fig.patch.set_facecolor("none")
        ax.set_facecolor("none")
        x_positions = list(range(len(weeks)))
        values = [val for _, val in series_data]

        ax.axhline(metric.target_value, color="#f43f5e", linestyle="--", linewidth=2.0, alpha=0.85)

        if metric.key in TIME_METRICS:
            ax.set_ylabel("Time", color="#475569", fontsize=14)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: format_to_time_str(x)))
            target_label = f" Target {format_to_time_str(metric.target_value)}"
            valid_values = [val for val in values if val is not None]
            if valid_values:
                all_vals = valid_values + [metric.target_value]
                ymin = min(all_vals) - 0.5
                ymax = max(all_vals) + 0.5
                if ymax - ymin < 4.0:
                    center = (ymin + ymax) / 2.0
                    ymin = center - 2.0
                    ymax = center + 2.0
                ax.set_ylim(ymin, ymax)
        else:
            ax.set_ylabel(metric.unit, color="#475569", fontsize=14)
            target_label = f" Target {metric.target_value:g} {metric.unit}"
            valid_values = [val for val in values if val is not None]
            if valid_values:
                ymax = max(valid_values + [metric.target_value]) * 1.15
                ax.set_ylim(0, ymax)

        segment_x: list[int] = []
        segment_y: list[float] = []
        for x, value in zip(x_positions, values, strict=True):
            if value is None:
                if segment_x:
                    ax.plot(
                        segment_x,
                        segment_y,
                        color=metric.color,
                        linewidth=3.5,
                        marker="o",
                        markersize=9,
                        markeredgecolor="#ffffff",
                        markeredgewidth=2.0,
                    )
                    segment_x, segment_y = [], []
            else:
                segment_x.append(x)
                segment_y.append(value)
        if segment_x:
            ax.plot(
                segment_x,
                segment_y,
                color=metric.color,
                linewidth=3.5,
                marker="o",
                markersize=9,
                markeredgecolor="#ffffff",
                markeredgewidth=2.0,
            )

        ax.set_xticks(x_positions)
        ax.set_xticklabels(weeks, rotation=35, ha="right", color="#475569", fontsize=10)
        ax.tick_params(axis="x", colors="#475569", labelsize=10)
        ax.tick_params(axis="y", colors="#475569", labelsize=12)
        ax.grid(axis="y", color="#cbd5e1", alpha=0.7, linestyle=":")
        for spine_name, spine in ax.spines.items():
            spine.set_visible(spine_name not in ["top", "right"])
            spine.set_color("#cbd5e1")
        ax.text(
            0.99,
            metric.target_value,
            target_label,
            transform=ax.get_yaxis_transform(),
            color="#f43f5e",
            ha="right",
            va="bottom",
            fontsize=12,
            fontweight="bold",
        )
        fig.tight_layout()
        buf = io.StringIO()
        fig.savefig(buf, format="svg", bbox_inches="tight", transparent=True)
        plt.close(fig)
        charts[metric.key] = clean_and_prefix_svg(buf.getvalue(), f"weekly_{metric.key}")

    return charts


HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Apple Watch Health Weekly Report</title>
  <style>
    html { scroll-snap-type: y mandatory; scroll-behavior: smooth; }
    body { margin: 0; background: #f8fafc; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; overflow-x: hidden; }
    .slide-wrapper { width: 100vw; height: 100vh; display: flex; align-items: center; justify-content: center; overflow: hidden; scroll-snap-align: start; box-sizing: border-box; }
    .slide { box-sizing: border-box; width: 1920px; height: 1080px; padding: 48px 64px; background: #ffffff; display: flex; flex-direction: column; gap: 28px; border: 1px solid #e2e8f0; border-radius: 16px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.08); transform-origin: center center; flex-shrink: 0; }
    .header { display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 2px solid #f1f5f9; padding-bottom: 18px; }
    h1 { margin: 0; font-size: 54px; font-weight: 800; color: #0f172a; }
    .period { color: #64748b; font-size: 28px; font-weight: 600; }
    .content { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 48px; min-height: 0; flex-grow: 1; }
    .chart-container { display: flex; align-items: center; justify-content: center; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 24px; min-height: 0; }
    .chart, .chart svg { display: block; width: 100%; height: auto; background: none; }
    .data-panel { display: flex; flex-direction: column; gap: 24px; min-height: 0; }
    .table-container { flex-grow: 1; overflow-y: auto; border: 1px solid #e2e8f0; border-radius: 8px; background: #ffffff; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 17px; text-align: left; color: #0f172a; }
    .data-table th, .data-table td { padding: 14px 16px; border-bottom: 1px solid #e2e8f0; }
    .data-table th { background: #f8fafc; color: #64748b; font-weight: 700; text-transform: uppercase; font-size: 14px; position: sticky; top: 0; }
    .empty-row { color: #64748b; text-align: center; }
    .goal-card { background: #f8fafc; border: 1px solid #e2e8f0; border-left: 5px solid #38bdf8; padding: 20px 24px; border-radius: 0 8px 8px 0; font-size: 20px; font-weight: 500; color: #475569; display: flex; justify-content: space-between; align-items: center; }
    .goal-value { font-weight: 700; color: #38bdf8; }
  </style>
</head>
<body>
{% for slide in slides %}
  <div class="slide-wrapper">
    <section class="slide">
      <div class="header">
        <h1>{{ slide.name }} Weekly Trend</h1>
        <div class="period">{{ period }}</div>
      </div>
      <div class="content">
        <div class="chart-container"><div class="chart">{{ slide.chart_svg | safe }}</div></div>
        <div class="data-panel">
          <div class="table-container">
            <table class="data-table">
              <thead><tr><th>Week</th><th>Average</th><th>Max / Min</th><th>Achievement</th></tr></thead>
              <tbody>
              {% if slide.table_rows %}
                {% for row in slide.table_rows %}
                <tr><td><strong>{{ row.week }}</strong><br>{{ row.range }}</td><td>{{ row.average }}</td><td>{{ row.max_min }}</td><td>{{ row.achievement }}</td></tr>
                {% endfor %}
              {% else %}
                <tr><td colspan="4" class="empty-row">No weekly data</td></tr>
              {% endif %}
              </tbody>
            </table>
          </div>
          <div class="goal-card" style="border-left-color: {{ slide.color }}"><span>Target Goal:</span><span class="goal-value" style="color: {{ slide.color }}">{{ slide.goal_text }}</span></div>
        </div>
      </div>
    </section>
  </div>
{% endfor %}
<script>
  function scaleSlides(){const tw=1920,th=1080;const scale=Math.min((window.innerWidth-40)/tw,(window.innerHeight-40)/th);document.querySelectorAll('.slide').forEach(s=>{s.style.transform='scale('+scale+')';});}
  window.addEventListener('resize',scaleSlides);window.addEventListener('DOMContentLoaded',scaleSlides);window.addEventListener('load',scaleSlides);
  let currentSlideIndex=0;const wrappers=document.querySelectorAll('.slide-wrapper');
  document.addEventListener('keydown',(e)=>{if(['ArrowDown','ArrowRight','PageDown',' '].includes(e.key)){e.preventDefault();if(currentSlideIndex<wrappers.length-1){currentSlideIndex++;wrappers[currentSlideIndex].scrollIntoView({behavior:'smooth'});}}else if(['ArrowUp','ArrowLeft','PageUp'].includes(e.key)){e.preventDefault();if(currentSlideIndex>0){currentSlideIndex--;wrappers[currentSlideIndex].scrollIntoView({behavior:'smooth'});}}else if(e.key==='Home'){e.preventDefault();currentSlideIndex=0;wrappers[0].scrollIntoView({behavior:'smooth'});}else if(e.key==='End'){e.preventDefault();currentSlideIndex=wrappers.length-1;wrappers[currentSlideIndex].scrollIntoView({behavior:'smooth'});}});
</script>
</body>
</html>"""
)


def _format_metric_value(metric_key: str, value: object, unit: str = "") -> str:
    if metric_key in TIME_METRICS:
        return format_to_time_str(value)
    if pd.isna(value):
        return "-"
    unit_label = f" {unit}" if unit else ""
    return format_float(float(value)) + unit_label


def _limit_to_recent_weeks(
    df: pd.DataFrame, max_weeks: int = WEEKLY_REPORT_MAX_WEEKS
) -> pd.DataFrame:
    weeks = df[["week", "week_start"]].drop_duplicates().sort_values("week_start")
    recent_weeks = weeks.tail(max_weeks)["week"]
    return df[df["week"].isin(recent_weeks)].sort_values(["week_start", "metric"])


def generate_weekly_report(csv_path: Path, output_dir: Path) -> Path:
    """Generate the weekly trend report HTML using the aggregated weekly CSV."""
    df = _limit_to_recent_weeks(load_weekly_trend_data(csv_path))
    charts = generate_weekly_trend_charts(df)
    weeks = df[["week", "week_start", "week_end"]].drop_duplicates().sort_values("week_start")
    period = f"{weeks.iloc[0]['week_start'].date().isoformat()} ~ {weeks.iloc[-1]['week_end'].date().isoformat()}"

    slides = []
    for metric_key, metric in METRIC_DEFINITIONS.items():
        metric_df = df[df["metric"] == metric_key].sort_values("week_start")
        table_rows = []
        for _, row in metric_df.iterrows():
            max_val = _format_metric_value(metric_key, row["maximum"])
            min_val = _format_metric_value(metric_key, row["minimum"])
            ach_rate = row["achievement_rate"]
            ach_days = row["achieved_days"]
            valid_days = row["valid_days"]
            table_rows.append(
                {
                    "week": row["week"],
                    "range": f"{row['week_start'].date().isoformat()} - {row['week_end'].date().isoformat()}",
                    "average": _format_metric_value(metric_key, row["average"], metric.unit),
                    "max_min": "-"
                    if max_val == "-" and min_val == "-"
                    else f"{max_val} / {min_val}",
                    "achievement": f"{float(ach_rate):.1f}% ({int(ach_days)}/{int(valid_days)}d)"
                    if not pd.isna(ach_rate)
                    else "-",
                }
            )

        target = (
            format_to_time_str(metric.target_value)
            if metric_key in TIME_METRICS
            else f"{metric.target_value:g} {metric.unit}"
        )
        slides.append(
            {
                "key": metric_key,
                "name": metric.name,
                "color": metric.color,
                "chart_svg": charts.get(metric_key, ""),
                "table_rows": table_rows,
                "goal_text": f"{'<=' if metric.lower_is_better else '>='} {target}",
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)
    output_html_path = output_dir / "apple_watch_health_weekly_report.html"
    output_html_path.write_text(
        HTML_TEMPLATE.render(slides=slides, period=period), encoding="utf-8"
    )
    return output_html_path
