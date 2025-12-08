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
        text = '\u201cquoted\u201d and `\u201ccode\u201d`'
        result = normalize_text(text)
        # Outside code: smart quotes become regular
        assert result.startswith('"quoted"')
        # Inside code: preserved (smart quotes stay as-is)
        assert '`\u201ccode\u201d`' in result


class TestEscapedCharacters:
    """Tests for escaped character normalization."""

    def test_escaped_bold_markers(self):
        """Test that \\*\\* is unescaped to **."""
        text = "This is \\*\\*bold\\*\\* text"
        result = normalize_text(text)
        assert result == "This is **bold** text"

    def test_smart_quotes_normalized(self):
        """Test that smart quotes are converted to regular quotes."""
        text = '\u201cHello\u201d and \u201cWorld\u201d'  # LEFT/RIGHT DOUBLE QUOTATION MARKS
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

    def test_whitespace_only_line_removed_completely(self):
        """Test that whitespace-only lines are removed (not converted to empty lines)."""
        text = "- PoW로 블록을 생성\n \n- longest chain"
        result = normalize_text(text)
        assert result == "- PoW로 블록을 생성\n- longest chain"

    def test_line_with_only_spaces_removed(self):
        """Test that lines with only spaces are removed."""
        text = "line1\n \nline2"
        result = normalize_text(text)
        assert result == "line1\nline2"

    def test_line_with_tabs_removed(self):
        """Test that lines with only tabs are removed."""
        text = "line1\n\t\nline2"
        result = normalize_text(text)
        assert result == "line1\nline2"

    def test_multiple_whitespace_lines(self):
        """Test multiple consecutive whitespace-only lines."""
        text = "line1\n \n \n \nline2"
        result = normalize_text(text)
        # Multiple whitespace-only lines are all removed
        assert result == "line1\nline2"

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


class TestSubItemIndentation:
    """Tests for sub-item indentation normalization."""

    def test_single_space_indent_to_four(self):
        """Test that 1-space indent before list marker becomes 4 spaces."""
        text = "- Parent\n - Child"
        result = normalize_text(text)
        assert result == "- Parent\n    - Child"

    def test_two_space_indent_to_four(self):
        """Test that 2-space indent before list marker becomes 4 spaces."""
        text = "- Parent\n  - Child"
        result = normalize_text(text)
        assert result == "- Parent\n    - Child"

    def test_three_space_indent_to_four(self):
        """Test that 3-space indent before list marker becomes 4 spaces."""
        text = "- Parent\n   - Child"
        result = normalize_text(text)
        assert result == "- Parent\n    - Child"

    def test_four_space_indent_preserved(self):
        """Test that 4-space indent is preserved."""
        text = "- Parent\n    - Child"
        result = normalize_text(text)
        assert result == "- Parent\n    - Child"

    def test_user_example_turing_machine(self):
        """Test the user's example with Turing machine sub-items."""
        text = """- Turing machine이면:
 - 테이프 내용, 헤드 위치, 현재 제어 상태(q)
- CPU면:
 - 레지스터들, 메모리 내용, PC(program counter), 플래그 등"""
        result = normalize_text(text)
        expected = """- Turing machine이면:
    - 테이프 내용, 헤드 위치, 현재 제어 상태(q)
- CPU면:
    - 레지스터들, 메모리 내용, PC(program counter), 플래그 등"""
        assert result == expected


