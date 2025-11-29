"""Heuristic-based query extractor using pattern matching."""

import re
from typing import List, Optional, Tuple

from chatweave.extractors.base import QueryExtractor


class HeuristicQueryExtractor(QueryExtractor):
    """Rule-based extractor for question summary sections.

    Supports multiple patterns found in different platforms:
    - ChatGPT: "## 1. 질문 정리" or "## 1\\. 질문 정리"
    - Gemini: "## 🧐 질문 정리 (Context Refinement)"
    - Claude: No standard pattern (returns None)
    """

    # Start patterns (compiled regex)
    START_PATTERNS: List[re.Pattern] = [
        re.compile(r'^##\s*1\\?\.\s*질문\s*정리', re.MULTILINE),  # 1. or 1\.
        re.compile(r'^##\s+🧐\s*질문\s*정리', re.MULTILINE),
        re.compile(r'^##\s+⚙️\s*질문\s*정리', re.MULTILINE),
        re.compile(r'^##\s*질문\s*정리', re.MULTILINE),
    ]

    # End patterns (priority order)
    END_PATTERNS: List[re.Pattern] = [
        re.compile(r'^##\s+', re.MULTILINE),  # Next ## heading
        re.compile(r'^\*\s*\*\s*\*\s*$', re.MULTILINE),  # * * *
        re.compile(r'^---+\s*$', re.MULTILINE),  # ---
    ]

    def extract(self, assistant_content: str) -> Optional[str]:
        """Extract question summary from assistant response.

        Args:
            assistant_content: The raw content of an assistant message

        Returns:
            Extracted question summary text, or None if not found
        """
        if not assistant_content:
            return None

        # Find start position
        start_match, start_end = self._find_section_start(assistant_content)
        if start_match is None:
            return None

        # Find end position (after the start)
        remaining_content = assistant_content[start_end:]
        end_pos = self._find_section_end(remaining_content)

        # Extract section content
        section_content = remaining_content[:end_pos].strip()

        # Clean up the extracted content
        return self._clean_content(section_content) or None

    def _find_section_start(self, content: str) -> Tuple[Optional[re.Match], int]:
        """Find the start of the question summary section.

        Returns:
            Tuple of (match object or None, end position of match)
        """
        for pattern in self.START_PATTERNS:
            match = pattern.search(content)
            if match:
                # Return position after the heading line
                line_end = content.find('\n', match.end())
                if line_end == -1:
                    line_end = len(content)
                return match, line_end + 1
        return None, 0

    def _find_section_end(self, content: str) -> int:
        """Find the end of the question summary section.

        Returns:
            Position of the section end
        """
        earliest_end = len(content)

        for pattern in self.END_PATTERNS:
            match = pattern.search(content)
            if match and match.start() < earliest_end:
                earliest_end = match.start()

        return earliest_end

    def _clean_content(self, content: str) -> str:
        """Clean up extracted content.

        - Remove leading/trailing whitespace
        - Remove escaped characters (e.g., \\n, \\*)
        - Normalize whitespace
        """
        if not content:
            return ""

        # Remove common markdown escapes
        content = content.replace('\\*', '*')
        content = content.replace('\\-', '-')
        content = content.replace('\\[', '[')
        content = content.replace('\\]', ']')

        # Normalize whitespace (preserve paragraph breaks)
        lines = content.split('\n')
        lines = [line.strip() for line in lines]
        content = '\n'.join(lines)

        # Remove multiple blank lines
        while '\n\n\n' in content:
            content = content.replace('\n\n\n', '\n\n')

        return content.strip()
