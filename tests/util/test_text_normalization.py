"""Tests for text normalization utilities."""

import pytest

from chatweave.util.text_normalization import normalize_text


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_empty_string(self):
        """Test that empty string is returned as-is."""
        assert normalize_text("") == ""

    def test_none_value(self):
        """Test that None is returned as-is."""
        assert normalize_text(None) is None

    def test_single_space(self):
        """Test that single spaces are preserved."""
        assert normalize_text("a b c") == "a b c"

    def test_multiple_spaces(self):
        """Test that multiple consecutive spaces are collapsed to single space."""
        assert normalize_text("a  b") == "a b"
        assert normalize_text("a   b   c") == "a b c"
        assert normalize_text("hello     world") == "hello world"

    def test_single_newline(self):
        """Test that single newlines are preserved."""
        text = "line1\nline2"
        assert normalize_text(text) == "line1\nline2"

    def test_double_newline(self):
        """Test that double newlines are preserved."""
        text = "para1\n\npara2"
        assert normalize_text(text) == "para1\n\npara2"

    def test_multiple_newlines(self):
        """Test that multiple consecutive newlines are collapsed to double newline."""
        assert normalize_text("a\n\n\nb") == "a\n\nb"
        assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is removed."""
        assert normalize_text("  hello  ") == "hello"
        assert normalize_text("\n\nhello\n\n") == "hello"
        assert normalize_text("  hello world  ") == "hello world"

    def test_unicode_normalization(self):
        """Test that Unicode is normalized to NFC form."""
        # Combining characters (NFD) should be normalized to precomposed (NFC)
        # Example: "é" can be represented as single char (U+00E9) or as "e" + combining acute (U+0065 U+0301)
        nfd = "e\u0301"  # NFD form (decomposed)
        nfc = "\u00e9"  # NFC form (precomposed)
        assert normalize_text(nfd) == nfc

    def test_korean_text(self):
        """Test normalization with Korean text."""
        text = "안녕하세요    세계"
        assert normalize_text(text) == "안녕하세요 세계"

    def test_mixed_whitespace(self):
        """Test text with mixed spaces and newlines."""
        text = "  hello   world  \n\n\n  next paragraph  "
        # Note: normalize_text only strips leading/trailing whitespace from entire text,
        # not from individual lines after newlines
        expected = "hello world \n\n next paragraph"
        assert normalize_text(text) == expected

    def test_real_world_example(self):
        """Test with realistic conversation text."""
        text = """
        RWA 토큰화에 대해   설명해줘


        자세히   부탁해
        """
        # Note: normalize_text only strips leading/trailing whitespace from entire text
        expected = "RWA 토큰화에 대해 설명해줘\n\n 자세히 부탁해"
        assert normalize_text(text) == expected
