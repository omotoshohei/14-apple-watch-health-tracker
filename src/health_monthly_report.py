from __future__ import annotations

import argparse
import calendar
import html
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Template

DEFAULT_GEMINI_MODEL = "gemini-3.5-flash"
INSIGHT_FALLBACK = "No insight available for this metric due to API communication error."


@dataclass(frozen=True)
class MetricDefinition:
    key: str
    name: str
    record_type: str
    unit: str
    target_value: float
    aggregation: str
    color: str


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
    achieved_days: int
    valid_days: int
    missing_days: int
    achievement_rate: float | None


METRIC_DEFINITIONS: dict[str, MetricDefinition] = {
    "sleep_duration": MetricDefinition(
        key="sleep_duration",
        name="Sleep Duration",
        record_type="HKCategoryTypeIdentifierSleepAnalysis",
        unit="hours",
        target_value=7.0,
        aggregation="duration_hours",
        color="#38bdf8",
    ),
    "steps": MetricDefinition(
        key="steps",
        name="Steps",
        record_type="HKQuantityTypeIdentifierStepCount",
        unit="steps",
        target_value=8000.0,
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
}

RECORD_TYPE_TO_METRIC = {metric.record_type: metric for metric in METRIC_DEFINITIONS.values()}
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
            metric = RECORD_TYPE_TO_METRIC.get(record_type or "")
            if metric is None:
                elem.clear()
                continue

            raw_value = elem.attrib.get("value")
            if metric.key == "sleep_duration" and not (raw_value or "").startswith(ASLEEP_PREFIX):
                elem.clear()
                continue
            if metric.key == "stand_hours" and raw_value != STOOD_VALUE:
                elem.clear()
                continue

            start = parse_apple_datetime(elem.attrib["startDate"])
            end = parse_apple_datetime(elem.attrib["endDate"])
            if not overlaps_target_month(start, end, target_year, target_month):
                elem.clear()
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

    for metric in METRIC_DEFINITIONS.values():
        values: dict[date, float] = {}
        seen_dates: set[date] = set()
        stand_hours: dict[date, set[int]] = {}

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
            else:
                local_day = record.start.date()
                if local_day in index:
                    values[local_day] = values.get(local_day, 0.0) + float(record.value or 0)
                    seen_dates.add(local_day)

        if metric.aggregation == "unique_hours":
            values = {day: float(len(hours)) for day, hours in stand_hours.items()}

        series = pd.Series(pd.NA, index=index, dtype="Float64")
        for day in seen_dates:
            series.loc[day] = values.get(day, 0.0)
        results[metric.key] = series

    return results


def calculate_stats(series: pd.Series, target_value: float) -> MetricStats:
    """Calculate statistics while excluding missing days."""
    valid = series.dropna().astype(float)
    if valid.empty:
        return MetricStats(None, None, 0, 0, int(series.isna().sum()), None)
    achieved_days = int((valid >= target_value).sum())
    valid_days = int(valid.count())
    return MetricStats(
        average=float(valid.mean()),
        maximum=float(valid.max()),
        achieved_days=achieved_days,
        valid_days=valid_days,
        missing_days=int(series.isna().sum()),
        achievement_rate=achieved_days / valid_days * 100,
    )


def format_float(value: float | None) -> str:
    """Format an optional float for prompts and templates."""
    return "N/A" if value is None else f"{value:.1f}"


def daily_values_text(series: pd.Series) -> str:
    """Render daily values with missing days marked as N/A."""
    lines = []
    for day, value in series.items():
        rendered = "N/A" if pd.isna(value) else f"{float(value):.1f}"
        lines.append(f"{day:%Y-%m-%d}: {rendered}")
    return "\n".join(lines)


def build_insight_prompt(
    metric: MetricDefinition,
    series: pd.Series,
    stats: MetricStats,
    target_year: int,
    target_month: int,
) -> str:
    """Build the Gemini prompt for one metric."""
    average = format_float(stats.average)
    maximum = format_float(stats.maximum)
    achievement_rate = format_float(stats.achievement_rate)
    return f"""You are a health analysis assistant.
Analyze the following monthly health data for a user's Apple Watch metric: '{metric.name}'.

- Target Month: {target_year}-{target_month:02d}
- Target Value: {metric.target_value:g} {metric.unit} or more
- Average Value (excluding missing days): {average} {metric.unit}
- Maximum Value: {maximum} {metric.unit}
- Goal Achievement Rate: {achievement_rate}%
  ({stats.achieved_days} out of {stats.valid_days} active days)
- Missing Days (Watch not worn): {stats.missing_days} days

Daily Values (Missing days are marked as 'N/A'):
{daily_values_text(series)}

Instruction:
Please generate a concise summary comment in English (exactly 1 or 2 sentences).
The comment must describe the overall trend, target achievement status,
and one simple improvement point if needed.
Output only plain text with no markdown, greetings, or labels."""


def generate_chart(
    metric: MetricDefinition,
    series: pd.Series,
    output_dir: Path,
    target_year: int,
    target_month: int,
) -> Path:
    """Generate a daily bar chart PNG for one metric."""
    output_dir.mkdir(parents=True, exist_ok=True)
    image_path = output_dir / f"{metric.key}.png"
    labels = [f"{day:%m/%d}" for day in series.index]
    values = [None if pd.isna(value) else float(value) for value in series]

    fig, ax = plt.subplots(figsize=(13, 6.6), dpi=150)
    fig.patch.set_facecolor("none")
    ax.set_facecolor("none")
    x_positions = list(range(len(labels)))
    ax.bar(
        [x for x, value in zip(x_positions, values, strict=True) if value is not None],
        [value for value in values if value is not None],
        color=metric.color,
        width=0.72,
    )
    ax.axhline(metric.target_value, color="#ef4444", linestyle="--", linewidth=1.8, alpha=0.82)
    ax.set_title(f"{metric.name} - {target_year}-{target_month:02d}", color="#0f172a", pad=16)
    ax.set_ylabel(metric.unit, color="#475569")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels, rotation=45, ha="right", color="#475569", fontsize=8)
    ax.tick_params(axis="y", colors="#475569")
    ax.grid(axis="y", color="#e2e8f0", alpha=0.7)
    for spine_name, spine in ax.spines.items():
        if spine_name in ["top", "right"]:
            spine.set_visible(False)
        else:
            spine.set_color("#cbd5e1")
    ax.text(
        0.995,
        metric.target_value,
        f" Target {metric.target_value:g} {metric.unit}",
        transform=ax.get_yaxis_transform(),
        color="#ef4444",
        ha="right",
        va="bottom",
        fontsize=9,
    )
    fig.tight_layout()
    fig.savefig(image_path, transparent=True)
    plt.close(fig)
    return image_path