class TestLineContinuation:
    """Tests for line continuation merging."""

    def test_single_space_continuation_merged(self):
        """Test that line starting with 1 space (no marker) is merged."""
        text = '- "시작,\n 계속"'
        result = normalize_text(text)
        assert result == '- "시작, 계속"'

    def test_two_space_continuation_merged(self):
        """Test that line starting with 2 spaces (no marker) is merged."""
        text = '- "시작,\n  계속"'
        result = normalize_text(text)
        assert result == '- "시작, 계속"'

    def test_three_space_continuation_merged(self):
        """Test that line starting with 3 spaces (no marker) is merged."""
        text = '- "시작,\n   계속"'
        result = normalize_text(text)
        assert result == '- "시작, 계속"'

    def test_four_space_continuation_not_merged(self):
        """Test that 4-space continuation is NOT merged (but spaces collapse to 1)."""
        text = '- "시작,\n    계속"'
        result = normalize_text(text)
        # 4칸은 continuation trigger 안 함, but multiple spaces → 1 space
        assert result == '- "시작,\n 계속"'

    def test_continuation_vs_subitem(self):
        """Test distinction between continuation and sub-item."""
        text = "- Parent\n 계속 텍스트\n - Child"
        result = normalize_text(text)
        # 공백+텍스트 → 병합, 공백+대시 → 들여쓰기
        assert result == "- Parent 계속 텍스트\n    - Child"

    def test_user_example_line_continuation(self):
        """Test the user's example with line continuation."""
        text = '''- "과거에 무슨 일이 있었든,
 지금 이 state와 앞으로 들어올 input(트랜잭션/요청)만 알면,
 이후 시스템의 동작을 완전히 시뮬레이션 할 수 있다"는 것.'''
        result = normalize_text(text)
        expected = '- "과거에 무슨 일이 있었든, 지금 이 state와 앞으로 들어올 input(트랜잭션/요청)만 알면, 이후 시스템의 동작을 완전히 시뮬레이션 할 수 있다"는 것.'
        assert result == expected

    def test_multiple_continuations(self):
        """Test multiple continuation lines."""
        text = "- Line 1\n continues\n more\n - Sub"
        result = normalize_text(text)
        assert result == "- Line 1 continues more\n    - Sub"


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


class TestNumberedListIndentation:
    """Tests for numbered list indentation normalization."""

    def test_single_space_numbered_to_four(self):
        """Test that 1-space indent before numbered list becomes 4 spaces."""
        text = "- Parent:\n 1. First"
        result = normalize_text(text)
        assert result == "- Parent:\n    1. First"

    def test_two_space_numbered_to_four(self):
        """Test that 2-space indent before numbered list becomes 4 spaces."""
        text = "- Parent:\n  1. First"
        result = normalize_text(text)
        assert result == "- Parent:\n    1. First"

    def test_three_space_numbered_to_four(self):
        """Test that 3-space indent before numbered list becomes 4 spaces."""
        text = "- Parent:\n   1. First"
        result = normalize_text(text)
        assert result == "- Parent:\n    1. First"

    def test_two_digit_numbered_list(self):
        """Test numbered list with two digits."""
        text = "- Parent:\n 10. Tenth"
        result = normalize_text(text)
        assert result == "- Parent:\n    10. Tenth"

    def test_user_example_blockchain(self):
        """Test user's blockchain example with numbered sub-items."""
        text = """- 블록체인 노드들은 모두 같은 것을 공유한다:
 1. 초기 상태
 2. 상태 전이 함수
 3. 합의된 트랜잭션 순서"""
        result = normalize_text(text)
        expected = """- 블록체인 노드들은 모두 같은 것을 공유한다:
    1. 초기 상태
    2. 상태 전이 함수
    3. 합의된 트랜잭션 순서"""
        assert result == expected


class TestDoubleDashCleanup:
    """Tests for double dash cleanup."""

    def test_double_dash_to_single(self):
        """Test that '- - text' becomes '- text'."""
        # Note: leading whitespace is stripped by normalize_text()
        text = "    - - 입력 순서"
        result = normalize_text(text)
        assert result == "- 입력 순서"

    def test_double_dash_at_line_start(self):
        """Test double dash at line start."""
        text = "- - 텍스트"
        result = normalize_text(text)
        assert result == "- 텍스트"

    def test_double_dash_in_nested_list(self):
        """Test double dash in nested list context."""
        text = """- 알고리즘 혹은 프로그램 =
    - **State transition function**을 구현한 것
    - - 입력 순서/입력 소스"""
        result = normalize_text(text)
        expected = """- 알고리즘 혹은 프로그램 =
    - **State transition function**을 구현한 것
    - 입력 순서/입력 소스"""
        assert result == expected


