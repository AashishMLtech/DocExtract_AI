import pytest

from document_extractor.image_processor import prepare_image


def test_invalid_image_handling():
    with pytest.raises(Exception):
        prepare_image(b"not-an-image", 1024)
