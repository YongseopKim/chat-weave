"""Platform inference from filename and metadata."""

import re
from pathlib import Path
from typing import Optional

from chatweave.models.conversation import Platform


# Filename patterns for platform inference
PLATFORM_PATTERNS = {
    "chatgpt": re.compile(r"^chatgpt[_-]", re.IGNORECASE),
    "claude": re.compile(r"^claude[_-]", re.IGNORECASE),
    "gemini": re.compile(r"^gemini[_-]", re.IGNORECASE),
}


def infer_platform_from_filename(filename: str) -> Optional[Platform]:
    """Infer platform from filename pattern.

    Patterns:
        - chatgpt_*.jsonl -> chatgpt
        - claude_*.jsonl -> claude
        - gemini_*.jsonl -> gemini

    Args:
        filename: Name of the file (not full path)

    Returns:
        Platform literal if matched, None otherwise

    Examples:
        >>> infer_platform_from_filename("chatgpt_20251129T114242.jsonl")
        'chatgpt'
        >>> infer_platform_from_filename("claude-export.jsonl")
        'claude'
        >>> infer_platform_from_filename("unknown.jsonl")
        None
    """
    for platform, pattern in PLATFORM_PATTERNS.items():
        if pattern.match(filename):
            return platform  # type: ignore
    return None


def infer_platform(
    jsonl_path: Path,
    metadata: Optional[dict] = None,
    override: Optional[Platform] = None,
) -> Platform:
    """Infer platform with priority: override > metadata > filename.

    Args:
        jsonl_path: Path to JSONL file
        metadata: Parsed metadata dict (if already loaded)
        override: Explicit platform override from CLI

    Returns:
        Platform literal

    Raises:
        ValueError: If platform cannot be inferred

    Examples:
        >>> from pathlib import Path
        >>> infer_platform(Path("chatgpt_export.jsonl"), override="claude")
        'claude'
        >>> infer_platform(Path("chatgpt_export.jsonl"), metadata={"platform": "chatgpt"})
        'chatgpt'
        >>> infer_platform(Path("chatgpt_export.jsonl"))
        'chatgpt'
    """
    # Priority 1: Explicit override
    if override:
        return override

    # Priority 2: Metadata
    if metadata and metadata.get("platform"):
        platform = metadata.get("platform")
        if platform in ("chatgpt", "claude", "gemini"):
            return platform  # type: ignore

    # Priority 3: Filename
    platform = infer_platform_from_filename(jsonl_path.name)
    if platform:
        return platform

    # Cannot infer
    raise ValueError(
        f"Cannot infer platform for '{jsonl_path.name}'. "
        f"Either add 'platform' to metadata, rename file to "
        f"'chatgpt_*.jsonl', 'claude_*.jsonl', or 'gemini_*.jsonl', "
        f"or use --platform option."
    )
