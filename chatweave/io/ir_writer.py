"""IR writer for saving ConversationIR and QAUnitIR to JSON files."""

import json
from pathlib import Path

from chatweave.models.conversation import ConversationIR
from chatweave.models.qa_unit import QAUnitIR
from chatweave.models.session import MultiModelSessionIR


def _get_unique_path(output_dir: Path, base_name: str, extension: str = ".json") -> Path:
    """Get unique file path, adding numeric suffix if file exists.

    Args:
        output_dir: Directory for output file
        base_name: Base filename without extension
        extension: File extension (default: .json)

    Returns:
        Unique Path that doesn't exist yet

    Examples:
        If chatgpt_conv_abc123.json exists:
        - Returns chatgpt_conv_abc123_1.json
        If chatgpt_conv_abc123_1.json also exists:
        - Returns chatgpt_conv_abc123_2.json
    """
    output_path = output_dir / f"{base_name}{extension}"

    if not output_path.exists():
        return output_path

    # File exists, find unique suffix
    counter = 1
    while True:
        output_path = output_dir / f"{base_name}_{counter}{extension}"
        if not output_path.exists():
            return output_path
        counter += 1


def write_conversation_ir(
    conversation_ir: ConversationIR, output_dir: Path, indent: int = 2
) -> Path:
    """Write ConversationIR to JSON file.

    Output filename format: {platform}_conv_{conversation_id}.json
    e.g., chatgpt_conv_692ad5eb-bb18-8320-bd15-9ae4442dcb26.json

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

    # Generate unique filename (adds _1, _2, etc. if file exists)
    base_name = f"{conversation_ir.platform}_conv_{conversation_ir.conversation_id}"
    output_path = _get_unique_path(output_dir, base_name)

    # Convert to dictionary
    ir_dict = conversation_ir.to_dict()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_dict, f, indent=indent, ensure_ascii=False)

    return output_path


def write_qa_unit_ir(
    qa_unit_ir: QAUnitIR, output_dir: Path, indent: int = 2
) -> Path:
    """Write QAUnitIR to JSON file.

    Output filename format: {platform}_qau_{conversation_id}.json
    e.g., chatgpt_qau_692ad5eb-bb18-8320-bd15-9ae4442dcb26.json

    Args:
        qa_unit_ir: QAUnitIR object to save
        output_dir: Directory to save JSON file
        indent: JSON indentation level (default: 2)

    Returns:
        Path to written JSON file

    Raises:
        OSError: If directory creation or file writing fails
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename (adds _1, _2, etc. if file exists)
    base_name = f"{qa_unit_ir.platform}_qau_{qa_unit_ir.conversation_id}"
    output_path = _get_unique_path(output_dir, base_name)

    # Convert to dictionary
    ir_dict = qa_unit_ir.to_dict()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_dict, f, indent=indent, ensure_ascii=False)

    return output_path


def write_session_ir(
    session_ir: MultiModelSessionIR, output_dir: Path, indent: int = 2
) -> Path:
    """Write MultiModelSessionIR to JSON file.

    Output filename format: mms_{session_id}.json

    Args:
        session_ir: MultiModelSessionIR object to save
        output_dir: Directory to save JSON file
        indent: JSON indentation level (default: 2)

    Returns:
        Path to written JSON file

    Raises:
        OSError: If directory creation or file writing fails
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename (adds _1, _2, etc. if file exists)
    base_name = f"mms_{session_ir.session_id}"
    output_path = _get_unique_path(output_dir, base_name)

    # Convert to dictionary
    ir_dict = session_ir.to_dict()

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ir_dict, f, indent=indent, ensure_ascii=False)

    return output_path
