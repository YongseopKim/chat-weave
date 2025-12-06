"""Data models for conversation intermediate representation."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

Role = Literal["user", "assistant"]
Platform = Literal["chatgpt", "claude", "gemini", "grok"]


@dataclass
class MessageIR:
    """Individual message unit in a conversation.

    Attributes:
        id: Unique message identifier (e.g., "m0001")
        index: Zero-based position in conversation
        role: Message role (user or assistant)
        timestamp: Message creation time
        raw_content: Original text content (empty string allowed)
        normalized_content: Normalized text (whitespace/newline cleaned)
        content_format: Content format (default: "markdown")
        query_hash: Hash of normalized content (user messages only)
        meta: Additional metadata
    """

    id: str
    index: int
    role: Role
    timestamp: datetime
    raw_content: str
    normalized_content: Optional[str] = None
    content_format: str = "markdown"
    query_hash: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "index": self.index,
            "role": self.role,
            "timestamp": self.timestamp.isoformat(),
            "raw_content": self.raw_content,
            "normalized_content": self.normalized_content,
            "content_format": self.content_format,
            "query_hash": self.query_hash,
            "meta": self.meta,
        }


@dataclass
class ConversationIR:
    """Platform-specific conversation representation.

    Attributes:
        schema: Schema version identifier
        platform: Platform name (chatgpt, claude, gemini)
        conversation_id: Unique conversation identifier
        meta: Conversation metadata (url, exported_at, etc.)
        messages: List of messages in conversation
    """

    platform: Platform
    conversation_id: str
    meta: Dict[str, Any]
    messages: List[MessageIR]
    schema: str = "conversation-ir/v1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "platform": self.platform,
            "conversation_id": self.conversation_id,
            "meta": self.meta,
            "messages": [msg.to_dict() for msg in self.messages],
        }
