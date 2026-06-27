from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Add src directory to path so we can import health_report
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from health_report import convert_html_images_to_data_uris, generate_report

# Load environment variables
load_dotenv()

# Set up page configurations
st.set_page_config(
    page_title="Apple Watch Health Report Generator",
    page_icon="⌚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for rich premium aesthetics
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Header Gradient styling */
    .header-container {
        background: linear-gradient(135deg, #1e1b4b 0%, #311042 50%, #4c0519 100%);
        padding: 2.5rem;
        border-radius: 1.25rem;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.15), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        position: relative;
        overflow: hidden;
    }
    
    .header-container::after {
        content: "";
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(99, 102, 241, 0.15) 0%, rgba(0, 0, 0, 0) 70%);
        pointer-events: none;
    }
    
    .header-title {
        font-size: 2.75rem;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.03em;
        background: linear-gradient(to right, #ffffff, #f472b6, #6366f1);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .header-subtitle {
        font-size: 1.15rem;
        font-weight: 400;
        color: #cbd5e1;
        margin-top: 0.75rem;
        letter-spacing: -0.01em;
    }
    
    /* Input Container styling */
    .control-card {
        background-color: #ffffff;
        padding: 2rem;
        border-radius: 1rem;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        margin-bottom: 1.5rem;
    }
    
    /* Pulse animation for generating report state */
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
    }
    .pulse-text {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        font-weight: 600;
        color: #4f46e5;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Header Section
st.markdown(
    """
    <div class="header-container">
        <h1 class="header-title">⌚ Apple Watch Health Report</h1>
        <div class="header-subtitle">Upload your Apple Health XML export, choose a target month,
        and generate an interactive dashboard report complete with daily charts and
        monthly metric statistics.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Select Target Month and Year
current_year = datetime.now().year
years = list(range(current_year, 2019, -1))
months = list(range(1, 13))

st.sidebar.markdown("### 📅 Report Period")
target_year = st.sidebar.selectbox("Year", options=years, index=0)
target_month = st.sidebar.selectbox("Month", options=months, index=datetime.now().month - 1)

# Main UI layout split into two columns
col_control, col_preview = st.columns([1, 2])

# Left column: Controls and uploads
with col_control:
    st.markdown("### 📂 Upload Export Data")

    # Apple Health XML File Uploader
    uploaded_file = st.file_uploader(
        "Upload export.xml from Apple Health",
        type=["xml"],
        help=(
            "To get this file, open the Health app on your iPhone, "
            "tap your profile pic, select 'Export Health Data', "
            "and unzip the downloaded archive."
        ),
    )

    # Info on upload limit config
    st.markdown(
        """
        <small style="color: #64748b;">
        Note: The file size limit is configured to 1024MB.
        For extremely large exports, parsing may take a few moments.
        </small>
        """,
        unsafe_allow_html=True,
    )

    generate_btn = st.button(
        "🚀 Generate Monthly Report",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )

# Right column: Report generator output and preview
with col_preview:
    if generate_btn:
        if not uploaded_file:
            st.error("Please upload an Apple Health XML file first.")
        else:
            status_container = st.container()
            with status_container:
                st.markdown(
                    '<p class="pulse-text">Processing Apple Health XML data...</p>',
                    unsafe_allow_html=True,
                )

            progress_bar = st.progress(0)

            # Setup temporary working directories
            temp_dir = tempfile.mkdtemp()
            temp_xml_path = Path(temp_dir) / "uploaded_export.xml"
            temp_output_dir = Path(temp_dir) / "output"

            try:
                # Write uploaded XML to temp file
                progress_bar.progress(10)
                with open(temp_xml_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                # Execute report generation
                progress_bar.progress(30)
                status_container.markdown(
                    '<p class="pulse-text">Analyzing metrics and generating charts...</p>',
                    unsafe_allow_html=True,
                )

                # Generate report (this saves HTML + assets/png charts to temp_output_dir)
                report_path = generate_report(
                    xml_path=temp_xml_path,
                    target_year=target_year,
                    target_month=target_month,
                    output_dir=temp_output_dir,
                )

                progress_bar.progress(70)
                status_container.markdown(
                    '<p class="pulse-text">Inlining images to build self-contained report...</p>',
                    unsafe_allow_html=True,
                )

                # Read generated HTML
                html_content = report_path.read_text(encoding="utf-8")

                # Inline assets/*.png to base64 Data URIs
                self_contained_html = convert_html_images_to_data_uris(
                    html_content, temp_output_dir
                )

                progress_bar.progress(100)
                status_container.success("🎉 Monthly health report generated successfully!")

                # Download Button for self-contained HTML
                download_filename = (
                    f"apple_watch_health_monthly_report_{target_year}_{target_month:02d}.html"
                )
                st.download_button(
                    label="📥 Download Self-Contained Report HTML",
                    data=self_contained_html,
                    file_name=download_filename,
                    mime="text/html",
                    use_container_width=True,
                )

                # Display embedded HTML preview using st.components.v1.html
                st.markdown("### 🖥️ Report Preview")
                st.components.v1.html(
                    self_contained_html,
                    height=700,
                    scrolling=True,
                )

            except Exception as e:
                progress_bar.empty()
                status_container.error(f"Failed to generate report: {str(e)}")
            finally:
                # Cleanup temp directories
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
    else:
        st.info(
            "Upload your XML file and click 'Generate Monthly Report' "
            "to preview and download the report."
        )
