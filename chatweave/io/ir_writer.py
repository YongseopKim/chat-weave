"""IR writer for saving ConversationIR to JSON files."""

import json
from pathlib import Path

from chatweave.models.conversation import ConversationIR


def write_conversation_ir(
    conversation_ir: ConversationIR, output_dir: Path, indent: int = 2
) -> Path:
    """Write ConversationIR to JSON file.

    Output filename format: {platform}_{conversation_id}.json
    e.g., chatgpt_692ad5eb-bb18-8320-bd15-9ae4442dcb26.json

    Args:
        conversation_ir: ConversationIR object to save
        output_dir: Directory to save JSON file
        indent: JSON indentation level (default: 2)

    Returns:
        Path to written JSON file

    Raises:
        OSError: If directory creation or file writing fails
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    filename = f"{conversation_ir.platform}_{conversation_ir.conversation_id}.json"
    output_path = output_dir / filename

    # Convert to dictionary
    ir_dict = conversation_ir.to_dict()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_dict, f, indent=indent, ensure_ascii=False)

    return output_path
