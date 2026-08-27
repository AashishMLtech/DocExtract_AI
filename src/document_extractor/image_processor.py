from __future__ import annotations

import io
from PIL import Image, ImageOps


def prepare_image(image_bytes: bytes, max_edge: int) -> bytes:
    with Image.open(io.BytesIO(image_bytes)) as image:
        image = ImageOps.exif_transpose(image).convert("RGB")
        image.thumbnail((max_edge, max_edge))
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", optimize=True, quality=85)
        return buffer.getvalue()
