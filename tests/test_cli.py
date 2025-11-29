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
        assert "JSONL file(s)" in captured.out
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
        assert "Error: Path not found" in captured.err

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

    def test_build_ir_single_file_input(self, sample_session_dir, tmp_path, monkeypatch):
        """Test processing a single JSONL file."""
        output_dir = tmp_path / "ir"
        single_file = sample_session_dir / "chatgpt_20251129T114242.jsonl"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(single_file), "--output", str(output_dir)]
        )

        # Run CLI
        main()

        # Verify output file was created
        session_ir_file = output_dir / "session-ir" / "multi-file-session.json"
        assert session_ir_file.exists()

    def test_build_ir_multiple_files_input(self, sample_session_dir, tmp_path, monkeypatch):
        """Test processing multiple JSONL files."""
        output_dir = tmp_path / "ir"
        file1 = sample_session_dir / "chatgpt_20251129T114242.jsonl"
        file2 = sample_session_dir / "claude_20251129T114247.jsonl"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(file1), str(file2), "--output", str(output_dir)]
        )

        # Run CLI
        main()

        # Verify output file was created
        session_ir_file = output_dir / "session-ir" / "multi-file-session.json"
        assert session_ir_file.exists()

    def test_build_ir_platform_override(self, tmp_path, monkeypatch):
        """Test --platform option for platform override."""
        # Create a test JSONL file without platform metadata
        test_file = tmp_path / "test.jsonl"
        with open(test_file, "w") as f:
            f.write('{"_meta":true,"url":"","exported_at":""}\n')
            f.write('{"role":"user","content":"test question","timestamp":"2025-01-01T00:00:00Z"}\n')
            f.write('{"role":"assistant","content":"test answer","timestamp":"2025-01-01T00:00:05Z"}\n')

        output_dir = tmp_path / "ir"

        # Mock sys.argv with --platform
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(test_file), "--output", str(output_dir), "--platform", "chatgpt"]
        )

        # Run CLI
        main()

        # Verify output file was created
        session_ir_file = output_dir / "session-ir" / "multi-file-session.json"
        assert session_ir_file.exists()

    def test_build_ir_working_dir_option(self, sample_session_dir, tmp_path, monkeypatch):
        """Test --working-dir option for progress.json location."""
        output_dir = tmp_path / "ir"
        working_dir = tmp_path / "working"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir), "--working-dir", str(working_dir)]
        )

        # Run CLI
        main()

        # Verify progress.json was created in working_dir
        progress_file = working_dir / "progress.json"
        assert progress_file.exists()

        # Verify output file was created in output_dir
        session_ir_file = output_dir / "session-ir" / "sample-session.json"
        assert session_ir_file.exists()

    def test_build_ir_log_file_option(self, sample_session_dir, tmp_path, monkeypatch):
        """Test --log-file option creates log file."""
        output_dir = tmp_path / "ir"
        log_file = tmp_path / "chatweave.log"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir), "--log-file", str(log_file)]
        )

        # Run CLI
        main()

        # Verify log file was created
        assert log_file.exists()

        # Verify log file contains expected content
        with open(log_file) as f:
            log_content = f.read()
            assert "Parsing" in log_content
            assert "SessionIR" in log_content

    def test_build_ir_quiet_option(self, sample_session_dir, tmp_path, monkeypatch, capsys):
        """Test --quiet option suppresses stdout output."""
        output_dir = tmp_path / "ir"

        # Mock sys.argv
        monkeypatch.setattr(
            sys,
            "argv",
            ["chatweave", "build-ir", str(sample_session_dir), "--output", str(output_dir), "--quiet"]
        )

        # Run CLI
        main()

        # Verify no output to stdout
        captured = capsys.readouterr()
        assert captured.out == ""

        # Verify output file was still created
        session_ir_file = output_dir / "session-ir" / "sample-session.json"
        assert session_ir_file.exists()
