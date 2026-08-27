from document_extractor.text_router import choose_route


def test_good_text_route():
    assert choose_route("Invoice subtotal total tax qty", 0.1) == "text"


def test_poor_text_route():
    assert choose_route("x x x", 0.9) == "vision"
