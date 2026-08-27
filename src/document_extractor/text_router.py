from __future__ import annotations

BUSINESS_KEYWORDS = {"invoice", "receipt", "subtotal", "tax", "total", "amount", "quantity", "qty", "description", "price", "unit", "po", "purchase order", "vendor", "invoice number", "invoice no", "date", "line item"}
INSTRUCTION_KEYWORDS = {"system prompt", "instructions", "routing behavior", "validation", "architecture", "api key", "developer", "project structure", "extract", "model", "prompt", "requirements"}


def choose_route(text: str, threshold: float) -> str:
    if not text or not text.strip():
        return "vision"
    chars = len(text)
    words = len(text.split())
    readable = sum(ch.isprintable() for ch in text) / max(1, len(text))
    keyword_hits = sum(1 for k in BUSINESS_KEYWORDS if k in text.lower())
    score = (min(chars / 500, 1) + min(words / 100, 1) + readable + min(keyword_hits / 5, 1)) / 4
    return "text" if score >= threshold else "vision"


def looks_like_business_document(text: str) -> bool:
    if not text or not text.strip():
        return False
    lower = text.lower()
    business_hits = sum(1 for k in BUSINESS_KEYWORDS if k in lower)
    instruction_hits = sum(1 for k in INSTRUCTION_KEYWORDS if k in lower)
    has_money_like_text = any(token in lower for token in ("$", "₹", "€", "subtotal", "total", "tax", "invoice"))
    return (business_hits >= 2 or has_money_like_text) and instruction_hits < 3
