"""Tests for NormalizationPass ABC and PassRunner."""

import pytest

from chatweave.normalization.base import (
    NormalizationPass,
    PassRunner,
    PostConditionError,
)
from chatweave.normalization.context import NormalizationContext


class IdentityPass(NormalizationPass):
    """A pass that does nothing (for testing)."""

    @property
    def name(self) -> str:
        return "Identity"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return text


class UppercasePass(NormalizationPass):
    """A pass that uppercases text (for testing)."""

    @property
    def name(self) -> str:
        return "Uppercase"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return text.upper()


class AppendXPass(NormalizationPass):
    """A pass that appends 'X' until length >= 5 (for convergence testing)."""

    @property
    def name(self) -> str:
        return "AppendX"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        if len(text) < 5:
            return text + "X"
        return text


class ConditionalPass(NormalizationPass):
    """A pass with pre_condition that checks for 'trigger' keyword."""

    @property
    def name(self) -> str:
        return "Conditional"

    def pre_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return "trigger" in text

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return text.replace("trigger", "TRIGGERED")


class FailingPostConditionPass(NormalizationPass):
    """A pass whose post_condition always fails (for testing strict mode)."""

    @property
    def name(self) -> str:
        return "FailingPostCondition"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return text

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return False


class NoLowercasePostConditionPass(NormalizationPass):
    """A pass that uppercases and checks no lowercase remains."""

    @property
    def name(self) -> str:
        return "NoLowercase"

    def action(self, text: str, ctx: NormalizationContext) -> str:
        return text.upper()

    def post_condition(self, text: str, ctx: NormalizationContext) -> bool:
        return text == text.upper()


class TestNormalizationPassABC:
    """Test NormalizationPass abstract base class."""

    def test_cannot_instantiate_abc(self):
        """NormalizationPass cannot be instantiated directly."""
        with pytest.raises(TypeError):
            NormalizationPass()

    def test_concrete_pass_requires_name(self):
        """Concrete pass must implement name property."""

        class NoNamePass(NormalizationPass):
            def action(self, text: str, ctx: NormalizationContext) -> str:
                return text

        with pytest.raises(TypeError):
            NoNamePass()

    def test_concrete_pass_requires_action(self):
        """Concrete pass must implement action method."""

        class NoActionPass(NormalizationPass):
            @property
            def name(self) -> str:
                return "NoAction"

        with pytest.raises(TypeError):
            NoActionPass()

    def test_default_pre_condition_returns_true(self):
        """Default pre_condition should return True."""
        pass_ = IdentityPass()
        ctx = NormalizationContext()
        assert pass_.pre_condition("any text", ctx) is True

    def test_default_post_condition_returns_true(self):
        """Default post_condition should return True."""
        pass_ = IdentityPass()
        ctx = NormalizationContext()
        assert pass_.post_condition("any text", ctx) is True


class TestPassRunner:
    """Test PassRunner execution logic."""

    def test_run_single_pass(self):
        """Runner should execute single pass."""
        runner = PassRunner([UppercasePass()])
        result = runner.run("hello")
        assert result == "HELLO"

    def test_run_multiple_passes_in_order(self):
        """Runner should execute passes in order."""

        class PrependAPass(NormalizationPass):
            @property
            def name(self) -> str:
                return "PrependA"

            def action(self, text: str, ctx: NormalizationContext) -> str:
                if not text.startswith("A"):
                    return "A" + text
                return text

        runner = PassRunner([PrependAPass(), UppercasePass()])
        result = runner.run("hello")
        assert result == "AHELLO"

    def test_pass_convergence(self):
        """Each pass should repeat until no change."""
        runner = PassRunner([AppendXPass()])
        result = runner.run("ab")
        assert result == "abXXX"  # Appends X until length >= 5
        assert len(result) == 5

    def test_pass_convergence_already_stable(self):
        """Pass should run once if already stable."""
        runner = PassRunner([AppendXPass()])
        result = runner.run("already long enough")
        assert result == "already long enough"

    def test_pre_condition_skips_pass(self):
        """Pass should be skipped if pre_condition returns False."""
        runner = PassRunner([ConditionalPass()])
        result = runner.run("no keyword here")
        assert result == "no keyword here"

    def test_pre_condition_runs_pass(self):
        """Pass should run if pre_condition returns True."""
        runner = PassRunner([ConditionalPass()])
        result = runner.run("has trigger word")
        assert result == "has TRIGGERED word"

    def test_context_passed_to_all_passes(self):
        """Same context should be passed through all passes."""

        class RecordingPass(NormalizationPass):
            def __init__(self, marker: str):
                self.marker = marker

            @property
            def name(self) -> str:
                return f"Recording_{self.marker}"

            def action(self, text: str, ctx: NormalizationContext) -> str:
                ctx.code_blocks.append(self.marker)
                return text

        runner = PassRunner([RecordingPass("A"), RecordingPass("B")])
        ctx = NormalizationContext()
        runner.run("text", ctx)
        assert ctx.code_blocks == ["A", "B"]

    def test_context_created_if_not_provided(self):
        """Runner should create context if not provided."""
        runner = PassRunner([IdentityPass()])
        result = runner.run("text")  # No ctx argument
        assert result == "text"

    def test_empty_passes_list(self):
        """Runner with no passes should return text unchanged."""
        runner = PassRunner([])
        result = runner.run("hello")
        assert result == "hello"


