"""Unified parser for all platforms using standard JSONL format."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from chatweave.io.jsonl_loader import load_jsonl
from chatweave.models.conversation import ArtifactIR, ConversationIR, MessageIR, Platform
from chatweave.parsers.base import ConversationParser
from chatweave.util.hashing import compute_query_hash
from chatweave.util.platform_inference import infer_platform
from chatweave.util.text_normalization import (
    clean_gemini_assistant,
    clean_grok_assistant,
    normalize_text,
)


class UnifiedParser(ConversationParser):
    """Parser for standard JSONL format used by all platforms.

    Handles JSONL exports from ChatGPT, Claude, and Gemini that follow
    the standardized format with _meta line and message lines.
    """

    def __init__(self):
        """Initialize unified parser."""
        self.platform = "unified"

    def parse(
        self, jsonl_path: Path, platform_override: Optional[Platform] = None
    ) -> ConversationIR:
        """Parse JSONL file and convert to ConversationIR.

        Args:
            jsonl_path: Path to JSONL export file
            platform_override: Optional platform override (from CLI --platform option)

        Returns:
            ConversationIR object with normalized messages

        Raises:
            ValueError: If platform cannot be inferred or format is invalid
            FileNotFoundError: If file does not exist
        """
        # Load JSONL file
        metadata, messages, artifacts = load_jsonl(jsonl_path)

        # Infer platform with priority: override > metadata > filename
        platform = infer_platform(jsonl_path, metadata, platform_override)

        # Generate conversation ID from filename or URL
        conversation_id = self._generate_conversation_id(jsonl_path, metadata)

        # Convert messages to MessageIR
        message_irs = []
        for index, msg_data in enumerate(messages):
            message_ir = self._convert_message(msg_data, index, platform)
            message_irs.append(message_ir)

        # Convert artifacts to ArtifactIR
        artifact_irs = [
            self._convert_artifact(a, i) for i, a in enumerate(artifacts)
        ]

        # Create ConversationIR
        return ConversationIR(
            platform=platform,
            conversation_id=conversation_id,
            meta=metadata,
            messages=message_irs,
            artifacts=artifact_irs,
        )

    def _generate_conversation_id(
        self, jsonl_path: Path, metadata: dict
    ) -> str:
        """Generate conversation ID from filename or metadata.

        Args:
            jsonl_path: Path to JSONL file
            metadata: Metadata dictionary

        Returns:
            Conversation ID string
        """
        # Try to extract from URL if available
        url = metadata.get("url", "")
        if url:
            # Remove query string from URL
            url_without_query = url.split("?")[0]
            # Extract conversation ID from URL
            # e.g., https://chatgpt.com/c/692ad5eb-... -> 692ad5eb-...
            # e.g., https://claude.ai/chat/43917b24-... -> 43917b24-...
            parts = url_without_query.rstrip("/").split("/")
            if len(parts) >= 2:
                return parts[-1]

        # Fallback: use filename without extension
        return jsonl_path.stem

    def _convert_message(
        self, msg_data: dict, index: int, platform: Platform
    ) -> MessageIR:
        """Convert message dict to MessageIR.

        Args:
            msg_data: Message data dictionary
            index: Message index in conversation
            platform: Platform identifier for platform-specific cleaning

        Returns:
            MessageIR object
        """
        # Generate message ID
        msg_id = f"m{index:04d}"

        # Extract fields
        role = msg_data["role"]
        raw_content = msg_data.get("content", "")
        timestamp_str = msg_data.get("timestamp", "")

        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            # Fallback to epoch if parsing fails
            timestamp = datetime.fromtimestamp(0)

        # Apply platform-specific cleaning for assistant responses
        content_to_normalize = raw_content
        if role == "assistant" and raw_content:
            if platform == "gemini":
                content_to_normalize = clean_gemini_assistant(raw_content)
            elif platform == "grok":
                content_to_normalize = clean_grok_assistant(raw_content)

        # Normalize content
        normalized_content = (
            normalize_text(content_to_normalize) if content_to_normalize else None
        )

        # Compute query hash for user messages
        query_hash = None
        if role == "user" and normalized_content:
            query_hash = compute_query_hash(normalized_content)

        return MessageIR(
            id=msg_id,
            index=index,
            role=role,
            timestamp=timestamp,
            raw_content=raw_content,
            normalized_content=normalized_content,
            query_hash=query_hash,
        )

    def _convert_artifact(self, artifact_data: dict, index: int) -> ArtifactIR:
        """Convert artifact dict to ArtifactIR.

        Args:
            artifact_data: Artifact data dictionary
            index: Artifact index in conversation

        Returns:
            ArtifactIR object
        """
        artifact_id = f"a{index:04d}"
        title = artifact_data.get("title", "")
        version = artifact_data.get("version")
        content = artifact_data.get("content", "")

        # Remaining fields go into meta
        known_keys = {"title", "version", "content"}
        meta = {k: v for k, v in artifact_data.items() if k not in known_keys}

        return ArtifactIR(
            id=artifact_id,
            title=title,
            version=version,
            content=content,
            meta=meta,
        )
