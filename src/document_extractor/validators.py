from __future__ import annotations

from decimal import Decimal

from .models import ExtractionResult, ValidationReport


def _close(a: Decimal | None, b: Decimal | None, tol: Decimal) -> bool:
    if a is None or b is None:
        return True
    return abs(a - b) <= tol


def validate_business_rules(result: ExtractionResult, tolerance: Decimal) -> ValidationReport:
    warnings = list(result.warnings)
    line_items_valid = True
    comparable_items = 0
    for item in result.line_items:
        if item.quantity <= 0 or item.unit_price < 0 or item.total_price < 0:
            line_items_valid = False
            warnings.append("One or more line items has an invalid numeric value.")
        if not _close(item.quantity * item.unit_price, item.total_price, tolerance):
            line_items_valid = False
            warnings.append(f"Line-item math mismatch for {item.description}.")
        comparable_items += 1
    subtotal_valid = True
    if result.subtotal is not None and comparable_items > 0:
        subtotal = sum((item.total_price for item in result.line_items), Decimal("0"))
        if not _close(subtotal, result.subtotal, tolerance):
            subtotal_valid = False
            warnings.append("Line items do not reconcile with subtotal.")
    elif result.subtotal is not None and comparable_items == 0:
        warnings.append("Subtotal could not be reconciled because no usable line-item totals were available.")
    total_valid = True
    required_total_parts = [result.subtotal, result.discount, result.shipping_amount, result.tax_amount, result.total_amount]
    if result.total_amount is not None and any(part is not None for part in required_total_parts[:4]):
        calc = (result.subtotal or Decimal("0")) - (result.discount or Decimal("0")) + (result.shipping_amount or Decimal("0")) + (result.tax_amount or Decimal("0"))
        if not _close(calc, result.total_amount, tolerance):
            total_valid = False
            warnings.append("Grand total does not reconcile.")
    elif result.total_amount is not None:
        warnings.append("Grand total could not be fully reconciled because some components were missing.")
    status = "validated"
    if warnings:
        status = "validated_with_warnings"
    if not (line_items_valid and subtotal_valid and total_valid):
        status = "validation_failed"
    return ValidationReport(line_items_valid=line_items_valid, subtotal_valid=subtotal_valid, total_valid=total_valid, status=status, warnings=list(dict.fromkeys(warnings)))
