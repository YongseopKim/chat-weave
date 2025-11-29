"""Tests for session data models."""

import pytest

from chatweave.models.session import (
    MultiModelSessionIR,
    PerPlatformQARef,
    PromptGroup,
)


class TestPerPlatformQARef:
    """Tests for PerPlatformQARef dataclass."""

    def test_create_per_platform_qa_ref(self):
        """Test creating a PerPlatformQARef instance."""
        ref = PerPlatformQARef(
            platform="chatgpt",
            qa_id="q0000",
            conversation_id="test-123",
            prompt_text="What is RWA?",
            prompt_similarity=1.0,
            missing_prompt=False,
            missing_context=False,
        )

        assert ref.platform == "chatgpt"
        assert ref.qa_id == "q0000"
        assert ref.conversation_id == "test-123"
        assert ref.prompt_text == "What is RWA?"
        assert ref.prompt_similarity == 1.0
        assert ref.missing_prompt is False
        assert ref.missing_context is False

    def test_per_platform_qa_ref_defaults(self):
        """Test PerPlatformQARef default values."""
        ref = PerPlatformQARef(
            platform="claude",
            qa_id="q0001",
            conversation_id="test-456",
        )

        assert ref.prompt_text is None
        assert ref.prompt_similarity is None
        assert ref.missing_prompt is False
        assert ref.missing_context is False

    def test_per_platform_qa_ref_to_dict(self):
        """Test PerPlatformQARef.to_dict() serialization."""
        ref = PerPlatformQARef(
            platform="gemini",
            qa_id="q0002",
            conversation_id="xyz-789",
            prompt_text="Example question",
            prompt_similarity=0.95,
            missing_prompt=True,
            missing_context=False,
        )

        result = ref.to_dict()

        assert result["platform"] == "gemini"
        assert result["qa_id"] == "q0002"
        assert result["conversation_id"] == "xyz-789"
        assert result["prompt_text"] == "Example question"
        assert result["prompt_similarity"] == 0.95
        assert result["missing_prompt"] is True
        assert result["missing_context"] is False

    def test_missing_prompt_flag(self):
        """Test missing_prompt flag for Claude edge case."""
        ref = PerPlatformQARef(
            platform="claude",
            qa_id="q0000",
            conversation_id="test",
            prompt_text=None,
            missing_prompt=True,
        )

        assert ref.missing_prompt is True
        result = ref.to_dict()
        assert result["missing_prompt"] is True


class TestPromptGroup:
    """Tests for PromptGroup dataclass."""

    def test_create_prompt_group(self):
        """Test creating a PromptGroup instance."""
        canonical_prompt = {
            "text": "What is RWA?",
            "language": None,
            "source": {"platform": "chatgpt", "qa_id": "q0000"},
        }

        refs = [
            PerPlatformQARef(
                platform="chatgpt",
                qa_id="q0000",
                conversation_id="test-1",
                prompt_similarity=1.0,
            )
        ]

        prompt_group = PromptGroup(
            prompt_key="p0000",
            canonical_prompt=canonical_prompt,
            depends_on=[],
            per_platform=refs,
        )

        assert prompt_group.prompt_key == "p0000"
        assert prompt_group.canonical_prompt["text"] == "What is RWA?"
        assert prompt_group.depends_on == []
        assert len(prompt_group.per_platform) == 1

    def test_prompt_group_defaults(self):
        """Test PromptGroup default values."""
        prompt_group = PromptGroup(
            prompt_key="p0001",
            canonical_prompt={"text": "Test"},
        )

        assert prompt_group.depends_on == []
        assert prompt_group.per_platform == []
        assert prompt_group.meta == {}

    def test_prompt_group_to_dict(self):
        """Test PromptGroup.to_dict() serialization."""
        refs = [
            PerPlatformQARef(
                platform="chatgpt",
                qa_id="q0000",
                conversation_id="test",
                prompt_similarity=1.0,
            ),
            PerPlatformQARef(
                platform="claude",
                qa_id="q0000",
                conversation_id="test",
                prompt_similarity=1.0,
            ),
        ]

        prompt_group = PromptGroup(
            prompt_key="p0000",
            canonical_prompt={"text": "Question", "language": None},
            depends_on=[],
            per_platform=refs,
        )

        result = prompt_group.to_dict()

        assert result["prompt_key"] == "p0000"
        assert result["canonical_prompt"]["text"] == "Question"
        assert result["depends_on"] == []
        assert len(result["per_platform"]) == 2
        assert isinstance(result["per_platform"][0], dict)
        assert result["per_platform"][0]["platform"] == "chatgpt"

    def test_prompt_group_with_dependencies(self):
        """Test PromptGroup with depends_on."""
        prompt_group = PromptGroup(
            prompt_key="p0001",
            canonical_prompt={"text": "Follow-up question"},
            depends_on=["p0000"],
        )

        assert prompt_group.depends_on == ["p0000"]
        result = prompt_group.to_dict()
        assert result["depends_on"] == ["p0000"]


