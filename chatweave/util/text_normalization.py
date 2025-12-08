"""Text normalization utilities for consistent processing."""

import re
import unicodedata


def _extract_code_blocks(text: str) -> tuple[str, list[str]]:
    """Extract code blocks and replace with placeholders.

    Args:
        text: Text containing code blocks

    Returns:
        Tuple of (text with placeholders, list of extracted code blocks)
    """
    code_blocks = []
    placeholder_base = "\x00CODE_BLOCK_{}\x00"

    # Match fenced code blocks (```)
    def replace_fenced(match):
        code_blocks.append(match.group(0))
        return placeholder_base.format(len(code_blocks) - 1)

    # Match fenced code blocks with optional language identifier
    text = re.sub(r"```[^\n]*\n.*?```", replace_fenced, text, flags=re.DOTALL)

    # Match inline code (`)
    def replace_inline(match):
        code_blocks.append(match.group(0))
        return placeholder_base.format(len(code_blocks) - 1)

    text = re.sub(r"`[^`\n]+`", replace_inline, text)

    return text, code_blocks


def _restore_code_blocks(text: str, code_blocks: list[str]) -> str:
    """Restore code blocks from placeholders.

    Args:
        text: Text with placeholders
        code_blocks: List of original code blocks

    Returns:
        Text with code blocks restored
    """
    for i, block in enumerate(code_blocks):
        placeholder = f"\x00CODE_BLOCK_{i}\x00"
        text = text.replace(placeholder, block)
    return text


