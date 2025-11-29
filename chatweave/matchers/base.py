"""Base class for query matchers."""

from abc import ABC, abstractmethod
from typing import List

from chatweave.models.qa_unit import QAUnit


class QueryMatcher(ABC):
    """Abstract base class for matching QA units by question similarity.

    Query matchers group QA units from different platforms that answer
    the same question, enabling cross-platform alignment.
    """

    @abstractmethod
    def match(self, units: List[QAUnit]) -> List[List[QAUnit]]:
        """Group QA units by question similarity.

        Args:
            units: List of QA units from multiple platforms

        Returns:
            List of groups, where each group contains QA units
            answering the same question
        """
        pass
