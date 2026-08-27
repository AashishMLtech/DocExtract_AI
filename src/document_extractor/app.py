from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from document_extractor.config import get_settings
from document_extractor.error_handlers import friendly_error
from document_extractor.extractor import GroqExtractor

logging.basicConfig(level=logging.INFO)

st.set_page_config(
    page_title="Document Data Extractor",
    page_icon="▦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
      .block-container {
        padding-top: 1.35rem;
        padding-bottom: 2rem;
      }
      .hero {
        padding: 1.4rem 1.5rem;
        border-radius: 20px;
        background: linear-gradient(135deg, #0b1220 0%, #152238 52%, #20324f 100%);
        color: white;
        box-shadow: 0 18px 48px rgba(15, 23, 42, 0.16);
        margin-bottom: 1rem;
      }
      .hero h1 {
        margin: 0;
        font-size: 2rem;
        line-height: 1.12;
      }
      .hero p {
        margin: 0.5rem 0 0;
        color: rgba(255,255,255,0.83);
        font-size: 0.98rem;
      }
      .surface {
        padding: 1rem 1.1rem;
        border: 1px solid rgba(148,163,184,0.22);
        border-radius: 16px;
        background: white;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);
      }
      .pill {
        display: inline-block;
        padding: 0.35rem 0.65rem;
        border-radius: 999px;
        background: #e2e8f0;
        color: #0f172a;
        font-size: 0.8rem;
        margin-right: 0.35rem;
        margin-bottom: 0.35rem;
      }
      .section-title {
        font-size: 1rem;
        font-weight: 700;
        color: #0f172a;
        margin: 1rem 0 0.4rem;
      }
      .metric-label {
        color: #64748b;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
      }
      .metric-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #0f172a;
      }
      .subtle {
        color: #64748b;
        font-size: 0.92rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)

settings = get_settings()

st.markdown(
    """
    <div class="hero">
      <h1>Advanced Document Data Extractor</h1>
      <p>Professional invoice, receipt, and purchase-order extraction with deterministic validation and controlled API usage.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div style="margin-bottom: 0.9rem;">
      <span class="pill">Hybrid extraction</span>
      <span class="pill">Validated JSON</span>
      <span class="pill">Free-tier aware</span>
      <span class="pill">Client-ready output</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Workspace</div>', unsafe_allow_html=True)
main_left, main_right = st.columns([1.25, 0.75], gap="large")

with main_left:
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.subheader("Upload document")
    st.write("Choose a business document and process it with hybrid text/vision routing.")
    upload = st.file_uploader(
        "Drop a file here",
        type=["pdf", "png", "jpg", "jpeg"],
        help="Upload a business document up to 10 MB.",
        label_visibility="collapsed",
    )

    process_clicked = False
    if upload:
        st.caption(f"Selected file: {upload.name}  |  {(upload.size / (1024 * 1024)):.2f} MB")
        file_suffix = Path(upload.name).suffix.lower()
        if file_suffix in {".png", ".jpg", ".jpeg"}:
            st.image(upload.getvalue(), caption="Preview", use_container_width=True)
        else:
            st.info("PDF preview is rendered during processing.")
        process_clicked = st.button("Process document", type="primary", use_container_width=True)
    else:
        st.info("Upload a PDF or image to begin.")
    st.markdown("</div>", unsafe_allow_html=True)

with main_right:
    st.markdown('<div class="surface">', unsafe_allow_html=True)
    st.subheader("How it works")
    st.markdown(
        """
        <div class="subtle">
        Native PDF text is preferred first. Vision is only used when text quality is poor or missing.
        Non-business or instruction-like files are skipped locally so free-tier API usage is preserved.
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Document types**")
    st.write("Invoice")
    st.write("Receipt")
    st.write("Purchase order")
    st.markdown("**Output**")
    st.write("Validated JSON")
    st.write("Warnings")
    st.write("Downloadable file")
    st.markdown("</div>", unsafe_allow_html=True)

if upload and process_clicked:
    if upload.size > settings.max_file_size_mb * 1024 * 1024:
        st.error(f"This file is larger than the {settings.max_file_size_mb} MB limit.")
    else:
        try:
            with st.spinner("Reading, extracting, and validating..."):
                result, report, metadata = GroqExtractor(settings).process(upload.getvalue(), Path(upload.name).suffix)

            status_icon = "✅" if report.status == "validated" else "⚠️" if report.status == "validated_with_warnings" else "❌"
            status_color = "#16a34a" if report.status == "validated" else "#d97706" if report.status == "validated_with_warnings" else "#dc2626"

            st.markdown(
                f"""
                <div class="surface" style="margin-top:1rem;">
                  <div class="metric-label">Processing status</div>
                  <div class="metric-value" style="color:{status_color};">{status_icon} {report.status.replace('_', ' ').title()}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            stat_a, stat_b, stat_c = st.columns(3)
            stat_a.metric("Document Type", result.document_type.title())
            stat_b.metric("Method", metadata["extraction_mode"].replace("_", " ").title())
            stat_c.metric("Pages", f"{metadata['processed_pages']}/{metadata['total_pages']}")

            left_col, right_col = st.columns([1.08, 0.92], gap="large")

            with left_col:
                st.markdown("#### Extracted data")
                tabs = st.tabs(["Business JSON", "Validation", "Warnings"])

                with tabs[0]:
                    st.json(json.loads(result.model_dump_json()))
                    st.download_button(
                        "Download JSON",
                        result.model_dump_json(indent=2),
                        "extraction.json",
                        "application/json",
                        use_container_width=True,
                    )

                with tabs[1]:
                    checks = {
                        "schema_valid": report.schema_valid,
                        "date_valid": report.date_valid,
                        "line_items_valid": report.line_items_valid,
                        "line_item_math_valid": report.line_item_math_valid,
                        "subtotal_valid": report.subtotal_valid,
                        "total_valid": report.total_valid,
                        "document_identity_consistent": report.document_identity_consistent,
                    }
                    for name, value in checks.items():
                        st.write(f"**{name.replace('_', ' ').title()}**: {'Pass' if value else 'Fail'}")

                with tabs[2]:
                    warnings = list(dict.fromkeys(result.warnings + report.warnings))
                    if warnings:
                        for warning in warnings:
                            st.warning(warning)
                    else:
                        st.success("No warnings were generated.")

            with right_col:
                st.markdown("#### Summary")
                st.metric("Confidence", result.overall_confidence if result.overall_confidence is not None else "Unknown")
                st.metric("Duration", f"{metadata['duration_seconds']}s")
                st.metric("Retries", metadata["retry_count"])
                st.metric("Skipped pages", metadata["skipped_pages"])

                st.markdown("#### Snapshot")
                snapshot = [
                    ("Vendor", result.vendor_name or "Not found"),
                    ("Invoice ID", result.invoice_id or "Not found"),
                    ("Date", result.date or "Not found"),
                    ("Currency", result.currency or "Not found"),
                    ("Subtotal", str(result.subtotal) if result.subtotal is not None else "Not found"),
                    ("Total", str(result.total_amount) if result.total_amount is not None else "Not found"),
                ]
                for label, value in snapshot:
                    st.write(f"**{label}:** {value}")

                if upload.name.lower().endswith((".png", ".jpg", ".jpeg")):
                    st.caption("Preview")
                    st.image(upload.getvalue(), use_container_width=True)

        except Exception as error:
            st.error(friendly_error(error))
