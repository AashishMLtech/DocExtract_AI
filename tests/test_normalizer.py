from document_extractor.normalizer import normalize_date, normalize_money


def test_money_normalization():
    assert str(normalize_money("$1,250.50")) == "1250.50"


def test_date_normalization():
    assert normalize_date("27/08/2026") == "2026-08-27"
