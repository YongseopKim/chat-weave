"""Pytest configuration and fixtures."""

from pathlib import Path

import pytest


@pytest.fixture
def sample_session_dir():
    """Path to sample session directory with JSONL files."""
    return Path(__file__).parent.parent / "examples" / "sample-session"


@pytest.fixture
def chatgpt_jsonl(sample_session_dir):
    """Path to ChatGPT JSONL file."""
    return sample_session_dir / "chatgpt_20251129T114242.jsonl"


@pytest.fixture
def claude_jsonl(sample_session_dir):
    """Path to Claude JSONL file."""
    return sample_session_dir / "claude_20251129T114247.jsonl"


@pytest.fixture
def gemini_jsonl(sample_session_dir):
    """Path to Gemini JSONL file."""
    return sample_session_dir / "gemini_20251129T114250.jsonl"


@pytest.fixture
def temp_output_dir(tmp_path):
    """Temporary directory for test output."""
    output_dir = tmp_path / "ir"
    output_dir.mkdir()
    return output_dir
