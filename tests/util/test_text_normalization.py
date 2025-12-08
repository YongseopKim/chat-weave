"""Tests for text normalization utilities."""

import pytest

from chatweave.util.text_normalization import (
    clean_gemini_assistant,
    clean_grok_assistant,
    normalize_text,
)


class TestNormalizeText:
    """Tests for normalize_text function."""

    def test_empty_string(self):
        """Test that empty string is returned as-is."""
        assert normalize_text("") == ""

    def test_none_value(self):
        """Test that None is returned as-is."""
        assert normalize_text(None) is None

    def test_single_space(self):
        """Test that single spaces are preserved."""
        assert normalize_text("a b c") == "a b c"

    def test_multiple_spaces(self):
        """Test that multiple consecutive spaces are collapsed to single space."""
        assert normalize_text("a  b") == "a b"
        assert normalize_text("a   b   c") == "a b c"
        assert normalize_text("hello     world") == "hello world"

    def test_single_newline(self):
        """Test that single newlines are preserved."""
        text = "line1\nline2"
        assert normalize_text(text) == "line1\nline2"

    def test_double_newline(self):
        """Test that double newlines are preserved."""
        text = "para1\n\npara2"
        assert normalize_text(text) == "para1\n\npara2"

    def test_multiple_newlines(self):
        """Test that multiple consecutive newlines are collapsed to double newline."""
        assert normalize_text("a\n\n\nb") == "a\n\nb"
        assert normalize_text("a\n\n\n\n\nb") == "a\n\nb"

    def test_leading_trailing_whitespace(self):
        """Test that leading and trailing whitespace is removed."""
        assert normalize_text("  hello  ") == "hello"
        assert normalize_text("\n\nhello\n\n") == "hello"
        assert normalize_text("  hello world  ") == "hello world"

    def test_unicode_normalization(self):
        """Test that Unicode is normalized to NFC form."""
        # Combining characters (NFD) should be normalized to precomposed (NFC)
        # Example: "e" can be represented as single char (U+00E9) or as "e" + combining acute (U+0065 U+0301)
        nfd = "e\u0301"  # NFD form (decomposed)
        nfc = "\u00e9"  # NFC form (precomposed)
        assert normalize_text(nfd) == nfc

    def test_korean_text(self):
        """Test normalization with Korean text."""
        text = "안녕하세요    세계"
        assert normalize_text(text) == "안녕하세요 세계"

    def test_mixed_whitespace(self):
        """Test text with mixed spaces and newlines."""
        text = "  hello   world  \n\n\n  next paragraph  "
        # Multiple spaces collapse, multiple newlines collapse to double
        # Note: leading space on "  next paragraph" becomes " next paragraph" after space collapse
        expected = "hello world \n\n next paragraph"
        assert normalize_text(text) == expected

    def test_real_world_example(self):
        """Test with realistic conversation text."""
        text = """
        RWA 토큰화에 대해   설명해줘

        자세히   부탁해
        """
        # Multiple spaces collapse, leading indentation (spaces) collapse to single space
        expected = "RWA 토큰화에 대해 설명해줘\n\n 자세히 부탁해"
        assert normalize_text(text) == expected


class TestCodeBlockPreservation:
    """Tests for code block preservation during normalization."""

    def test_inline_code_preserved(self):
        """Test that inline code is preserved without normalization."""
        text = "Use `\\*\\*bold\\*\\*` for emphasis"
        result = normalize_text(text)
        assert "`\\*\\*bold\\*\\*`" in result

    def test_fenced_code_block_preserved(self):
        """Test that fenced code blocks are preserved without normalization."""
        text = """Here is code:

```python
text = "Hello  World"  # Multiple spaces
x = "\\*\\*test\\*\\*"
```

Done."""
        result = normalize_text(text)
        # Code block content should be unchanged
        assert '"Hello  World"' in result
        assert '"\\*\\*test\\*\\*"' in result

    def test_code_block_with_smart_quotes_outside(self):
        """Test that smart quotes outside code blocks are normalized."""
        text = '"quoted" and `"code"`'
        result = normalize_text(text)
        # Outside code: smart quotes become regular
        assert result.startswith('"quoted"')
        # Inside code: preserved
        assert '`"code"`' in result


