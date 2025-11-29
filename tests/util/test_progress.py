"""Tests for progress tracking module."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from chatweave.util.progress import ProgressStep, ProgressTracker


class TestProgressStep:
    """Test cases for ProgressStep dataclass."""

    def test_default_values(self):
        """Should have correct default values."""
        step = ProgressStep(name="parse")
        assert step.name == "parse"
        assert step.status == "pending"
        assert step.started_at is None
        assert step.completed_at is None
        assert step.details == {}
        assert step.error is None

    def test_to_dict(self):
        """Should convert to dictionary correctly."""
        started = datetime(2025, 11, 30, 10, 0, 0)
        completed = datetime(2025, 11, 30, 10, 0, 5)
        step = ProgressStep(
            name="parse",
            status="completed",
            started_at=started,
            completed_at=completed,
            details={"files": 3},
            error=None,
        )
        result = step.to_dict()
        assert result["name"] == "parse"
        assert result["status"] == "completed"
        assert result["started_at"] == "2025-11-30T10:00:00"
        assert result["completed_at"] == "2025-11-30T10:00:05"
        assert result["details"] == {"files": 3}
        assert result["error"] is None


class TestProgressTracker:
    """Test cases for ProgressTracker."""

    def test_initialization(self, tmp_path):
        """Should initialize with default steps."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        assert len(tracker.steps) == 4
        assert tracker.steps[0].name == "parse"
        assert tracker.steps[1].name == "build_qa_ir"
        assert tracker.steps[2].name == "build_session_ir"
        assert tracker.steps[3].name == "write_output"
        assert tracker.status == "pending"

    def test_set_input(self, tmp_path):
        """Should set input information."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.set_input("directory", "/path/to/session", ["file1.jsonl", "file2.jsonl"])
        assert tracker.input_info["type"] == "directory"
        assert tracker.input_info["path"] == "/path/to/session"
        assert tracker.input_info["files"] == ["file1.jsonl", "file2.jsonl"]

    def test_start_step(self, tmp_path):
        """Should mark step as in_progress."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.start_step("parse", details={"files": 3})
        parse_step = tracker._get_step("parse")
        assert parse_step.status == "in_progress"
        assert parse_step.started_at is not None
        assert parse_step.details["files"] == 3
        assert tracker.status == "in_progress"

    def test_complete_step(self, tmp_path):
        """Should mark step as completed."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.start_step("parse")
        tracker.complete_step("parse", details={"platforms": ["chatgpt", "claude"]})
        parse_step = tracker._get_step("parse")
        assert parse_step.status == "completed"
        assert parse_step.completed_at is not None
        assert parse_step.details["platforms"] == ["chatgpt", "claude"]

    def test_fail_step(self, tmp_path):
        """Should mark step as error."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.start_step("parse")
        tracker.fail_step("parse", "Invalid file format")
        parse_step = tracker._get_step("parse")
        assert parse_step.status == "error"
        assert parse_step.error == "Invalid file format"
        assert tracker.status == "error"
        assert tracker.error == "Invalid file format"

    def test_complete(self, tmp_path):
        """Should mark process as completed."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.complete({"session_ir": "/path/to/output.json"})
        assert tracker.status == "completed"
        assert tracker.output_info["session_ir"] == "/path/to/output.json"

    def test_fail(self, tmp_path):
        """Should mark process as failed."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.fail("Unexpected error occurred")
        assert tracker.status == "error"
        assert tracker.error == "Unexpected error occurred"

    def test_get_step_unknown_raises_error(self, tmp_path):
        """Should raise ValueError for unknown step."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        with pytest.raises(ValueError) as exc_info:
            tracker._get_step("unknown")  # type: ignore
        assert "Unknown step" in str(exc_info.value)

    def test_writes_progress_file(self, tmp_path):
        """Should write progress.json when enabled."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=True)
        tracker.set_input("directory", "/path/to/session", ["file1.jsonl"])
        tracker.start_step("parse")

        progress_file = tmp_path / "progress.json"
        assert progress_file.exists()

        with open(progress_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema"] == "progress/v1"
        assert data["status"] == "in_progress"
        assert data["input"]["type"] == "directory"
        assert len(data["steps"]) == 4
        assert data["steps"][0]["status"] == "in_progress"

    def test_disabled_does_not_write_file(self, tmp_path):
        """Should not write progress.json when disabled."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=False)
        tracker.set_input("directory", "/path/to/session", ["file1.jsonl"])
        tracker.start_step("parse")

        progress_file = tmp_path / "progress.json"
        assert not progress_file.exists()

    def test_full_workflow(self, tmp_path):
        """Should track full workflow correctly."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=True)

        # Set input
        tracker.set_input("directory", "/path/to/session", ["file1.jsonl", "file2.jsonl"])

        # Step 1: Parse
        tracker.start_step("parse", details={"files": 2})
        tracker.complete_step("parse", details={"platforms": ["chatgpt", "claude"]})

        # Step 2: Build QA IR
        tracker.start_step("build_qa_ir")
        tracker.complete_step("build_qa_ir", details={"qa_units": 10})

        # Step 3: Build Session IR
        tracker.start_step("build_session_ir")
        tracker.complete_step("build_session_ir", details={"prompts": 5})

        # Step 4: Write output
        tracker.start_step("write_output")
        tracker.complete_step("write_output")

        # Complete
        tracker.complete({"session_ir": "/output/session.json"})

        # Verify file
        progress_file = tmp_path / "progress.json"
        with open(progress_file, encoding="utf-8") as f:
            data = json.load(f)

        assert data["status"] == "completed"
        assert data["steps"][0]["status"] == "completed"
        assert data["steps"][1]["status"] == "completed"
        assert data["steps"][2]["status"] == "completed"
        assert data["steps"][3]["status"] == "completed"
        assert data["output"]["session_ir"] == "/output/session.json"

    def test_progress_file_schema(self, tmp_path):
        """Should write correct JSON schema."""
        tracker = ProgressTracker(output_dir=tmp_path, enabled=True)
        tracker.set_input("file", "/path/to/file.jsonl", ["file.jsonl"])

        progress_file = tmp_path / "progress.json"
        with open(progress_file, encoding="utf-8") as f:
            data = json.load(f)

        # Check required fields
        assert "schema" in data
        assert "started_at" in data
        assert "updated_at" in data
        assert "status" in data
        assert "input" in data
        assert "steps" in data
        assert "output" in data
        assert "error" in data

        # Check schema version
        assert data["schema"] == "progress/v1"
