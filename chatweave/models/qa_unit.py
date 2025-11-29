"""Data models for QA unit intermediate representation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from chatweave.models.conversation import Platform


@dataclass
class QAUnit:
    """A single question-answer pair extracted from a conversation.

    Attributes:
        qa_id: Unique identifier (e.g., "q0001")
        platform: Platform name
        conversation_id: Parent conversation ID
        user_message_ids: List of user message IDs in this QA
        assistant_message_ids: List of assistant message IDs
        question_from_user: Extracted question text from user message(s)
        question_from_assistant_summary: Extracted from assistant's "질문 정리" section
        user_query_hash: Hash from first user message (for matching)
        meta: Additional metadata
    """

    qa_id: str
    platform: Platform
    conversation_id: str
    user_message_ids: List[str]
    assistant_message_ids: List[str]
    question_from_user: Optional[str] = None
    question_from_assistant_summary: Optional[str] = None
    user_query_hash: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "qa_id": self.qa_id,
            "platform": self.platform,
            "conversation_id": self.conversation_id,
            "user_message_ids": self.user_message_ids,
            "assistant_message_ids": self.assistant_message_ids,
            "question_from_user": self.question_from_user,
            "question_from_assistant_summary": self.question_from_assistant_summary,
            "user_query_hash": self.user_query_hash,
            "meta": self.meta,
        }


@dataclass
class QAUnitIR:
    """Collection of QA units from a single conversation.

    Attributes:
        schema: Schema version identifier
        platform: Platform name
        conversation_id: Unique conversation identifier
        qa_units: List of QA units in this conversation
    """

    platform: Platform
    conversation_id: str
    qa_units: List[QAUnit]
    schema: str = "qa-unit-ir/v1"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "platform": self.platform,
            "conversation_id": self.conversation_id,
            "qa_units": [unit.to_dict() for unit in self.qa_units],
        }
