
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from modules.extractor import extract_pdf_text_with_ocr, demo_extract
from modules.validator import validate_invoice, sha256
from modules.database import init_db, save_run, get_runs


# --------------------------------------------------
# APPLICATION CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SmartInvoice AI",
    page_icon="🧾",
    layout="wide"
)

init_db()


# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------

st.markdown("""
<style>
.block-container {
    padding-top: 1.4rem;
    max-width: 1450px;
}

div[data-testid="stMetric"] {
    background: var(--secondary-background-color);
    border: 1px solid rgba(128,128,128,.22);
    padding: 14px;
    border-radius: 12px;
}

div[data-testid="stMetric"] label,
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: var(--text-color) !important;
}
</style>
""", unsafe_allow_html=True)


# --------------------------------------------------
# LOAD PURCHASE ORDERS
# --------------------------------------------------

@st.cache_data
def load_pos():
    return pd.read_csv(ROOT / "data" / "purchase_orders.csv")


pos = load_pos()
runs = get_runs()


# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------

st.title("🧾 SmartInvoice AI")

st.caption(
    "Local invoice intelligence • Extract → Match → "
    "Validate → Explain"
)


# --------------------------------------------------
# SIDEBAR CONFIGURATION
# --------------------------------------------------

with st.sidebar:

    st.header("Control panel")

    page = st.radio(
        "Navigate",
        ["Overview", "Process invoice", "Run history"]
    )

    st.divider()

    st.caption("Invoice validation")

    tolerance = st.slider(
        "PO amount tolerance (%)",
        0.0, 10.0, 2.0, 0.5
    )

    st.divider()

    st.caption("GST validation")

    gst_rate = st.number_input(
        "GST rate (%)",
        min_value=0.0,
        max_value=100.0,
        value=18.0,
        step=1.0
    )

    gst_basis_label = st.selectbox(
        "Invoice amount represents",
        [
            "Taxable amount (GST added)",
            "Total including GST"
        ]
    )

    gst_amount_basis = (
        "taxable"
        if gst_basis_label == "Taxable amount (GST added)"
        else "inclusive"
    )

    gst_tolerance = st.number_input(
        "GST tolerance (₹)",
        min_value=0.0,
        value=1.0,
        step=0.5
    )

    st.divider()

    st.info(
        "No paid API required. Uses local PDF extraction, "
        "Tesseract OCR and deterministic validation."
    )

    st.caption("Flagged invoices require human review.")


# --------------------------------------------------
# STATUS DISPLAY
# --------------------------------------------------

def status_badge(status):

    if status == "Approved":
        st.success(
            "APPROVED — all configured checks passed"
        )

    elif status == "Rejected":
        st.error(
            "REJECTED — a blocking condition was detected"
        )

    else:
        st.warning(
            "NEEDS REVIEW — human verification required"
        )


# --------------------------------------------------
# OVERVIEW DASHBOARD
# --------------------------------------------------