class TestTableSeparation:
    """Tests for table followed by text separation."""

    def test_table_followed_by_text_gets_blank_line(self):
        """Test that text after table row is separated by blank line."""
        text = """| A | B |
| 1 | 2 |
**Bold text after table**"""
        result = normalize_text(text)
        expected = """| A | B |
| 1 | 2 |

**Bold text after table**"""
        assert result == expected

    def test_table_rows_not_separated(self):
        """Test that consecutive table rows are not separated."""
        text = """| Header |
|--------|
| Value |"""
        result = normalize_text(text)
        expected = """| Header |
|--------|
| Value |"""
        assert result == expected

    def test_user_example_table_insight(self):
        """Test user's example with table followed by insight text."""
        text = """| 구분 | State 구조 |
| --- | --- |
| Bitcoin | UTXO Set |
**금룡섭 님을 위한 Insight:** 분석하세요."""
        result = normalize_text(text)
        expected = """| 구분 | State 구조 |
| --- | --- |
| Bitcoin | UTXO Set |

**금룡섭 님을 위한 Insight:** 분석하세요."""
        assert result == expected


class TestExtraBacktickNormalization:
    """Tests for normalizing extra backticks (LLM error)."""

    def test_four_backticks_to_three(self):
        """Test that 4 backticks become 3."""
        text = "````solidity\ncode\n```"
        result = normalize_text(text)
        assert result == "```solidity\ncode\n```"

    def test_four_backticks_closing(self):
        """Test that 4 backticks in closing become 3."""
        text = "```python\ncode\n````"
        result = normalize_text(text)
        assert result == "```python\ncode\n```"

    def test_user_example_solidity(self):
        """Test user's example with 4 backticks."""
        text = """````solidity
// comment
function test() {
    return 1;
}
```"""
        result = normalize_text(text)
        expected = """```solidity
// comment
function test() {
    return 1;
}
```"""
        assert result == expected


class TestCodeBlockIndentation:
    """Tests for code block indentation normalization."""

    def test_single_space_code_block_to_four(self):
        """Test that 1-space indent before code block becomes 4 spaces."""
        text = """- 각 트랜잭션:
 ```text
    inputs:  기존 UTXO들 소비
    outputs: 새로운 UTXO들 생성
    ```"""
        result = normalize_text(text)
        expected = """- 각 트랜잭션:
    ```text
    inputs:  기존 UTXO들 소비
    outputs: 새로운 UTXO들 생성
    ```"""
        assert result == expected

    def test_two_space_code_block_to_four(self):
        """Test that 2-space indent before code block becomes 4 spaces."""
        text = "- Parent:\n  ```python\ncode\n```"
        result = normalize_text(text)
        assert result == "- Parent:\n    ```python\ncode\n```"

    def test_code_block_content_preserved(self):
        """Test that code block content is not modified."""
        text = """- Item:
 ```
 space inside
 ```"""
        result = normalize_text(text)
        # Code block marker gets 4-space indent, content preserved
        expected = """- Item:
    ```
 space inside
 ```"""
        assert result == expected


class TestTopLevelNumberedListContinuation:
    """Tests for top-level numbered list continuation."""

    def test_numbered_list_continuation(self):
        """Test line continuation in numbered list items."""
        text = '''1. CS에서 "state"는,
 "앞으로의 행동"이다.'''
        result = normalize_text(text)
        expected = '1. CS에서 "state"는, "앞으로의 행동"이다.'
        assert result == expected

    def test_numbered_list_multi_line_continuation(self):
        """Test multiple line continuation in numbered list items."""
        text = '''1. CS에서 "state"는 그냥 데이터 그 자체라기보다,
 "앞으로의 행동을 완전히 결정하기에 충분한 정보 묶음"이다.
 (과거의 history를 압축한 요약본)'''
        result = normalize_text(text)
        expected = '1. CS에서 "state"는 그냥 데이터 그 자체라기보다, "앞으로의 행동을 완전히 결정하기에 충분한 정보 묶음"이다. (과거의 history를 압축한 요약본)'
        assert result == expected

    def test_multiple_numbered_items_with_continuation(self):
        """Test multiple numbered items each with continuation."""
        text = '''1. 첫번째 항목,
 계속됨.
2. 두번째 항목,
 역시 계속.'''
        result = normalize_text(text)
        expected = '''1. 첫번째 항목, 계속됨.
2. 두번째 항목, 역시 계속.'''
        assert result == expected


