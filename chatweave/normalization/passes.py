"""Normalization pass implementations."""

import re
import unicodedata

from chatweave.normalization.base import NormalizationPass
from chatweave.normalization.context import NormalizationContext


class CodeBlockProtectionPass(NormalizationPass):
    """Extract code blocks and replace with placeholders.

    This pass must run first to protect code block content from
    being modified by subsequent passes.
    """

    @property
    def name(self) -> str:
        return "CodeBlockProtection"

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return "`" in text

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Normalize extra backticks to exactly 3 (common LLM error)
        text = re.sub(r"^(`{4,})", "```", text, flags=re.MULTILINE)

        # Match fenced code blocks (```)
        def replace_fenced(match):
            ctx.code_blocks.append(match.group(0))
            return ctx.placeholder_base.format(len(ctx.code_blocks) - 1)

        text = re.sub(
            r"```[^\n]*\n.*?```", replace_fenced, text, flags=re.DOTALL
        )

        # Match inline code (`)
        def replace_inline(match):
            ctx.code_blocks.append(match.group(0))
            return ctx.placeholder_base.format(len(ctx.code_blocks) - 1)

        text = re.sub(r"`[^`\n]+`", replace_inline, text)

        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No raw fenced code blocks should remain (only placeholders)
        # Simple check: no ``` patterns outside of placeholders
        temp = text
        for i in range(len(ctx.code_blocks)):
            temp = temp.replace(ctx.placeholder_base.format(i), "")
        return "```" not in temp


class UnicodeNormalizationPass(NormalizationPass):
    """Normalize Unicode to NFC form."""

    @property
    def name(self) -> str:
        return "UnicodeNormalization"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return unicodedata.normalize("NFC", text)

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return unicodedata.is_normalized("NFC", text)


