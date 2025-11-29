"""Tests for IR writer utilities."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from chatweave.io.ir_writer import write_conversation_ir, write_qa_unit_ir
from chatweave.models.conversation import ConversationIR, MessageIR
from chatweave.models.qa_unit import QAUnit, QAUnitIR


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
        assert output_path.name == "chatgpt_test-123.json"

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
            ("chatgpt", "692ad5eb-bb18-8320-bd15-9ae4442dcb26", "chatgpt_692ad5eb-bb18-8320-bd15-9ae4442dcb26.json"),
            ("claude", "43917b24-af4b-48b2-9507-19841ca73e37", "claude_43917b24-af4b-48b2-9507-19841ca73e37.json"),
            ("gemini", "60e8895807bb7c29", "gemini_60e8895807bb7c29.json"),
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

    def test_overwrite_existing_file(self, tmp_path):
        """Test that existing file is overwritten."""
        conversation_ir = ConversationIR(
            platform="chatgpt",
            conversation_id="same-id",
            meta={},
            messages=[]
        )

        # Write first time
        output_path1 = write_conversation_ir(conversation_ir, tmp_path)
        with open(output_path1, "r", encoding="utf-8") as f:
            data1 = json.load(f)
        assert len(data1["messages"]) == 0

        # Update and write again
        conversation_ir.messages.append(
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=datetime(2025, 11, 29, 10, 0, 0),
                raw_content="New message",
                normalized_content="New message"
            )
        )
        output_path2 = write_conversation_ir(conversation_ir, tmp_path)

        # Should be same path
        assert output_path1 == output_path2

        # Content should be updated
        with open(output_path2, "r", encoding="utf-8") as f:
            data2 = json.load(f)
        assert len(data2["messages"]) == 1


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
        assert output_path.name == "chatgpt_test-123.json"

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
            expected_filename = f"{platform}_{conv_id}.json"
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
