"""Hash-based query matcher."""

from typing import Dict, List

from chatweave.matchers.base import QueryMatcher
from chatweave.models.qa_unit import QAUnit


class HashQueryMatcher(QueryMatcher):
    """Match QA units by exact user_query_hash equality.

    Groups QA units that have identical user_query_hash values,
    indicating they answer the same question. Units without a hash
    become individual singleton groups.
    """

    def match(self, units: List[QAUnit]) -> List[List[QAUnit]]:
        """Group QA units by user_query_hash.

        Args:
            units: List of QA units from multiple platforms

        Returns:
            List of groups ordered by first occurrence.
            Units with same hash are grouped together.
            Units without hash (None) become singleton groups at the end.
        """
        hash_groups: Dict[str, List[QAUnit]] = {}
        no_hash_units: List[QAUnit] = []
        hash_order: List[str] = []

        for unit in units:
            if unit.user_query_hash is None:
                no_hash_units.append(unit)
            else:
                hash_val = unit.user_query_hash
                if hash_val not in hash_groups:
                    hash_groups[hash_val] = []
                    hash_order.append(hash_val)
                hash_groups[hash_val].append(unit)

        # Build result: hash groups first (in order of first occurrence),
        # then no-hash units as singletons
        result: List[List[QAUnit]] = []

        for hash_val in hash_order:
            result.append(hash_groups[hash_val])

        for unit in no_hash_units:
            result.append([unit])

        return result
