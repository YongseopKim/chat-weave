"""Pipeline for building MultiModelSessionIR from multiple QAUnitIR."""

from typing import Any, Dict, List, Optional

from chatweave.matchers.base import QueryMatcher
from chatweave.matchers.hash import HashQueryMatcher
from chatweave.models.qa_unit import QAUnit, QAUnitIR
from chatweave.models.session import (
    MultiModelSessionIR,
    PerPlatformQARef,
    PromptGroup,
)


def build_session_ir(
    qa_units: Dict[str, QAUnitIR],
    session_id: str,
    matcher: Optional[QueryMatcher] = None,
) -> MultiModelSessionIR:
    """Build MultiModelSessionIR from multiple QAUnitIR.

    Aligns QA units from different platforms by matching questions.

    Args:
        qa_units: Dict mapping platform name to QAUnitIR
        session_id: Identifier for this session (e.g., directory name)
        matcher: QueryMatcher to use (defaults to HashQueryMatcher)

    Returns:
        MultiModelSessionIR with aligned prompt groups
    """
    if matcher is None:
        matcher = HashQueryMatcher()

    # Collect all QA units from all platforms
    all_units = _collect_all_units(qa_units)

    # Group QA units by question similarity
    groups = matcher.match(all_units)

    # Create PromptGroup objects with dependency tracking
    prompts = _create_prompt_groups(groups, qa_units)

    # Build conversation reference list
    conversations = _build_conversation_list(qa_units)

    return MultiModelSessionIR(
        session_id=session_id,
        platforms=list(qa_units.keys()),
        conversations=conversations,
        prompts=prompts,
    )


def _collect_all_units(qa_units: Dict[str, QAUnitIR]) -> List[QAUnit]:
    """Flatten all QA units from all platforms.

    Args:
        qa_units: Dict mapping platform name to QAUnitIR

    Returns:
        Flat list of all QA units
    """
    all_units = []
    for qa_ir in qa_units.values():
        all_units.extend(qa_ir.qa_units)
    return all_units


def _build_conversation_list(qa_units: Dict[str, QAUnitIR]) -> List[Dict[str, str]]:
    """Build list of conversation references.

    Args:
        qa_units: Dict mapping platform name to QAUnitIR

    Returns:
        List of dicts with platform and conversation_id
    """
    conversations = []
    for platform, qa_ir in qa_units.items():
        conversations.append({
            "platform": platform,
            "conversation_id": qa_ir.conversation_id,
        })
    return conversations


def _create_prompt_groups(
    groups: List[List[QAUnit]],
    qa_units: Dict[str, QAUnitIR],
) -> List[PromptGroup]:
    """Create PromptGroup objects with dependency tracking.

    Args:
        groups: List of QA unit groups (same question)
        qa_units: Dict mapping platform to QAUnitIR (for context)

    Returns:
        List of PromptGroup objects
    """
    prompts = []

    for index, group in enumerate(groups):
        prompt_key = f"p{index:04d}"

        # Select canonical unit (platform priority: alphabetical)
        canonical_unit = _select_canonical_unit(group)

        # Build canonical_prompt
        canonical_prompt = _build_canonical_prompt(canonical_unit)

        # Build depends_on (sequential dependency)
        depends_on = []
        if index > 0:
            # This prompt depends on the previous one
            depends_on = [f"p{index - 1:04d}"]

        # Build per-platform references
        per_platform = _build_per_platform_refs(group, depends_on, qa_units)

        prompt_group = PromptGroup(
            prompt_key=prompt_key,
            canonical_prompt=canonical_prompt,
            depends_on=depends_on,
            per_platform=per_platform,
        )
        prompts.append(prompt_group)

    return prompts


def _select_canonical_unit(group: List[QAUnit]) -> QAUnit:
    """Select canonical unit by platform priority.

    Platform priority: alphabetical order (chatgpt > claude > gemini)

    Args:
        group: List of QA units answering the same question

    Returns:
        Selected canonical QAUnit
    """
    # Sort by platform alphabetically
    sorted_units = sorted(group, key=lambda u: u.platform)
    return sorted_units[0]


def _build_canonical_prompt(unit: QAUnit) -> Dict[str, Any]:
    """Build canonical_prompt dict from QA unit.

    Args:
        unit: The canonical QA unit

    Returns:
        Dict with text, language, and source
    """
    # Use question_from_user if available, otherwise assistant_summary
    text = unit.question_from_user
    if not text or text.strip() == "":
        text = unit.question_from_assistant_summary

    return {
        "text": text,
        "language": None,  # Deferred to v0.4 (langdetect)
        "source": {
            "platform": unit.platform,
            "qa_id": unit.qa_id,
        },
    }


def _build_per_platform_refs(
    group: List[QAUnit],
    depends_on: List[str],
    qa_units: Dict[str, QAUnitIR],
) -> List[PerPlatformQARef]:
    """Build per-platform QA references.

    Args:
        group: List of QA units in this prompt group
        depends_on: List of prompt_keys this depends on
        qa_units: Dict mapping platform to QAUnitIR (for missing_context check)

    Returns:
        List of PerPlatformQARef objects
    """
    refs = []

    for unit in group:
        # Determine prompt_text
        prompt_text = unit.question_from_user
        if not prompt_text or prompt_text.strip() == "":
            prompt_text = unit.question_from_assistant_summary

        # Determine missing_prompt
        missing_prompt = False
        if not unit.question_from_user or unit.question_from_user.strip() == "":
            missing_prompt = True

        # Determine missing_context
        # If this prompt depends on previous prompts, check if this platform
        # has those dependent QA units
        missing_context = False
        if depends_on:
            # Get the dependent prompt index (e.g., "p0000" -> 0)
            for dep_key in depends_on:
                dep_index = int(dep_key[1:])  # Remove 'p' prefix
                # Check if this platform has a QA unit at that index
                platform_qa_ir = qa_units.get(unit.platform)
                if platform_qa_ir and dep_index < len(platform_qa_ir.qa_units):
                    # Context exists
                    pass
                else:
                    missing_context = True
                    break

        # prompt_similarity: 1.0 for hash-based match (since they're in same group)
        prompt_similarity = 1.0 if unit.user_query_hash else None

        ref = PerPlatformQARef(
            platform=unit.platform,
            qa_id=unit.qa_id,
            conversation_id=unit.conversation_id,
            prompt_text=prompt_text,
            prompt_similarity=prompt_similarity,
            missing_prompt=missing_prompt,
            missing_context=missing_context,
        )
        refs.append(ref)

    return refs
