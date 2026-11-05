# SmartInvoice AI — Invoice Processing (PS-1)

A local-first invoice-processing prototype for the Zamp AI Solutions Analyst case study.

**Workflow:** Upload PDF → extract invoice fields → match purchase order → validate duplicates, vendor, PO status, amount and GST → explain decision → save audit history.

## Features

- PDF text extraction using PyMuPDF.
- Local OCR fallback for scanned PDFs using Tesseract OCR.
- Rule-based extraction of vendor, invoice number/date, PO number, invoice amount and tax.
- Purchase-order matching from `data/purchase_orders.csv`.
- Deterministic validation for duplicate files/invoice identities, missing fields, vendor mismatch, PO status and amount tolerance.
- GST arithmetic validation using a configurable GST rate, amount basis and tolerance.
- Three outcomes: **Approved**, **Needs Review**, and **Rejected**.
- Streamlit interface with process-stage feedback, decision explanation, overview dashboard and run history.
- SQLite audit history and CSV export.

## Technology

- Python
- Streamlit
- PyMuPDF
- Tesseract OCR + pytesseract (optional OCR path)
- pandas
- SQLite
- Regular expressions and deterministic business rules

> **AI transparency:** This implementation is a local, rule-based document-processing prototype. It does not call a generative AI model or a paid API. The completeness score is a heuristic field-completeness measure, not calibrated model confidence.

## Project structure

```text
SmartInvoice-AI/
├── app.py
├── requirements.txt
├── data/
│   └── purchase_orders.csv
├── modules/
│   ├── extractor.py
│   ├── validator.py
│   ├── gst_validator.py
│   └── database.py
├── samples/
│   └── *.pdf
├── tests/
│   ├── test_validation.py
│   └── test_gst.py
└── docs/
    ├── architecture.md
    ├── test_report.md
    └── demo_script.md
```

## Windows setup

Open the project root in VS Code. In PowerShell:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

If PowerShell blocks activation, run this once in that terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

The app opens at `http://localhost:8501` (or the port Streamlit reports).

### Existing virtual environment

If your environment is already created at `data\venv`, activate it from the project root with:

```powershell
.\data\venv\Scripts\Activate.ps1
```

## Optional scanned-PDF OCR setup

`pytesseract` is only the Python wrapper. Install the separate Tesseract OCR application for Windows. The current development machine used:

```text
C:\Program Files\Tesseract-OCR\tesseract.exe
```

The extractor is configured to use that path when it exists. If Tesseract is not installed, selectable-text PDFs can still be processed, but scanned/image-only PDFs will not have OCR fallback.

## Run tests

From the project root with the virtual environment active:

```powershell
python tests/test_validation.py
python tests/test_gst.py
```

If the project uses pytest and it is installed, you can also run:

```powershell
python -m pytest -q
```

## Demo test scenarios

Use the test report in `docs/test_report.md`. The three demonstrated scenarios are:
1. Correct invoice and GST → Approved.
2. Incorrect GST → Needs Review.
3. PO amount mismatch → Needs Review.

## Data and audit history

- `data/purchase_orders.csv` is a synthetic demonstration PO register.
- `data/invoice_history.db` is created automatically and stores processing history locally.
- Do not delete the SQLite database if you need to preserve audit history. For a clean demo, back it up first and only reset synthetic demo records.

## Assumptions and limitations

- Sample vendors, invoices, POs and tolerance values are synthetic demonstration data, not Zamp/company records or policy.
- Extraction depends on labelled fields and supported invoice layouts. New vendor layouts may require additional parsing rules.
- GST validation checks arithmetic for the configured rate and amount basis; it does not verify GSTINs, tax jurisdiction, HSN/SAC classifications, input-tax-credit eligibility or legal compliance.
- The PO comparison is a simplified header-level comparison. Real workflows may need line-item matching, partial invoicing, freight/discount handling, currency conversion and tax-inclusive versus tax-exclusive PO semantics.
- Duplicate identity uses vendor + invoice number; production systems need stronger identity and vendor-master controls.
- OCR quality depends on scan resolution, skew, language and document quality.
- A human approver must review flagged cases. The prototype does not initiate or execute payments.

## Production improvements

1. Support multiple invoice layouts with layout-aware extraction and confidence calibration.
2. Validate vendor tax identifiers and PO line items.
3. Handle partial invoices, split POs, credit notes, discounts and multiple tax rates.
4. Add authentication, role-based approvals, encrypted storage and retention controls.
5. Add structured logs, monitoring, error queues and a secure deployment pipeline.
6. Expand tests with representative, anonymised real-world invoices and measured OCR accuracy.

## Case study deliverables

The candidate guide asks for a live/runnable process and a five-minute demo video. This repository documentation supports those deliverables; the running Streamlit app and a recorded demo still need to be shared through the submission channels requested by the hiring coordinator.
