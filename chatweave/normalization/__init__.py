"""Pass-based text normalization module.

Provides a compiler-pass inspired architecture for text normalization.
"""

from chatweave.normalization.base import (
    NormalizationPass,
    PassRunner,
    PostConditionError,
)
from chatweave.normalization.context import NormalizationContext
from chatweave.normalization.passes import (
    CodeBlockProtectionPass,
    CodeBlockRestorationPass,
    EscapeSequencePass,
    LineContinuationPass,
    ListStructurePass,
    TableStructurePass,
    UnicodeNormalizationPass,
    WhitespacePass,
)


def create_default_runner(strict: bool = False) -> PassRunner:
    """Create a PassRunner with all default normalization passes.

    Args:
        strict: If True, raise PostConditionError on post_condition failures.

    Returns:
        Configured PassRunner with all 8 normalization passes.
    """
    passes = [
        CodeBlockProtectionPass(),
        UnicodeNormalizationPass(),
        ListStructurePass(),
        TableStructurePass(),
        LineContinuationPass(),  # Must run before WhitespacePass
        WhitespacePass(),
        EscapeSequencePass(),
        CodeBlockRestorationPass(),
    ]
    return PassRunner(passes, strict=strict)


__all__ = [
    # Base classes
    "NormalizationPass",
    "PassRunner",
    "PostConditionError",
    "NormalizationContext",
    # Passes
    "CodeBlockProtectionPass",
    "CodeBlockRestorationPass",
    "EscapeSequencePass",
    "LineContinuationPass",
    "ListStructurePass",
    "TableStructurePass",
    "UnicodeNormalizationPass",
    "WhitespacePass",
    # Factory
    "create_default_runner",
]
