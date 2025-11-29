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


@pytest.fixture
def sample_conversation_ir(chatgpt_jsonl):
    """Parse ChatGPT JSONL into ConversationIR."""
    from chatweave.parsers.unified import UnifiedParser
    parser = UnifiedParser()
    return parser.parse(chatgpt_jsonl)


@pytest.fixture
def sample_qa_unit_ir(sample_conversation_ir):
    """Build QAUnitIR from sample ConversationIR."""
    from chatweave.pipeline.build_qa_ir import build_qa_ir
    return build_qa_ir(sample_conversation_ir)


@pytest.fixture
def sample_multi_qa_unit_ir(chatgpt_jsonl, claude_jsonl, gemini_jsonl):
    """Build QAUnitIR from all three platforms."""
    from chatweave.parsers.unified import UnifiedParser
    from chatweave.pipeline.build_qa_ir import build_qa_ir

    parser = UnifiedParser()
    qa_units = {}

    for jsonl_path in [chatgpt_jsonl, claude_jsonl, gemini_jsonl]:
        conversation_ir = parser.parse(jsonl_path)
        qa_ir = build_qa_ir(conversation_ir)
        qa_units[qa_ir.platform] = qa_ir

    return qa_units


@pytest.fixture
def sample_session_ir(sample_multi_qa_unit_ir):
    """Build MultiModelSessionIR from sample data."""
    from chatweave.pipeline.build_session_ir import build_session_ir
    return build_session_ir(sample_multi_qa_unit_ir, "sample-session")
