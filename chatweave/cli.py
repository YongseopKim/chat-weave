"""Command-line interface for ChatWeave."""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from chatweave.io.ir_writer import (
    write_conversation_ir,
    write_qa_unit_ir,
    write_session_ir,
)
from chatweave.models.conversation import Platform
from chatweave.parsers.unified import UnifiedParser
from chatweave.pipeline.build_qa_ir import build_qa_ir
from chatweave.pipeline.build_session_ir import build_session_ir
from chatweave.util.logging_config import setup_logging
from chatweave.util.progress import ProgressTracker


def _collect_jsonl_files(inputs: List[Path]) -> List[Path]:
    """Collect all JSONL files from inputs (files or directories).

    Args:
        inputs: List of file paths or directory paths

    Returns:
        List of JSONL file paths

    Raises:
        SystemExit: If no JSONL files found
    """
    jsonl_files = []

    for input_path in inputs:
        input_path = input_path.resolve()

        if not input_path.exists():
            print(f"Error: Path not found: {input_path}", file=sys.stderr)
            sys.exit(1)

        if input_path.is_file():
            if input_path.suffix == ".jsonl":
                jsonl_files.append(input_path)
            else:
                print(f"Error: Not a JSONL file: {input_path}", file=sys.stderr)
                sys.exit(1)
        elif input_path.is_dir():
            dir_files = list(input_path.glob("*.jsonl"))
            if not dir_files:
                print(f"Error: No JSONL files found in {input_path}", file=sys.stderr)
                sys.exit(1)
            jsonl_files.extend(dir_files)
        else:
            print(f"Error: Invalid path: {input_path}", file=sys.stderr)
            sys.exit(1)

    if not jsonl_files:
        print("Error: No JSONL files found", file=sys.stderr)
        sys.exit(1)

    return jsonl_files


