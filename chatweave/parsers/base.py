"""Base class for conversation parsers."""

from abc import ABC, abstractmethod
from pathlib import Path

from chatweave.models.conversation import ConversationIR


class ConversationParser(ABC):
    """Abstract base class for platform-specific conversation parsers.

    Each parser is responsible for converting platform JSONL exports
    to the standardized ConversationIR format.
    """

    platform: str

    @abstractmethod
    def parse(self, jsonl_path: Path) -> ConversationIR:
        """Parse JSONL file and convert to ConversationIR.

        Args:
            jsonl_path: Path to platform JSONL export file

        Returns:
            ConversationIR object

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file does not exist
        """
        pass
