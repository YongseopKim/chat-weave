"""Tests for heuristic query extractor."""

import pytest

from chatweave.extractors.heuristic import HeuristicQueryExtractor


class TestHeuristicQueryExtractor:
    """Tests for HeuristicQueryExtractor."""

    def test_extract_chatgpt_pattern(self):
        """Test extraction of ChatGPT '## 1. 질문 정리' pattern."""
        extractor = HeuristicQueryExtractor()
        content = """## 1. 질문 정리

Claude의 code 실행 환경에서 Node.js 관련 쓰레드가 너무 많이 생성되어 메모리가 터지는 상황입니다.

* * *

## 2. 답변 요약

다음은 Node.js 쓰레드 수를 제어하는 방법입니다.
"""
        result = extractor.extract(content)

        assert result is not None
        assert "Claude의 code 실행 환경" in result
        assert "Node.js 관련 쓰레드" in result
        assert "* * *" not in result  # Should not include section divider

    def test_extract_chatgpt_pattern_with_escaped_dot(self):
        """Test extraction with escaped dot '## 1\\. 질문 정리'."""
        extractor = HeuristicQueryExtractor()
        content = """## 1\\. 질문 정리

RWA 토큰화에 대한 질문입니다.

* * *

## 2\\. 답변
"""
        result = extractor.extract(content)

        assert result is not None
        assert "RWA 토큰화" in result

    def test_extract_gemini_pattern(self):
        """Test extraction of Gemini '## 🧐 질문 정리' pattern."""
        extractor = HeuristicQueryExtractor()
        content = """## 🧐 질문 정리 (Context Refinement)

금룡섭의 질문은 **Claude의 코드 실행 환경** 내에서 문제를 제기하고 있습니다.

* * *

## 📝 답변 요약
"""
        result = extractor.extract(content)

        assert result is not None
        assert "금룡섭의 질문" in result
        assert "Claude의 코드 실행 환경" in result
        assert "Context Refinement" not in result  # Should not include heading suffix

    def test_extract_no_pattern(self):
        """Test returns None for Claude (no pattern)."""
        extractor = HeuristicQueryExtractor()
        content = """Node.js 스레드 수를 제어하는 주요 방법들:

## libuv 스레드풀 크기 조절

UV_THREADPOOL_SIZE 환경 변수를 사용하여 조절할 수 있습니다.
"""
        result = extractor.extract(content)

        assert result is None

    def test_extract_empty_content(self):
        """Test empty string handling."""
        extractor = HeuristicQueryExtractor()
        result = extractor.extract("")

        assert result is None

    def test_extract_none_content(self):
        """Test None handling."""
        extractor = HeuristicQueryExtractor()
        # Type ignore for intentional test of edge case
        result = extractor.extract(None)  # type: ignore

        assert result is None

    def test_section_end_at_hr(self):
        """Test section ends at horizontal rule '* * *'."""
        extractor = HeuristicQueryExtractor()
        content = """## 질문 정리

This is the question summary.

* * *

This should not be included.
"""
        result = extractor.extract(content)

        assert result == "This is the question summary."
        assert "should not be included" not in result

    def test_section_end_at_heading(self):
        """Test section ends at next '##' heading."""
        extractor = HeuristicQueryExtractor()
        content = """## 1. 질문 정리

Question summary here.

## 2. 답변 요약

This should not be included.
"""
        result = extractor.extract(content)

        assert result == "Question summary here."
        assert "답변 요약" not in result
        assert "should not be included" not in result

    def test_section_end_at_triple_dash(self):
        """Test section ends at '---' horizontal rule."""
        extractor = HeuristicQueryExtractor()
        content = """## 질문 정리

Summary content.

---

More content below.
"""
        result = extractor.extract(content)

        assert result == "Summary content."
        assert "More content" not in result

    def test_section_end_at_eof(self):
        """Test section ends at end of content."""
        extractor = HeuristicQueryExtractor()
        content = """## 1. 질문 정리

This is the only content.
No section divider."""

        result = extractor.extract(content)

        assert result is not None
        assert "This is the only content" in result
        assert "No section divider" in result

    def test_clean_content_escapes(self):
        """Test removal of markdown escapes."""
        extractor = HeuristicQueryExtractor()
        content = """## 질문 정리

Question with \\* asterisks \\* and \\- dashes \\[brackets\\].

* * *
"""
        result = extractor.extract(content)

        assert result is not None
        assert "\\*" not in result
        assert "* asterisks *" in result
        assert "\\-" not in result
        assert "- dashes" in result
        assert "[brackets]" in result

    def test_clean_content_whitespace(self):
        """Test whitespace normalization."""
        extractor = HeuristicQueryExtractor()
        content = """## 질문 정리

  Line with extra spaces

Another line


Too many blank lines above.

* * *
"""
        result = extractor.extract(content)

        assert result is not None
        # Leading/trailing whitespace removed from lines
        assert "  Line" not in result
        assert "Line with extra spaces" in result
        # Multiple blank lines collapsed to double newline
        assert "\n\n\n" not in result
        assert "Another line\n\nToo many blank lines" in result

    def test_multiline_content(self):
        """Test extraction of multi-paragraph content."""
        extractor = HeuristicQueryExtractor()
        content = """## 1. 질문 정리

First paragraph of the question.

Second paragraph with more details.

Third paragraph.

* * *

## 2. Answer
"""
        result = extractor.extract(content)

        assert result is not None
        assert "First paragraph" in result
        assert "Second paragraph" in result
        assert "Third paragraph" in result
        # Paragraphs should be preserved
        assert "\n\n" in result

    def test_pattern_priority(self):
        """Test that first matching pattern is used."""
        extractor = HeuristicQueryExtractor()
        # Document with multiple possible patterns
        content = """## 1. 질문 정리

First summary.

## 질문 정리

Second summary (should not be matched).
"""
        result = extractor.extract(content)

        assert result == "First summary."
        assert "Second summary" not in result