def get_gemini_insight(prompt: str, api_key: str, model: str = DEFAULT_GEMINI_MODEL) -> str:
    """Generate one English insight using Gemini."""
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model=model, contents=prompt)
    except Exception as exc:
        raise RuntimeError(INSIGHT_FALLBACK) from exc

    text = getattr(response, "text", "") or ""
    return text.strip() or INSIGHT_FALLBACK


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
      padding: 80px 100px;
      background: #ffffff;
      display: flex;
      flex-direction: column;
      gap: 36px;
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
      padding-bottom: 24px;
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
      gap: 36px;
      min-height: 0;
      flex-grow: 1;
      justify-content: space-between;
    }
    .chart {
      width: 100%;
      height: 520px;
      object-fit: contain;
      background: none;
    }
    .insight {
      display: grid;
      grid-template-columns: 280px 1fr;
      column-gap: 48px;
      row-gap: 12px;
      border-top: 2px solid #f1f5f9;
      padding-top: 32px;
    }
    .label {
      grid-column: 1;
      grid-row: 1;
      color: #0284c7;
      font-size: 24px;
      font-weight: 800;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .summary {
      grid-column: 2;
      grid-row: 1 / span 2;
      color: #334155;
      font-size: 32px;
      line-height: 1.5;
      align-self: center;
    }
    .goal {
      grid-column: 1;
      grid-row: 2;
      color: #64748b;
      font-size: 20px;
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
        <img class="chart" src="{{ slide.image_path }}" alt="{{ slide.name }} daily chart">
        <aside class="insight">
          <div class="label">Gemini Insight</div>
          <div class="summary">{{ slide.insight }}</div>
          <div class="goal">Goal: {{ slide.target_value }} {{ slide.unit }} or more</div>
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
        safe_slides.append(
            {
                **slide,
                "insight": html.escape(str(slide["insight"])),
            }
        )
    output_path.write_text(
        HTML_TEMPLATE.render(slides=safe_slides, year=year, month=f"{month:02d}"),
        encoding="utf-8",
    )
    return output_path


def validate_inputs(xml_path: Path, api_key: str | None) -> str:
    """Validate required runtime inputs and return the API key."""
    if not xml_path.exists():
        raise FileNotFoundError(
            "Error: export.xml not found. Please place the exported XML file "
            "in the project root directory."
        )
    if not api_key:
        raise ValueError(
            "Error: GEMINI_API_KEY environment variable is not set. "
            "Please set it before running the script."
        )
    return api_key


def generate_report(
    xml_path: Path,
    target_year: int,
    target_month: int,
    output_dir: Path,
    api_key: str,
    model: str = DEFAULT_GEMINI_MODEL,
) -> Path:
    """Run the full report generation workflow."""
    records = parse_health_records(xml_path, target_year, target_month)
    daily_series = aggregate_daily_metrics(records, target_year, target_month)
    assets_dir = output_dir / "assets"
    slides: list[dict[str, Any]] = []

    for metric in METRIC_DEFINITIONS.values():
        series = daily_series[metric.key]
        stats = calculate_stats(series, metric.target_value)
        chart_path = generate_chart(metric, series, assets_dir, target_year, target_month)
        prompt = build_insight_prompt(metric, series, stats, target_year, target_month)
        try:
            insight = get_gemini_insight(prompt, api_key=api_key, model=model)
        except RuntimeError:
            insight = INSIGHT_FALLBACK
        slides.append(
            {
                "name": metric.name,
                "image_path": chart_path.relative_to(output_dir).as_posix(),
                "insight": insight,
                "target_value": f"{metric.target_value:g}",
                "unit": metric.unit,
            }
        )

    html_path = (
        output_dir / f"apple_watch_health_monthly_report_{target_year}_{target_month:02d}.html"
    )
    return render_html_report(slides, html_path, target_year, target_month)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Generate an Apple Watch health monthly HTML report."
    )
    parser.add_argument("--year", type=int, required=True, help="Target year, for example 2026.")
    parser.add_argument(
        "--month", type=int, required=True, choices=range(1, 13), help="Target month 1-12."
    )
    parser.add_argument(
        "--xml", type=Path, default=Path("export.xml"), help="Path to Apple Health export.xml."
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("output"), help="Report output directory."
    )
    parser.add_argument("--model", default=DEFAULT_GEMINI_MODEL, help="Gemini model name.")
    return parser.parse_args()


def main() -> int:
    """CLI entry point."""
    args = parse_args()
    try:
        api_key = validate_inputs(args.xml, os.getenv("GEMINI_API_KEY"))
        output_path = generate_report(
            args.xml, args.year, args.month, args.output_dir, api_key, args.model
        )
    except (FileNotFoundError, ValueError) as exc:
        print(exc)
        return 1
    print(f"Report generated: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
