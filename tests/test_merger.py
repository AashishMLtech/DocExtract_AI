from decimal import Decimal

from document_extractor.merger import merge_results
from document_extractor.models import ExtractionResult, LineItem


def test_merge_and_deduplicate():
    a = ExtractionResult(document_type="invoice", invoice_id="1", line_items=[LineItem(description="A", quantity=Decimal("1"), unit_price=Decimal("1"), total_price=Decimal("1"))])
    b = ExtractionResult(document_type="invoice", invoice_id="1", line_items=[LineItem(description="A", quantity=Decimal("1"), unit_price=Decimal("1"), total_price=Decimal("1"))])
    merged, warnings = merge_results([a, b])
    assert len(merged.line_items) == 1
    assert not warnings
