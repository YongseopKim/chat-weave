"""Tests for QA unit data models."""

import pytest

from chatweave.models.qa_unit import QAUnit, QAUnitIR


class TestQAUnit:
    """Tests for QAUnit dataclass."""

    def test_create_qa_unit(self):
        """Test creating a QAUnit instance."""
        qa_unit = QAUnit(
            qa_id="q0000",
            platform="chatgpt",
            conversation_id="test-123",
            user_message_ids=["m0000"],
            assistant_message_ids=["m0001"],
            question_from_user="What is RWA?",
            question_from_assistant_summary="질문: RWA 토큰화란?",
            user_query_hash="abc123"
        )

        assert qa_unit.qa_id == "q0000"
        assert qa_unit.platform == "chatgpt"
        assert qa_unit.conversation_id == "test-123"
        assert qa_unit.user_message_ids == ["m0000"]
        assert qa_unit.assistant_message_ids == ["m0001"]
        assert qa_unit.question_from_user == "What is RWA?"
        assert qa_unit.question_from_assistant_summary == "질문: RWA 토큰화란?"
        assert qa_unit.user_query_hash == "abc123"

    def test_qa_unit_defaults(self):
        """Test QAUnit default values."""
        qa_unit = QAUnit(
            qa_id="q0001",
            platform="claude",
            conversation_id="test-456",
            user_message_ids=["m0002"],
            assistant_message_ids=["m0003"]
        )

        assert qa_unit.question_from_user is None
        assert qa_unit.question_from_assistant_summary is None
        assert qa_unit.user_query_hash is None
        assert qa_unit.meta == {}

    def test_qa_unit_to_dict(self):
        """Test QAUnit.to_dict() serialization."""
        qa_unit = QAUnit(
            qa_id="q0002",
            platform="gemini",
            conversation_id="xyz-789",
            user_message_ids=["m0004", "m0005"],
            assistant_message_ids=["m0006"],
            question_from_user="Multiple user messages",
            question_from_assistant_summary="Summary",
            user_query_hash="hash456",
            meta={"custom": "value"}
        )

        result = qa_unit.to_dict()

        assert result["qa_id"] == "q0002"
        assert result["platform"] == "gemini"
        assert result["conversation_id"] == "xyz-789"
        assert result["user_message_ids"] == ["m0004", "m0005"]
        assert result["assistant_message_ids"] == ["m0006"]
        assert result["question_from_user"] == "Multiple user messages"
        assert result["question_from_assistant_summary"] == "Summary"
        assert result["user_query_hash"] == "hash456"
        assert result["meta"] == {"custom": "value"}

    def test_qa_unit_with_multiple_messages(self):
        """Test QAUnit with multiple user/assistant messages."""
        qa_unit = QAUnit(
            qa_id="q0003",
            platform="chatgpt",
            conversation_id="test",
            user_message_ids=["m0000", "m0001", "m0002"],
            assistant_message_ids=["m0003", "m0004"]
        )

        assert len(qa_unit.user_message_ids) == 3
        assert len(qa_unit.assistant_message_ids) == 2

        result = qa_unit.to_dict()
        assert len(result["user_message_ids"]) == 3
        assert len(result["assistant_message_ids"]) == 2

    def test_qa_unit_empty_content(self):
        """Test QAUnit with empty content (Claude edge case)."""
        qa_unit = QAUnit(
            qa_id="q0004",
            platform="claude",
            conversation_id="test",
            user_message_ids=["m0000"],
            assistant_message_ids=["m0001"],
            question_from_user="",  # Empty
            question_from_assistant_summary=None  # None for Claude
        )

        result = qa_unit.to_dict()
        assert result["question_from_user"] == ""
        assert result["question_from_assistant_summary"] is None

    def test_platform_types(self):
        """Test different platform types."""
        for platform in ["chatgpt", "claude", "gemini"]:
            qa_unit = QAUnit(
                qa_id="q0000",
                platform=platform,
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"]
            )
            assert qa_unit.platform == platform
            result = qa_unit.to_dict()
            assert result["platform"] == platform


class TestQAUnitIR:
    """Tests for QAUnitIR dataclass."""

    def test_create_qa_unit_ir(self):
        """Test creating a QAUnitIR instance."""
        qa_units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test-123",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                question_from_user="Question 1",
                user_query_hash="hash1"
            ),
            QAUnit(
                qa_id="q0001",
                platform="chatgpt",
                conversation_id="test-123",
                user_message_ids=["m0002"],
                assistant_message_ids=["m0003"],
                question_from_user="Question 2",
                user_query_hash="hash2"
            )
        ]

        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="test-123",
            qa_units=qa_units
        )

        assert qa_unit_ir.platform == "chatgpt"
        assert qa_unit_ir.conversation_id == "test-123"
        assert len(qa_unit_ir.qa_units) == 2
        assert qa_unit_ir.qa_units[0].qa_id == "q0000"
        assert qa_unit_ir.qa_units[1].qa_id == "q0001"

    def test_qa_unit_ir_default_schema(self):
        """Test QAUnitIR default schema value."""
        qa_unit_ir = QAUnitIR(
            platform="claude",
            conversation_id="abc",
            qa_units=[]
        )

        assert qa_unit_ir.schema == "qa-unit-ir/v1"

    def test_qa_unit_ir_to_dict(self):
        """Test QAUnitIR.to_dict() serialization."""
        qa_units = [
            QAUnit(
                qa_id="q0000",
                platform="gemini",
                conversation_id="xyz-789",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"]
            )
        ]

        qa_unit_ir = QAUnitIR(
            platform="gemini",
            conversation_id="xyz-789",
            qa_units=qa_units
        )

        result = qa_unit_ir.to_dict()

        assert result["schema"] == "qa-unit-ir/v1"
        assert result["platform"] == "gemini"
        assert result["conversation_id"] == "xyz-789"
        assert len(result["qa_units"]) == 1
        assert isinstance(result["qa_units"][0], dict)
        assert result["qa_units"][0]["qa_id"] == "q0000"

    def test_qa_units_serialized_as_dicts(self):
        """Test that QA units are converted to dictionaries in to_dict()."""
        qa_units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"]
            ),
            QAUnit(
                qa_id="q0001",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0002"],
                assistant_message_ids=["m0003"]
            )
        ]

        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="test",
            qa_units=qa_units
        )

        result = qa_unit_ir.to_dict()

        # All QA units should be dicts
        assert all(isinstance(qa, dict) for qa in result["qa_units"])
        assert result["qa_units"][0]["qa_id"] == "q0000"
        assert result["qa_units"][1]["qa_id"] == "q0001"

    def test_qa_unit_ir_empty_units(self):
        """Test QAUnitIR with no QA units."""
        qa_unit_ir = QAUnitIR(
            platform="chatgpt",
            conversation_id="empty",
            qa_units=[]
        )

        result = qa_unit_ir.to_dict()
        assert result["qa_units"] == []

    def test_qa_unit_ir_platform_types(self):
        """Test QAUnitIR with different platform types."""
        for platform in ["chatgpt", "claude", "gemini"]:
            qa_unit_ir = QAUnitIR(
                platform=platform,
                conversation_id="test",
                qa_units=[]
            )
            assert qa_unit_ir.platform == platform
            result = qa_unit_ir.to_dict()
            assert result["platform"] == platform
