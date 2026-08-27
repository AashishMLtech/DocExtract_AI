from decimal import Decimal

from document_extractor.models import ExtractionResult, LineItem
from document_extractor.validators import validate_business_rules


def test_valid_line_arithmetic():
    result = ExtractionResult(line_items=[LineItem(description="A", quantity=Decimal("2"), unit_price=Decimal("5"), total_price=Decimal("10"))], subtotal=Decimal("10"), total_amount=Decimal("10"))
    report = validate_business_rules(result, Decimal("0.01"))
    assert report.status in {"validated", "validated_with_warnings"}


def test_invalid_line_arithmetic():
    result = ExtractionResult(line_items=[LineItem(description="A", quantity=Decimal("2"), unit_price=Decimal("5"), total_price=Decimal("11"))])
    report = validate_business_rules(result, Decimal("0.01"))
    assert not report.line_item_math_valid
