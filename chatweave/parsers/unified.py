"""Unified parser for all platforms using standard JSONL format."""

from datetime import datetime
from pathlib import Path
from typing import cast

from chatweave.io.jsonl_loader import load_jsonl
from chatweave.models.conversation import ConversationIR, MessageIR, Platform
from chatweave.parsers.base import ConversationParser
from chatweave.util.hashing import compute_query_hash
from chatweave.util.text_normalization import normalize_text


class UnifiedParser(ConversationParser):
    """Parser for standard JSONL format used by all platforms.

    Handles JSONL exports from ChatGPT, Claude, and Gemini that follow
    the standardized format with _meta line and message lines.
    """

    def __init__(self):
        """Initialize unified parser."""
        self.platform = "unified"

    def parse(self, jsonl_path: Path) -> ConversationIR:
        """Parse JSONL file and convert to ConversationIR.

        Args:
            jsonl_path: Path to JSONL export file

        Returns:
            ConversationIR object with normalized messages

        Raises:
            ValueError: If platform is not supported or format is invalid
            FileNotFoundError: If file does not exist
        """
        # Load JSONL file
        metadata, messages = load_jsonl(jsonl_path)

        # Extract platform from metadata
        platform_str = metadata.get("platform")
        if platform_str not in ("chatgpt", "claude", "gemini"):
            raise ValueError(
                f"Unsupported platform: {platform_str}. "
                f"Expected one of: chatgpt, claude, gemini"
            )
        platform = cast(Platform, platform_str)

        # Generate conversation ID from filename or URL
        conversation_id = self._generate_conversation_id(jsonl_path, metadata)

        # Convert messages to MessageIR
        message_irs = []
        for index, msg_data in enumerate(messages):
            message_ir = self._convert_message(msg_data, index)
            message_irs.append(message_ir)

        # Create ConversationIR
        return ConversationIR(
            platform=platform,
            conversation_id=conversation_id,
            meta=metadata,
            messages=message_irs,
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
            # Extract conversation ID from URL
            # e.g., https://chatgpt.com/c/692ad5eb-... -> 692ad5eb-...
            # e.g., https://claude.ai/chat/43917b24-... -> 43917b24-...
            parts = url.rstrip("/").split("/")
            if len(parts) >= 2:
                return f"{metadata['platform']}-{parts[-1]}"

        # Fallback: use filename without extension
        return jsonl_path.stem

    def _convert_message(self, msg_data: dict, index: int) -> MessageIR:
        """Convert message dict to MessageIR.

        Args:
            msg_data: Message data dictionary
            index: Message index in conversation

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

        # Normalize content
        normalized_content = normalize_text(raw_content) if raw_content else None

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
