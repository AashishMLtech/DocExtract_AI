from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator, model_validator


class LineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal

    @field_validator("description")
    @classmethod
    def non_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description cannot be empty")
        return value


class ExtractionResult(BaseModel):
    document_type: str = "unknown"
    vendor_name: str | None = None
    date: str | None = None
    invoice_id: str | None = None
    currency: str | None = None
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: Decimal | None = None
    discount: Decimal | None = None
    shipping_amount: Decimal | None = None
    tax_amount: Decimal | None = None
    total_amount: Decimal | None = None
    overall_confidence: float | None = None
    warnings: list[str] = Field(default_factory=list)

    @field_validator("document_type")
    @classmethod
    def document_type_allowed(cls, value: str) -> str:
        return value if value in {"invoice", "receipt", "purchase_order", "unknown"} else "unknown"

    @model_validator(mode="after")
    def confidence_bounds(self):
        if self.overall_confidence is not None and not (0 <= self.overall_confidence <= 1):
            raise ValueError("overall_confidence must be between 0 and 1")
        return self


class ValidationReport(BaseModel):
    schema_valid: bool = True
    date_valid: bool = True
    line_items_valid: bool = True
    line_item_math_valid: bool = True
    subtotal_valid: bool = True
    total_valid: bool = True
    document_identity_consistent: bool = True
    status: str = "validated"
    warnings: list[str] = Field(default_factory=list)