def normalize_text(text: str) -> str:
    """Normalize text by cleaning whitespace, newlines, and escaped characters.

    Normalization steps:
    1. Extract code blocks (preserve them from normalization)
    2. Normalize Unicode characters (NFC form)
    3. Remove duplicate list markers (- - text -> - text)
    4. Normalize sub-item indentation (1-3 spaces + dash/number -> 4 spaces)
       - Handles both dash (-) and numbered lists (1., 2., etc.)
    5. Merge line continuations (1-3 space indent + non-marker -> join with prev line)
       - Only when NOT preceded by empty line (paragraph break)
    6. Replace multiple consecutive spaces with single space
    7. Remove lines with only whitespace (e.g., \\n \\n -> \\n)
    8. Replace multiple consecutive newlines with double newline
    9. Unescape markdown characters: \\*\\* -> **, smart quotes -> regular quotes
    10. Unescape characters in headings: \\. -> ., \\[ -> [, \\] -> ]
    11. Strip leading/trailing whitespace
    12. Restore code blocks

    Args:
        text: Raw text content

    Returns:
        Normalized text string
    """
    if not text:
        return text

    # Normalize extra backticks to exactly 3 (common LLM error: ```` instead of ```)
    # Must run BEFORE code block extraction
    text = re.sub(r"^(`{4,})", "```", text, flags=re.MULTILINE)

    # Extract code blocks to preserve them
    text, code_blocks = _extract_code_blocks(text)

    # Normalize Unicode to NFC form
    text = unicodedata.normalize("NFC", text)

    # === NEW: Dedent indented list after heading ===
    # Heading + \n + indented list → Heading + \n\n + root list
    # Must run BEFORE other list processing
    def _dedent_list_after_heading(text: str) -> str:
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
                    base_indent = len(base_indent_match.group(1)) if base_indent_match else 0
                    while j < len(lines):
                        if not lines[j].strip():
                            # Empty line - keep as is
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
                            # Dedent by base_indent
                            result.append(lines[j][base_indent:])
                            j += 1
                        elif lines[j].strip():
                            # Non-indented non-empty line - stop dedenting
                            break
                        else:
                            j += 1
                    i = j - 1
            i += 1
        return "\n".join(result)

    text = _dedent_list_after_heading(text)

    # === NEW: Dedent indented list after colon text ===
    # text: + \n + indented list → text: + \n + root list
    # Must run BEFORE other list processing
    def _dedent_list_after_colon_text(text: str) -> str:
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
                    # Find base indent and dedent the block
                    base_indent_match = re.match(r"^( +)", lines[j])
                    base_indent = len(base_indent_match.group(1)) if base_indent_match else 0
                    while j < len(lines):
                        if not lines[j].strip():
                            # Empty line - keep as is
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
                            # Dedent by base_indent
                            result.append(lines[j][base_indent:])
                            j += 1
                        elif lines[j].strip():
                            # Non-indented non-empty line - stop dedenting
                            break
                        else:
                            j += 1
                    i = j - 1
            i += 1
        return "\n".join(result)

    text = _dedent_list_after_colon_text(text)

    # Remove dash after blockquote marker: "> - text" → "> text"
    text = re.sub(r"^> - ", "> ", text, flags=re.MULTILINE)

    # Remove duplicate list markers: "- - " → "- "
    # Must run before other list processing
    text = re.sub(r"^(\s*)- - ", r"\1- ", text, flags=re.MULTILINE)

    # Remove empty list items: lines that are just "- " or "    - " with no content
    # Pattern: \n + optional spaces + dash + optional whitespace + \n
    # Use lookahead (?=\n) to not consume the trailing newline
    text = re.sub(r"\n *-[ \t]*(?=\n)", "", text)

    # Sub-item indentation normalization: \n + 1~3 spaces + list marker → \n + 4 spaces + marker
    # Handles dash (-), numbered lists (1., 2., 10.), and code block placeholders (\x00)
    # MUST run BEFORE continuation merging so these items get 4-space indent first
    text = re.sub(r"\n {1,3}(-|\d+\.|\x00)", r"\n    \1", text)

    # === NEW: Table always at root level ===
    # Remove all indentation from table rows
    # Pattern: \n + any spaces + | → \n + |
    text = re.sub(r"\n +\|", r"\n|", text)

    # Also handle table at start of text (after strip)
    text = re.sub(r"^ +\|", "|", text)

    # Remove blank lines between table rows
    # Pattern: | + \n\n+ + | → | + \n + |
    while True:
        new_text = re.sub(r"(\|)\n\n+(\|)", r"\1\n\2", text)
        if new_text == text:
            break
        text = new_text

    # Add blank line before table (when preceded by non-table content)
    # Pattern: non-pipe char + \n + | → char + \n\n + |
    # But not when previous line ends with |
    text = re.sub(r"([^\|\n])\n(\|)", r"\1\n\n\2", text)

    # === NEW: Indent numbered list after dash with colon ===
    # When a dash item ends with : and is followed by numbered list at root level,
    # the numbered list becomes sub-item (4-space indent)
    # Pattern: - text: + \n + 1. → - text: + \n + 4spaces + 1.
    def _indent_numbered_after_dash_colon(text: str) -> str:
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
                    # Add 4-space indent to numbered item
                    result.append("    " + lines[j])
                    j += 1
                if j > i + 1:
                    i = j - 1
            i += 1
        return "\n".join(result)

    text = _indent_numbered_after_dash_colon(text)

    # Indent dash list items after numbered items
    # When a numbered item (1., 2., etc.) is followed by dash items, those dashes become sub-items
    # Pattern: numbered item line + blank lines + dash at root level → indent dash by 4 spaces
    # Also increases existing 4-space indent to 8-space indent
    def _indent_dash_block_after_numbered(match: re.Match) -> str:
        """Indent root-level dashes in the block as sub-items of the numbered item."""
        numbered_line = match.group(1)
        middle_block = match.group(2)
        next_part = match.group(3) if match.group(3) else ""

        # Skip if no dashes in the middle block
        if "-" not in middle_block:
            return numbered_line + middle_block + next_part

        # Replace blank lines before root-level dash with newline + 4-space indent
        # Also add 4 spaces to already-indented dashes (4 → 8)
        def indent_dashes(m: re.Match) -> str:
            prefix = m.group(1) or ""
            if prefix == "    ":
                return "        -"  # 4 spaces → 8 spaces
            else:
                return "    -"  # root level → 4 spaces

        # Apply to lines starting with dash (with or without indent)
        indented = re.sub(r"^(    )?(-)", indent_dashes, middle_block, flags=re.MULTILINE)
        # Remove leading blank lines (between numbered item and first dash)
        indented = re.sub(r"^\n+", "", indented)
        # Remove blank lines before dashes (they should be single newline now)
        indented = re.sub(r"\n\n+(\s*-)", r"\n\1", indented)
        return numbered_line + indented + next_part

    # Match: numbered item at START OF LINE + middle content (non-greedy until next numbered or end)
    # Use (?:^|\n) to match start of string or after newline (don't use MULTILINE with $)
    # (?:(?!\n\d+\.).)* matches any char except start of new numbered item
    pattern = r"((?:^|\n)\d+\.[^\n]*\n)((?:(?!\n\d+\.).)*?)(\n\d+\.|$)"
    text = re.sub(pattern, _indent_dash_block_after_numbered, text, flags=re.DOTALL)

    # Line continuation merging: \n + 1~3 spaces + non-list-marker char → space + char
    # MUST run AFTER sub-item normalization (numbered lists now have 4 spaces)
    # (?<!\n) prevents merging after empty lines (paragraph breaks)
    # Apply repeatedly to handle multiple continuation lines
    while True:
        new_text = re.sub(r"(?<!\n)\n {1,3}([^-\s])", r" \1", text)
        if new_text == text:
            break
        text = new_text

    # Replace multiple spaces with single space (only within lines, not at line start)
    # (?<=\S) ensures we only collapse spaces after non-whitespace chars
    # This preserves leading indentation like "    -" after sub-item normalization
    text = re.sub(r"(?<=\S) +", " ", text)

    # Collapse leading spaces to single space (except for list markers, code blocks, and tables)
    # Pattern matches: \n + spaces + non-list-marker char
    # Preserves "    -", "    1.", "    \x00" (code block), and "    |" (table)
    # (?!\d+\.) negative lookahead excludes numbered list markers
    # [^-\s\x00|] excludes dash, whitespace, code block placeholder, and pipe (table)
    text = re.sub(r"\n( +)(?!\d+\.)([^-\s\x00|])", lambda m: "\n " + m.group(2), text)

    # Remove lines with only whitespace
    # This handles \n \n patterns (lines with only spaces) by removing them entirely
    # Apply repeatedly to handle consecutive whitespace-only lines
    while True:
        new_text = re.sub(r"\n[ \t]+\n", "\n", text)
        if new_text == text:
            break
        text = new_text

    # Add blank line after table rows when followed by non-table content
    # Pattern: | at end of line + \n + non-whitespace, non-pipe char → insert blank line
    # Excludes: |\n    | (indented table row continuation)
    # Uses negative lookahead to skip lines starting with spaces followed by |
    text = re.sub(r"(\|)\n(?! *\|)([^\n])", r"\1\n\n\2", text)

    # Replace multiple newlines with double newline
    text = re.sub(r"\n\n+", "\n\n", text)

    # Unescape markdown bold/italic markers
    text = text.replace("\\*\\*", "**")

    # Normalize smart quotes to regular quotes
    text = text.replace('\u201c', '"')  # LEFT DOUBLE QUOTATION MARK
    text = text.replace('\u201d', '"')  # RIGHT DOUBLE QUOTATION MARK

    # Unescape characters in headings only
    # Pattern: line starting with # followed by escaped characters
    # \. -> . (escaped period after number in headings)
    text = re.sub(r"^(#{1,6}[^\n]*?)\\\.", r"\1.", text, flags=re.MULTILINE)
    # \[ -> [ (escaped bracket in headings)
    text = re.sub(r"^(#{1,6}[^\n]*?)\\\[", r"\1[", text, flags=re.MULTILINE)
    # \] -> ] (escaped bracket in headings)
    text = re.sub(r"^(#{1,6}[^\n]*?)\\\]", r"\1]", text, flags=re.MULTILINE)

    # Strip leading/trailing whitespace
    text = text.strip()

    # Restore code blocks
    text = _restore_code_blocks(text, code_blocks)

    return text


