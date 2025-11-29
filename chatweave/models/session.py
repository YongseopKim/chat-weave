"""Data models for multi-model session intermediate representation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from chatweave.models.conversation import Platform


@dataclass
class PerPlatformQARef:
    """Reference to a QA unit from a specific platform.

    Attributes:
        platform: Platform name
        qa_id: QA unit identifier from that platform
        conversation_id: Conversation identifier
        prompt_text: The actual question text from this platform
        prompt_similarity: Similarity score with canonical prompt (0.0-1.0)
        missing_prompt: True if user content is empty
        missing_context: True if dependent prompts are missing for this platform
    """

    platform: Platform
    qa_id: str
    conversation_id: str
    prompt_text: Optional[str] = None
    prompt_similarity: Optional[float] = None
    missing_prompt: bool = False
    missing_context: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "platform": self.platform,
            "qa_id": self.qa_id,
            "conversation_id": self.conversation_id,
            "prompt_text": self.prompt_text,
            "prompt_similarity": self.prompt_similarity,
            "missing_prompt": self.missing_prompt,
            "missing_context": self.missing_context,
        }


@dataclass
class PromptGroup:
    """A group of QA units answering the same question across platforms.

    Attributes:
        prompt_key: Unique identifier (e.g., "p0000")
        canonical_prompt: Representative question (text, language, source)
        depends_on: List of prompt_keys this depends on (for follow-up questions)
        per_platform: QA references from each platform
        meta: Additional metadata
    """

    prompt_key: str
    canonical_prompt: Dict[str, Any]
    depends_on: List[str] = field(default_factory=list)
    per_platform: List[PerPlatformQARef] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "prompt_key": self.prompt_key,
            "canonical_prompt": self.canonical_prompt,
            "depends_on": self.depends_on,
            "per_platform": [ref.to_dict() for ref in self.per_platform],
            "meta": self.meta,
        }


@dataclass
class MultiModelSessionIR:
    """Cross-platform session alignment.

    Attributes:
        session_id: Session identifier (e.g., directory name)
        platforms: List of platforms in this session
        conversations: List of conversation references
        prompts: List of aligned prompt groups
        schema: Schema version identifier
        meta: Additional metadata
    """

    session_id: str
    platforms: List[Platform]
    conversations: List[Dict[str, str]]
    prompts: List[PromptGroup]
    schema: str = "multi-model-session-ir/v1"
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "schema": self.schema,
            "session_id": self.session_id,
            "platforms": self.platforms,
            "conversations": self.conversations,
            "prompts": [prompt.to_dict() for prompt in self.prompts],
            "meta": self.meta,
        }
