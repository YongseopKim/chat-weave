"""Tests for individual normalization passes."""

import pytest

from chatweave.normalization.context import NormalizationContext
from chatweave.normalization.passes import (
    CodeBlockProtectionPass,
    CodeBlockRestorationPass,
    EscapeSequencePass,
    ListStructurePass,
    TableStructurePass,
    UnicodeNormalizationPass,
    WhitespacePass,
)


class TestCodeBlockProtectionPass:
    """Test CodeBlockProtectionPass."""

    def test_name(self):
        pass_ = CodeBlockProtectionPass()
        assert pass_.name == "CodeBlockProtection"

    def test_pre_condition_true_with_backtick(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("has `code` here", ctx) is True

    def test_pre_condition_false_without_backtick(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("no backticks here", ctx) is False

    def test_extracts_fenced_code_block(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        text = "before\n```python\ncode\n```\nafter"
        result = pass_.action(text, ctx)
        assert len(ctx.code_blocks) == 1
        assert "```python\ncode\n```" in ctx.code_blocks[0]
        assert "\x00CODE_BLOCK_0\x00" in result
        assert "before" in result
        assert "after" in result

    def test_extracts_inline_code(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        text = "use `inline` code"
        result = pass_.action(text, ctx)
        assert len(ctx.code_blocks) == 1
        assert ctx.code_blocks[0] == "`inline`"
        assert "\x00CODE_BLOCK_0\x00" in result

    def test_extracts_multiple_code_blocks(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        text = "`a` and `b` and ```\nc\n```"
        result = pass_.action(text, ctx)
        assert len(ctx.code_blocks) == 3

    def test_normalizes_extra_backticks(self):
        """4+ backticks should become 3."""
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        text = "````python\ncode\n````"
        result = pass_.action(text, ctx)
        # After normalization, should be extracted as ```
        assert len(ctx.code_blocks) == 1
        assert ctx.code_blocks[0].startswith("```")

    def test_post_condition_no_raw_fenced_blocks(self):
        pass_ = CodeBlockProtectionPass()
        ctx = NormalizationContext()
        ctx.code_blocks = ["```code```"]
        # Good: only placeholder remains
        assert pass_.post_condition("text \x00CODE_BLOCK_0\x00 text", ctx) is True
        # Bad: raw ``` still in text (outside placeholder)
        assert pass_.post_condition("```still here```", ctx) is False


class TestUnicodeNormalizationPass:
    """Test UnicodeNormalizationPass."""

    def test_name(self):
        pass_ = UnicodeNormalizationPass()
        assert pass_.name == "UnicodeNormalization"

    def test_normalizes_nfc(self):
        pass_ = UnicodeNormalizationPass()
        ctx = NormalizationContext()
        # NFD form: e + combining accent
        nfd = "cafe\u0301"  # café in NFD
        result = pass_.action(nfd, ctx)
        # Should become NFC: é as single char
        assert result == "café"
        assert len(result) == 4  # NFC: c-a-f-é

    def test_post_condition_is_nfc(self):
        pass_ = UnicodeNormalizationPass()
        ctx = NormalizationContext()
        assert pass_.post_condition("café", ctx) is True
        # NFD is not valid
        assert pass_.post_condition("cafe\u0301", ctx) is False


class TestListStructurePass:
    """Test ListStructurePass."""

    def test_name(self):
        pass_ = ListStructurePass()
        assert pass_.name == "ListStructure"

    def test_pre_condition_true_with_dash(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("- item", ctx) is True

    def test_pre_condition_true_with_numbered(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("1. item", ctx) is True

    def test_pre_condition_false_no_list(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("just text", ctx) is False

    def test_removes_double_dash(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- - double dash"
        result = pass_.action(text, ctx)
        assert result == "- double dash"

    def test_removes_blockquote_dash(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "> - quoted list"
        result = pass_.action(text, ctx)
        assert result == "> quoted list"

    def test_removes_empty_list_items(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- item1\n- \n- item2"
        result = pass_.action(text, ctx)
        assert result == "- item1\n- item2"

    def test_normalizes_sub_item_indent_1_to_4(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- parent\n - child"  # 1 space
        result = pass_.action(text, ctx)
        assert "    - child" in result  # 4 spaces

    def test_normalizes_sub_item_indent_2_to_4(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- parent\n  - child"  # 2 spaces
        result = pass_.action(text, ctx)
        assert "    - child" in result  # 4 spaces

    def test_normalizes_sub_item_indent_3_to_4(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- parent\n   - child"  # 3 spaces
        result = pass_.action(text, ctx)
        assert "    - child" in result  # 4 spaces

    def test_preserves_4_space_indent(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- parent\n    - child"  # already 4 spaces
        result = pass_.action(text, ctx)
        assert "    - child" in result

    def test_normalizes_numbered_list_indent(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- parent\n  1. child"  # 2 spaces
        result = pass_.action(text, ctx)
        assert "    1. child" in result

    def test_dedent_list_after_heading(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "##### Title\n    - item"
        result = pass_.action(text, ctx)
        # Should have blank line after heading and dedented list
        assert "##### Title\n\n- item" in result

    def test_dedent_list_after_colon(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "핵심은:\n    - 항목"
        result = pass_.action(text, ctx)
        assert "핵심은:\n- 항목" in result

    def test_indent_numbered_after_dash_colon(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        text = "- Title:\n1. item"
        result = pass_.action(text, ctx)
        assert "    1. item" in result

    def test_post_condition_no_double_dash(self):
        pass_ = ListStructurePass()
        ctx = NormalizationContext()
        assert pass_.post_condition("- single dash", ctx) is True
        assert pass_.post_condition("- - double", ctx) is False


class TestTableStructurePass:
    """Test TableStructurePass."""

    def test_name(self):
        pass_ = TableStructurePass()
        assert pass_.name == "TableStructure"

    def test_pre_condition_true_with_pipe(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("| col |", ctx) is True

    def test_pre_condition_false_no_pipe(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("no table here", ctx) is False

    def test_removes_table_indentation(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        text = "text\n    | col1 | col2 |"
        result = pass_.action(text, ctx)
        assert "\n| col1 | col2 |" in result

    def test_removes_blank_lines_between_rows(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        text = "| row1 |\n\n| row2 |"
        result = pass_.action(text, ctx)
        assert result == "| row1 |\n| row2 |"

    def test_adds_blank_line_before_table(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        text = "text\n| table |"
        result = pass_.action(text, ctx)
        assert "text\n\n| table |" in result

    def test_adds_blank_line_after_table(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        text = "| table |\ntext"
        result = pass_.action(text, ctx)
        assert "| table |\n\ntext" in result

    def test_post_condition_no_indented_tables(self):
        pass_ = TableStructurePass()
        ctx = NormalizationContext()
        assert pass_.post_condition("| table |", ctx) is True
        assert pass_.post_condition("\n    | indented |", ctx) is False


class TestLineContinuationPass:
    """Test LineContinuationPass."""

    def test_name(self):
        from chatweave.normalization.passes import LineContinuationPass
        pass_ = LineContinuationPass()
        assert pass_.name == "LineContinuation"

    def test_merges_line_continuation(self):
        """1-3 space continuation should join to previous line."""
        from chatweave.normalization.passes import LineContinuationPass
        pass_ = LineContinuationPass()
        ctx = NormalizationContext()
        text = "line one\n continuation"  # 1 space indent
        result = pass_.action(text, ctx)
        assert result == "line one continuation"

    def test_does_not_merge_4_space_indent(self):
        """4+ space indent is sub-item, not continuation."""
        from chatweave.normalization.passes import LineContinuationPass
        pass_ = LineContinuationPass()
        ctx = NormalizationContext()
        text = "line one\n    not continuation"
        result = pass_.action(text, ctx)
        assert "\n    not" in result  # newline and indent preserved

    def test_does_not_merge_after_blank_line(self):
        """Continuation only applies when not after empty line."""
        from chatweave.normalization.passes import LineContinuationPass
        pass_ = LineContinuationPass()
        ctx = NormalizationContext()
        text = "paragraph one\n\n next paragraph"
        result = pass_.action(text, ctx)
        assert "\n\n" in result  # paragraph break preserved


class TestWhitespacePass:
    """Test WhitespacePass."""

    def test_name(self):
        pass_ = WhitespacePass()
        assert pass_.name == "Whitespace"

    def test_collapses_multiple_spaces(self):
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        text = "word    word"
        result = pass_.action(text, ctx)
        assert result == "word word"

    def test_preserves_leading_indent(self):
        """Leading indent in middle of text should be preserved."""
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        text = "parent\n    - indented item"
        result = pass_.action(text, ctx)
        assert "\n    -" in result

    def test_removes_whitespace_only_lines(self):
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        text = "line1\n   \nline2"
        result = pass_.action(text, ctx)
        assert "\n   \n" not in result

    def test_collapses_multiple_newlines(self):
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        text = "line1\n\n\n\nline2"
        result = pass_.action(text, ctx)
        assert result == "line1\n\nline2"

    def test_strips_leading_trailing(self):
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        text = "  \n  text  \n  "
        result = pass_.action(text, ctx)
        assert result == "text"

    def test_post_condition_no_triple_newline(self):
        pass_ = WhitespacePass()
        ctx = NormalizationContext()
        assert pass_.post_condition("a\n\nb", ctx) is True
        assert pass_.post_condition("a\n\n\nb", ctx) is False


class TestEscapeSequencePass:
    """Test EscapeSequencePass."""

    def test_name(self):
        pass_ = EscapeSequencePass()
        assert pass_.name == "EscapeSequence"

    def test_unescapes_bold_markers(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        text = "\\*\\*bold\\*\\*"
        result = pass_.action(text, ctx)
        assert result == "**bold**"

    def test_normalizes_left_smart_quote(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        text = "\u201cquoted\u201d"  # "quoted"
        result = pass_.action(text, ctx)
        assert result == '"quoted"'

    def test_unescapes_period_in_heading(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        text = "# Section 1\\. Title"
        result = pass_.action(text, ctx)
        assert result == "# Section 1. Title"

    def test_unescapes_brackets_in_heading(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        text = "## Title \\[note\\]"
        result = pass_.action(text, ctx)
        assert result == "## Title [note]"

    def test_preserves_escapes_outside_heading(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        text = "regular text \\. with escapes"
        result = pass_.action(text, ctx)
        # Should preserve escapes outside headings
        assert "\\." in result

    def test_post_condition_no_smart_quotes(self):
        pass_ = EscapeSequencePass()
        ctx = NormalizationContext()
        assert pass_.post_condition('"normal"', ctx) is True
        assert pass_.post_condition("\u201cquoted\u201d", ctx) is False


class TestCodeBlockRestorationPass:
    """Test CodeBlockRestorationPass."""

    def test_name(self):
        pass_ = CodeBlockRestorationPass()
        assert pass_.name == "CodeBlockRestoration"

    def test_pre_condition_true_with_blocks(self):
        pass_ = CodeBlockRestorationPass()
        ctx = NormalizationContext()
        ctx.code_blocks = ["```code```"]
        assert pass_.pre_condition("text", ctx) is True

    def test_pre_condition_false_without_blocks(self):
        pass_ = CodeBlockRestorationPass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("text", ctx) is False

    def test_restores_single_block(self):
        pass_ = CodeBlockRestorationPass()
        ctx = NormalizationContext()
        ctx.code_blocks = ["```python\ncode\n```"]
        text = "before\n\x00CODE_BLOCK_0\x00\nafter"
        result = pass_.action(text, ctx)
        assert result == "before\n```python\ncode\n```\nafter"

    def test_restores_multiple_blocks(self):
        pass_ = CodeBlockRestorationPass()
        ctx = NormalizationContext()
        ctx.code_blocks = ["`a`", "`b`"]
        text = "\x00CODE_BLOCK_0\x00 and \x00CODE_BLOCK_1\x00"
        result = pass_.action(text, ctx)
        assert result == "`a` and `b`"

    def test_post_condition_no_placeholders(self):
        pass_ = CodeBlockRestorationPass()
        ctx = NormalizationContext()
        assert pass_.post_condition("normal text", ctx) is True
        assert pass_.post_condition("\x00CODE_BLOCK_0\x00", ctx) is False


class TestPassIntegration:
    """Test passes work together correctly."""

    def test_code_blocks_preserved_through_pipeline(self):
        """Code block content should not be modified by other passes."""
        from chatweave.normalization.base import PassRunner

        runner = PassRunner([
            CodeBlockProtectionPass(),
            WhitespacePass(),
            CodeBlockRestorationPass(),
        ])
        text = "text\n```\n   spaces   \n```\nmore"
        result = runner.run(text)
        # Spaces inside code block should be preserved
        assert "   spaces   " in result

    def test_full_pipeline_order(self):
        """All 7 passes should work in correct order."""
        from chatweave.normalization.base import PassRunner

        runner = PassRunner([
            CodeBlockProtectionPass(),
            UnicodeNormalizationPass(),
            ListStructurePass(),
            TableStructurePass(),
            WhitespacePass(),
            EscapeSequencePass(),
            CodeBlockRestorationPass(),
        ])
        text = "- - item\n```code```"
        result = runner.run(text)
        assert "- item" in result  # double dash removed
        assert "```code```" in result  # code preserved
