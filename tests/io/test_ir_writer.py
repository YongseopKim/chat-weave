"""Tests for IR writer utilities."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from chatweave.io.ir_writer import (
    write_conversation_ir,
    write_qa_unit_ir,
    write_session_ir,
)
from chatweave.models.conversation import ConversationIR, MessageIR
from chatweave.models.qa_unit import QAUnit, QAUnitIR
from chatweave.models.session import (
    MultiModelSessionIR,
    PerPlatformQARef,
    PromptGroup,
)


class TestWriteConversationIR:
    """Tests for write_conversation_ir function."""

    def test_write_basic_ir(self, tmp_path):
        """Test writing a basic ConversationIR to JSON file."""
        # Create a simple ConversationIR
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="test-123",
            meta={"url": "https://chatgpt.com/c/test-123"},
            messages=[
                MessageIR(
                    id="m0000",
                    index=0,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 0),
                    raw_content="Hello",
                    normalized_content="Hello",
                    query_hash="abc123"
                )
            ]
        )

        # Write to file
        output_path = write_conversation_ir(conversation_ir, tmp_path)

        # Verify file was created
        assert output_path.exists()
        assert output_path.parent == tmp_path

        # Verify filename format
        assert output_path.name == "chatgpt_conv_test-123.json"

        # Verify file contents
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema"] == "conversation-ir/v1"
        assert data["platform"] == "chatgpt"
        assert data["conversation_id"] == "test-123"
        assert len(data["messages"]) == 1
        assert data["messages"][0]["id"] == "m0000"
        assert data["messages"][0]["raw_content"] == "Hello"

    def test_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "path" / "ir"

        conversation_ir = ConversationIR(
            platform="claude",
            conversation_id="abc",
            meta={},
            messages=[]
        )

        output_path = write_conversation_ir(conversation_ir, nested_dir)

        assert output_path.exists()
        assert output_path.parent == nested_dir

    def test_filename_format(self, tmp_path):
        """Test filename format for different platforms and IDs."""
        test_cases = [
            ("chatgpt", "692ad5eb-bb18-8320-bd15-9ae4442dcb26", "chatgpt_conv_692ad5eb-bb18-8320-bd15-9ae4442dcb26.json"),
            ("claude", "43917b24-af4b-48b2-9507-19841ca73e37", "claude_conv_43917b24-af4b-48b2-9507-19841ca73e37.json"),
            ("gemini", "60e8895807bb7c29", "gemini_conv_60e8895807bb7c29.json"),
        ]

        for platform, conv_id, expected_filename in test_cases:
            conversation_ir = ConversationIR(
                platform=platform,
                conversation_id=conv_id,
                meta={},
                messages=[]
            )
            output_path = write_conversation_ir(conversation_ir, tmp_path)
            assert output_path.name == expected_filename

    def test_json_indentation(self, tmp_path):
        """Test that JSON is properly indented."""
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={"url": "test"},
            messages=[
                MessageIR(
                    id="m0000",
                    index=0,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 0),
                    raw_content="Test",
                    normalized_content="Test"
                )
            ]
        )

        output_path = write_conversation_ir(conversation_ir, tmp_path, indent=2)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that JSON is indented (contains newlines and spaces)
        assert "\n" in content
        assert "  " in content

    def test_utf8_encoding(self, tmp_path):
        """Test that UTF-8 content is properly encoded."""
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="korean-test",
            meta={"url": "test"},
            messages=[
                MessageIR(
                    id="m0000",
                    index=0,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 0),
                    raw_content="안녕하세요 👋",
                    normalized_content="안녕하세요 👋"
                )
            ]
        )

        output_path = write_conversation_ir(conversation_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["messages"][0]["raw_content"] == "안녕하세요 👋"

    def test_ensure_ascii_false(self, tmp_path):
        """Test that ensure_ascii=False is used (non-ASCII chars not escaped)."""
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=[
                MessageIR(
                    id="m0000",
                    index=0,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 0),
                    raw_content="안녕",
                    normalized_content="안녕"
                )
            ]
        )

        output_path = write_conversation_ir(conversation_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Korean characters should appear as-is, not as \uXXXX escape sequences
        assert "안녕" in content
        assert "\\u" not in content

    def test_multiple_messages(self, tmp_path):
        """Test writing IR with multiple messages."""
        conversation_ir = ConversationIR(
            platform="claude",
            conversation_id="multi-msg",
            meta={},
            messages=[
                MessageIR(
                    id="m0000",
                    index=0,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 0),
                    raw_content="Question 1",
                    normalized_content="Question 1",
                    query_hash="hash1"
                ),
                MessageIR(
                    id="m0001",
                    index=1,
                    role="assistant",
                    timestamp=datetime(2025, 11, 29, 10, 0, 5),
                    raw_content="Answer 1",
                    normalized_content="Answer 1"
                ),
                MessageIR(
                    id="m0002",
                    index=2,
                    role="user",
                    timestamp=datetime(2025, 11, 29, 10, 0, 10),
                    raw_content="Question 2",
                    normalized_content="Question 2",
                    query_hash="hash2"
                ),
            ]
        )

        output_path = write_conversation_ir(conversation_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        assert data["messages"][2]["role"] == "user"

    def test_duplicate_filename_adds_suffix(self, tmp_path):
        """Test that duplicate filenames get numeric suffix."""
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="same-id",
            meta={},
            messages=[]
        )

        # Write first time
        output_path1 = write_conversation_ir(conversation_ir, tmp_path)
        assert output_path1.name == "chatgpt_conv_same-id.json"

        # Write again - should get _1 suffix
        output_path2 = write_conversation_ir(conversation_ir, tmp_path)
        assert output_path2.name == "chatgpt_conv_same-id_1.json"

        # Write third time - should get _2 suffix
        output_path3 = write_conversation_ir(conversation_ir, tmp_path)
        assert output_path3.name == "chatgpt_conv_same-id_2.json"

        # All files should exist
        assert output_path1.exists()
        assert output_path2.exists()
        assert output_path3.exists()

        # All paths should be different
        assert output_path1 != output_path2 != output_path3


class TestWriteQAUnitIR:
    """Tests for write_qa_unit_ir function."""

    def test_write_basic_qa_ir(self, tmp_path):
        """Test writing a basic QAUnitIR to JSON file."""
        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="test-123",
            qa_units=[
                QAUnit(
                    qa_id="q0000",
                    platform="chatgpt",
                    conversation_id="test-123",
                    user_message_ids=["m0000"],
                    assistant_message_ids=["m0001"],
                    question_from_user="Question 1",
                    question_from_assistant_summary="Summary 1",
                    user_query_hash="hash1"
                )
            ]
        )

        output_path = write_qa_unit_ir(qa_unit_ir, tmp_path)

        assert output_path.exists()
        assert output_path.parent == tmp_path
        assert output_path.name == "chatgpt_qau_test-123.json"

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema"] == "qa-unit-ir/v1"
        assert data["platform"] == "chatgpt"
        assert data["conversation_id"] == "test-123"
        assert len(data["qa_units"]) == 1
        assert data["qa_units"][0]["qa_id"] == "q0000"
        assert data["qa_units"][0]["question_from_user"] == "Question 1"

    def test_qa_ir_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "qa-unit-ir"

        qa_unit_ir = QAUnitIR(
            platform="claude",
            conversation_id="abc",
            qa_units=[]
        )

        output_path = write_qa_unit_ir(qa_unit_ir, nested_dir)

        assert output_path.exists()
        assert output_path.parent == nested_dir

    def test_qa_ir_filename_format(self, tmp_path):
        """Test filename format for different platforms and IDs."""
        test_cases = [
            ("chatgpt", "692ad5eb-bb18-8320-bd15-9ae4442dcb26"),
            ("claude", "43917b24-af4b-48b2-9507-19841ca73e37"),
            ("gemini", "60e8895807bb7c29"),
        ]

        for platform, conv_id in test_cases:
            qa_unit_ir = QAUnitIR(
                platform=platform,
                conversation_id=conv_id,
                qa_units=[]
            )
            output_path = write_qa_unit_ir(qa_unit_ir, tmp_path)
            expected_filename = f"{platform}_qau_{conv_id}.json"
            assert output_path.name == expected_filename

    def test_qa_ir_utf8_encoding(self, tmp_path):
        """Test that UTF-8 content is properly encoded."""
        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="korean-test",
            qa_units=[
                QAUnit(
                    qa_id="q0000",
                    platform="chatgpt",
                    conversation_id="korean-test",
                    user_message_ids=["m0000"],
                    assistant_message_ids=["m0001"],
                    question_from_user="안녕하세요 👋",
                    question_from_assistant_summary="한국어 질문 정리"
                )
            ]
        )

        output_path = write_qa_unit_ir(qa_unit_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["qa_units"][0]["question_from_user"] == "안녕하세요 👋"
        assert data["qa_units"][0]["question_from_assistant_summary"] == "한국어 질문 정리"

    def test_duplicate_filename_adds_suffix(self, tmp_path):
        """Test that duplicate filenames get numeric suffix."""
        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="same-id",
            qa_units=[]
        )

        # Write first time
        output_path1 = write_qa_unit_ir(qa_unit_ir, tmp_path)
        assert output_path1.name == "chatgpt_qau_same-id.json"

        # Write again - should get _1 suffix
        output_path2 = write_qa_unit_ir(qa_unit_ir, tmp_path)
        assert output_path2.name == "chatgpt_qau_same-id_1.json"

        # Write third time - should get _2 suffix
        output_path3 = write_qa_unit_ir(qa_unit_ir, tmp_path)
        assert output_path3.name == "chatgpt_qau_same-id_2.json"

        # All files should exist
        assert output_path1.exists()
        assert output_path2.exists()
        assert output_path3.exists()


class TestWriteSessionIR:
    """Tests for write_session_ir function."""

    def test_write_basic_session_ir(self, tmp_path):
        """Test writing a basic MultiModelSessionIR to JSON file."""
        session_ir = MultiModelSessionIR(
            session_id="test-session",
            platforms=["chatgpt"],
            conversations=[
                {"platform": "chatgpt", "conversation_id": "test-123"}
            ],
            prompts=[
                PromptGroup(
                    prompt_key="p0000",
                    canonical_prompt={
                        "text": "Question 1",
                        "language": None,
                        "source": {"platform": "chatgpt", "qa_id": "q0000"},
                    },
                    per_platform=[
                        PerPlatformQARef(
                            platform="chatgpt",
                            qa_id="q0000",
                            conversation_id="test-123",
                            prompt_similarity=1.0,
                        )
                    ],
                )
            ],
        )

        output_path = write_session_ir(session_ir, tmp_path)

        assert output_path.exists()
        assert output_path.parent == tmp_path
        assert output_path.name == "mms_test-session.json"

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema"] == "multi-model-session-ir/v1"
        assert data["session_id"] == "test-session"
        assert data["platforms"] == ["chatgpt"]
        assert len(data["conversations"]) == 1
        assert len(data["prompts"]) == 1
        assert data["prompts"][0]["prompt_key"] == "p0000"

    def test_session_ir_directory_creation(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        nested_dir = tmp_path / "nested" / "session-ir"

        session_ir = MultiModelSessionIR(
            session_id="test",
            platforms=[],
            conversations=[],
            prompts=[],
        )

        output_path = write_session_ir(session_ir, nested_dir)

        assert output_path.exists()
        assert output_path.parent == nested_dir

    def test_session_ir_filename_format(self, tmp_path):
        """Test filename format for session IR."""
        test_cases = [
            "sample-session",
            "multi-platform-test",
            "2025-11-30-topic",
        ]

        for session_id in test_cases:
            session_ir = MultiModelSessionIR(
                session_id=session_id,
                platforms=[],
                conversations=[],
                prompts=[],
            )
            output_path = write_session_ir(session_ir, tmp_path)
            expected_filename = f"mms_{session_id}.json"
            assert output_path.name == expected_filename

    def test_session_ir_utf8_encoding(self, tmp_path):
        """Test that UTF-8 content is properly encoded."""
        session_ir = MultiModelSessionIR(
            session_id="korean-session",
            platforms=["chatgpt"],
            conversations=[
                {"platform": "chatgpt", "conversation_id": "test"}
            ],
            prompts=[
                PromptGroup(
                    prompt_key="p0000",
                    canonical_prompt={
                        "text": "안녕하세요 👋",
                        "language": None,
                        "source": {"platform": "chatgpt", "qa_id": "q0000"},
                    },
                )
            ],
        )

        output_path = write_session_ir(session_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["prompts"][0]["canonical_prompt"]["text"] == "안녕하세요 👋"

    def test_session_ir_multi_platform(self, tmp_path):
        """Test writing session IR with multiple platforms."""
        session_ir = MultiModelSessionIR(
            session_id="multi-platform",
            platforms=["chatgpt", "claude", "gemini"],
            conversations=[
                {"platform": "chatgpt", "conversation_id": "chat-1"},
                {"platform": "claude", "conversation_id": "claude-1"},
                {"platform": "gemini", "conversation_id": "gemini-1"},
            ],
            prompts=[
                PromptGroup(
                    prompt_key="p0000",
                    canonical_prompt={
                        "text": "Aligned question",
                        "language": None,
                        "source": {"platform": "chatgpt", "qa_id": "q0000"},
                    },
                    per_platform=[
                        PerPlatformQARef(
                            platform="chatgpt",
                            qa_id="q0000",
                            conversation_id="chat-1",
                            prompt_similarity=1.0,
                        ),
                        PerPlatformQARef(
                            platform="claude",
                            qa_id="q0000",
                            conversation_id="claude-1",
                            prompt_similarity=1.0,
                        ),
                        PerPlatformQARef(
                            platform="gemini",
                            qa_id="q0000",
                            conversation_id="gemini-1",
                            prompt_similarity=1.0,
                        ),
                    ],
                )
            ],
        )

        output_path = write_session_ir(session_ir, tmp_path)

        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert len(data["platforms"]) == 3
        assert len(data["conversations"]) == 3
        assert len(data["prompts"][0]["per_platform"]) == 3

    def test_duplicate_filename_adds_suffix(self, tmp_path):
        """Test that duplicate filenames get numeric suffix."""
        session_ir = MultiModelSessionIR(
            session_id="same-session",
            platforms=[],
            conversations=[],
            prompts=[],
        )

        # Write first time
        output_path1 = write_session_ir(session_ir, tmp_path)
        assert output_path1.name == "mms_same-session.json"

        # Write again - should get _1 suffix
        output_path2 = write_session_ir(session_ir, tmp_path)
        assert output_path2.name == "mms_same-session_1.json"

        # Write third time - should get _2 suffix
        output_path3 = write_session_ir(session_ir, tmp_path)
        assert output_path3.name == "mms_same-session_2.json"

        # All files should exist
        assert output_path1.exists()
        assert output_path2.exists()
        assert output_path3.exists()
