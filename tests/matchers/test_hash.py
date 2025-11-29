"""Tests for hash-based query matcher."""

import pytest

from chatweave.matchers.hash import HashQueryMatcher
from chatweave.models.qa_unit import QAUnit


class TestHashQueryMatcher:
    """Tests for HashQueryMatcher."""

    def test_match_identical_hashes(self):
        """Test grouping units with identical hashes."""
        units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test-1",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0000",
                platform="claude",
                conversation_id="test-2",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0000",
                platform="gemini",
                conversation_id="test-3",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
        ]

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        assert len(groups) == 1
        assert len(groups[0]) == 3
        assert all(u.user_query_hash == "hash1" for u in groups[0])

    def test_match_different_hashes(self):
        """Test grouping units with different hashes."""
        units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test-1",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0001",
                platform="chatgpt",
                conversation_id="test-1",
                user_message_ids=["m0002"],
                assistant_message_ids=["m0003"],
                user_query_hash="hash2",
            ),
        ]

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        assert len(groups) == 2
        assert len(groups[0]) == 1
        assert len(groups[1]) == 1
        assert groups[0][0].user_query_hash == "hash1"
        assert groups[1][0].user_query_hash == "hash2"

    def test_match_preserves_order(self):
        """Test that groups are ordered by first occurrence."""
        units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash_b",
            ),
            QAUnit(
                qa_id="q0001",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0002"],
                assistant_message_ids=["m0003"],
                user_query_hash="hash_a",
            ),
            QAUnit(
                qa_id="q0002",
                platform="claude",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash_b",
            ),
        ]

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        # Order should be hash_b, hash_a (first occurrence)
        assert len(groups) == 2
        assert groups[0][0].user_query_hash == "hash_b"
        assert groups[1][0].user_query_hash == "hash_a"

    def test_match_units_without_hash(self):
        """Test units without hash become singletons."""
        units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0001",
                platform="claude",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash=None,  # No hash
            ),
            QAUnit(
                qa_id="q0002",
                platform="gemini",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash=None,  # No hash
            ),
        ]

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        # hash1 group + 2 singletons
        assert len(groups) == 3
        assert len(groups[0]) == 1  # hash1 group
        assert len(groups[1]) == 1  # singleton 1
        assert len(groups[2]) == 1  # singleton 2
        assert groups[1][0].user_query_hash is None
        assert groups[2][0].user_query_hash is None

    def test_match_empty_list(self):
        """Test matching empty list."""
        matcher = HashQueryMatcher()
        groups = matcher.match([])

        assert groups == []

    def test_match_mixed_hashes_and_none(self):
        """Test mixture of hashed and non-hashed units."""
        units = [
            QAUnit(
                qa_id="q0000",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0001",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0002"],
                assistant_message_ids=["m0003"],
                user_query_hash=None,
            ),
            QAUnit(
                qa_id="q0002",
                platform="claude",
                conversation_id="test",
                user_message_ids=["m0000"],
                assistant_message_ids=["m0001"],
                user_query_hash="hash1",
            ),
            QAUnit(
                qa_id="q0003",
                platform="chatgpt",
                conversation_id="test",
                user_message_ids=["m0004"],
                assistant_message_ids=["m0005"],
                user_query_hash="hash2",
            ),
        ]

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        # hash1 (2 units), hash2 (1 unit), None singleton
        assert len(groups) == 3
        assert len(groups[0]) == 2  # hash1
        assert len(groups[1]) == 1  # hash2
        assert len(groups[2]) == 1  # None

    def test_multi_platform_same_hash(self):
        """Test realistic scenario: 3 platforms, 4 questions each."""
        units = []
        platforms = ["chatgpt", "claude", "gemini"]
        hashes = ["hash_a", "hash_b", "hash_c", "hash_d"]

        for hash_val in hashes:
            for platform in platforms:
                units.append(
                    QAUnit(
                        qa_id=f"q{hashes.index(hash_val):04d}",
                        platform=platform,
                        conversation_id=f"{platform}-test",
                        user_message_ids=["m0000"],
                        assistant_message_ids=["m0001"],
                        user_query_hash=hash_val,
                    )
                )

        matcher = HashQueryMatcher()
        groups = matcher.match(units)

        # Should have 4 groups (one per hash)
        assert len(groups) == 4
        # Each group should have 3 units (one per platform)
        for group in groups:
            assert len(group) == 3
            # All units in group should have same hash
            assert len(set(u.user_query_hash for u in group)) == 1
