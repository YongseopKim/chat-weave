"""Base classes for normalization passes."""

from abc import ABC, abstractmethod
from typing import Optional

from chatweave.normalization.context import NormalizationContext


class PostConditionError(Exception):
    """Raised when a post_condition fails in strict mode."""

    def __init__(
        self, pass_name: str, message: str, text_sample: str = ""
    ) -> None:
        self.pass_name = pass_name
        self.message = message
        self.text_sample = text_sample
        super().__init__(f"Pass '{pass_name}' post_condition failed: {message}")


class NormalizationPass(ABC):
    """Abstract base class for normalization passes.

    Each pass represents a single transformation step in the normalization pipeline.
    Passes are executed in sequence, with each pass repeating until convergence.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name for this pass."""
        pass

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        """Check if this pass should run.

        Args:
            text: Current text state.
            ctx: Shared normalization context.

        Returns:
            True if pass should run, False to skip.
        """
        return True

    @abstractmethod
    def action(self, text: str, ctx: NormalizationContext) -> str:
        """Transform the text.

        Args:
            text: Current text state.
            ctx: Shared normalization context.

        Returns:
            Transformed text.
        """
        pass

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        """Check invariant that must hold after this pass.

        Args:
            text: Text after action completed.
            ctx: Shared normalization context.

        Returns:
            True if invariant holds, False if violated.
        """
        return True


class PassRunner:
    """Executes normalization passes with per-pass convergence.

    Each pass repeats until no change (convergence), then moves to next pass.
    In strict mode, PostConditionError is raised if post_condition fails.
    """

    def __init__(
        self,
        passes: list[NormalizationPass],
        strict: bool = False,
        max_iterations: int = 100,
    ) -> None:
        """Initialize PassRunner.

        Args:
            passes: List of passes to execute in order.
            strict: If True, raise PostConditionError on post_condition failure.
            max_iterations: Safety limit for convergence loop per pass.
        """
        self.passes = passes
        self.strict = strict
        self.max_iterations = max_iterations

    def run(
        self, text: str, ctx: Optional[NormalizationContext] = None
    ) -> str:
        """Run all passes in sequence.

        Args:
            text: Input text to normalize.
            ctx: Optional context for sharing state between passes.
                 If not provided, a new context is created.

        Returns:
            Normalized text after all passes complete.

        Raises:
            PostConditionError: If strict=True and a post_condition fails.
        """
        if ctx is None:
            ctx = NormalizationContext()

        for pass_ in self.passes:
            # Check pre_condition
            if not pass_.pre_condition(text, ctx):
                continue

            # Run until convergence (or max_iterations)
            for _ in range(self.max_iterations):
                new_text = pass_.action(text, ctx)
                if new_text == text:
                    break
                text = new_text

            # Check post_condition in strict mode
            if self.strict and not pass_.post_condition(text, ctx):
                raise PostConditionError(
                    pass_name=pass_.name,
                    message="Post-condition check failed",
                    text_sample=text[:200] if len(text) > 200 else text,
                )

        return text
