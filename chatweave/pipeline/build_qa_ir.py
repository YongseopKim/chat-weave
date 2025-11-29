"""Pipeline for building QAUnitIR from ConversationIR."""

from typing import List, Optional, Tuple

from chatweave.extractors.base import QueryExtractor
from chatweave.extractors.heuristic import HeuristicQueryExtractor
from chatweave.models.conversation import ConversationIR, MessageIR
from chatweave.models.qa_unit import QAUnit, QAUnitIR


def build_qa_ir(
    conversation: ConversationIR,
    extractor: Optional[QueryExtractor] = None,
) -> QAUnitIR:
    """Build QAUnitIR from ConversationIR.

    Groups messages into QA units and extracts question summaries.

    Args:
        conversation: ConversationIR to process
        extractor: QueryExtractor to use (defaults to HeuristicQueryExtractor)

    Returns:
        QAUnitIR containing extracted QA units
    """
    if extractor is None:
        extractor = HeuristicQueryExtractor()

    # Group messages into QA units
    qa_groups = _group_messages_into_qa(conversation.messages)

    # Convert groups to QAUnit objects
    qa_units = []
    for index, (user_msgs, assistant_msgs) in enumerate(qa_groups):
        qa_unit = _create_qa_unit(
            index=index,
            user_messages=user_msgs,
            assistant_messages=assistant_msgs,
            platform=conversation.platform,
            conversation_id=conversation.conversation_id,
            extractor=extractor,
        )
        qa_units.append(qa_unit)

    return QAUnitIR(
        platform=conversation.platform,
        conversation_id=conversation.conversation_id,
        qa_units=qa_units,
    )


def _group_messages_into_qa(
    messages: List[MessageIR],
) -> List[Tuple[List[MessageIR], List[MessageIR]]]:
    """Group messages into QA pairs.

    Strategy: Collect consecutive user messages, then consecutive assistant
    messages to form one QA unit.

    Args:
        messages: List of messages in conversation order

    Returns:
        List of tuples: (user_messages, assistant_messages)
    """
    groups = []
    current_user_msgs: List[MessageIR] = []
    current_assistant_msgs: List[MessageIR] = []

    for msg in messages:
        if msg.role == "user":
            # If we have assistant messages, this starts a new QA unit
            if current_assistant_msgs:
                if current_user_msgs:  # Only add if we have user messages
                    groups.append((current_user_msgs, current_assistant_msgs))
                current_user_msgs = []
                current_assistant_msgs = []
            current_user_msgs.append(msg)

        elif msg.role == "assistant":
            # Skip assistant messages before any user message
            if current_user_msgs:
                current_assistant_msgs.append(msg)

    # Don't forget the last group
    if current_user_msgs and current_assistant_msgs:
        groups.append((current_user_msgs, current_assistant_msgs))

    return groups


def _create_qa_unit(
    index: int,
    user_messages: List[MessageIR],
    assistant_messages: List[MessageIR],
    platform: str,
    conversation_id: str,
    extractor: QueryExtractor,
) -> QAUnit:
    """Create a QAUnit from grouped messages.

    Args:
        index: QA unit index (0-based)
        user_messages: List of user messages in this QA
        assistant_messages: List of assistant messages
        platform: Platform name
        conversation_id: Parent conversation ID
        extractor: QueryExtractor for summary extraction

    Returns:
        QAUnit object
    """
    qa_id = f"q{index:04d}"

    # Extract message IDs
    user_message_ids = [msg.id for msg in user_messages]
    assistant_message_ids = [msg.id for msg in assistant_messages]

    # Get question from user (combine if multiple messages)
    question_from_user = None
    if user_messages:
        user_contents = [msg.raw_content for msg in user_messages if msg.raw_content]
        if user_contents:
            question_from_user = "\n\n".join(user_contents)

    # Extract question summary from assistant response
    question_from_assistant_summary = None
    if assistant_messages:
        # Try first assistant message (usually has the summary)
        first_assistant_content = assistant_messages[0].raw_content
        question_from_assistant_summary = extractor.extract(first_assistant_content)

    # Get query hash from first user message
    user_query_hash = None
    if user_messages and user_messages[0].query_hash:
        user_query_hash = user_messages[0].query_hash

    return QAUnit(
        qa_id=qa_id,
        platform=platform,
        conversation_id=conversation_id,
        user_message_ids=user_message_ids,
        assistant_message_ids=assistant_message_ids,
        question_from_user=question_from_user,
        question_from_assistant_summary=question_from_assistant_summary,
        user_query_hash=user_query_hash,
    )
