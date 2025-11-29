"""Base class for query extractors."""

from abc import ABC, abstractmethod
from typing import Optional


class QueryExtractor(ABC):
    """Abstract base class for extracting question summaries from responses.

    Query extractors analyze assistant responses to extract the question
    being answered, typically from sections like "질문 정리".
    """

    @abstractmethod
    def extract(self, assistant_content: str) -> Optional[str]:
        """Extract question summary from assistant response.

        Args:
            assistant_content: The raw content of an assistant message

        Returns:
            Extracted question summary, or None if not found
        """
        pass
