"""Tests for src.preprocessing.clean_text."""

from src.preprocessing import clean_text


def test_lowercases():
    assert clean_text("Great PRODUCT") == "great product"


def test_removes_punctuation():
    assert clean_text("Amazing, love it!") == "amazing love it"


def test_collapses_whitespace():
    assert clean_text("too    many   spaces") == "too many spaces"


def test_strips_leading_and_trailing_space():
    assert clean_text("  padded text  ") == "padded text"


def test_keeps_digits():
    # numbers carry meaning in feedback (e.g. "2 days"), so they must survive
    assert clean_text("Broke after 2 days!") == "broke after 2 days"


def test_already_clean_is_unchanged():
    assert clean_text("simple clean text") == "simple clean text"


def test_empty_string():
    assert clean_text("") == ""


def test_only_punctuation_becomes_empty():
    assert clean_text("!!! ??? ...") == ""