class TestEscapedCharacters:
    """Tests for escaped character normalization."""

    def test_escaped_bold_markers(self):
        """Test that \\*\\* is unescaped to **."""
        text = "This is \\*\\*bold\\*\\* text"
        result = normalize_text(text)
        assert result == "This is **bold** text"

    def test_smart_quotes_normalized(self):
        """Test that smart quotes are converted to regular quotes."""
        text = '"Hello" and "World"'
        result = normalize_text(text)
        assert result == '"Hello" and "World"'

    def test_escaped_period_in_heading(self):
        """Test that escaped periods in headings are unescaped."""
        text = "### 1\\. First Item\n### 2\\. Second Item"
        result = normalize_text(text)
        assert result == "### 1. First Item\n### 2. Second Item"

    def test_escaped_brackets_in_heading(self):
        """Test that escaped brackets in headings are unescaped."""
        text = "#### \\[Section\\] Title"
        result = normalize_text(text)
        assert result == "#### [Section] Title"

    def test_escaped_chars_not_in_heading_preserved(self):
        """Test that escaped characters outside headings are not changed."""
        text = "Regular text with \\. and \\[ and \\]"
        result = normalize_text(text)
        # These should remain escaped since they're not in headings
        assert "\\." in result
        assert "\\[" in result
        assert "\\]" in result


class TestWhitespaceLines:
    """Tests for whitespace-only line handling."""

    def test_line_with_only_spaces_removed(self):
        """Test that lines with only spaces are converted to empty lines."""
        text = "line1\n \nline2"
        result = normalize_text(text)
        assert result == "line1\n\nline2"

    def test_line_with_tabs_removed(self):
        """Test that lines with only tabs are converted to empty lines."""
        text = "line1\n\t\nline2"
        result = normalize_text(text)
        assert result == "line1\n\nline2"

    def test_multiple_whitespace_lines(self):
        """Test multiple consecutive whitespace-only lines."""
        text = "line1\n \n \n \nline2"
        result = normalize_text(text)
        # Multiple whitespace-only lines become empty lines, then collapse to double newline
        assert result == "line1\n\nline2"

    def test_user_example_bullet_list(self):
        """Test the user's example with bullet list items."""
        text = '''- "state(상태)"가 정확히 무엇인지,

- 왜 어떤 맥락에서는 "computer(계산)"보다 "state(상태)"가 강조되는지,

- 특히 "블록체인 = 글로벌 스테이트 머신"이라는 표현이 무엇을 강조하는지,

- 그리고 본인이 생각한 "상태 = 데이터, 알고리즘 = 그 상태를 바꾸는 것"이라는 관점이 얼마나 타당한지에 대한 질문.'''
        result = normalize_text(text)
        expected = '''- "state(상태)"가 정확히 무엇인지,

- 왜 어떤 맥락에서는 "computer(계산)"보다 "state(상태)"가 강조되는지,

- 특히 "블록체인 = 글로벌 스테이트 머신"이라는 표현이 무엇을 강조하는지,

- 그리고 본인이 생각한 "상태 = 데이터, 알고리즘 = 그 상태를 바꾸는 것"이라는 관점이 얼마나 타당한지에 대한 질문.'''
        assert result == expected


