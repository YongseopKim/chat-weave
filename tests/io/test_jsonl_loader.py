"""Tests for JSONL loader utilities."""

import json
from pathlib import Path

import pytest

from chatweave.io.jsonl_loader import load_jsonl


class TestLoadJsonl:
    """Tests for load_jsonl function."""

    def test_valid_jsonl(self, tmp_path):
        """Test loading valid JSONL file."""
        jsonl_file = tmp_path / "test.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt", "url": "https://chatgpt.com/c/123", "exported_at": "2025-11-29T10:00:00Z"}\n')
            f.write('{"role": "user", "content": "Hello", "timestamp": "2025-11-29T10:00:05Z"}\n')
            f.write('{"role": "assistant", "content": "Hi there!", "timestamp": "2025-11-29T10:00:10Z"}\n')

        metadata, messages = load_jsonl(jsonl_file)

        assert metadata["platform"] == "chatgpt"
        assert metadata["url"] == "https://chatgpt.com/c/123"
        assert "_meta" not in metadata  # _meta flag should be removed

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there!"

    def test_file_not_found(self):
        """Test that FileNotFoundError is raised for non-existent file."""
        non_existent = Path("/non/existent/file.jsonl")
        with pytest.raises(FileNotFoundError, match="JSONL file not found"):
            load_jsonl(non_existent)

    def test_missing_metadata(self, tmp_path):
        """Test that ValueError is raised when first line is not metadata."""
        jsonl_file = tmp_path / "no_meta.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"role": "user", "content": "Hello"}\n')

        with pytest.raises(ValueError, match="must be metadata"):
            load_jsonl(jsonl_file)

    def test_invalid_json(self, tmp_path):
        """Test that JSONDecodeError is raised for invalid JSON."""
        jsonl_file = tmp_path / "invalid.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt"}\n')
            f.write('not valid json\n')

        with pytest.raises(json.JSONDecodeError):
            load_jsonl(jsonl_file)

    def test_missing_role_in_message(self, tmp_path):
        """Test that ValueError is raised when message lacks 'role' field."""
        jsonl_file = tmp_path / "no_role.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt"}\n')
            f.write('{"content": "Hello", "timestamp": "2025-11-29T10:00:00Z"}\n')

        with pytest.raises(ValueError, match="missing 'role' or 'content'"):
            load_jsonl(jsonl_file)

    def test_missing_content_in_message(self, tmp_path):
        """Test that ValueError is raised when message lacks 'content' field."""
        jsonl_file = tmp_path / "no_content.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt"}\n')
            f.write('{"role": "user", "timestamp": "2025-11-29T10:00:00Z"}\n')

        with pytest.raises(ValueError, match="missing 'role' or 'content'"):
            load_jsonl(jsonl_file)

    def test_empty_lines_ignored(self, tmp_path):
        """Test that empty lines are ignored."""
        jsonl_file = tmp_path / "with_empty.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt"}\n')
            f.write('\n')
            f.write('{"role": "user", "content": "Hello"}\n')
            f.write('  \n')
            f.write('{"role": "assistant", "content": "Hi"}\n')

        metadata, messages = load_jsonl(jsonl_file)

        assert len(messages) == 2
        assert messages[0]["content"] == "Hello"
        assert messages[1]["content"] == "Hi"

    def test_empty_file(self, tmp_path):
        """Test that empty file raises ValueError for missing metadata."""
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.touch()

        with pytest.raises(ValueError, match="No metadata found"):
            load_jsonl(jsonl_file)

    def test_metadata_only(self, tmp_path):
        """Test that file with only metadata is valid."""
        jsonl_file = tmp_path / "meta_only.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt", "url": "https://chatgpt.com"}\n')

        metadata, messages = load_jsonl(jsonl_file)

        assert metadata["platform"] == "chatgpt"
        assert len(messages) == 0

    def test_utf8_encoding(self, tmp_path):
        """Test that UTF-8 encoding is handled correctly."""
        jsonl_file = tmp_path / "utf8.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt"}\n')
            f.write('{"role": "user", "content": "안녕하세요 👋"}\n')

        metadata, messages = load_jsonl(jsonl_file)

        assert messages[0]["content"] == "안녕하세요 👋"

    def test_extra_metadata_fields(self, tmp_path):
        """Test that extra metadata fields are preserved."""
        jsonl_file = tmp_path / "extra_fields.jsonl"
        with open(jsonl_file, "w", encoding="utf-8") as f:
            f.write('{"_meta": true, "platform": "chatgpt", "custom_field": "value", "number": 42}\n')

        metadata, messages = load_jsonl(jsonl_file)

        assert metadata["custom_field"] == "value"
        assert metadata["number"] == 42