class TestTableSubItemIndentation:
    """Tests for table normalization - tables are always at root level."""

    def test_table_single_space_to_root(self):
        """Test that 1-space indent before table becomes root level."""
        text = "- 대표적 모델:\n | A | B |"
        result = normalize_text(text)
        assert result == "- 대표적 모델:\n\n| A | B |"

    def test_table_two_space_to_root(self):
        """Test that 2-space indent before table becomes root level."""
        text = "- 모델:\n  | A | B |"
        result = normalize_text(text)
        assert result == "- 모델:\n\n| A | B |"

    def test_table_blank_lines_between_rows_removed(self):
        """Test that blank lines between table rows are removed."""
        text = "- 모델:\n | A |\n\n | B |"
        result = normalize_text(text)
        expected = "- 모델:\n\n| A |\n| B |"
        assert result == expected

    def test_user_example_fsm_table(self):
        """Test user's example with FSM table - tables at root level."""
        text = """- 대표적 모델:
 | 모델 | State·Memory | 계산 능력 |

 | --- | --- | --- |

 | FSM | 유한 상태 | 정규 언어 |

 | PDA | 유한 상태 + 스택 | 문맥자유 언어 |

 | Turing Machine | 유한 제어 + 무한 테이프 | 튜링 완전 |"""
        result = normalize_text(text)
        expected = """- 대표적 모델:

| 모델 | State·Memory | 계산 능력 |
| --- | --- | --- |
| FSM | 유한 상태 | 정규 언어 |
| PDA | 유한 상태 + 스택 | 문맥자유 언어 |
| Turing Machine | 유한 제어 + 무한 테이프 | 튜링 완전 |"""
        assert result == expected


class TestBlockquoteDashRemoval:
    """Tests for blockquote dash removal."""

    def test_quote_dash_removed(self):
        """Test that '> - text' becomes '> text'."""
        text = "> - 비트코인 UTXO"
        result = normalize_text(text)
        assert result == "> 비트코인 UTXO"

    def test_quote_dash_multiple_lines(self):
        """Test multiple lines with quote + dash."""
        text = "> - 비트코인\n>\n> - 이더리움"
        result = normalize_text(text)
        expected = "> 비트코인\n>\n> 이더리움"
        assert result == expected

    def test_user_example_quote_list(self):
        """Test user's example with quoted list items."""
        text = """> - 비트코인 UTXO 모델
>
> - 이더리움 account 모델
>
> - 병렬 실행 (Parallel Execution) - Solana, Monad"""
        result = normalize_text(text)
        expected = """> 비트코인 UTXO 모델
>
> 이더리움 account 모델
>
> 병렬 실행 (Parallel Execution) - Solana, Monad"""
        assert result == expected


