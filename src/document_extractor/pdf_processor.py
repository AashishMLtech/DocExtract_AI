from __future__ import annotations

import fitz


def inspect_pdf(data: bytes, max_pages: int) -> tuple[list[str], int]:
    doc = fitz.open(stream=data, filetype="pdf")
    total = doc.page_count
    pages = [doc.load_page(i).get_text("text") for i in range(min(total, max_pages))]
    doc.close()
    return pages, total


def render_page(data: bytes, page_number: int, max_edge: int) -> bytes:
    doc = fitz.open(stream=data, filetype="pdf")
    page = doc.load_page(page_number)
    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
    image_bytes = pix.tobytes("png")
    doc.close()
    return image_bytes
