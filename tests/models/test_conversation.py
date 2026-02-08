"""Tests for conversation data models."""

from datetime import datetime

import pytest

from chatweave.models.conversation import ArtifactIR, ConversationIR, MessageIR


class TestMessageIR:
    """Tests for MessageIR dataclass."""

    def test_create_message_ir(self):
        """Test creating a MessageIR instance."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        message = MessageIR(
            id="m0000",
            index=0,
            role="user",
            timestamp=timestamp,
            raw_content="Hello, World!",
            normalized_content="Hello, World!",
            query_hash="abc123"
        )

        assert message.id == "m0000"
        assert message.index == 0
        assert message.role == "user"
        assert message.timestamp == timestamp
        assert message.raw_content == "Hello, World!"
        assert message.normalized_content == "Hello, World!"
        assert message.query_hash == "abc123"

    def test_message_ir_defaults(self):
        """Test MessageIR default values."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        message = MessageIR(
            id="m0000",
            index=0,
            role="assistant",
            timestamp=timestamp,
            raw_content="Response"
        )

        assert message.normalized_content is None
        assert message.content_format == "markdown"
        assert message.query_hash is None
        assert message.meta == {}

    def test_message_ir_to_dict(self):
        """Test MessageIR.to_dict() serialization."""
        timestamp = datetime(2025, 11, 29, 10, 0, 5)
        message = MessageIR(
            id="m0001",
            index=1,
            role="user",
            timestamp=timestamp,
            raw_content="Test",
            normalized_content="Test",
            query_hash="hash123",
            meta={"custom": "value"}
        )

        result = message.to_dict()

        assert result["id"] == "m0001"
        assert result["index"] == 1
        assert result["role"] == "user"
        assert result["timestamp"] == "2025-11-29T10:00:05"
        assert result["raw_content"] == "Test"
        assert result["normalized_content"] == "Test"
        assert result["content_format"] == "markdown"
        assert result["query_hash"] == "hash123"
        assert result["meta"] == {"custom": "value"}

    def test_timestamp_iso_format(self):
        """Test that timestamp is converted to ISO format string."""
        timestamp = datetime(2025, 11, 29, 14, 30, 45)
        message = MessageIR(
            id="m0000",
            index=0,
            role="user",
            timestamp=timestamp,
            raw_content="Test"
        )

        result = message.to_dict()
        assert result["timestamp"] == "2025-11-29T14:30:45"

    def test_empty_raw_content(self):
        """Test MessageIR with empty raw_content (Claude edge case)."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        message = MessageIR(
            id="m0000",
            index=0,
            role="user",
            timestamp=timestamp,
            raw_content="",  # Empty content
            normalized_content=""
        )

        result = message.to_dict()
        assert result["raw_content"] == ""
        assert result["normalized_content"] == ""

    def test_assistant_no_query_hash(self):
        """Test that assistant messages don't have query_hash."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        message = MessageIR(
            id="m0001",
            index=1,
            role="assistant",
            timestamp=timestamp,
            raw_content="Response"
        )

        result = message.to_dict()
        assert result["query_hash"] is None


