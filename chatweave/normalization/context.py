"""Normalization context for sharing state between passes."""

from dataclasses import dataclass, field


@dataclass
class NormalizationContext:
    """Shared state between normalization passes.

    Attributes:
        code_blocks: List of extracted code blocks (populated by CodeBlockProtectionPass).
        placeholder_base: Format string for code block placeholders.
    """

    code_blocks: list[str] = field(default_factory=list)
    placeholder_base: str = "\x00CODE_BLOCK_{}\x00"
