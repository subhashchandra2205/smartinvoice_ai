
import re
import os
import fitz
import pytesseract


# --------------------------------------------------
# TESSERACT CONFIGURATION
# --------------------------------------------------

tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(tesseract_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_path


# --------------------------------------------------
# PDF TEXT EXTRACTION
# --------------------------------------------------

def extract_pdf_text(pdf_bytes: bytes) -> str:
    """Extract selectable text from all PDF pages."""

    with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
        return "\n".join(
            page.get_text("text") for page in doc
        ).strip()


def extract_pdf_text_with_ocr(pdf_bytes: bytes):
    """
    Try selectable text first.
    If empty, use local Tesseract OCR.

    Returns (text, method, warning).
    """

    text = extract_pdf_text(pdf_bytes)

    if text.strip():
        return text, "PyMuPDF text extraction", None

    try:
        from PIL import Image

        pages_text = []

        with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
            for page in doc:
                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False
                )

                image = Image.frombytes(
                    "RGB",
                    [pix.width, pix.height],
                    pix.samples
                )

                page_text = pytesseract.image_to_string(image)
                pages_text.append(page_text)

        ocr_text = "\n".join(pages_text).strip()

        if ocr_text:
            return ocr_text, "Local Tesseract OCR", None

        return "", "OCR", "OCR ran but could not read any text."

    except ImportError:
        return "", "OCR unavailable", (
            "Install pytesseract, Pillow and the "
            "Tesseract OCR application."
        )

    except Exception as exc:
        return "", "OCR error", f"OCR could not run: {exc}"


# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------

def _clean(value):
    return re.sub(
        r"\s+",
        " ",
        str(value or "")
    ).strip(" \t:;,-")


def _first(patterns, text, flags=re.IGNORECASE | re.MULTILINE):
    for pattern in patterns:
        match = re.search(pattern, text, flags)

        if match:
            return _clean(match.group(1))

    return ""


def _amount(value):
    if not value:
        return None

    cleaned = re.sub(r"[^\d.,]", "", str(value))
    cleaned = cleaned.replace(",", "")

    try:
        return round(float(cleaned), 2)

    except ValueError:
        return None


# --------------------------------------------------
# INVOICE DATA EXTRACTION
# --------------------------------------------------

def demo_extract(
    text: str,
    extraction_method="Local rule-based extraction"
) -> dict:

    """
    Local invoice parser.
    No paid API required.
    Extracts invoice details using regular expressions.
    """

    # INVOICE NUMBER

    invoice_no = _first([
        r"(?:invoice\s*(?:number|no\.?|#)|inv\s*(?:number|no\.?|#))\s*[:#-]?\s*([A-Z0-9][A-Z0-9/_-]+)"
    ], text)

    # PURCHASE ORDER NUMBER

    po_no = _first([
        r"(?:purchase\s*order(?:\s*(?:number|no\.?|#))?|PO(?:\s*(?:number|no\.?|#))?)\s*[:#-]?\s*((?:PO|P\.O\.)[-/\s]?[A-Z0-9-]+)"
    ], text)

    # INVOICE DATE

    inv_date = _first([
        r"(?:invoice\s*date|date\s*of\s*invoice|date)\s*[:#-]?\s*([0-9]{4}-[0-9]{1,2}-[0-9]{1,2}|[0-9]{1,2}[-/][A-Za-z]{3}[-/][0-9]{2,4}|[0-9]{1,2}[-/][0-9]{1,2}[-/][0-9]{2,4})"
    ], text)

    # INVOICE TOTAL

    total_raw = _first([
        r"(?:grand\s+total|invoice\s+total|total\s+amount|amount\s+due|net\s+payable|total)\s*[:#-]?\s*(?:(?:INR|Rs\.?|₹|USD|\$)\s*)?([0-9][0-9,]*(?:\.\d{1,2})?)"
    ], text)

    # TAX / GST AMOUNT

    tax_raw = _first([
        r"(?:(?:total\s+)?(?:GST|IGST|CGST|SGST|tax)(?:\s+amount)?)\s*[:#-]?\s*(?:(?:INR|Rs\.?|₹)\s*)?([0-9][0-9,]*(?:\.\d{1,2})?)",

        r"(?:INR|Rs\.?|₹)\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*(?:tax|GST)",

        r"(?:tax|GST)\s*[:#-]?\s*([0-9][0-9,]*(?:\.\d{1,2})?)",

        r"(?:tax|GST)\s*[:#-]?\s*(?:(?:INR|Rs\.?|₹)\s*)?([0-9][0-9,]*(?:\.\d{1,2})?)"
    ], text)

    # OCR FALLBACK:
    # Tesseract sometimes removes the "Tax:" label.
    # Example: standalone line "INR 1800"

    if not tax_raw:
        tax_raw = _first([
            r"^\s*(?:INR|Rs\.?|₹)\s*([0-9][0-9,]*(?:\.\d{1,2})?)\s*$"
        ], text)

    # VENDOR NAME

    vendor = _first([
        r"(?:vendor|supplier|seller)\s*(?:name)?\s*[:#-]\s*([^\n]+)",

        r"(?:billed\s+by|from)\s*[:#-]\s*([^\n]+)"
    ], text)

    if not vendor:

        ignored = {
            "tax invoice",
            "invoice",
            "bill",
            "invoice copy",
            "original"
        }

        for line in text.splitlines():

            candidate = _clean(line)

            if (
                candidate
                and candidate.lower() not in ignored
                and not re.search(
                    r"\b(invoice|gstin|phone|email|www\.)\b",
                    candidate,
                    re.I
                )
            ):
                vendor = candidate[:120]
                break

    # CONFIDENCE SCORE

    fields = [
        vendor,
        invoice_no,
        inv_date,
        po_no,
        total_raw
    ]

    found = sum(bool(x) for x in fields)

    confidence = round(found / len(fields), 2)

    # CURRENCY

    currency = "INR"

    if re.search(r"\bUSD\b|\$", text, re.I):
        currency = "USD"

    # FINAL OUTPUT

    return {
        "vendor_name": vendor or None,

        "invoice_number": invoice_no or None,

        "invoice_date": inv_date or None,

        "po_number": (
            po_no.upper().replace(" ", "").replace("/", "-")
            if po_no else None
        ),

        "total_amount": _amount(total_raw),

        "tax_amount": _amount(tax_raw),

        "currency": currency,

        "extraction_method": extraction_method,

        "confidence": confidence,

        "missing_fields": [
            name
            for name, value in [
                ("vendor_name", vendor),
                ("invoice_number", invoice_no),
                ("invoice_date", inv_date),
                ("po_number", po_no),
                ("total_amount", total_raw)
            ]
            if not value
        ]
    }
