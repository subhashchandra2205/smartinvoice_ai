import pandas as pd
from modules.validator import validate_invoice

def test_approved_invoice():
    pos = pd.DataFrame([{
        "po_number":"PO-1","vendor_name":"ABC Supplies Pvt Ltd",
        "po_amount":10000,"status":"Approved"
    }])
    invoice = {
        "vendor_name":"ABC Supplies Pvt Ltd","invoice_number":"INV-1",
        "po_number":"PO-1","total_amount":10100,"confidence":0.9
    }
    result = validate_invoice(invoice, pos, [], tolerance_pct=2)
    assert result["status"] == "Approved"

def test_missing_invoice_number_needs_review():
    pos = pd.DataFrame([{
        "po_number":"PO-1","vendor_name":"ABC Supplies Pvt Ltd",
        "po_amount":10000,"status":"Approved"
    }])
    invoice = {
        "vendor_name":"ABC Supplies Pvt Ltd","invoice_number":"",
        "po_number":"PO-1","total_amount":10000,"confidence":0.9
    }
    result = validate_invoice(invoice, pos, [], tolerance_pct=2)
    assert result["status"] == "Needs Review"
