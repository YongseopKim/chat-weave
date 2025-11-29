"""Tests for CLI functionality."""

import sys
from pathlib import Path

import pytest

from chatweave.cli import main


class TestBuildIRCommand:
    """Test cases for build-ir command."""

    def test_build_ir_creates_output_file(self, sample_session_dir, tmp_path, monkeypatch):
        """Test that build-ir creates output file in default location."""
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir)]
        )

        # Run CLI
        main()

        # Verify output file was created
        session_ir_file = output_dir / "session-ir" / "sample-session.json"
        assert session_ir_file.exists()
        assert session_ir_file.stat().st_size > 0

    def test_build_ir_dry_run_no_file_created(self, sample_session_dir, tmp_path, monkeypatch, capsys):
        """Test that --dry-run does not create output files."""
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir), "--dry-run"]
        )

        # Run CLI
        main()

        # Verify no output file was created
        session_ir_dir = output_dir / "session-ir"
        assert not session_ir_dir.exists()

        # Verify dry run summary was printed
        captured = capsys.readouterr()
        assert "Dry Run Summary" in captured.out
        assert "Would write to:" in captured.out

    def test_build_ir_verbose_output(self, sample_session_dir, tmp_path, monkeypatch, capsys):
        """Test that --verbose prints detailed output."""
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir), "--verbose"]
        )

        # Run CLI
        main()

        # Verify verbose output was printed
        captured = capsys.readouterr()
        assert "Found" in captured.out
        assert "JSONL files:" in captured.out
        assert "Parsing" in captured.out
        assert "Platform:" in captured.out
        assert "QA units:" in captured.out
        assert "Summary" in captured.out

    def test_build_ir_custom_output_dir(self, sample_session_dir, tmp_path, monkeypatch):
        """Test that --output option works correctly."""
        custom_output = tmp_path / "custom_output"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(custom_output)]
        )

        # Run CLI
        main()

        # Verify output file was created in custom location
        session_ir_file = custom_output / "session-ir" / "sample-session.json"
        assert session_ir_file.exists()

    def test_build_ir_nonexistent_directory(self, tmp_path, monkeypatch, capsys):
        """Test that nonexistent directory causes exit(1)."""
        nonexistent_dir = tmp_path / "does_not_exist"
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(nonexistent_dir), "--output", str(output_dir)]
        )

        # Expect SystemExit with code 1
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1

        # Verify error message was printed to stderr
        captured = capsys.readouterr()
        assert "Error: Session directory not found" in captured.err

    def test_build_ir_no_jsonl_files(self, empty_session_dir, tmp_path, monkeypatch, capsys):
        """Test that directory with no JSONL files causes exit(1)."""
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(empty_session_dir), "--output", str(output_dir)]
        )

        # Expect SystemExit with code 1
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 1

        # Verify error message was printed to stderr
        captured = capsys.readouterr()
        assert "Error: No JSONL files found" in captured.err

    def test_build_ir_missing_required_arg(self, monkeypatch, capsys):
        """Test that missing session_dir argument causes exit(2)."""
        # Mock sys.argv with missing session_dir
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir"]
        )

        # Expect SystemExit with code 2 (argparse error)
        with pytest.raises(SystemExit) as excinfo:
            main()

        assert excinfo.value.code == 2

        # Verify error message was printed
        captured = capsys.readouterr()
        assert "required" in captured.err.lower() or "positional arguments" in captured.err.lower()
