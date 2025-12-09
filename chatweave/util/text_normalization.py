"""Text normalization utilities for consistent processing.

This module provides a backward-compatible facade over the pass-based
normalization system in chatweave.normalization.
"""

import re

from chatweave.normalization import NormalizationContext, create_default_runner

# Lazy-initialized default runner
_default_runner = None


def _get_runner():
    """Get or create the default PassRunner instance."""
    global _default_runner
    if _default_runner is None:
        _default_runner = create_default_runner()
    return _default_runner


def normalize_text(text: str) -> str:
    """Normalize text by cleaning whitespace, newlines, and escaped characters.

    Normalization steps (via pass-based architecture):
    1. Extract code blocks (preserve them from normalization)
    2. Normalize Unicode characters (NFC form)
    3. Normalize list structure (dedent, indentation, empty items)
    4. Normalize table structure (root level, row spacing)
    5. Normalize whitespace (continuation, spaces, newlines)
    6. Normalize escape sequences (unescape markdown, smart quotes)
    7. Restore code blocks

    Args:
        text: Raw text content

    Returns:
        Normalized text string
    """
    if not text:
        return text

    runner = _get_runner()
    ctx = NormalizationContext()
    return runner.run(text, ctx)


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
