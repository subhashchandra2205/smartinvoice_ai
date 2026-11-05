# Test report — SmartInvoice AI

The following three end-to-end test scenarios were run through the Streamlit application on 5 November 2026. Results below are based on the application screenshots shared during testing.

| Test | Input scenario | Expected outcome | Observed outcome | Result |
|---|---|---|---|---|
| 1 | Fresh invoice `INV-ABC-002`; vendor and PO match; taxable amount ₹10,000; GST ₹1,800 at 18% | Approved | Approved | PASS |
| 2 | Invoice `INV-GST-FAIL-001`; taxable amount ₹10,000; extracted GST ₹1,200 instead of ₹1,800 | Needs Review | Needs Review | PASS |
| 3 | Invoice with taxable amount ₹12,000 against PO-1001 amount ₹10,000; 2% PO tolerance | Needs Review | Needs Review | PASS |

## Test 1 — Happy path

- Invoice number: `INV-ABC-002`
- Vendor: ABC Supplies Pvt Ltd
- PO: `PO-1001`
- Taxable amount: ₹10,000
- GST at 18%: ₹1,800
- Expected GST: ₹1,800
- GST difference: ₹0
- Observed decision: **Approved**

## Test 2 — Incorrect GST

- Invoice number: `INV-GST-FAIL-001`
- Taxable amount: ₹10,000
- Extracted GST: ₹1,200
- Expected GST at 18%: ₹1,800
- Difference: ₹600, greater than the configured ₹1 tolerance
- Observed decision: **Needs Review**

## Test 3 — PO amount mismatch

- PO: `PO-1001`
- PO amount: ₹10,000
- Invoice taxable amount: ₹12,000
- Difference: 20%, greater than the configured 2% PO tolerance
- GST settings: 18%, taxable amount basis, ₹1 tolerance
- Observed decision: **Needs Review**

## Additional cases previously exercised

The development/testing conversation also showed:
- Scanned invoice OCR extraction using local Tesseract.
- Vendor mismatch resulting in Needs Review.
- Duplicate PDF detection resulting in Rejected.
- Duplicate invoice identity detection.
- Missing invoice number / incomplete extraction routed to review.

These are qualitative checks from the development run; retain screenshots or rerun them if formal evidence is required.

## Test configuration

- GST rate: 18%
- GST amount basis: Taxable amount (GST added)
- GST tolerance: ₹1
- PO amount tolerance: 2%
- PO reference: `PO-1001`
- PO/vendor values are synthetic demonstration data.

## Interpretation

The three primary scenarios behaved as designed in the demonstrated runs. This is a small scenario-based test set, not evidence of production-grade accuracy across arbitrary vendor invoice layouts. Further testing with varied invoice templates, scan quality, tax structures and PO edge cases is required.
