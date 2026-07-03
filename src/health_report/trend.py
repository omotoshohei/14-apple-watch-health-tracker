from __future__ import annotations

import io
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from jinja2 import Template
from matplotlib.ticker import FuncFormatter

from .report import (
    METRIC_DEFINITIONS,
    clean_and_prefix_svg,
    format_float,
    format_to_time_str,
)


def load_monthly_trend_data(csv_path: Path) -> pd.DataFrame:
    """Load and validate monthly trend data from CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Error: Monthly metrics CSV file not found: {csv_path}")

    # Expected column datatypes
    dtypes = {
        "month": "str",
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

    required_cols = [
        "month",
        "metric",
        "average",
        "maximum",
        "minimum",
        "achievement_rate",
        "achieved_days",
        "valid_days",
    ]
    for col in required_cols:
        if col not in df.columns:
            raise ValueError(f"Error: Missing required column in monthly CSV: {col}")

    # Ensure month sorting
    df = df.sort_values("month")
    return df


def generate_trend_charts(df: pd.DataFrame) -> dict[str, str]:
    """Generate inline SVG trend line charts for all metrics, optimized for Dark Mode."""
    charts: dict[str, str] = {}
    months = sorted(df["month"].unique())

    for metric_key, metric in METRIC_DEFINITIONS.items():
        metric_df = df[df["metric"] == metric_key]

        # Build month aligned series
        series_data = []
        for m in months:
            row = metric_df[metric_df["month"] == m]
            if not row.empty and not pd.isna(row.iloc[0]["average"]):
                series_data.append((m, float(row.iloc[0]["average"])))
            else:
                series_data.append((m, None))

        fig, ax = plt.subplots(figsize=(10.0, 5.8), dpi=150)
        fig.patch.set_facecolor("none")
        ax.set_facecolor("none")

        x_positions = list(range(len(months)))
        valid_x = [i for i, (_, val) in enumerate(series_data) if val is not None]
        valid_y = [val for _, val in series_data if val is not None]

        # Draw target line (red dashed line)
        ax.axhline(metric.target_value, color="#f43f5e", linestyle="--", linewidth=2.0, alpha=0.85)

        # Draw Y label & formatter
        if metric.key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
            ax.set_ylabel("Time", color="#475569", fontsize=14)
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, pos: format_to_time_str(x)))
            target_label = f" Target {format_to_time_str(metric.target_value)}"

            # Dynamic Y range
            if valid_y:
                all_vals = valid_y + [metric.target_value]
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
            # Ensure Y starts at 0 for standard metrics
            if valid_y:
                ymax = max(valid_y + [metric.target_value]) * 1.15
                ax.set_ylim(0, ymax)

        # Plot data
        if valid_x:
            ax.plot(
                valid_x,
                valid_y,
                color=metric.color,
                linewidth=3.5,
                marker="o",
                markersize=9,
                markeredgecolor="#ffffff",
                markeredgewidth=2.0,
            )
            ax.fill_between(
                valid_x,
                valid_y,
                color=metric.color,
                alpha=0.12,
            )

        # Styling for Light Theme
        ax.set_xticks(x_positions)
        ax.set_xticklabels(months, color="#475569", fontsize=11)
        ax.tick_params(axis="x", colors="#475569", labelsize=11)
        ax.tick_params(axis="y", colors="#475569", labelsize=12)
        ax.grid(axis="y", color="#cbd5e1", alpha=0.7, linestyle=":")

        # Hide unnecessary spines
        for spine_name, spine in ax.spines.items():
            if spine_name in ["top", "right"]:
                spine.set_visible(False)
            else:
                spine.set_color("#cbd5e1")

        # Target label text
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

        # Clean and prefix SVG
        svg_content = clean_and_prefix_svg(buf.getvalue(), f"trend_{metric.key}")
        charts[metric.key] = svg_content

    return charts


HTML_TEMPLATE = Template(
    """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Apple Watch Health Trend Report</title>
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
      font-size: 54px;
      font-weight: 800;
      letter-spacing: -0.02em;
      color: #0f172a;
    }
    .period {
      color: #64748b;
      font-size: 28px;
      font-weight: 600;
    }
    .content {
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 48px;
      min-height: 0;
      flex-grow: 1;
    }
    .chart-container {
      display: flex;
      align-items: center;
      justify-content: center;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 12px;
      padding: 24px;
      min-height: 0;
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
    .data-panel {
      display: flex;
      flex-direction: column;
      gap: 24px;
      min-height: 0;
    }
    .table-container {
      flex-grow: 1;
      overflow-y: auto;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      background: #ffffff;
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 18px;
      text-align: left;
      color: #0f172a;
    }
    .data-table th, .data-table td {
      padding: 16px 20px;
      border-bottom: 1px solid #e2e8f0;
    }
    .data-table th {
      background: #f8fafc;
      color: #64748b;
      font-weight: 700;
      text-transform: uppercase;
      font-size: 15px;
      letter-spacing: 0.05em;
      position: sticky;
      top: 0;
    }
    .data-table tr:last-child td {
      border-bottom: none;
    }
    .data-table tr:hover td {
      background: #f1f5f9;
    }
    .goal-card {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-left: 5px solid #38bdf8;
      padding: 20px 24px;
      border-radius: 0 8px 8px 0;
      font-size: 20px;
      font-weight: 500;
      color: #475569;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .goal-value {
      font-weight: 700;
      color: #38bdf8;
    }
  </style>
</head>
<body>
{% for slide in slides %}
  <div class="slide-wrapper">
    <section class="slide">
      <div class="header">
        <h1>{{ slide.name }} Trend</h1>
        <div class="period">{{ period }}</div>
      </div>
      <div class="content">
        <div class="chart-container">
          <div class="chart">
            {{ slide.chart_svg | safe }}
          </div>
        </div>
        <div class="data-panel">
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Month</th>
                  <th>Average</th>
                  <th>Max / Min</th>
                  <th>Achievement</th>
                </tr>
              </thead>
              <tbody>
                {% for row in slide.table_rows %}
                <tr>
                  <td><strong>{{ row.month }}</strong></td>
                  <td>{{ row.average }}</td>
                  <td>{{ row.max_min }}</td>
                  <td>{{ row.achievement }}</td>
                </tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
          <div class="goal-card" style="border-left-color: {{ slide.color }}">
            <span>Target Goal:</span>
            <span class="goal-value" style="color: {{ slide.color }}">{{ slide.goal_text }}</span>
          </div>
        </div>
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


def generate_trend_report(csv_path: Path, output_dir: Path) -> Path:
    """Generate the trend report HTML using the aggregated monthly CSV."""
    df = load_monthly_trend_data(csv_path)
    charts = generate_trend_charts(df)

    # Determine the time period range
    months = sorted(df["month"].unique())
    if len(months) >= 2:
        period_str = f"{months[0]} ~ {months[-1]}"
    elif len(months) == 1:
        period_str = months[0]
    else:
        period_str = "No Data"

    output_dir.mkdir(parents=True, exist_ok=True)
    output_html_path = output_dir / "apple_watch_health_monthly_report.html"

    slides = []
    for metric_key, metric in METRIC_DEFINITIONS.items():
        metric_df = df[df["metric"] == metric_key]

        table_rows = []
        for _, row in metric_df.iterrows():
            avg_val = row["average"]
            max_val = row["maximum"]
            min_val = row["minimum"]
            ach_rate = row["achievement_rate"]
            ach_days = row["achieved_days"]
            v_days = row["valid_days"]

            # Formatting
            if metric_key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
                avg_str = format_to_time_str(avg_val)
                max_str = format_to_time_str(max_val)
                min_str = format_to_time_str(min_val)
                max_min_str = f"{max_str} / {min_str}"
            else:
                unit_label = f" {metric.unit}" if metric.unit else ""
                avg_str = format_float(avg_val) + unit_label if not pd.isna(avg_val) else "-"
                max_str = format_float(max_val) if not pd.isna(max_val) else "-"
                min_str = format_float(min_val) if not pd.isna(min_val) else "-"
                if not pd.isna(max_val) or not pd.isna(min_val):
                    max_min_str = f"{max_str} / {min_str}"
                else:
                    max_min_str = "-"

            ach_str = f"{ach_rate:.1f}% ({ach_days}/{v_days}d)" if not pd.isna(ach_rate) else "-"

            table_rows.append(
                {
                    "month": row["month"],
                    "average": avg_str,
                    "max_min": max_min_str,
                    "achievement": ach_str,
                }
            )

        # Goal text formatting
        if metric_key in ("sleep_onset", "wake_time", "first_morning_awake_time"):
            target_str = format_to_time_str(metric.target_value)
        else:
            target_str = f"{metric.target_value:g} {metric.unit}"

        op_str = "<=" if metric.lower_is_better else ">="
        goal_text = f"{op_str} {target_str}"

        slides.append(
            {
                "key": metric_key,
                "name": metric.name,
                "color": metric.color,
                "chart_svg": charts.get(metric_key, ""),
                "table_rows": table_rows,
                "goal_text": goal_text,
            }
        )

    # Render HTML
    html_content = HTML_TEMPLATE.render(slides=slides, period=period_str)

    output_html_path.write_text(html_content, encoding="utf-8")
    return output_html_path
