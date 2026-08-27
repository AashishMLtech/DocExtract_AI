from __future__ import annotations

import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

NULL_LIKE = {"", "none", "null", "n/a", "na", "-", "--"}


def normalize_null(value):
    if value is None:
        return None
    if isinstance(value, str) and value.strip().lower() in NULL_LIKE:
        return None
    return value


def normalize_currency(value):
    value = normalize_null(value)
    if value is None:
        return None
    s = str(value).strip().upper()
    mapping = {"$": "USD", "US$": "USD", "EUR": "EUR", "₹": "INR", "INR": "INR", "GBP": "GBP"}
    return mapping.get(s, s[:3]) if len(s) > 1 else mapping.get(s, s)


def normalize_money(value):
    value = normalize_null(value)
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    s = re.sub(r"[^\d,.\-]", "", str(value).strip())
    if not s:
        return None
    if "," in s and "." not in s:
        s = s.replace(",", ".") if s.count(",") == 1 and len(s.split(",")[-1]) <= 2 else s.replace(",", "")
    elif "," in s and "." in s:
        s = s.replace(",", "")
    try:
        return Decimal(s).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def normalize_date(value):
    value = normalize_null(value)
    if value is None:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%b %d, %Y", "%d %b %Y", "%B %d, %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            pass
    return None