class TestDashAfterNumbered:
    """Tests for dash list indentation after numbered items."""

    def test_dash_after_numbered_indented(self):
        """Test that dash after numbered item becomes sub-item."""
        text = "1. Title\n\n- Item"
        result = normalize_text(text)
        expected = "1. Title\n    - Item"
        assert result == expected

    def test_multiple_dashes_after_numbered(self):
        """Test multiple dashes after numbered all become sub-items."""
        text = "1. Title\n\n- Item1\n- Item2"
        result = normalize_text(text)
        expected = "1. Title\n    - Item1\n    - Item2"
        assert result == expected

    def test_nested_dash_becomes_double_indent(self):
        """Test that already-indented dash gets additional indent."""
        text = "1. Title\n\n- Item\n    - SubItem"
        result = normalize_text(text)
        expected = "1. Title\n    - Item\n        - SubItem"
        assert result == expected

    def test_stops_at_next_numbered(self):
        """Test that indentation stops at next numbered item."""
        text = "1. First\n\n- Sub\n\n2. Second"
        result = normalize_text(text)
        expected = "1. First\n    - Sub\n\n2. Second"
        assert result == expected

    def test_user_example_solana(self):
        """Test user's Solana example."""
        text = """1. Solana – Sealevel / Access list

- 트랜잭션이 "읽기/쓰기할 account 목록"을 사전에 선언.
- 런타임이:
    - conflict-free한 트랜잭션들을 병렬 실행 (thread·core full 활용).
- 실질적으로 state I/O를 "account-level 락 + 정적 스케줄링"으로 분산."""
        result = normalize_text(text)
        expected = """1. Solana – Sealevel / Access list
    - 트랜잭션이 "읽기/쓰기할 account 목록"을 사전에 선언.
    - 런타임이:
        - conflict-free한 트랜잭션들을 병렬 실행 (thread·core full 활용).
    - 실질적으로 state I/O를 "account-level 락 + 정적 스케줄링"으로 분산."""
        assert result == expected


class TestEmptyListItemRemoval:
    """Tests for empty list item removal."""

    def test_empty_subitem_removed(self):
        """Test that empty sub-item is removed."""
        text = "- Parent\n    -\n- Next"
        result = normalize_text(text)
        expected = "- Parent\n- Next"
        assert result == expected

    def test_empty_root_item_removed(self):
        """Test that empty root item is removed."""
        text = "- First\n-\n- Third"
        result = normalize_text(text)
        expected = "- First\n- Third"
        assert result == expected

    def test_empty_item_with_spaces_removed(self):
        """Test that item with only spaces is removed."""
        text = "- First\n-   \n- Third"
        result = normalize_text(text)
        expected = "- First\n- Third"
        assert result == expected

    def test_user_example_state_structure(self):
        """Test user's State structure example."""
        text = """- **State 구조:** **Key-Value Store (Merkle Patricia Trie).**
    -
- **State Transition:** **제자리 수정 (In-place Mutation).**
    -
    - 데이터가 삭제되지 않고 값이 덮어씌워집니다."""
        result = normalize_text(text)
        expected = """- **State 구조:** **Key-Value Store (Merkle Patricia Trie).**
- **State Transition:** **제자리 수정 (In-place Mutation).**
    - 데이터가 삭제되지 않고 값이 덮어씌워집니다."""
        assert result == expected


class TestNumberedListAfterDash:
    """Tests for numbered list becoming sub-item after dash with colon."""

    def test_numbered_after_dash_colon_same_indent(self):
        """Numbered list at same indent after dash: becomes sub-item."""
        text = "- **문제**:\n1. 첫번째"
        result = normalize_text(text)
        expected = "- **문제**:\n    1. 첫번째"
        assert result == expected

    def test_multiple_numbered_after_dash(self):
        """Multiple numbered items all become sub-items."""
        text = "- Title:\n1. First\n2. Second"
        result = normalize_text(text)
        expected = "- Title:\n    1. First\n    2. Second"
        assert result == expected

    def test_numbered_after_dash_no_colon_unchanged(self):
        """Numbered after dash without colon stays unchanged."""
        text = "- Title\n1. First"
        result = normalize_text(text)
        # No colon, so numbered list should NOT be indented
        expected = "- Title\n1. First"
        assert result == expected

    def test_user_example_problem_list(self):
        """User's example: numbered list after **문제**:."""
        text = """    - **문제**:
    1. 전역 state I/O 병목
    2. state bloat로 인한 full node 비용 상승
    3. state 보관·검증 비용 때문에 탈중앙성 위축"""
        result = normalize_text(text)
        expected = """- **문제**:
    1. 전역 state I/O 병목
    2. state bloat로 인한 full node 비용 상승
    3. state 보관·검증 비용 때문에 탈중앙성 위축"""
        assert result == expected