def build_ir_command(args):
    """Build IR from input files or directories."""
    # Setup logging
    logger = setup_logging(
        verbose=args.verbose,
        quiet=args.quiet,
        log_file=args.log_file,
    )

    # Resolve paths
    output_dir = args.output.resolve()
    working_dir = args.working_dir.resolve() if args.working_dir else output_dir

    # Collect JSONL files
    logger.info(f"Collecting JSONL files from {len(args.input)} input(s)...")
    jsonl_files = _collect_jsonl_files(args.input)
    logger.info(f"Found {len(jsonl_files)} JSONL file(s)")

    if args.verbose:
        for f in jsonl_files:
            logger.debug(f"  - {f.name}")

    # Initialize progress tracker
    progress = ProgressTracker(output_dir=working_dir, enabled=not args.dry_run)
    input_type = "directory" if len(args.input) == 1 and args.input[0].is_dir() else "files"
    progress.set_input(
        input_type=input_type,
        path=str(args.input[0]) if len(args.input) == 1 else "multiple",
        files=[f.name for f in jsonl_files],
    )

    try:
        # Step 1: Parse and build QAUnitIR for each platform
        logger.info("Step 1: Parsing JSONL files...")
        progress.start_step("parse", details={"files": len(jsonl_files)})

        parser = UnifiedParser()
        qa_units = {}
        conversation_irs = []

        for jsonl_path in jsonl_files:
            logger.info(f"Parsing {jsonl_path.name}...")

            # Validate platform override (only for single file input)
            platform_override = None
            if args.platform:
                if len(jsonl_files) > 1:
                    logger.warning(
                        "--platform option is ignored when processing multiple files"
                    )
                else:
                    platform_override = args.platform

            conversation_ir = parser.parse(jsonl_path, platform_override)
            qa_ir = build_qa_ir(conversation_ir)

            # Store ConversationIR in list (to handle multiple files from same platform)
            conversation_irs.append(conversation_ir)

            # Store QAUnitIR by platform (SessionIR expects dict keyed by platform)
            # If same platform appears multiple times, last one wins (for session alignment)
            qa_units[qa_ir.platform] = qa_ir

            logger.info(f"  Platform: {qa_ir.platform}")
            logger.debug(f"  Conversation ID: {qa_ir.conversation_id}")
            logger.debug(f"  QA units: {len(qa_ir.qa_units)}")

        progress.complete_step(
            "parse", details={"platforms": list(qa_units.keys())}
        )

        # If step is "conversation", write ConversationIR files and exit
        if args.step == "conversation":
            logger.info("Step 2: Writing ConversationIR files...")
            progress.start_step("write_output")

            conversation_output_dir = output_dir / "conversation-ir"
            written_files = []

            for conversation_ir in conversation_irs:
                output_path = write_conversation_ir(conversation_ir, conversation_output_dir)
                written_files.append(output_path)
                logger.info(f"  {output_path.name}")

            progress.complete_step("write_output", details={"files": len(written_files)})
            progress.complete({"conversation_ir_files": [str(f) for f in written_files]})

            logger.info(f"\nConversationIR written to: {conversation_output_dir}")
            logger.info(f"Total files: {len(written_files)}")
            return

        # Step 2: Build QAUnitIR (already done above)
        progress.start_step("build_qa_ir")
        total_qa_units = sum(len(qa_ir.qa_units) for qa_ir in qa_units.values())
        logger.info(f"Step 2: Built {total_qa_units} QA unit(s) across {len(qa_units)} platform(s)")
        progress.complete_step("build_qa_ir", details={"qa_units_total": total_qa_units})

        # If step is "qa", write QAUnitIR files and exit
        if args.step == "qa":
            logger.info("Step 3: Writing QAUnitIR files...")
            progress.start_step("write_output")

            qa_output_dir = output_dir / "qa-unit-ir"
            written_files = []

            for platform, qa_ir in qa_units.items():
                output_path = write_qa_unit_ir(qa_ir, qa_output_dir)
                written_files.append(output_path)
                logger.info(f"  {output_path.name}")

            progress.complete_step("write_output", details={"files": len(written_files)})
            progress.complete({"qa_unit_ir_files": [str(f) for f in written_files]})

            logger.info(f"\nQAUnitIR written to: {qa_output_dir}")
            logger.info(f"Total files: {len(written_files)}")
            return

        # Step 3: Build SessionIR
        logger.info("Step 3: Building SessionIR...")
        progress.start_step("build_session_ir")

        # Determine session ID
        if len(args.input) == 1 and args.input[0].is_dir():
            session_id = args.input[0].name
        else:
            session_id = "multi-file-session"

        session_ir = build_session_ir(qa_units, session_id)

        logger.info(f"  Session ID: {session_id}")
        logger.info(f"  Platforms: {', '.join(session_ir.platforms)}")
        logger.info(f"  Prompt groups: {len(session_ir.prompts)}")

        progress.complete_step(
            "build_session_ir", details={"prompt_groups": len(session_ir.prompts)}
        )

        # Step 4: Dry run mode - only preview
        if args.dry_run:
            logger.info("\n=== Dry Run Summary ===")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Platforms: {', '.join(session_ir.platforms)}")
            logger.info(f"Total prompt groups: {len(session_ir.prompts)}")

            for i, prompt in enumerate(session_ir.prompts):
                canonical_text = prompt.canonical_prompt["text"]
                preview = (
                    canonical_text[:60] + "..."
                    if len(canonical_text) > 60
                    else canonical_text
                )
                logger.info(f"\n  Prompt {i} ({prompt.prompt_key}):")
                logger.info(f"    Text: {preview}")
                logger.info(f"    Depends on: {prompt.depends_on or 'None'}")
                logger.info(f"    Platforms: {len(prompt.per_platform)}")

            output_path = output_dir / "session-ir" / f"{session_id}.json"
            logger.info(f"\nWould write to: {output_path}")
            return

        # Step 5: Write to file
        logger.info("Step 4: Writing output...")
        progress.start_step("write_output")

        session_output_dir = output_dir / "session-ir"
        output_path = write_session_ir(session_ir, session_output_dir)
        logger.info(f"SessionIR written to: {output_path}")

        progress.complete_step("write_output")
        progress.complete({"session_ir": str(output_path)})

        # Display summary
        if args.verbose:
            logger.info("\n=== Summary ===")
            for i, prompt in enumerate(session_ir.prompts):
                canonical_text = prompt.canonical_prompt["text"]
                preview = (
                    canonical_text[:60] + "..."
                    if len(canonical_text) > 60
                    else canonical_text
                )
                logger.info(f"\nPrompt {i} ({prompt.prompt_key}):")
                logger.info(f"  Canonical: {preview}")
                logger.info(f"  Depends on: {prompt.depends_on}")
                logger.info(f"  Platforms: {len(prompt.per_platform)}")
                for ref in prompt.per_platform:
                    logger.info(
                        f"    - {ref.platform}: {ref.qa_id} "
                        f"(similarity: {ref.prompt_similarity})"
                    )

    except Exception as e:
        logger.error(f"Error: {e}")
        progress.fail(str(e))
        raise


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="chatweave",
        description="Multi-platform LLM conversation alignment and comparison toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # build-ir subcommand
    build_parser = subparsers.add_parser(
        "build-ir", help="Build intermediate representation from JSONL file(s) or directory"
    )
    build_parser.add_argument(
        "input",
        type=Path,
        nargs="+",
        help="JSONL file(s) or directory containing JSONL files",
    )
    build_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("ir"),
        help="Output directory for IR files (default: ./ir/)",
    )
    build_parser.add_argument(
        "--working-dir",
        "-w",
        type=Path,
        default=None,
        help="Working directory for intermediate files (default: same as --output)",
    )
    build_parser.add_argument(
        "--platform",
        "-p",
        type=str,
        choices=["chatgpt", "claude", "gemini"],
        default=None,
        help="Override platform detection (single file only)",
    )
    build_parser.add_argument(
        "--step",
        "-s",
        type=str,
        choices=["conversation", "qa", "session"],
        default="session",
        help="Processing step to execute (default: session)",
    )
    build_parser.add_argument(
        "--log-file",
        type=Path,
        default=None,
        help="Path to log file (default: no file logging)",
    )
    build_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing files"
    )
    build_parser.add_argument(
        "--quiet",
        "--silent",
        "-q",
        action="store_true",
        help="Suppress stdout output",
    )
    build_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    if args.command == "build-ir":
        build_ir_command(args)


if __name__ == "__main__":
    main()