class ListStructurePass(NormalizationPass):
    """Normalize list structure.

    Handles:
    - Dedent indented lists after headings
    - Dedent indented lists after colon text
    - Remove dash after blockquote (> -)
    - Remove duplicate dashes (- -)
    - Remove empty list items
    - Normalize sub-item indentation (1-3 spaces -> 4 spaces)
    - Indent numbered list after dash with colon
    - Indent dash block after numbered items
    """

    @property
    def name(self) -> str:
        return "ListStructure"

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return "-" in text or re.search(r"\d+\.", text) is not None

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Dedent list after heading
        text = self._dedent_list_after_heading(text)

        # Dedent list after colon text
        text = self._dedent_list_after_colon_text(text)

        # Remove dash after blockquote marker
        text = re.sub(r"^> - ", "> ", text, flags=re.MULTILINE)

        # Remove duplicate list markers
        text = re.sub(r"^(\s*)- - ", r"\1- ", text, flags=re.MULTILINE)

        # Remove empty list items
        text = re.sub(r"\n *-[ \t]*(?=\n)", "", text)

        # Sub-item indentation normalization (1-3 spaces -> 4)
        text = re.sub(r"\n {1,3}(-|\d+\.|\x00)", r"\n    \1", text)

        # Indent numbered list after dash with colon
        text = self._indent_numbered_after_dash_colon(text)

        # Indent dash block after numbered items
        text = self._indent_dash_block_after_numbered(text)

        return text

    def _dedent_list_after_heading(self, text: str) -> str:
        """Dedent indented list that follows a heading."""
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            result.append(line)
            # Detect heading (# to ######)
            if re.match(r"^#{1,6} ", line):
                j = i + 1
                # Check if next line is indented list (4+ spaces + -)
                if j < len(lines) and re.match(r"^ {4,}- ", lines[j]):
                    # Add blank line after heading
                    result.append("")
                    # Find base indent and dedent the block
                    base_indent_match = re.match(r"^( +)", lines[j])
                    base_indent = (
                        len(base_indent_match.group(1)) if base_indent_match else 0
                    )
                    while j < len(lines):
                        if not lines[j].strip():
                            result.append("")
                            j += 1
                            continue
                        current_indent_match = re.match(r"^( *)", lines[j])
                        current_indent = (
                            len(current_indent_match.group(1))
                            if current_indent_match
                            else 0
                        )
                        if current_indent >= base_indent and lines[j].strip():
                            result.append(lines[j][base_indent:])
                            j += 1
                        elif lines[j].strip():
                            break
                        else:
                            j += 1
                    i = j - 1
            i += 1
        return "\n".join(result)

    def _dedent_list_after_colon_text(self, text: str) -> str:
        """Dedent indented list that follows text ending with colon."""
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            result.append(line)
            # Detect non-heading text ending with colon
            if (
                line.strip().endswith(":")
                and not line.strip().startswith("#")
                and not line.strip().startswith("-")
            ):
                j = i + 1
                # Check if next line is indented list (4+ spaces + -)
                if j < len(lines) and re.match(r"^ {4,}- ", lines[j]):
                    base_indent_match = re.match(r"^( +)", lines[j])
                    base_indent = (
                        len(base_indent_match.group(1)) if base_indent_match else 0
                    )
                    while j < len(lines):
                        if not lines[j].strip():
                            result.append("")
                            j += 1
                            continue
                        current_indent_match = re.match(r"^( *)", lines[j])
                        current_indent = (
                            len(current_indent_match.group(1))
                            if current_indent_match
                            else 0
                        )
                        if current_indent >= base_indent and lines[j].strip():
                            result.append(lines[j][base_indent:])
                            j += 1
                        elif lines[j].strip():
                            break
                        else:
                            j += 1
                    i = j - 1
            i += 1
        return "\n".join(result)

    def _indent_numbered_after_dash_colon(self, text: str) -> str:
        """Indent numbered list that follows dash item ending with colon."""
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            result.append(line)
            # Detect dash item ending with colon
            if re.match(r"^- .+:$", line):
                j = i + 1
                # Check if next line is numbered list at root level
                while j < len(lines) and re.match(r"^\d+\. ", lines[j]):
                    result.append("    " + lines[j])
                    j += 1
                if j > i + 1:
                    i = j - 1
            i += 1
        return "\n".join(result)

    def _indent_dash_block_after_numbered(self, text: str) -> str:
        """Indent root-level dashes as sub-items of numbered items."""
        # Check if processing is needed: numbered followed by root-level dash
        # If no root-level dash after numbered item, already processed (idempotent)
        # Pattern requires line start (^|\n) and space after number to avoid
        # matching "5-1." as numbered item (the "1." part would incorrectly match)
        if not re.search(r"(?:^|\n)\d+\. [^\n]*\n\n*-", text):
            return text

        def process_match(match: re.Match) -> str:
            numbered_line = match.group(1)
            middle_block = match.group(2)
            next_part = match.group(3) if match.group(3) else ""

            if "-" not in middle_block:
                return numbered_line + middle_block + next_part

            def indent_dashes(m: re.Match) -> str:
                prefix = m.group(1) or ""
                if prefix == "    ":
                    return "        -"
                else:
                    return "    -"

            indented = re.sub(
                r"^(    )?(-)", indent_dashes, middle_block, flags=re.MULTILINE
            )
            indented = re.sub(r"^\n+", "", indented)
            indented = re.sub(r"\n\n+(\s*-)", r"\n\1", indented)
            return numbered_line + indented + next_part

        # Pattern requires space after \d+\. to match only real numbered items
        # e.g., "1. item" matches but "5-1.item" does not
        pattern = r"((?:^|\n)\d+\. [^\n]*\n)((?:(?!\n\d+\. ).)*?)(\n\d+\. |$)"
        return re.sub(pattern, process_match, text, flags=re.DOTALL)

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No double dashes at line start
        return re.search(r"^(\s*)- - ", text, re.MULTILINE) is None


class TableStructurePass(NormalizationPass):
    """Normalize table structure.

    Handles:
    - Remove indentation from table rows (tables always at root)
    - Remove blank lines between table rows
    - Add blank line before table
    - Add blank line after table
    """

    @property
    def name(self) -> str:
        return "TableStructure"

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return "|" in text

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Remove indentation from table rows
        text = re.sub(r"\n +\|", r"\n|", text)
        text = re.sub(r"^ +\|", "|", text)

        # Remove blank lines between table rows
        while True:
            new_text = re.sub(r"(\|)\n\n+(\|)", r"\1\n\2", text)
            if new_text == text:
                break
            text = new_text

        # Add blank line before table
        text = re.sub(r"([^\|\n])\n(\|)", r"\1\n\n\2", text)

        # Add blank line after table
        text = re.sub(r"(\|)\n(?! *\|)([^\n])", r"\1\n\n\2", text)

        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No indented table rows
        return re.search(r"\n +\|", text) is None


