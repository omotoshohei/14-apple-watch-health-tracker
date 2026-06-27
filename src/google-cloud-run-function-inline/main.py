from __future__ import annotations

# ruff: noqa: E402, I001

import html
import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

import functions_framework
from flask import Request, Response
from werkzeug.utils import secure_filename

os.environ.setdefault("MPLCONFIGDIR", "/tmp/matplotlib")


MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(32 * 1024 * 1024)))


def render_form(error: str | None = None) -> Response:
    current_year = datetime.now().year
    years = "\n".join(
        f'<option value="{year}">{year}</option>' for year in range(current_year, 2019, -1)
    )
    months = "\n".join(
        f'<option value="{month}"{" selected" if month == datetime.now().month else ""}>'
        f"{month:02d}</option>"
        for month in range(1, 13)
    )
    error_html = f'<p class="error">{html.escape(error)}</p>' if error else ""
    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Apple Watch Health Report</title>
  <style>
    body {{
      margin: 0;
      background: #f8fafc;
      color: #0f172a;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }}
    main {{
      max-width: 760px;
      margin: 48px auto;
      padding: 0 24px;
    }}
    h1 {{
      margin: 0 0 12px;
      font-size: 34px;
      line-height: 1.15;
    }}
    p {{
      color: #475569;
      line-height: 1.6;
    }}
    form {{
      margin-top: 28px;
      display: grid;
      gap: 18px;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 24px;
      box-shadow: 0 16px 35px rgba(15, 23, 42, 0.08);
    }}
    label {{
      display: grid;
      gap: 8px;
      font-weight: 700;
    }}
    input, select, button {{
      font: inherit;
      border-radius: 6px;
    }}
    input, select {{
      border: 1px solid #cbd5e1;
      padding: 10px 12px;
      background: #ffffff;
    }}
    .row {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
    }}
    button {{
      border: 0;
      background: #0f172a;
      color: #ffffff;
      padding: 13px 16px;
      font-weight: 800;
      cursor: pointer;
    }}
    .error {{
      color: #b91c1c;
      background: #fee2e2;
      border: 1px solid #fecaca;
      border-radius: 6px;
      padding: 12px 14px;
    }}
    .note {{
      font-size: 14px;
    }}
  </style>
</head>
<body>
  <main>
    <h1>Apple Watch Health Monthly Report</h1>
    <p>
      Upload Apple Health <code>export.xml</code>, choose a month,
      and generate a self-contained HTML report.
    </p>
    {error_html}
    <form method="post" enctype="multipart/form-data">
      <label>
        Apple Health export.xml
        <input name="export_xml" type="file" accept=".xml,text/xml,application/xml" required>
      </label>
      <div class="row">
        <label>
          Year
          <select name="year" required>{years}</select>
        </label>
        <label>
          Month
          <select name="month" required>{months}</select>
        </label>
      </div>
      <button type="submit">Generate Report</button>
      <p class="note">
        The Cloud Run function generates the report without external AI API keys.
        For large Apple Health exports, use a full Cloud Run service instead
        of the inline function editor.
      </p>
    </form>
  </main>
</body>
</html>"""
    return Response(page, mimetype="text/html")


def parse_target_period(request: Request) -> tuple[int, int]:
    try:
        year = int(request.form.get("year", ""))
        month = int(request.form.get("month", ""))
    except ValueError as exc:
        raise ValueError("Year and month must be numeric.") from exc
    if year < 2020 or year > datetime.now().year:
        raise ValueError("Year is outside the supported range.")
    if month < 1 or month > 12:
        raise ValueError("Month must be between 1 and 12.")
    return year, month


@functions_framework.http
def apple_watch_health_report(request: Request) -> Response:
    if request.method == "GET":
        return render_form()
    if request.method != "POST":
        return Response("Method not allowed", status=405)

    if request.content_length and request.content_length > MAX_UPLOAD_BYTES:
        max_mb = MAX_UPLOAD_BYTES // (1024 * 1024)
        return render_form(f"Upload is too large for this inline function. Limit: {max_mb} MB.")

    uploaded_file = request.files.get("export_xml")
    if uploaded_file is None or not uploaded_file.filename:
        return render_form("Please upload Apple Health export.xml.")

    filename = secure_filename(uploaded_file.filename)
    if not filename.lower().endswith(".xml"):
        return render_form("Please upload an XML file.")

    temp_dir = Path(tempfile.mkdtemp(prefix="health-report-", dir="/tmp"))
    try:
        from html_utils import convert_html_images_to_data_uris
        from report import generate_report

        xml_path = temp_dir / "export.xml"
        output_dir = temp_dir / "output"
        uploaded_file.save(xml_path)

        year, month = parse_target_period(request)
        report_path = generate_report(
            xml_path=xml_path,
            target_year=year,
            target_month=month,
            output_dir=output_dir,
        )
        html_content = report_path.read_text(encoding="utf-8")
        self_contained_html = convert_html_images_to_data_uris(html_content, output_dir)
        download_name = f"apple_watch_health_monthly_report_{year}_{month:02d}.html"
        return Response(
            self_contained_html,
            mimetype="text/html",
            headers={"Content-Disposition": f'inline; filename="{download_name}"'},
        )
    except Exception as exc:
        return render_form(f"Failed to generate report: {exc}")
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
