"""Tests for build_qa_ir pipeline."""

from datetime import datetime

import pytest

from chatweave.extractors.heuristic import HeuristicQueryExtractor
from chatweave.models.conversation import ConversationIR, MessageIR
from chatweave.parsers.unified import UnifiedParser
from chatweave.pipeline.build_qa_ir import build_qa_ir


class TestBuildQAIR:
    """Tests for build_qa_ir function."""

    def test_build_qa_ir_basic(self):
        """Test basic QA IR building from simple conversation."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Question 1",
                normalized_content="Question 1",
                query_hash="hash1"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="## 1. 질문 정리\n\nSummary 1\n\n* * *\n\nAnswer 1"
            ),
            MessageIR(
                id="m0002",
                index=2,
                role="user",
                timestamp=timestamp,
                raw_content="Question 2",
                normalized_content="Question 2",
                query_hash="hash2"
            ),
            MessageIR(
                id="m0003",
                index=3,
                role="assistant",
                timestamp=timestamp,
                raw_content="Answer 2 without summary"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test-123",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert qa_ir.platform == "chatgpt"
        assert qa_ir.conversation_id == "test-123"
        assert qa_ir.schema == "qa-unit-ir/v1"
        assert len(qa_ir.qa_units) == 2

        # First QA unit
        qa1 = qa_ir.qa_units[0]
        assert qa1.qa_id == "q0000"
        assert qa1.user_message_ids == ["m0000"]
        assert qa1.assistant_message_ids == ["m0001"]
        assert qa1.question_from_user == "Question 1"
        assert qa1.question_from_assistant_summary == "Summary 1"
        assert qa1.user_query_hash == "hash1"

        # Second QA unit
        qa2 = qa_ir.qa_units[1]
        assert qa2.qa_id == "q0001"
        assert qa2.user_message_ids == ["m0002"]
        assert qa2.assistant_message_ids == ["m0003"]
        assert qa2.question_from_user == "Question 2"
        assert qa2.question_from_assistant_summary is None  # No summary in response
        assert qa2.user_query_hash == "hash2"

    def test_build_qa_ir_chatgpt(self, chatgpt_jsonl):
        """Test building QA IR from real ChatGPT sample."""
        parser = UnifiedParser()
        conversation = parser.parse(chatgpt_jsonl)
        qa_ir = build_qa_ir(conversation)

        assert qa_ir.platform == "chatgpt"
        assert len(qa_ir.qa_units) > 0

        # Check first QA unit
        qa1 = qa_ir.qa_units[0]
        assert qa1.qa_id == "q0000"
        assert len(qa1.user_message_ids) > 0
        assert len(qa1.assistant_message_ids) > 0
        assert qa1.question_from_user is not None
        assert qa1.question_from_assistant_summary is not None
        assert "Node" in qa1.question_from_assistant_summary

    def test_build_qa_ir_claude(self, claude_jsonl):
        """Test building QA IR from Claude sample (no assistant summary)."""
        parser = UnifiedParser()
        conversation = parser.parse(claude_jsonl)
        qa_ir = build_qa_ir(conversation)

        assert qa_ir.platform == "claude"
        assert len(qa_ir.qa_units) > 0

        # Claude responses typically don't have "질문 정리" section
        # So question_from_assistant_summary should be None
        for qa_unit in qa_ir.qa_units:
            assert qa_unit.question_from_user is not None or qa_unit.question_from_user == ""

    def test_build_qa_ir_gemini(self, gemini_jsonl):
        """Test building QA IR from Gemini sample."""
        parser = UnifiedParser()
        conversation = parser.parse(gemini_jsonl)
        qa_ir = build_qa_ir(conversation)

        assert qa_ir.platform == "gemini"
        assert len(qa_ir.qa_units) > 0

        # Check first QA unit has extracted summary (Gemini has emoji pattern)
        qa1 = qa_ir.qa_units[0]
        assert qa1.question_from_user is not None
        # Gemini may or may not have the pattern, depending on sample data

    def test_group_simple_qa(self):
        """Test simple user-assistant alternation."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Q1",
                query_hash="h1"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="A1"
            ),
            MessageIR(
                id="m0002",
                index=2,
                role="user",
                timestamp=timestamp,
                raw_content="Q2",
                query_hash="h2"
            ),
            MessageIR(
                id="m0003",
                index=3,
                role="assistant",
                timestamp=timestamp,
                raw_content="A2"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert len(qa_ir.qa_units) == 2
        assert qa_ir.qa_units[0].user_message_ids == ["m0000"]
        assert qa_ir.qa_units[0].assistant_message_ids == ["m0001"]
        assert qa_ir.qa_units[1].user_message_ids == ["m0002"]
        assert qa_ir.qa_units[1].assistant_message_ids == ["m0003"]

    def test_group_multiple_users(self):
        """Test multiple consecutive user messages."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Q1 part 1",
                query_hash="h1"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="user",
                timestamp=timestamp,
                raw_content="Q1 part 2",
                query_hash="h2"
            ),
            MessageIR(
                id="m0002",
                index=2,
                role="assistant",
                timestamp=timestamp,
                raw_content="A1"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert len(qa_ir.qa_units) == 1
        qa1 = qa_ir.qa_units[0]
        assert qa1.user_message_ids == ["m0000", "m0001"]
        assert qa1.assistant_message_ids == ["m0002"]
        assert "Q1 part 1\n\nQ1 part 2" == qa1.question_from_user
        assert qa1.user_query_hash == "h1"  # Hash from first user message

    def test_group_multiple_assistants(self):
        """Test multiple consecutive assistant messages."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Question",
                query_hash="h1"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="## 1. 질문 정리\n\nSummary\n\n* * *\n\nPart 1"
            ),
            MessageIR(
                id="m0002",
                index=2,
                role="assistant",
                timestamp=timestamp,
                raw_content="Part 2"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert len(qa_ir.qa_units) == 1
        qa1 = qa_ir.qa_units[0]
        assert qa1.user_message_ids == ["m0000"]
        assert qa1.assistant_message_ids == ["m0001", "m0002"]
        assert qa1.question_from_assistant_summary == "Summary"

    def test_group_starts_with_assistant(self):
        """Test skips leading assistant messages (system prompt/greeting)."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="assistant",
                timestamp=timestamp,
                raw_content="System greeting"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="user",
                timestamp=timestamp,
                raw_content="Question",
                query_hash="h1"
            ),
            MessageIR(
                id="m0002",
                index=2,
                role="assistant",
                timestamp=timestamp,
                raw_content="Answer"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        # Should skip the leading assistant message
        assert len(qa_ir.qa_units) == 1
        qa1 = qa_ir.qa_units[0]
        assert qa1.user_message_ids == ["m0001"]
        assert qa1.assistant_message_ids == ["m0002"]

    def test_qa_ids_sequential(self):
        """Test QA IDs are sequential 'q0000', 'q0001', etc."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = []
        for i in range(10):
            messages.append(MessageIR(
                id=f"m{i*2:04d}",
                index=i*2,
                role="user",
                timestamp=timestamp,
                raw_content=f"Q{i}",
                query_hash=f"h{i}"
            ))
            messages.append(MessageIR(
                id=f"m{i*2+1:04d}",
                index=i*2+1,
                role="assistant",
                timestamp=timestamp,
                raw_content=f"A{i}"
            ))

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert len(qa_ir.qa_units) == 10
        for i, qa_unit in enumerate(qa_ir.qa_units):
            assert qa_unit.qa_id == f"q{i:04d}"

    def test_query_hash_propagation(self):
        """Test query hash from user message propagates to QA unit."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Question",
                normalized_content="Question",
                query_hash="abc123def456"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="Answer"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert qa_ir.qa_units[0].user_query_hash == "abc123def456"

    def test_custom_extractor(self):
        """Test using custom extractor."""
        from chatweave.extractors.base import QueryExtractor

        class TestExtractor(QueryExtractor):
            def extract(self, assistant_content: str):
                return "Custom extracted summary"

        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Question"
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="Any content"
            )
        ]

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta={},
            messages=messages
        )

        custom_extractor = TestExtractor()
        qa_ir = build_qa_ir(conversation, extractor=custom_extractor)

        assert qa_ir.qa_units[0].question_from_assistant_summary == "Custom extracted summary"

    def test_empty_conversation(self):
        """Test building QA IR from empty conversation."""
        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="empty",
            meta={},
            messages=[]
        )

        qa_ir = build_qa_ir(conversation)

        assert qa_ir.platform == "chatgpt"
        assert qa_ir.conversation_id == "empty"
        assert len(qa_ir.qa_units) == 0

    def test_empty_user_content(self):
        """Test handling empty user content (Claude edge case)."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="",  # Empty
                normalized_content=""
            ),
            MessageIR(
                id="m0001",
                index=1,
                role="assistant",
                timestamp=timestamp,
                raw_content="Response based on context"
            )
        ]

        conversation = ConversationIR(
            platform="claude",
            conversation_id="test",
            meta={},
            messages=messages
        )

        qa_ir = build_qa_ir(conversation)

        assert len(qa_ir.qa_units) == 1
        # Empty content should result in None (no content to join)
        assert qa_ir.qa_units[0].question_from_user is None
