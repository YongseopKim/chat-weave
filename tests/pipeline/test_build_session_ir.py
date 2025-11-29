"""Tests for build_session_ir pipeline."""

import pytest

from chatweave.matchers.hash import HashQueryMatcher
from chatweave.models.qa_unit import QAUnit, QAUnitIR
from chatweave.pipeline.build_session_ir import build_session_ir


class TestBuildSessionIR:
    """Tests for build_session_ir function."""

    def test_build_session_ir_single_platform(self):
        """Test building session IR with single platform."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
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
                        user_query_hash="hash1",
                    )
                ],
            )
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        assert session_ir.session_id == "test-session"
        assert session_ir.platforms == ["chatgpt"]
        assert len(session_ir.conversations) == 1
        assert session_ir.conversations[0]["platform"] == "chatgpt"
        assert len(session_ir.prompts) == 1
        assert session_ir.prompts[0].prompt_key == "p0000"

    def test_build_session_ir_multi_platform_matching_hashes(self):
        """Test building session IR with 3 platforms and matching hashes."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="chatgpt-123",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="chatgpt-123",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question 1",
                        user_query_hash="hash1",
                    ),
                    QAUnit(
                        qa_id="q0001",
                        platform="chatgpt",
                        conversation_id="chatgpt-123",
                        user_message_ids=["m0002"],
                        assistant_message_ids=["m0003"],
                        question_from_user="Question 2",
                        user_query_hash="hash2",
                    ),
                ],
            ),
            "claude": QAUnitIR(
                platform="claude",
                conversation_id="claude-456",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="claude",
                        conversation_id="claude-456",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question 1",
                        user_query_hash="hash1",
                    ),
                    QAUnit(
                        qa_id="q0001",
                        platform="claude",
                        conversation_id="claude-456",
                        user_message_ids=["m0002"],
                        assistant_message_ids=["m0003"],
                        question_from_user="Question 2",
                        user_query_hash="hash2",
                    ),
                ],
            ),
            "gemini": QAUnitIR(
                platform="gemini",
                conversation_id="gemini-789",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="gemini",
                        conversation_id="gemini-789",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question 1",
                        user_query_hash="hash1",
                    ),
                    QAUnit(
                        qa_id="q0001",
                        platform="gemini",
                        conversation_id="gemini-789",
                        user_message_ids=["m0002"],
                        assistant_message_ids=["m0003"],
                        question_from_user="Question 2",
                        user_query_hash="hash2",
                    ),
                ],
            ),
        }

        session_ir = build_session_ir(qa_units_dict, "multi-platform-session")

        assert session_ir.session_id == "multi-platform-session"
        assert set(session_ir.platforms) == {"chatgpt", "claude", "gemini"}
        assert len(session_ir.conversations) == 3
        assert len(session_ir.prompts) == 2  # 2 unique questions

        # Each prompt should have 3 platform refs
        for prompt in session_ir.prompts:
            assert len(prompt.per_platform) == 3

    def test_canonical_prompt_selection(self):
        """Test that canonical prompt is selected from alphabetically first platform."""
        qa_units_dict = {
            "gemini": QAUnitIR(
                platform="gemini",
                conversation_id="gemini-1",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="gemini",
                        conversation_id="gemini-1",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Gemini question",
                        user_query_hash="hash1",
                    )
                ],
            ),
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="chatgpt-1",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="chatgpt-1",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="ChatGPT question",
                        user_query_hash="hash1",
                    )
                ],
            ),
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        # Canonical should be from chatgpt (alphabetically first)
        canonical = session_ir.prompts[0].canonical_prompt
        assert canonical["source"]["platform"] == "chatgpt"
        assert canonical["text"] == "ChatGPT question"

    def test_depends_on_sequential(self):
        """Test that depends_on creates sequential dependency chain."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Q1",
                        user_query_hash="hash1",
                    ),
                    QAUnit(
                        qa_id="q0001",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0002"],
                        assistant_message_ids=["m0003"],
                        question_from_user="Q2",
                        user_query_hash="hash2",
                    ),
                    QAUnit(
                        qa_id="q0002",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0004"],
                        assistant_message_ids=["m0005"],
                        question_from_user="Q3",
                        user_query_hash="hash3",
                    ),
                ],
            )
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        assert len(session_ir.prompts) == 3
        assert session_ir.prompts[0].depends_on == []
        assert session_ir.prompts[1].depends_on == ["p0000"]
        assert session_ir.prompts[2].depends_on == ["p0001"]

    def test_missing_prompt_flag(self):
        """Test missing_prompt flag for empty question_from_user."""
        qa_units_dict = {
            "claude": QAUnitIR(
                platform="claude",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="claude",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="",  # Empty
                        question_from_assistant_summary="Summary from assistant",
                        user_query_hash="hash1",
                    )
                ],
            )
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        ref = session_ir.prompts[0].per_platform[0]
        assert ref.missing_prompt is True
        assert ref.prompt_text == "Summary from assistant"

    def test_prompt_similarity_for_hash_match(self):
        """Test that prompt_similarity is 1.0 for hash-based matches."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question",
                        user_query_hash="hash1",
                    )
                ],
            ),
            "claude": QAUnitIR(
                platform="claude",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="claude",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question",
                        user_query_hash="hash1",
                    )
                ],
            ),
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        for ref in session_ir.prompts[0].per_platform:
            assert ref.prompt_similarity == 1.0

    def test_custom_matcher(self):
        """Test that custom matcher can be injected."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="Question",
                        user_query_hash="hash1",
                    )
                ],
            )
        }

        custom_matcher = HashQueryMatcher()
        session_ir = build_session_ir(
            qa_units_dict, "test-session", matcher=custom_matcher
        )

        assert session_ir.session_id == "test-session"
        assert len(session_ir.prompts) == 1

    def test_canonical_prompt_language_is_null(self):
        """Test that canonical_prompt.language is None (deferred to v0.4)."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id="q0000",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        question_from_user="한글 질문",
                        user_query_hash="hash1",
                    )
                ],
            )
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        canonical = session_ir.prompts[0].canonical_prompt
        assert canonical["language"] is None

    def test_empty_qa_units(self):
        """Test handling of empty QA units dict."""
        session_ir = build_session_ir({}, "empty-session")

        assert session_ir.session_id == "empty-session"
        assert session_ir.platforms == []
        assert session_ir.conversations == []
        assert session_ir.prompts == []

    def test_conversation_list_creation(self):
        """Test that conversations list is correctly created."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="chat-id",
                qa_units=[],
            ),
            "claude": QAUnitIR(
                platform="claude",
                conversation_id="claude-id",
                qa_units=[],
            ),
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        assert len(session_ir.conversations) == 2
        conv_dict = {c["platform"]: c["conversation_id"] for c in session_ir.conversations}
        assert conv_dict["chatgpt"] == "chat-id"
        assert conv_dict["claude"] == "claude-id"

    def test_prompt_key_format(self):
        """Test that prompt_key uses correct format (p0000, p0001, etc)."""
        qa_units_dict = {
            "chatgpt": QAUnitIR(
                platform="chatgpt",
                conversation_id="test",
                qa_units=[
                    QAUnit(
                        qa_id=f"q{i:04d}",
                        platform="chatgpt",
                        conversation_id="test",
                        user_message_ids=[f"m{i*2:04d}"],
                        assistant_message_ids=[f"m{i*2+1:04d}"],
                        question_from_user=f"Question {i}",
                        user_query_hash=f"hash{i}",
                    )
                    for i in range(10)
                ],
            )
        }

        session_ir = build_session_ir(qa_units_dict, "test-session")

        assert len(session_ir.prompts) == 10
        for i, prompt in enumerate(session_ir.prompts):
            assert prompt.prompt_key == f"p{i:04d}"
