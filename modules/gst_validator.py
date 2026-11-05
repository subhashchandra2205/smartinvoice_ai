
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def money(value):
    """Convert values safely to two-decimal currency amounts."""
    return Decimal(str(value)).quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP
    )


def validate_gst(
    amount,
    tax_amount,
    gst_rate=18,
    amount_basis="inclusive",
    tolerance=1.00
):
    """
    Validate GST calculations.

    amount_basis:
        inclusive = amount represents total including GST
        taxable   = amount represents amount before GST
    """

    try:
        amount = money(amount)
        tax_amount = money(tax_amount)
        rate = Decimal(str(gst_rate))
        tolerance = money(tolerance)

    except (InvalidOperation, TypeError, ValueError):
        return {
            "status": "REVIEW",
            "message": "Invalid or missing numerical values."
        }

    if amount < 0 or tax_amount < 0 or rate <= 0 or tolerance < 0:
        return {
            "status": "REVIEW",
            "message": "Amounts, GST rate and tolerance must be valid."
        }

    if amount_basis == "inclusive":

        # Total amount already includes GST.
        taxable_amount = money(
            amount / (Decimal("1") + rate / Decimal("100"))
        )

        expected_tax = money(amount - taxable_amount)
        expected_total = amount

    elif amount_basis == "taxable":

        # Total amount is before GST.
        taxable_amount = amount

        expected_tax = money(
            taxable_amount * rate / Decimal("100")
        )

        expected_total = money(
            taxable_amount + expected_tax
        )

    else:
        return {
            "status": "REVIEW",
            "message": "Unknown amount basis."
        }

    tax_difference = money(abs(tax_amount - expected_tax))

    calculated_total = money(taxable_amount + tax_amount)

    if tax_difference > tolerance:
        status = "FAIL"
        message = "GST amount does not match the expected calculation."

    else:
        status = "PASS"
        message = "GST calculation is within the configured tolerance."

    return {
        "status": status,
        "message": message,
        "gst_rate": float(rate),
        "amount_basis": amount_basis,
        "taxable_amount": float(taxable_amount),
        "extracted_tax": float(tax_amount),
        "expected_tax": float(expected_tax),
        "tax_difference": float(tax_difference),
        "calculated_total": float(calculated_total),
        "expected_total": float(expected_total),
        "tolerance": float(tolerance)
    }
