from src.scraper.utils import clean_text, safe_int


def test_clean_text_collapses_spaces():
    assert clean_text("  hello   world \n") == "hello world"


def test_safe_int_parses_numbers_with_commas():
    assert safe_int("1,234") == 1234
    assert safe_int("9.876") == 9876
    assert safe_int(None) is None
