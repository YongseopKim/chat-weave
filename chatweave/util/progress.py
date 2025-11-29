"""Progress tracking for CLI operations."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

StepName = Literal["parse", "build_qa_ir", "build_session_ir", "write_output"]
StepStatus = Literal["pending", "in_progress", "completed", "error"]
OverallStatus = Literal["pending", "in_progress", "completed", "error"]


@dataclass
class ProgressStep:
    """Individual progress step.

    Attributes:
        name: Step identifier
        status: Current status of the step
        started_at: When the step started
        completed_at: When the step completed
        details: Additional step-specific information
        error: Error message if step failed
    """

    name: StepName
    status: StepStatus = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "details": self.details,
            "error": self.error,
        }


@dataclass
class ProgressTracker:
    """Track progress of IR building process.

    Writes progress.json to output directory with step-by-step status.

    Attributes:
        output_dir: Directory where progress.json will be written
        enabled: Whether to write progress file (default: True)
    """

    output_dir: Path
    enabled: bool = True

    # Internal state
    started_at: datetime = field(default_factory=datetime.now)
    status: OverallStatus = "pending"
    input_info: Dict[str, Any] = field(default_factory=dict)
    steps: List[ProgressStep] = field(default_factory=list)
    output_info: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def __post_init__(self):
        """Initialize steps."""
        self.steps = [
            ProgressStep(name="parse"),
            ProgressStep(name="build_qa_ir"),
            ProgressStep(name="build_session_ir"),
            ProgressStep(name="write_output"),
        ]

    def set_input(self, input_type: str, path: str, files: List[str]):
        """Set input information.

        Args:
            input_type: "file", "directory", or "files"
            path: Path to input
            files: List of files being processed
        """
        self.input_info = {"type": input_type, "path": path, "files": files}
        self._write()

    def start_step(self, name: StepName, details: Optional[Dict] = None):
        """Mark step as started.

        Args:
            name: Step name
            details: Optional step-specific details
        """
        step = self._get_step(name)
        step.status = "in_progress"
        step.started_at = datetime.now()
        if details:
            step.details.update(details)
        self.status = "in_progress"
        self._write()

    def complete_step(self, name: StepName, details: Optional[Dict] = None):
        """Mark step as completed.

        Args:
            name: Step name
            details: Optional step-specific details
        """
        step = self._get_step(name)
        step.status = "completed"
        step.completed_at = datetime.now()
        if details:
            step.details.update(details)
        self._write()

    def fail_step(self, name: StepName, error: str):
        """Mark step as failed.

        Args:
            name: Step name
            error: Error message
        """
        step = self._get_step(name)
        step.status = "error"
        step.error = error
        self.status = "error"
        self.error = error
        self._write()

    def complete(self, output_paths: Dict[str, Any]):
        """Mark entire process as completed.

        Args:
            output_paths: Dictionary of output file paths
        """
        self.output_info = output_paths
        self.status = "completed"
        self._write()

    def fail(self, error: str):
        """Mark entire process as failed.

        Args:
            error: Error message
        """
        self.status = "error"
        self.error = error
        self._write()

    def _get_step(self, name: StepName) -> ProgressStep:
        """Get step by name.

        Args:
            name: Step name

        Returns:
            ProgressStep instance

        Raises:
            ValueError: If step name is unknown
        """
        for step in self.steps:
            if step.name == name:
                return step
        raise ValueError(f"Unknown step: {name}")

    def _write(self):
        """Write progress to progress.json file."""
        if not self.enabled:
            return

        progress_path = self.output_dir / "progress.json"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        data = {
            "schema": "progress/v1",
            "started_at": self.started_at.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "status": self.status,
            "input": self.input_info,
            "steps": [step.to_dict() for step in self.steps],
            "output": self.output_info,
            "error": self.error,
        }

        with open(progress_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
