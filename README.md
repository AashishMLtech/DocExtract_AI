# Document Data Extractor

## What It Does
Document Data Extractor turns messy business documents into clean, validated JSON. It supports invoices, receipts, and purchase orders in PDF and image form, then checks the output locally so the result is trustworthy before download or review.

## Features
- Hybrid PDF routing that prefers native text extraction and falls back to vision only when needed
- Deterministic normalization for dates, money, and null-like values
- Pydantic v2 schema validation with business-rule checks
- Multi-page merging with duplicate prevention and conflict warnings
- Streamlit interface with downloadable JSON output

## Architecture
See [`docs/architecture.md`](docs/architecture.md).

## How The Hybrid Pipeline Works
PDF pages are inspected with PyMuPDF first. If the extracted text is sufficiently usable, the page follows the text route. If the text is empty, fragmented, or low quality, the page is rendered and sent to Groq as a single-page vision request. Results are normalized, validated, and merged into a final document-level JSON object.

## Project Structure
- `src/document_extractor/` contains the application code
- `tests/` contains pytest coverage for validation and routing logic
- `samples/` contains example input documents
- `expected_outputs/` contains reference JSON outputs for the sample files

## Where To Make Changes
- Change the LLM/model: `src/document_extractor/extractor.py`, `src/document_extractor/prompts.py`, `.env`
- Change the schema: `src/document_extractor/models.py`
- Change financial checks: `src/document_extractor/validators.py`
- Change PDF handling: `src/document_extractor/pdf_processor.py`
- Change image preprocessing: `src/document_extractor/image_processor.py`
- Change text-vs-vision routing: `src/document_extractor/text_router.py`
- Change normalization: `src/document_extractor/normalizer.py`
- Change multi-page merging: `src/document_extractor/merger.py`
- Change the Streamlit UI: `src/document_extractor/app.py`
- Change configuration: `.env`, `src/document_extractor/config.py`
- Change prompts: `src/document_extractor/prompts.py`
- Add or update tests: `tests/`

## Tech Stack
Python 3.11+, Groq SDK, PyMuPDF, Pillow, Pydantic v2, python-dotenv, Streamlit, and pytest.

## Requirements
You need Python 3.11+ and a valid Groq API key.

## Setup & Installation
Windows:
```bash
git clone <YOUR_REPOSITORY_URL>
cd document-data-extractor
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

macOS/Linux:
```bash
git clone <YOUR_REPOSITORY_URL>
cd document-data-extractor
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Environment Variables
Set `GROQ_API_KEY` in `.env`, and optionally adjust the page limits, retry count, token limit, image size, and text-quality threshold to fit your workflow.

## How To Run
```bash
streamlit run src/document_extractor/app.py
```

## How To Test
```bash
pytest
```

## Sample Documents
The repository includes example layouts for:
- invoice
- receipt
- purchase order

Recommended sample files for testing:
- `docustruct_polished_invoice_test.pdf`
- `docustruct_purchase_order_layout_c.txt`

Reference/documentation PDF used during development:
- `Advanced Document Data Extractor.pdf`

## Expected Output
Each sample document has a matching JSON file in `expected_outputs/`. These files are intended to reflect the finished application’s output for the bundled sample documents.

## Validation Logic
Dates are normalized only when they are unambiguous. Monetary values use `Decimal` so arithmetic stays precise. Line items are validated with local math checks, and subtotal or grand-total reconciliation only runs when enough fields are available to make the check meaningful.

## Multi-Page Processing
Documents are processed within configured page budgets. Mixed PDFs can use text on some pages and vision on others. Any skipped pages are reported clearly so partial extraction is not mistaken for a complete result.

## Free-Tier Optimization
Native text is preferred whenever it is usable. Vision is applied one page at a time only when necessary. Retries are bounded, reasoning is disabled, and arithmetic/normalization are handled locally to keep API usage efficient.

## Error Handling
The app handles invalid uploads, missing API keys, malformed JSON, corrupted documents, and validation failures with user-safe messages instead of raw tracebacks.

## Known Failure Cases
Very low-resolution scans, severe blur, handwritten content, unusual table layouts, ambiguous dates, and API interruptions can still reduce extraction quality. The system is designed to be honest about those limits rather than guess.

## Tradeoffs & Future Improvements
This implementation favors reliability, validation, and cost control over maximum inference complexity. Future improvements could include OCR fallback, field-level confidence, batch processing, or API-backed workflows.

## Limitations
The project does not claim perfect accuracy and never invents missing values to force a complete schema.

## Deployment
For hosted deployments, store `GROQ_API_KEY` in the platform’s secret manager or environment settings. Do not commit credentials to the repository.
