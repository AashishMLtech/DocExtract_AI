from __future__ import annotations

from collections.abc import Iterable

from .models import ExtractionResult, LineItem


def merge_results(results: Iterable[ExtractionResult]) -> tuple[ExtractionResult, list[str]]:
    pages = list(results)
    if not pages:
        return ExtractionResult(), ["No page extraction was available."]
    warnings: list[str] = []
    fields = ["vendor_name", "date", "invoice_id", "currency", "subtotal", "discount", "shipping_amount", "tax_amount", "total_amount"]
    merged: dict[str, object | None] = {}
    for field in fields:
        values = [getattr(p, field) for p in pages if getattr(p, field) is not None]
        unique = list(dict.fromkeys(values))
        if len(unique) > 1:
            warnings.append(f"Conflicting {field.replace('_', ' ')} values were found across pages.")
        merged[field] = unique[0] if unique else None
    seen: set[tuple[str, str, str, str]] = set()
    items: list[LineItem] = []
    for page in pages:
        for item in page.line_items:
            key = (item.description.casefold().strip(), str(item.quantity), str(item.unit_price), str(item.total_price))
            if key not in seen:
                seen.add(key)
                items.append(item)
    document_types = [p.document_type for p in pages if p.document_type != "unknown"]
    confidence = min((p.overall_confidence for p in pages if p.overall_confidence is not None), default=None)
    merged_warnings = list(dict.fromkeys([w for p in pages for w in p.warnings] + warnings))
    return ExtractionResult(document_type=document_types[0] if document_types else "unknown", line_items=items, overall_confidence=confidence, warnings=merged_warnings, **merged), warnings