if page == "Overview":

    st.subheader("Operations overview")

    runs = get_runs()

    total = len(runs)

    approved = sum(
        r["status"] == "Approved" for r in runs
    )

    review = sum(
        r["status"] == "Needs Review" for r in runs
    )

    rejected = sum(
        r["status"] == "Rejected" for r in runs
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Invoices processed", total)
    c2.metric("Approved", approved)
    c3.metric("Needs review", review)
    c4.metric("Rejected", rejected)

    st.divider()

    left, right = st.columns([1.25, 1])

    with left:

        st.markdown("### Recent processing activity")

        if runs:

            df = pd.DataFrame(runs)[[
                "created_at",
                "filename",
                "vendor_name",
                "invoice_number",
                "total_amount",
                "status"
            ]]

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

        else:
            st.info(
                "No invoices processed yet. "
                "Open Process invoice to begin."
            )

    with right:

        st.markdown("### Decision distribution")

        if total:

            chart = pd.DataFrame({
                "Decision": [
                    "Approved",
                    "Needs Review",
                    "Rejected"
                ],
                "Count": [
                    approved,
                    review,
                    rejected
                ]
            })

            st.bar_chart(
                chart.set_index("Decision")
            )

        else:
            st.caption(
                "Chart appears after the first run."
            )

    with st.expander("Purchase order register"):

        st.dataframe(
            pos,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# PROCESS INVOICE
# --------------------------------------------------

elif page == "Process invoice":

    st.subheader("Process a new invoice")

    st.write(
        "Upload a PDF. The application first reads embedded "
        "text and then attempts local Tesseract OCR if required."
    )

    uploaded = st.file_uploader(
        "Choose invoice PDF",
        type=["pdf"]
    )

    if uploaded:

        pdf_bytes = uploaded.getvalue()

        file_hash = sha256(pdf_bytes)

        st.success(
            f"Uploaded: {uploaded.name} · "
            f"{len(pdf_bytes):,} bytes"
        )

        if st.button(
            "🚀 Process invoice",
            type="primary",
            use_container_width=True
        ):

            stages = st.status(
                "Starting invoice workflow...",
                expanded=True
            )

            try:

                # STAGE 1: PDF EXTRACTION

                stages.write(
                    "1/4 · Reading PDF and checking embedded text"
                )

                raw_text, extraction_method, warning = (
                    extract_pdf_text_with_ocr(pdf_bytes)
                )

                if not raw_text:

                    stages.update(
                        state="error",
                        label="Could not extract invoice text"
                    )

                    st.error(
                        warning or "No readable text found."
                    )

                    st.stop()

                # STAGE 2: INVOICE EXTRACTION

                stages.write(
                    f"2/4 · Extracting fields using "
                    f"{extraction_method}"
                )

                invoice = demo_extract(
                    raw_text,
                    extraction_method=extraction_method
                )

                # STAGE 3: VALIDATION INCLUDING GST

                stages.write(
                    "3/4 · Matching PO and validating GST"
                )

                history = get_runs()

                result = validate_invoice(
                    invoice,
                    pos,
                    history,
                    tolerance_pct=tolerance,
                    file_hash=file_hash,
                    gst_rate=gst_rate,
                    gst_amount_basis=gst_amount_basis,
                    gst_tolerance=gst_tolerance
                )

                # STAGE 4: SAVE AUDIT RECORD

                stages.write(
                    "4/4 · Saving decision and audit record"
                )

                save_run(
                    uploaded.name,
                    file_hash,
                    invoice,
                    result
                )

                stages.update(
                    state="complete",
                    label="Invoice processing completed"
                )

                st.session_state["last_invoice"] = invoice
                st.session_state["last_result"] = result
                st.session_state["last_filename"] = uploaded.name
                st.session_state["last_text"] = raw_text

            except Exception as e:

                stages.update(
                    state="error",
                    label="Processing failed"
                )

                st.exception(e)

    # --------------------------------------------------
    # DISPLAY PROCESSING RESULT
    # --------------------------------------------------

    if "last_result" in st.session_state:

        invoice = st.session_state["last_invoice"]

        result = st.session_state["last_result"]

        st.divider()

        st.markdown("### Final invoice decision")

        status_badge(result["status"])

        # INVOICE SUMMARY

        a, b, c = st.columns(3)

        a.metric(
            "Invoice number",
            invoice.get("invoice_number") or "Missing"
        )

        a.metric(
            "Vendor",
            invoice.get("vendor_name") or "Missing"
        )

        b.metric(
            "Invoice total",
            (
                f"{invoice['total_amount']:,.2f} "
                f"{invoice.get('currency', 'INR')}"
                if invoice.get("total_amount") is not None
                else "Missing"
            )
        )

        b.metric(
            "PO reference",
            invoice.get("po_number") or "Missing"
        )

        c.metric(
            "Completeness score",
            f"{float(invoice.get('confidence') or 0):.0%}"
        )

        c.metric(
            "Extraction method",
            invoice.get("extraction_method", "Unknown")
        )

        st.caption(
            "Completeness score is a heuristic based on "
            "required fields found, not calibrated AI confidence."
        )

        # EXTRACTED DATA

        with st.expander(
            "Extracted invoice data",
            expanded=True
        ):

            st.json(invoice)

        # PURCHASE ORDER COMPARISON

        with st.expander(
            "Purchase order comparison",
            expanded=True
        ):

            if result.get("matched_po"):

                po = result["matched_po"]

                st.dataframe(
                    pd.DataFrame([po]),
                    use_container_width=True,
                    hide_index=True
                )

                if invoice.get("total_amount") is not None:

                    variance = (
                        abs(
                            float(invoice["total_amount"])
                            - float(po["po_amount"])
                        )
                        / float(po["po_amount"])
                        * 100
                        if float(po["po_amount"]) != 0
                        else 0
                    )

                    st.metric(
                        "Amount variance",
                        f"{variance:.2f}%"
                    )

            else:

                st.info(
                    "No matching purchase order was found."
                )

        # --------------------------------------------------
        # GST VALIDATION RESULTS
        # --------------------------------------------------

        st.markdown("### GST validation")

        gst = result.get("gst_validation")

        if gst:

            if gst["status"] == "PASS":

                st.success(
                    "GST validation passed"
                )

            elif gst["status"] == "FAIL":

                st.error(
                    "GST validation failed"
                )

            else:

                st.warning(
                    "GST validation requires manual review"
                )

            g1, g2, g3 = st.columns(3)

            g1.metric(
                "Expected GST",
                f"₹{gst.get('expected_tax', 0):,.2f}"
            )

            g2.metric(
                "Extracted GST",
                f"₹{gst.get('extracted_tax', 0):,.2f}"
            )

            g3.metric(
                "GST difference",
                f"₹{gst.get('tax_difference', 0):,.2f}"
            )

            st.write(
                "**Taxable amount:** "
                f"₹{gst.get('taxable_amount', 0):,.2f}"
            )

            st.write(
                "**Expected invoice total:** "
                f"₹{gst.get('expected_total', 0):,.2f}"
            )

            st.caption(
                gst.get("message", "")
            )

            with st.expander(
                "Detailed GST calculation"
            ):

                st.json(gst)

        else:

            st.warning(
                "GST validation was not performed."
            )

        # DECISION EXPLANATION

        st.markdown("### Decision explanation")

        for reason in result["reasons"]:

            st.write("• " + reason)

        for check in result["checks"]:

            st.write("✓ " + check)

        # SOURCE TEXT

        with st.expander("Extracted source text"):

            st.text(
                st.session_state.get(
                    "last_text", ""
                )[:12000]
            )

        st.caption(
            "Prototype recommendation only. "
            "A human approver must authorise any payment."
        )


# --------------------------------------------------
# RUN HISTORY
# --------------------------------------------------

else:

    st.subheader("Processing history")

    runs = get_runs()

    if runs:

        df = pd.DataFrame(runs)

        cols = [
            "id",
            "created_at",
            "filename",
            "vendor_name",
            "invoice_number",
            "po_number",
            "total_amount",
            "status",
            "extraction_method"
        ]

        st.dataframe(
            df[cols],
            use_container_width=True,
            hide_index=True
        )

        st.download_button(
            "Download history as CSV",
            df[cols].to_csv(index=False),
            "invoice_processing_history.csv",
            "text/csv"
        )

    else:

        st.info(
            "No processing records yet."
        )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "SmartInvoice AI · Local-first case-study prototype · "
    "Sample procurement data · Configurable validation rules."
)
