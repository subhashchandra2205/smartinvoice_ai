# Five-minute demo script

**Goal:** Demonstrate a working invoice workflow, explain the decisions, and show how exceptions are routed to human review. Keep the app open and the three test PDFs ready before recording.

## 0:00–0:35 — Problem and solution

“Accounts Payable teams manually read invoices, match them to purchase orders, check amounts and tax, and decide whether they can proceed. SmartInvoice AI is a local-first prototype that automates the first-pass checks and makes the decision and its reasoning visible. It does not make payments.”

## 0:35–1:10 — Show the interface

Point out:
- Overview dashboard and processing history.
- PDF upload page.
- Live processing stages.
- Extracted fields, PO comparison, GST validation and decision explanation.
- SQLite-backed run history and CSV export.

## 1:10–2:10 — Happy path

Upload `01_fresh_approved_invoice.pdf`.

Narrate:
- The app reads embedded PDF text using PyMuPDF.
- It extracts vendor, invoice number, date, PO, taxable amount and GST.
- It matches PO-1001.
- At 18%, GST on ₹10,000 is ₹1,800; the extracted tax matches.
- The invoice is Approved under the configured demo rules.

## 2:10–3:10 — Edge case: incorrect GST

Upload `02_incorrect_gst_invoice.pdf`.

Narrate:
- The invoice amount is ₹10,000.
- Expected GST at 18% is ₹1,800, but the invoice contains ₹1,200.
- The ₹600 difference exceeds the ₹1 tolerance.
- The app routes it to Needs Review rather than approving it.

## 3:10–4:05 — Edge case: PO amount mismatch

Upload `03_po_amount_mismatch_invoice.pdf`.

Narrate:
- The invoice amount is ₹12,000 while the PO amount is ₹10,000.
- The 20% variance exceeds the configured 2% tolerance.
- GST arithmetic can pass independently, but the PO mismatch still means Needs Review.

## 4:05–5:00 — Close with design choices and limitations

“I chose deterministic rules for decisions that should be explainable and repeatable. OCR is local and optional; no paid API is required. The system records an audit history and keeps a human in the loop. The current prototype uses synthetic PO data and simplified invoice parsing. A production version would need layout-aware extraction, vendor/GSTIN verification, line-item and partial-PO matching, secure access controls and broader testing.”

## Recording checklist

- Close unrelated browser tabs and notifications.
- Confirm the app is running and all three PDFs are accessible.
- Use the same GST and PO tolerance settings for all runs.
- Avoid re-uploading an already processed PDF if duplicate detection is enabled; use the fresh test files supplied for the demo.
- Keep the video under five minutes.
