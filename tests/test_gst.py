
import sys
from pathlib import Path

# Add project root to Python import path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from modules.gst_validator import validate_gst


def test_gst():

    # Test 1: Correct tax-exclusive invoice
    result1 = validate_gst(
        10000, 1800, 18, "taxable"
    )
    print("\nTest 1:", result1)

    assert result1["status"] == "PASS"

    # Test 2: Incorrect GST
    result2 = validate_gst(
        10000, 1200, 18, "taxable"
    )
    print("\nTest 2:", result2)

    assert result2["status"] == "FAIL"

    # Test 3: Invalid amount
    result3 = validate_gst(
        -10000, 1800, 18, "taxable"
    )
    print("\nTest 3:", result3)

    assert result3["status"] == "REVIEW"

    print("\nAll GST tests passed!")


if __name__ == "__main__":
    test_gst()