class TestPassRunnerStrictMode:
    """Test PassRunner strict mode (post_condition enforcement)."""

    def test_strict_false_ignores_post_condition_failure(self):
        """Non-strict mode should not raise on post_condition failure."""
        runner = PassRunner([FailingPostConditionPass()], strict=False)
        result = runner.run("text")
        assert result == "text"  # No exception

    def test_strict_true_raises_on_post_condition_failure(self):
        """Strict mode should raise PostConditionError on failure."""
        runner = PassRunner([FailingPostConditionPass()], strict=True)
        with pytest.raises(PostConditionError) as exc_info:
            runner.run("text")
        assert exc_info.value.pass_name == "FailingPostCondition"

    def test_post_condition_error_contains_pass_name(self):
        """PostConditionError should include pass name."""
        runner = PassRunner([FailingPostConditionPass()], strict=True)
        with pytest.raises(PostConditionError) as exc_info:
            runner.run("text")
        assert "FailingPostCondition" in str(exc_info.value)

    def test_post_condition_checked_after_convergence(self):
        """Post_condition should be checked after pass converges."""
        runner = PassRunner([NoLowercasePostConditionPass()], strict=True)
        result = runner.run("hello")
        assert result == "HELLO"  # No exception, post_condition passes

    def test_strict_mode_default_is_false(self):
        """Default strict mode should be False."""
        runner = PassRunner([FailingPostConditionPass()])
        result = runner.run("text")  # Should not raise
        assert result == "text"


class TestPostConditionError:
    """Test PostConditionError exception."""

    def test_error_attributes(self):
        """Error should have pass_name and message attributes."""
        error = PostConditionError(
            pass_name="TestPass",
            message="invariant violated",
            text_sample="sample...",
        )
        assert error.pass_name == "TestPass"
        assert error.message == "invariant violated"
        assert error.text_sample == "sample..."

    def test_error_string_representation(self):
        """Error string should include pass name and message."""
        error = PostConditionError(
            pass_name="TestPass", message="invariant violated"
        )
        error_str = str(error)
        assert "TestPass" in error_str
        assert "invariant violated" in error_str

    def test_error_inherits_from_exception(self):
        """PostConditionError should be an Exception."""
        error = PostConditionError(pass_name="Test", message="msg")
        assert isinstance(error, Exception)


class TestPassRunnerMaxIterations:
    """Test PassRunner safety limit for convergence."""

    def test_max_iterations_prevents_infinite_loop(self):
        """Runner should stop after max iterations even if not converged."""

        class InfinitePass(NormalizationPass):
            @property
            def name(self) -> str:
                return "Infinite"

            def action(self, text: str, ctx: NormalizationContext) -> str:
                return text + "X"  # Never converges

        runner = PassRunner([InfinitePass()])
        result = runner.run("start")
        # Should have added X many times but stopped at limit
        assert len(result) > len("start")
        assert len(result) <= len("start") + 100  # max_iterations default