class TestConversationIR:
    """Tests for ConversationIR dataclass."""

    def test_create_conversation_ir(self):
        """Test creating a ConversationIR instance."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Question",
                normalized_content="Question",
                query_hash="hash1"
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
            conversation_id="test-123",
            meta={"url": "https://chatgpt.com/c/test-123"},
            messages=messages
        )

        assert conversation.platform == "chatgpt"
        assert conversation.conversation_id == "test-123"
        assert conversation.meta["url"] == "https://chatgpt.com/c/test-123"
        assert len(conversation.messages) == 2

    def test_conversation_ir_default_schema(self):
        """Test ConversationIR default schema value."""
        conversation = ConversationIR(
            platform="claude",
            conversation_id="abc",
            meta={},
            messages=[]
        )

        assert conversation.schema == "conversation-ir/v1"

    def test_conversation_ir_to_dict(self):
        """Test ConversationIR.to_dict() serialization."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Test",
                normalized_content="Test"
            )
        ]

        conversation = ConversationIR(
            platform="gemini",
            conversation_id="xyz-789",
            meta={"url": "https://gemini.google.com/app/xyz"},
            messages=messages
        )

        result = conversation.to_dict()

        assert result["schema"] == "conversation-ir/v1"
        assert result["platform"] == "gemini"
        assert result["conversation_id"] == "xyz-789"
        assert result["meta"]["url"] == "https://gemini.google.com/app/xyz"
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], dict)
        assert result["messages"][0]["id"] == "m0000"

    def test_messages_serialized_as_dicts(self):
        """Test that messages are converted to dictionaries in to_dict()."""
        timestamp = datetime(2025, 11, 29, 10, 0, 0)
        messages = [
            MessageIR(
                id="m0000",
                index=0,
                role="user",
                timestamp=timestamp,
                raw_content="Q1"
            ),
            MessageIR(
                id="m0001",
                index=1,
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

        result = conversation.to_dict()

        # All messages should be dicts
        assert all(isinstance(msg, dict) for msg in result["messages"])
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][1]["role"] == "assistant"

    def test_empty_messages(self):
        """Test ConversationIR with no messages."""
        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="empty",
            meta={},
            messages=[]
        )

        result = conversation.to_dict()
        assert result["messages"] == []

    def test_platform_types(self):
        """Test different platform types."""
        for platform in ["chatgpt", "claude", "gemini"]:
            conversation = ConversationIR(
                platform=platform,
                conversation_id="test",
                meta={},
                messages=[]
            )
            assert conversation.platform == platform
            result = conversation.to_dict()
            assert result["platform"] == platform

    def test_meta_fields(self):
        """Test various metadata fields."""
        meta = {
            "url": "https://example.com",
            "exported_at": "2025-11-29T10:00:00Z",
            "custom_field": "value",
            "number": 42,
            "nested": {"key": "value"}
        }

        conversation = ConversationIR(
            platform="chatgpt",
            conversation_id="test",
            meta=meta,
            messages=[]
        )

        result = conversation.to_dict()
        assert result["meta"] == meta
        assert result["meta"]["custom_field"] == "value"
        assert result["meta"]["number"] == 42
        assert result["meta"]["nested"]["key"] == "value"

    def test_conversation_ir_without_artifacts(self):
        """Test that ConversationIR without artifacts omits key from to_dict()."""
        conversation = ConversationIR(
            platform="claude",
            conversation_id="test",
            meta={},
            messages=[]
        )

        assert conversation.artifacts == []
        result = conversation.to_dict()
        assert "artifacts" not in result

    def test_conversation_ir_with_artifacts(self):
        """Test ConversationIR with artifacts includes them in to_dict()."""
        artifact = ArtifactIR(
            id="a0000",
            title="My Component",
            version="v1",
            content="export default function() {}"
        )

        conversation = ConversationIR(
            platform="claude",
            conversation_id="test",
            meta={},
            messages=[],
            artifacts=[artifact]
        )

        result = conversation.to_dict()
        assert "artifacts" in result
        assert len(result["artifacts"]) == 1
        assert result["artifacts"][0]["title"] == "My Component"


class TestArtifactIR:
    """Tests for ArtifactIR dataclass."""

    def test_create_artifact_ir(self):
        """Test creating an ArtifactIR instance."""
        artifact = ArtifactIR(
            id="a0000",
            title="My Component",
            version="v1",
            content="export default function() {}"
        )

        assert artifact.id == "a0000"
        assert artifact.title == "My Component"
        assert artifact.version == "v1"
        assert artifact.content == "export default function() {}"
        assert artifact.meta == {}

    def test_artifact_ir_defaults(self):
        """Test ArtifactIR default values."""
        artifact = ArtifactIR(id="a0000", title="Test")

        assert artifact.version is None
        assert artifact.content == ""
        assert artifact.meta == {}

    def test_artifact_ir_to_dict(self):
        """Test ArtifactIR.to_dict() serialization."""
        artifact = ArtifactIR(
            id="a0000",
            title="Component",
            version="v2",
            content="code here",
            meta={"language": "python"}
        )

        result = artifact.to_dict()

        assert result["id"] == "a0000"
        assert result["title"] == "Component"
        assert result["version"] == "v2"
        assert result["content"] == "code here"
        assert result["meta"] == {"language": "python"}

    def test_artifact_ir_to_dict_without_version(self):
        """Test that to_dict() omits version when None."""
        artifact = ArtifactIR(id="a0000", title="Test", content="body")

        result = artifact.to_dict()

        assert "version" not in result
        assert result["title"] == "Test"
        assert result["content"] == "body"
