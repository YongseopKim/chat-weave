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
    3. Replace multiple consecutive spaces with single space
    4. Replace lines with only whitespace with empty lines
    5. Replace multiple consecutive newlines with double newline
    6. Unescape markdown characters: \\*\\* -> **, smart quotes -> regular quotes
    7. Unescape characters in headings: \\. -> ., \\[ -> [, \\] -> ]
    8. Strip leading/trailing whitespace
    9. Restore code blocks

    Args:
        text: Raw text content

    Returns:
        Normalized text string
    """
    if not text:
        return text

    # Extract code blocks to preserve them
    text, code_blocks = _extract_code_blocks(text)

    # Normalize Unicode to NFC form
    text = unicodedata.normalize("NFC", text)

    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace lines with only whitespace with empty lines
    # This handles \n \n patterns (lines with only spaces)
    # Apply repeatedly to handle consecutive whitespace-only lines
    while True:
        new_text = re.sub(r"\n[ \t]+\n", "\n\n", text)
        if new_text == text:
            break
        text = new_text

    # Replace multiple newlines with double newline
    text = re.sub(r"\n\n+", "\n\n", text)

    # Unescape markdown bold/italic markers
    text = text.replace("\\*\\*", "**")

    # Normalize smart quotes to regular quotes
    text = text.replace('"', '"')
    text = text.replace('"', '"')

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
