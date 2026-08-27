# Architecture

```text
Upload
  |
  v
Input Validation
  |
+-+------------------+
|                    |
Image               PDF
|                    |
v                    v
Prepare image     PyMuPDF text extraction
|                    |
v                    v
Groq vision      Text quality check
|                /               \
v             good                poor
JSON           |                    |
parse          v                    v
|         text route          render page
v                                |
Normalize                         v
|                             Pillow
v                                |
Pydantic                         Groq vision
|                                |
v                                v
Business validation -> Merge -> Final validation -> Streamlit UI
```

The system favors native text extraction first for cost efficiency. Only pages with poor or unusable text are rendered and sent through the vision path. After extraction, all data is normalized, schema-validated, checked with deterministic business rules, merged across pages, and shown in the UI.