class LineContinuationPass(NormalizationPass):
    """Merge line continuations.

    Lines with 1-3 space indent (not after empty line) are continuations
    and should be merged with the previous line.
    """

    @property
    def name(self) -> str:
        return "LineContinuation"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Line continuation merging (1-3 spaces, not after empty line)
        # (?<!\n) prevents merging after empty lines (paragraph breaks)
        return re.sub(r"(?<!\n)\n {1,3}([^-\s])", r" \1", text)

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No 1-3 space continuations should remain (except after blank lines)
        # This is a soft check - some edge cases might remain
        return True


class WhitespacePass(NormalizationPass):
    """Normalize whitespace.

    Handles:
    - Multiple space collapse
    - Leading space normalization (4+ spaces to 1)
    - Whitespace-only line removal
    - Multiple newline collapse
    - Leading/trailing strip

    Note: Line continuation is handled by LineContinuationPass.
    """

    @property
    def name(self) -> str:
        return "Whitespace"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Collapse multiple spaces (only after non-whitespace)
        text = re.sub(r"(?<=\S) +", " ", text)

        # Collapse leading spaces (except for list markers, code blocks, tables)
        # Two cases to avoid triggering line continuation in convergence loop:
        # 1. After blank line: any spaces (2+) -> 1 space (safe, won't trigger line cont)
        text = re.sub(
            r"\n\n( {2,})(?!\d+\.)([^-\s\x00|])",
            lambda m: "\n\n " + m.group(2),
            text,
        )
        # 2. Not after blank line: only 4+ spaces -> 1 space (1-3 handled by LineContinuation)
        text = re.sub(
            r"(?<!\n)\n( {4,})(?!\d+\.)([^-\s\x00|])",
            lambda m: "\n " + m.group(2),
            text,
        )

        # Remove whitespace-only lines
        while True:
            new_text = re.sub(r"\n[ \t]+\n", "\n", text)
            if new_text == text:
                break
            text = new_text

        # Collapse multiple newlines to double
        text = re.sub(r"\n\n+", "\n\n", text)

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No triple newlines
        return "\n\n\n" not in text


class EscapeSequencePass(NormalizationPass):
    """Normalize escape sequences.

    Handles:
    - Unescape \\*\\* -> **
    - Smart quotes -> regular quotes
    - Unescape \\. in headings
    - Unescape \\[ and \\] in headings
    """

    @property
    def name(self) -> str:
        return "EscapeSequence"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        # Unescape bold markers
        text = text.replace("\\*\\*", "**")

        # Normalize smart quotes
        text = text.replace("\u201c", '"')  # LEFT DOUBLE QUOTATION MARK
        text = text.replace("\u201d", '"')  # RIGHT DOUBLE QUOTATION MARK

        # Unescape in headings only
        text = re.sub(
            r"^(#{1,6}[^\n]*?)\\\.", r"\1.", text, flags=re.MULTILINE
        )
        text = re.sub(
            r"^(#{1,6}[^\n]*?)\\\[", r"\1[", text, flags=re.MULTILINE
        )
        text = re.sub(
            r"^(#{1,6}[^\n]*?)\\\]", r"\1]", text, flags=re.MULTILINE
        )

        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No smart quotes
        return "\u201c" not in text and "\u201d" not in text


class CodeBlockRestorationPass(NormalizationPass):
    """Restore code blocks from placeholders.

    This pass must run last to restore code block content.
    """

    @property
    def name(self) -> str:
        return "CodeBlockRestoration"

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return len(ctx.code_blocks) > 0

    def action(self, text: str, ctx: NormalizationContext) -> str:
        for i, block in enumerate(ctx.code_blocks):
            placeholder = ctx.placeholder_base.format(i)
            text = text.replace(placeholder, block)
        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        # No placeholders should remain
        return "\x00CODE_BLOCK_" not in text
