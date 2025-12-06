"""Tests for platform inference module."""

from pathlib import Path

import pytest

from chatweave.util.platform_inference import infer_platform, infer_platform_from_filename


class TestInferPlatformFromFilename:
    """Test cases for filename-based platform inference."""

    def test_chatgpt_pattern_underscore(self):
        """Should match chatgpt_* pattern."""
        assert infer_platform_from_filename("chatgpt_20251129T114242.jsonl") == "chatgpt"

    def test_chatgpt_pattern_hyphen(self):
        """Should match chatgpt-* pattern."""
        assert infer_platform_from_filename("chatgpt-export.jsonl") == "chatgpt"

    def test_chatgpt_pattern_case_insensitive(self):
        """Should match ChatGPT_* (case insensitive)."""
        assert infer_platform_from_filename("ChatGPT_export.jsonl") == "chatgpt"

    def test_claude_pattern_underscore(self):
        """Should match claude_* pattern."""
        assert infer_platform_from_filename("claude_20251129T114247.jsonl") == "claude"

    def test_claude_pattern_hyphen(self):
        """Should match claude-* pattern."""
        assert infer_platform_from_filename("claude-export.jsonl") == "claude"

    def test_gemini_pattern_underscore(self):
        """Should match gemini_* pattern."""
        assert infer_platform_from_filename("gemini_20251129T114250.jsonl") == "gemini"

    def test_gemini_pattern_hyphen(self):
        """Should match gemini-* pattern."""
        assert infer_platform_from_filename("gemini-export.jsonl") == "gemini"

    def test_grok_pattern_underscore(self):
        """Should match grok_* pattern."""
        assert infer_platform_from_filename("grok_20251206T133524.jsonl") == "grok"

    def test_grok_pattern_hyphen(self):
        """Should match grok-* pattern."""
        assert infer_platform_from_filename("grok-export.jsonl") == "grok"

    def test_no_match_returns_none(self):
        """Should return None for unknown filename."""
        assert infer_platform_from_filename("unknown.jsonl") is None
        assert infer_platform_from_filename("export.jsonl") is None
        assert infer_platform_from_filename("chatgpt.jsonl") is None  # No separator


class TestInferPlatform:
    """Test cases for platform inference with priority."""

    def test_override_takes_highest_priority(self):
        """Override should take priority over metadata and filename."""
        path = Path("chatgpt_export.jsonl")
        metadata = {"platform": "gemini"}
        result = infer_platform(path, metadata=metadata, override="claude")
        assert result == "claude"

    def test_metadata_takes_priority_over_filename(self):
        """Metadata should take priority over filename."""
        path = Path("chatgpt_export.jsonl")
        metadata = {"platform": "claude"}
        result = infer_platform(path, metadata=metadata)
        assert result == "claude"

    def test_filename_used_when_no_metadata(self):
        """Filename should be used when metadata is not available."""
        path = Path("chatgpt_export.jsonl")
        result = infer_platform(path)
        assert result == "chatgpt"

    def test_filename_used_when_metadata_empty(self):
        """Filename should be used when metadata has no platform."""
        path = Path("claude_export.jsonl")
        metadata = {"url": "https://example.com"}
        result = infer_platform(path, metadata=metadata)
        assert result == "claude"

    def test_metadata_with_invalid_platform_uses_filename(self):
        """Should fall back to filename if metadata platform is invalid."""
        path = Path("gemini_export.jsonl")
        metadata = {"platform": "invalid"}
        result = infer_platform(path, metadata=metadata)
        assert result == "gemini"

    def test_cannot_infer_raises_error(self):
        """Should raise ValueError when platform cannot be inferred."""
        path = Path("unknown.jsonl")
        with pytest.raises(ValueError) as exc_info:
            infer_platform(path)
        assert "Cannot infer platform" in str(exc_info.value)
        assert "unknown.jsonl" in str(exc_info.value)
        assert "--platform" in str(exc_info.value)

    def test_cannot_infer_with_empty_metadata_raises_error(self):
        """Should raise ValueError when metadata is empty and filename doesn't match."""
        path = Path("export.jsonl")
        metadata = {}
        with pytest.raises(ValueError) as exc_info:
            infer_platform(path, metadata=metadata)
        assert "Cannot infer platform" in str(exc_info.value)

    def test_all_three_sources_override_wins(self):
        """When all three sources exist, override should win."""
        path = Path("chatgpt_export.jsonl")
        metadata = {"platform": "claude"}
        result = infer_platform(path, metadata=metadata, override="gemini")
        assert result == "gemini"

    def test_metadata_chatgpt(self):
        """Should use metadata platform for chatgpt."""
        path = Path("unknown.jsonl")
        metadata = {"platform": "chatgpt"}
        result = infer_platform(path, metadata=metadata)
        assert result == "chatgpt"

    def test_metadata_claude(self):
        """Should use metadata platform for claude."""
        path = Path("unknown.jsonl")
        metadata = {"platform": "claude"}
        result = infer_platform(path, metadata=metadata)
        assert result == "claude"

    def test_metadata_gemini(self):
        """Should use metadata platform for gemini."""
        path = Path("unknown.jsonl")
        metadata = {"platform": "gemini"}
        result = infer_platform(path, metadata=metadata)
        assert result == "gemini"

    def test_metadata_grok(self):
        """Should use metadata platform for grok."""
        path = Path("unknown.jsonl")
        metadata = {"platform": "grok"}
        result = infer_platform(path, metadata=metadata)
        assert result == "grok"
