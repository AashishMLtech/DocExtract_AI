from __future__ import annotations

import base64
import json
import logging
import time
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from groq import Groq

from .config import Settings, get_settings
from .error_handlers import UserFacingError
from .image_processor import prepare_image
from .merger import merge_results
from .models import ExtractionResult
from .normalizer import normalize_currency, normalize_date, normalize_money, normalize_null
from .pdf_processor import inspect_pdf, render_page
from .prompts import SYSTEM_PROMPT
from .text_router import choose_route, looks_like_business_document
from .validators import ValidationReport, validate_business_rules

logger = logging.getLogger(__name__)


def _clean_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise UserFacingError("The model returned malformed JSON.") from exc


def _normalize_payload(payload: dict[str, Any]) -> dict[str, Any]:
    for field in ("subtotal", "discount", "shipping_amount", "tax_amount", "total_amount"):
        if field in payload:
            payload[field] = normalize_money(payload[field])
    if "currency" in payload:
        payload["currency"] = normalize_currency(payload["currency"])
    if "date" in payload:
        payload["date"] = normalize_date(payload["date"])
    payload["document_type"] = normalize_null(payload.get("document_type")) or "unknown"
    payload["warnings"] = list(payload.get("warnings") or [])
    cleaned_items: list[dict[str, Any]] = []
    for index, item in enumerate(payload.get("line_items", []) or []):
        if not isinstance(item, dict):
            continue
        for field in ("quantity", "unit_price", "total_price"):
            item[field] = normalize_money(item.get(field))
        if item.get("total_price") is None and item.get("quantity") is not None and item.get("unit_price") is not None:
            item["total_price"] = item["quantity"] * item["unit_price"]
            payload["warnings"].append(
                f"Line item {index + 1} total price was missing and was computed locally from quantity and unit price."
            )
        missing = [field for field in ("description", "quantity", "unit_price", "total_price") if item.get(field) is None]
        if missing:
            payload["warnings"].append(f"Line item {index + 1} was incomplete and was skipped ({', '.join(missing)} missing).")
            continue
        cleaned_items.append(item)
    payload["line_items"] = cleaned_items
    return payload


class GroqExtractor:
    def __init__(self, settings: Settings | None = None, client: Groq | None = None):
        self.settings = settings or get_settings()
        if not self.settings.groq_api_key and client is None:
            raise UserFacingError("GROQ_API_KEY is missing. Add it to .env before processing a document.")
        self.client = client or Groq(api_key=self.settings.groq_api_key, timeout=self.settings.api_timeout_seconds)
        self.retry_count = 0

    def _request(self, messages: list[dict[str, Any]]) -> ExtractionResult:
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.settings.groq_model,
                    messages=[{"role": "system", "content": SYSTEM_PROMPT}, *messages],
                    response_format={"type": "json_object"},
                    reasoning_effort="none",
                    max_completion_tokens=self.settings.max_completion_tokens,
                )
                payload = _normalize_payload(_clean_json(response.choices[0].message.content))
                return ExtractionResult.model_validate(payload)
            except Exception as exc:
                last_error = exc
                logger.exception("Groq extraction request failed on attempt %s", attempt + 1)
                if attempt >= self.settings.max_retries:
                    break
                self.retry_count += 1
                logger.warning("Transient extraction request failed; retry %s", self.retry_count)
        detail = f"{type(last_error).__name__}: {last_error}" if last_error else "unknown error"
        raise UserFacingError(f"Extraction request failed. {detail}") from last_error

    def extract_text(self, text: str) -> ExtractionResult:
        return self._request([{"role": "user", "content": text}])

    def extract_image(self, image_data: bytes) -> ExtractionResult:
        encoded = base64.b64encode(prepare_image(image_data, self.settings.max_image_dimension)).decode("ascii")
        return self._request([
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the document data as JSON."},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded}"}},
                ],
            }
        ])

    def process(self, data: bytes, extension: str) -> tuple[ExtractionResult, ValidationReport, dict[str, Any]]:
        started = time.perf_counter()
        pages: list[ExtractionResult] = []
        vision_pages = 0
        skipped_pages = 0
        native_pages = 0
        extension = extension.lower()
        if extension == ".pdf":
            texts, total_pages = inspect_pdf(data, self.settings.max_pdf_pages)
            if total_pages > self.settings.max_pdf_pages:
                skipped_pages += total_pages - self.settings.max_pdf_pages
            joined_text = "\n".join(texts[: min(len(texts), 3)])
            if not looks_like_business_document(joined_text):
                result = ExtractionResult(
                    warnings=[
                        "The uploaded PDF does not appear to be a business document, so extraction was skipped to avoid unnecessary API usage."
                    ]
                )
                report = validate_business_rules(result, Decimal(str(self.settings.money_tolerance)))
                metadata = {
                    "total_pages": total_pages,
                    "processed_pages": 0,
                    "vision_pages": 0,
                    "native_pages": 0,
                    "skipped_pages": skipped_pages + len(texts),
                    "extraction_mode": "skipped_non_business_document",
                    "duration_seconds": round(time.perf_counter() - started, 2),
                    "retry_count": self.retry_count,
                }
                logger.info("Skipped non-business PDF without calling the model.")
                return result, report, metadata
            for page_number, text in enumerate(texts):
                route = choose_route(text, self.settings.text_quality_threshold)
                if route == "text":
                    native_pages += 1
                    pages.append(self.extract_text(text))
                elif vision_pages < self.settings.max_vision_pages:
                    vision_pages += 1
                    pages.append(self.extract_image(render_page(data, page_number, self.settings.max_image_dimension)))
                else:
                    skipped_pages += 1
        else:
            total_pages = 1
            vision_pages = 1
            pages.append(self.extract_image(data))
        result, merge_warnings = merge_results(pages)
        result.warnings.extend(merge_warnings)
        if skipped_pages:
            result.warnings.append(f"{skipped_pages} page(s) were skipped due to configured processing limits.")
        report = validate_business_rules(result, Decimal(str(self.settings.money_tolerance)))
        metadata = {
            "total_pages": total_pages,
            "processed_pages": len(pages),
            "vision_pages": vision_pages,
            "native_pages": native_pages,
            "skipped_pages": skipped_pages,
            "extraction_mode": "image_vision" if extension != ".pdf" else ("hybrid" if native_pages and vision_pages else "pdf_text" if native_pages else "pdf_vision_fallback"),
            "duration_seconds": round(time.perf_counter() - started, 2),
            "retry_count": self.retry_count,
        }
        logger.info("Processed %s pages via %s in %.2fs", len(pages), metadata["extraction_mode"], metadata["duration_seconds"])
        return result, report, metadata