class TestCleanGeminiAssistant:
    """Tests for clean_gemini_assistant function."""

    def test_empty_string(self):
        """Test that empty string is returned as-is."""
        assert clean_gemini_assistant("") == ""

    def test_none_value(self):
        """Test that None is returned as-is."""
        assert clean_gemini_assistant(None) is None

    def test_remove_thinking_indicator(self):
        """Test removal of '생각하는 과정 표시' at the beginning."""
        text = "생각하는 과정 표시\n\n실제 응답 내용입니다."
        result = clean_gemini_assistant(text)
        assert result == "실제 응답 내용입니다."

    def test_remove_sheets_export(self):
        """Test removal of 'Sheets로 내보내기' after tables."""
        text = """| Header |
|--------|
| Value |

Sheets로 내보내기

다음 내용"""
        result = clean_gemini_assistant(text)
        assert "Sheets로 내보내기" not in result
        assert "다음 내용" in result

    def test_remove_code_snippet_label(self):
        """Test removal of '코드 스니펫' before code blocks."""
        text = """설명입니다.

코드 스니펫

```python
print("hello")
```"""
        result = clean_gemini_assistant(text)
        assert "코드 스니펫" not in result
        assert '```python' in result

    def test_remove_source_at_end(self):
        """Test removal of '소스' at the end."""
        text = "응답 내용입니다.\n\n소스"
        result = clean_gemini_assistant(text)
        assert result == "응답 내용입니다."

    def test_full_gemini_response_cleaning(self):
        """Test cleaning a full Gemini response with all artifacts."""
        text = """생각하는 과정 표시

본론입니다.

| A | B |
|---|---|
| 1 | 2 |

Sheets로 내보내기

코드 예시:

코드 스니펫

```
code here
```

결론입니다.

소스"""
        result = clean_gemini_assistant(text)
        assert "생각하는 과정 표시" not in result
        assert "Sheets로 내보내기" not in result
        assert "코드 스니펫" not in result
        assert not result.endswith("소스")
        assert "본론입니다." in result
        assert "결론입니다." in result
        assert "```" in result


class TestCleanGrokAssistant:
    """Tests for clean_grok_assistant function."""

    def test_empty_string(self):
        """Test that empty string is returned as-is."""
        assert clean_grok_assistant("") == ""

    def test_none_value(self):
        """Test that None is returned as-is."""
        assert clean_grok_assistant(None) is None

    def test_remove_thinking_time(self):
        """Test removal of 'Ns동안 생각함' at the beginning."""
        text = "27s동안 생각함\n\n### 응답 제목"
        result = clean_grok_assistant(text)
        assert result == "### 응답 제목"

    def test_remove_thinking_time_short(self):
        """Test removal of short thinking time."""
        text = "5s동안 생각함\n\n응답"
        result = clean_grok_assistant(text)
        assert result == "응답"

    def test_remove_favicon_footer_simple(self):
        """Test removal of simple favicon footer."""
        text = """내용입니다.

![](https://www.google.com/s2/favicons?domain=coinmarketcap.com&sz=256)

![](https://www.google.com/s2/favicons?domain=creditcoin.org&sz=256)

1개의 웹페이지 31개의 웹페이지"""
        result = clean_grok_assistant(text)
        assert result == "내용입니다."

    def test_remove_favicon_footer_with_x_posts(self):
        """Test removal of footer with X posts."""
        text = """내용입니다.

![](https://pbs.twimg.com/profile_images/123/image_normal.jpg)

![](https://pbs.twimg.com/profile_images/456/image_normal.jpg)

𝕏 게시물 1개 𝕏 게시물 10개

![](https://www.google.com/s2/favicons?domain=example.com&sz=256)

1개의 웹페이지 22개의 웹페이지"""
        result = clean_grok_assistant(text)
        assert result == "내용입니다."
        assert "𝕏 게시물" not in result
        assert "웹페이지" not in result

    def test_full_grok_response_cleaning(self):
        """Test cleaning a full Grok response."""
        text = """27s동안 생각함

### Creditcoin (CTC) 개요

내용입니다.

![](https://www.google.com/s2/favicons?domain=coinmarketcap.com&sz=256)

![](https://www.google.com/s2/favicons?domain=creditcoin.org&sz=256)

1개의 웹페이지 31개의 웹페이지"""
        result = clean_grok_assistant(text)
        assert result == "### Creditcoin (CTC) 개요\n\n내용입니다."
        assert "동안 생각함" not in result
        assert "웹페이지" not in result

    def test_preserve_content_without_artifacts(self):
        """Test that content without Grok artifacts is preserved."""
        text = "일반적인 응답 내용입니다."
        result = clean_grok_assistant(text)
        assert result == text
