
from modules.gst_validator import validate_gst
import re
import hashlib


def normalize_name(value):
    return re.sub(r"[^a-z0-9]", "", str(value or "").lower())


def validate_invoice(
    invoice: dict,
    purchase_orders,
    processed_records,
    tolerance_pct=2.0,
    file_hash=None,
    gst_rate=18,
    gst_amount_basis="taxable",
    gst_tolerance=1.0
):
    """Apply invoice, PO, duplicate and GST validation rules."""

    reasons = []
    checks = []
    status = "Approved"

    po_number = str(invoice.get("po_number") or "").strip()
    inv_no = str(invoice.get("invoice_number") or "").strip()
    vendor = str(invoice.get("vendor_name") or "").strip()
    total = invoice.get("total_amount")
    tax_amount = invoice.get("tax_amount")

    gst_result = None

    def flag(level, message):
        nonlocal status

        reasons.append(message)

        if level == "reject":
            status = "Rejected"
        elif level == "review" and status != "Rejected":
            status = "Needs Review"

    # -------------------------------------------------
    # 1. GST VALIDATION
    # Run independently, even if the invoice is a duplicate.
    # -------------------------------------------------

    if total is not None and tax_amount is not None:
        try:
            gst_result = validate_gst(
                total,
                tax_amount,
                gst_rate=gst_rate,
                amount_basis=gst_amount_basis,
                tolerance=gst_tolerance
            )

            gst_status = str(gst_result.get("status", "")).upper()

            if gst_status == "PASS":
                checks.append(
                    "GST validation passed: " +
                    str(gst_result.get("message", ""))
                )

            elif gst_status == "FAIL":
                flag(
                    "review",
                    "GST validation failed: " +
                    str(gst_result.get("message", "Tax amount mismatch."))
                )

            else:
                flag(
                    "review",
                    "GST validation requires manual review: " +
                    str(gst_result.get("message", ""))
                )

        except Exception as error:
            flag(
                "review",
                f"GST validation could not be completed: {error}"
            )

    else:
        flag(
            "review",
            "GST validation requires both invoice total and tax amount."
        )

    # -------------------------------------------------
    # 2. DUPLICATE CHECKS
    # -------------------------------------------------

    for record in processed_records:

        if file_hash and record.get("file_hash") == file_hash:
            flag(
                "reject",
                "Exact duplicate file: this PDF has already been processed."
            )
            break

        if (
            inv_no
            and normalize_name(record.get("invoice_number"))
            == normalize_name(inv_no)
            and normalize_name(record.get("vendor_name"))
            == normalize_name(vendor)
        ):
            flag(
                "reject",
                "Duplicate invoice identity: vendor and invoice number already exist."
            )
            break

    # -------------------------------------------------
    # 3. REQUIRED FIELD CHECKS
    # -------------------------------------------------

    if not inv_no:
        flag("review", "Invoice number is missing.")

    if not vendor:
        flag("review", "Vendor name could not be extracted.")

    if not po_number:
        flag("review", "Purchase order reference is missing.")

    if total is None:
        flag("review", "Invoice total could not be extracted.")

    if float(invoice.get("confidence") or 0) < 0.60:
        flag(
            "review",
            "Extraction confidence is low; verify the extracted fields manually."
        )

    # -------------------------------------------------
    # 4. PURCHASE ORDER VALIDATION
    # -------------------------------------------------

    po = None

    if po_number:
        matches = purchase_orders[
            purchase_orders["po_number"].astype(str).str.upper()
            == po_number.upper()
        ]

        if not matches.empty:
            po = matches.iloc[0].to_dict()
        else:
            flag(
                "review",
                f"Purchase order {po_number} was not found."
            )

    if po:

        if str(po.get("status", "")).lower() != "approved":
            flag(
                "reject",
                f"Purchase order status is '{po.get('status')}', not Approved."
            )

        if (
            vendor
            and normalize_name(vendor)
            != normalize_name(po.get("vendor_name"))
        ):
            flag(
                "review",
                f"Vendor mismatch: invoice says '{vendor}', "
                f"PO lists '{po.get('vendor_name')}'."
            )

        if total is not None:
            try:
                po_amount = float(po["po_amount"])
                invoice_amount = float(total)

                diff_pct = (
                    abs(invoice_amount - po_amount) / po_amount * 100
                    if po_amount else 0
                )

                if diff_pct > tolerance_pct:
                    flag(
                        "review",
                        f"Amount variance is {diff_pct:.2f}%, "
                        f"exceeding the {tolerance_pct:.2f}% tolerance."
                    )
                else:
                    checks.append(
                        f"Amount variance {diff_pct:.2f}% is within "
                        f"{tolerance_pct:.2f}% tolerance."
                    )

            except (ValueError, TypeError, ZeroDivisionError):
                flag(
                    "review",
                    "Purchase order or invoice amount is invalid."
                )

    # -------------------------------------------------
    # 5. FINAL DECISION
    # -------------------------------------------------

    if not reasons:
        reasons.append("All configured validation checks passed.")

    return {
        "status": status,
        "reasons": reasons,
        "checks": checks,
        "matched_po": po,
        "tolerance_pct": tolerance_pct,
        "gst_validation": gst_result
    }


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
