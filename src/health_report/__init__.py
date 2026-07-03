from .html import convert_html_images_to_data_uris
from .preprocess import aggregate_daily_csv_to_monthly_csv, preprocess_xml_to_csv
from .report import (
    METRIC_DEFINITIONS,
    HealthRecord,
    MetricDefinition,
    MetricStats,
    StatSummaryItem,
    aggregate_daily_metrics,
    build_stats_summary,
    calculate_stats,
    clean_and_prefix_svg,
    format_to_time_str,
    generate_report,
    load_daily_metrics_from_csv,
    parse_health_records,
    render_html_report,
    validate_inputs,
)
from .weekly import aggregate_daily_csv_to_weekly_csv, generate_weekly_report

__all__ = [
    "METRIC_DEFINITIONS",
    "MetricDefinition",
    "MetricStats",
    "StatSummaryItem",
    "HealthRecord",
    "parse_health_records",
    "aggregate_daily_metrics",
    "calculate_stats",
    "build_stats_summary",
    "render_html_report",
    "validate_inputs",
    "generate_report",
    "convert_html_images_to_data_uris",
    "clean_and_prefix_svg",
    "preprocess_xml_to_csv",
    "aggregate_daily_csv_to_monthly_csv",
    "aggregate_daily_csv_to_weekly_csv",
    "generate_weekly_report",
    "load_daily_metrics_from_csv",
    "format_to_time_str",
]
