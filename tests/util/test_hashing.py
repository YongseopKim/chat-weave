"""Tests for hashing utilities."""

import pytest

from chatweave.util.hashing import compute_query_hash


class TestComputeQueryHash:
    """Tests for compute_query_hash function."""

    def test_empty_string(self):
        """Test that empty string returns empty string."""
        assert compute_query_hash("") == ""

    def test_deterministic(self):
        """Test that same input produces same hash."""
        text = "Hello, World!"
        hash1 = compute_query_hash(text)
        hash2 = compute_query_hash(text)
        assert hash1 == hash2

    def test_hash_length(self):
        """Test that hash is 64 characters (SHA256 hex digest)."""
        hash_value = compute_query_hash("test")
        assert len(hash_value) == 64
        assert all(c in "0123456789abcdef" for c in hash_value)

    def test_different_inputs(self):
        """Test that different inputs produce different hashes."""
        hash1 = compute_query_hash("text1")
        hash2 = compute_query_hash("text2")
        assert hash1 != hash2

    def test_case_sensitivity(self):
        """Test that hash is case-sensitive."""
        hash_lower = compute_query_hash("hello")
        hash_upper = compute_query_hash("HELLO")
        assert hash_lower != hash_upper

    def test_whitespace_sensitivity(self):
        """Test that hash is sensitive to whitespace."""
        hash1 = compute_query_hash("hello world")
        hash2 = compute_query_hash("helloworld")
        hash3 = compute_query_hash("hello  world")
        assert hash1 != hash2
        assert hash1 != hash3

    def test_korean_text(self):
        """Test hash with Korean text."""
        text = "안녕하세요"
        hash_value = compute_query_hash(text)
        assert len(hash_value) == 64
        # Same text should produce same hash
        assert hash_value == compute_query_hash(text)

    def test_emoji(self):
        """Test hash with emoji characters."""
        text = "Hello 👋 World 🌍"
        hash_value = compute_query_hash(text)
        assert len(hash_value) == 64
        assert hash_value == compute_query_hash(text)

    def test_multiline_text(self):
        """Test hash with multiline text."""
        text = "Line 1\nLine 2\nLine 3"
        hash_value = compute_query_hash(text)
        assert len(hash_value) == 64
        # Different newline count should produce different hash
        text2 = "Line 1\n\nLine 2\nLine 3"
        assert hash_value != compute_query_hash(text2)

    def test_special_characters(self):
        """Test hash with special characters."""
        text = "Special: @#$%^&*()_+-=[]{}|;:',.<>?/`~"
        hash_value = compute_query_hash(text)
        assert len(hash_value) == 64

    def test_known_hash(self):
        """Test against a known SHA256 hash value."""
        # "hello" in UTF-8 should produce this specific hash
        text = "hello"
        expected_hash = "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
        assert compute_query_hash(text) == expected_hash