def clean_gemini_assistant(text: str) -> str:
    """Clean Gemini-specific artifacts from assistant responses.

    Removes:
    - "생각하는 과정 표시" at the beginning
    - "Sheets로 내보내기" after tables
    - "코드 스니펫" before code blocks
    - "소스" at the end

    Args:
        text: Raw assistant response text from Gemini

    Returns:
        Cleaned text
    """
    if not text:
        return text

    # Remove "생각하는 과정 표시" at the beginning
    text = re.sub(r"^생각하는 과정 표시\s*\n+", "", text)

    # Remove "Sheets로 내보내기" after tables (standalone line)
    text = re.sub(r"\n+Sheets로 내보내기\s*\n*", "\n", text)

    # Remove "코드 스니펫" before code blocks (standalone line)
    text = re.sub(r"\n*코드 스니펫\s*\n+", "\n\n", text)

    # Remove "소스" at the end
    text = re.sub(r"\n+소스\s*$", "", text)

    return text


def clean_grok_assistant(text: str) -> str:
    """Clean Grok-specific artifacts from assistant responses.

    Removes:
    - "Ns동안 생각함" at the beginning (thinking time indicator)
    - Favicon images and web page count footer at the end

    Args:
        text: Raw assistant response text from Grok

    Returns:
        Cleaned text
    """
    if not text:
        return text

    # Remove "Ns동안 생각함" at the beginning (e.g., "27s동안 생각함", "5s동안 생각함")
    text = re.sub(r"^\d+s동안 생각함\s*\n+", "", text)

    # Remove favicon images and web page count footer at the end
    # Pattern: multiple lines of ![](url) followed by "N개의 웹페이지" text
    # This handles both simple and complex patterns:
    # - Simple: images + "1개의 웹페이지 31개의 웹페이지"
    # - Complex: images + "𝕏 게시물 N개" + more images + "N개의 웹페이지"
    pattern = r"(\n*!\[\]\([^\)]+\)\s*)+(\n*𝕏 게시물[^\n]*)?(\n*!\[\]\([^\)]+\)\s*)*\n*\d+개의 웹페이지[^\n]*$"
    text = re.sub(pattern, "", text, flags=re.DOTALL)

    return text
