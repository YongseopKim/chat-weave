"""Hashing utilities for generating query identifiers."""

import hashlib


def compute_query_hash(text: str) -> str:
    """Compute SHA256 hash of text for query matching.

    Used to identify identical questions across platforms.
    Hash is computed on normalized text to ensure consistency.

    Args:
        text: Normalized text content

    Returns:
        Hexadecimal SHA256 hash string (64 characters)
    """
    if not text:
        return ""

    # Encode text to UTF-8 bytes
    text_bytes = text.encode("utf-8")

    # Compute SHA256 hash
    hash_obj = hashlib.sha256(text_bytes)

    # Return hexadecimal digest
    return hash_obj.hexdigest()