class TestMultiModelSessionIR:
    """Tests for MultiModelSessionIR dataclass."""

    def test_create_multi_model_session_ir(self):
        """Test creating a MultiModelSessionIR instance."""
        conversations = [
            {"platform": "chatgpt", "conversation_id": "test-1"},
            {"platform": "claude", "conversation_id": "test-2"},
        ]

        prompts = [
            PromptGroup(
                prompt_key="p0000",
                canonical_prompt={"text": "Question 1"},
            )
        ]

        session_ir = MultiModelSessionIR(
            session_id="sample-session",
            platforms=["chatgpt", "claude"],
            conversations=conversations,
            prompts=prompts,
        )

        assert session_ir.session_id == "sample-session"
        assert session_ir.platforms == ["chatgpt", "claude"]
        assert len(session_ir.conversations) == 2
        assert len(session_ir.prompts) == 1

    def test_multi_model_session_ir_default_schema(self):
        """Test MultiModelSessionIR default schema value."""
        session_ir = MultiModelSessionIR(
            session_id="test",
            platforms=[],
            conversations=[],
            prompts=[],
        )

        assert session_ir.schema == "multi-model-session-ir/v1"

    def test_multi_model_session_ir_to_dict(self):
        """Test MultiModelSessionIR.to_dict() serialization."""
        conversations = [
            {"platform": "chatgpt", "conversation_id": "test-1"},
        ]

        refs = [
            PerPlatformQARef(
                platform="chatgpt",
                qa_id="q0000",
                conversation_id="test-1",
            )
        ]

        prompts = [
            PromptGroup(
                prompt_key="p0000",
                canonical_prompt={"text": "Question"},
                per_platform=refs,
            )
        ]

        session_ir = MultiModelSessionIR(
            session_id="test-session",
            platforms=["chatgpt"],
            conversations=conversations,
            prompts=prompts,
        )

        result = session_ir.to_dict()

        assert result["schema"] == "multi-model-session-ir/v1"
        assert result["session_id"] == "test-session"
        assert result["platforms"] == ["chatgpt"]
        assert len(result["conversations"]) == 1
        assert len(result["prompts"]) == 1
        assert isinstance(result["prompts"][0], dict)
        assert result["prompts"][0]["prompt_key"] == "p0000"

    def test_multi_platform_alignment(self):
        """Test session IR with multiple platforms."""
        conversations = [
            {"platform": "chatgpt", "conversation_id": "chat-1"},
            {"platform": "claude", "conversation_id": "claude-1"},
            {"platform": "gemini", "conversation_id": "gemini-1"},
        ]

        refs = [
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
        ]

        prompts = [
            PromptGroup(
                prompt_key="p0000",
                canonical_prompt={
                    "text": "Aligned question",
                    "language": None,
                    "source": {"platform": "chatgpt", "qa_id": "q0000"},
                },
                per_platform=refs,
            )
        ]

        session_ir = MultiModelSessionIR(
            session_id="multi-platform-test",
            platforms=["chatgpt", "claude", "gemini"],
            conversations=conversations,
            prompts=prompts,
        )

        result = session_ir.to_dict()

        assert len(result["platforms"]) == 3
        assert len(result["prompts"][0]["per_platform"]) == 3
