"""JSONL file loading utilities."""

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple


def load_jsonl(
    file_path: Path,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Load JSONL file and separate metadata, messages, and artifacts.

    Expected format:
    - First line: {"_meta": true, "platform": "...", "url": "...", "exported_at": "..."}
    - Message lines: {"role": "user|assistant", "content": "...", "timestamp": "..."}
    - Artifact lines: {"_artifact": true, "title": "...", "content": "...", ...}

    Args:
        file_path: Path to JSONL file

    Returns:
        Tuple of (metadata_dict, list_of_message_dicts, list_of_artifact_dicts)

    Raises:
        ValueError: If file format is invalid or metadata line is missing
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If JSON parsing fails
    """
    if not file_path.exists():
        raise FileNotFoundError(f"JSONL file not found: {file_path}")

    metadata = None
    messages = []
    artifacts = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except json.JSONDecodeError as e:
                raise json.JSONDecodeError(
                    f"Invalid JSON at line {line_num}: {e.msg}", e.doc, e.pos
                )

            # First line should be metadata
            if line_num == 1:
                if not data.get("_meta"):
                    raise ValueError(
                        f"First line must be metadata with '_meta': true, got: {data}"
                    )
                metadata = {
                    k: v for k, v in data.items() if k != "_meta"
                }  # Remove _meta flag
            elif data.get("_artifact"):
                # Artifact line: strip _artifact flag and collect
                artifact_data = {
                    k: v for k, v in data.items() if k != "_artifact"
                }
                artifacts.append(artifact_data)
            else:
                # Validate message structure
                if "role" not in data or "content" not in data:
                    raise ValueError(
                        f"Invalid message format at line {line_num}: missing 'role' or 'content'"
                    )
                messages.append(data)

    if metadata is None:
        raise ValueError("No metadata found in JSONL file")

    return metadata, messages, artifacts
