"""Text normalization utilities for consistent processing."""

import re


def normalize_text(text: str) -> str:
    """Normalize text by cleaning whitespace and newlines.

    Normalization steps:
    1. Replace multiple consecutive spaces with single space
    2. Replace multiple consecutive newlines with single newline
    3. Strip leading/trailing whitespace
    4. Normalize Unicode characters (NFC form)

    Args:
        text: Raw text content

    Returns:
        Normalized text string
    """
    if not text:
        return text

    # Normalize Unicode to NFC form
    import unicodedata

    text = unicodedata.normalize("NFC", text)

    # Replace multiple spaces with single space
    text = re.sub(r" +", " ", text)

    # Replace multiple newlines with single newline
    text = re.sub(r"\n\n+", "\n\n", text)

    # Strip leading/trailing whitespace
    text = text.strip()

    return text
