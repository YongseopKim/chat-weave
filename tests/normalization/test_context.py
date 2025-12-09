"""Tests for NormalizationContext."""

import pytest

from chatweave.normalization.context import NormalizationContext


class TestNormalizationContext:
    """Test NormalizationContext dataclass."""

    def test_default_code_blocks_empty(self):
        """Default code_blocks should be empty list."""
        ctx = NormalizationContext()
        assert ctx.code_blocks == []

    def test_default_placeholder_base(self):
        """Default placeholder_base should use null byte delimiters."""
        ctx = NormalizationContext()
        assert "\x00" in ctx.placeholder_base
        assert "CODE_BLOCK" in ctx.placeholder_base

    def test_placeholder_format(self):
        """Placeholder should be formattable with index."""
        ctx = NormalizationContext()
        placeholder = ctx.placeholder_base.format(0)
        assert placeholder == "\x00CODE_BLOCK_0\x00"
        placeholder = ctx.placeholder_base.format(42)
        assert placeholder == "\x00CODE_BLOCK_42\x00"

    def test_code_blocks_mutable(self):
        """code_blocks should be mutable for pass to populate."""
        ctx = NormalizationContext()
        ctx.code_blocks.append("```python\ncode\n```")
        assert len(ctx.code_blocks) == 1

    def test_separate_instances_independent(self):
        """Each context instance should have independent code_blocks."""
        ctx1 = NormalizationContext()
        ctx2 = NormalizationContext()
        ctx1.code_blocks.append("block1")
        assert ctx2.code_blocks == []