class TestHeadingFollowedByIndentedList:
    """Tests for heading followed by indented list."""

    def test_heading_plus_indented_list(self):
        """Heading followed by indented list gets blank line and root list."""
        text = "##### Title\n    - Item"
        result = normalize_text(text)
        expected = "##### Title\n\n- Item"
        assert result == expected

    def test_nested_items_after_heading(self):
        """Nested items maintain relative indent after dedent."""
        text = "### Title\n    - Parent\n        - Child"
        result = normalize_text(text)
        expected = "### Title\n\n- Parent\n    - Child"
        assert result == expected

    def test_user_example_heading_list(self):
        """User's example: heading followed by indented list."""
        text = """##### 4-1. 문제 정의
    - PoW/고전 PoS L1에서는:
        - 블록을 제안/투표하는 노드가 곧
        - state를 모두 들고 있고,
        - 트랜잭션도 직접 실행한다.
    - 합의 노드 수를 늘리면:
        - 네트워크 브로드캐스트, state sync, 실행 비용까지 같이 폭증."""
        result = normalize_text(text)
        expected = """##### 4-1. 문제 정의

- PoW/고전 PoS L1에서는:
    - 블록을 제안/투표하는 노드가 곧
    - state를 모두 들고 있고,
    - 트랜잭션도 직접 실행한다.
- 합의 노드 수를 늘리면:
    - 네트워크 브로드캐스트, state sync, 실행 비용까지 같이 폭증."""
        assert result == expected


class TestTableRootLevel:
    """Tests for table always at root level."""

    def test_table_4space_to_root(self):
        """4-space indented table becomes root level."""
        text = "Content:\n    | A | B |\n    | 1 | 2 |"
        result = normalize_text(text)
        expected = "Content:\n\n| A | B |\n| 1 | 2 |"
        assert result == expected

    def test_table_mixed_indent_rows(self):
        """Mixed indent table rows all become root."""
        text = "    | A |\n| B |"
        result = normalize_text(text)
        expected = "| A |\n| B |"
        assert result == expected

    def test_blank_line_before_table(self):
        """Blank line is added before table."""
        text = "- Item:\n| A | B |"
        result = normalize_text(text)
        expected = "- Item:\n\n| A | B |"
        assert result == expected

    def test_user_example_wrong_table(self):
        """User's example of incorrectly indented table."""
        text = """    | 측면 | ChatGPT | Claude |
| --- | --- | --- |
| 역사 정확 | 높음 | 최고 |"""
        result = normalize_text(text)
        expected = """| 측면 | ChatGPT | Claude |
| --- | --- | --- |
| 역사 정확 | 높음 | 최고 |"""
        assert result == expected


class TestColonTextFollowedByIndentedList:
    """Tests for colon text followed by indented list becoming root."""

    def test_colon_text_indented_list(self):
        """Indented list after colon text becomes root."""
        text = "핵심은:\n    - 항목1"
        result = normalize_text(text)
        expected = "핵심은:\n- 항목1"
        assert result == expected

    def test_preserves_sub_items(self):
        """Sub-items maintain relative indent."""
        text = "핵심은:\n    - Parent\n        - Child"
        result = normalize_text(text)
        expected = "핵심은:\n- Parent\n    - Child"
        assert result == expected

    def test_user_example_comprehensive(self):
        """User's comprehensive example with heading, list, and table."""
        text = """#### Stateless Client (Verkle Trees)
    - **State**: Compressed proofs...
    - **강점**: Light client sync...
    | 측면 | UTXO (Bitcoin) | Account (Eth) |
| --- | --- | --- |
| State | Parceled UTXO | Global mutable |"""
        result = normalize_text(text)
        expected = """#### Stateless Client (Verkle Trees)

- **State**: Compressed proofs...
- **강점**: Light client sync...

| 측면 | UTXO (Bitcoin) | Account (Eth) |
| --- | --- | --- |
| State | Parceled UTXO | Global mutable |"""
        assert result == expected
