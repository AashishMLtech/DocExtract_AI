from decimal import Decimal

import pytest

from document_extractor.models import ExtractionResult, LineItem


def test_valid_extraction_result():
    result = ExtractionResult(line_items=[LineItem(description="A", quantity=Decimal("2"), unit_price=Decimal("5"), total_price=Decimal("10"))])
    assert result.document_type == "unknown"


def test_invalid_confidence():
    with pytest.raises(Exception):
        ExtractionResult(overall_confidence=2)
