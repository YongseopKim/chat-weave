"""Command-line interface for ChatWeave."""

import argparse
import sys
from pathlib import Path

from chatweave.io.ir_writer import write_session_ir
from chatweave.parsers.unified import UnifiedParser
from chatweave.pipeline.build_qa_ir import build_qa_ir
from chatweave.pipeline.build_session_ir import build_session_ir


def build_ir_command(args):
    """Build IR from session directory."""
    session_dir = args.session_dir.resolve()
    output_dir = args.output.resolve()

    if not session_dir.exists() or not session_dir.is_dir():
        print(f"Error: Session directory not found: {session_dir}", file=sys.stderr)
        sys.exit(1)

    # Find all JSONL files
    jsonl_files = list(session_dir.glob("*.jsonl"))
    if not jsonl_files:
        print(f"Error: No JSONL files found in {session_dir}", file=sys.stderr)
        sys.exit(1)

    if args.verbose:
        print(f"Found {len(jsonl_files)} JSONL files:")
        for f in jsonl_files:
            print(f"  - {f.name}")

    # Parse and build QAUnitIR for each platform
    parser = UnifiedParser()
    qa_units = {}

    for jsonl_path in jsonl_files:
        if args.verbose:
            print(f"\nParsing {jsonl_path.name}...")

        conversation_ir = parser.parse(jsonl_path)
        qa_ir = build_qa_ir(conversation_ir)
        qa_units[qa_ir.platform] = qa_ir

        if args.verbose:
            print(f"  Platform: {qa_ir.platform}")
            print(f"  QA units: {len(qa_ir.qa_units)}")

    # Build SessionIR
    session_id = session_dir.name
    if args.verbose:
        print(f"\nBuilding SessionIR for '{session_id}'...")

    session_ir = build_session_ir(qa_units, session_id)

    if args.verbose:
        print(f"  Platforms: {session_ir.platforms}")
        print(f"  Prompt groups: {len(session_ir.prompts)}")

    # Dry run mode - only preview
    if args.dry_run:
        print("\n=== Dry Run Summary ===")
        print(f"Session ID: {session_id}")
        print(f"Platforms: {', '.join(session_ir.platforms)}")
        print(f"Total prompt groups: {len(session_ir.prompts)}")
        for i, prompt in enumerate(session_ir.prompts):
            canonical_text = prompt.canonical_prompt["text"]
            preview = canonical_text[:60] + "..." if len(canonical_text) > 60 else canonical_text
            print(f"\n  Prompt {i} ({prompt.prompt_key}):")
            print(f"    Text: {preview}")
            print(f"    Depends on: {prompt.depends_on or 'None'}")
            print(f"    Platforms: {len(prompt.per_platform)}")
        print(f"\nWould write to: {output_dir / 'session-ir' / f'{session_id}.json'}")
        return

    # Write to file
    session_output_dir = output_dir / "session-ir"
    output_path = write_session_ir(session_ir, session_output_dir)
    print(f"\nSessionIR written to: {output_path}")

    # Display summary
    if args.verbose:
        print("\n=== Summary ===")
        for i, prompt in enumerate(session_ir.prompts):
            canonical_text = prompt.canonical_prompt["text"]
            preview = canonical_text[:60] + "..." if len(canonical_text) > 60 else canonical_text
            print(f"\nPrompt {i} ({prompt.prompt_key}):")
            print(f"  Canonical: {preview}")
            print(f"  Depends on: {prompt.depends_on}")
            print(f"  Platforms: {len(prompt.per_platform)}")
            for ref in prompt.per_platform:
                print(f"    - {ref.platform}: {ref.qa_id} (similarity: {ref.prompt_similarity})")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="chatweave",
        description="Multi-platform LLM conversation alignment and comparison toolkit",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # build-ir subcommand
    build_parser = subparsers.add_parser(
        "build-ir", help="Build intermediate representation from session directory"
    )
    build_parser.add_argument(
        "session_dir", type=Path, help="Session directory containing JSONL files"
    )
    build_parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("ir"),
        help="Output directory for IR files (default: ./ir/)",
    )
    build_parser.add_argument(
        "--dry-run", action="store_true", help="Preview without writing files"
    )
    build_parser.add_argument(
        "--verbose", "-v", action="store_true", help="Show detailed output"
    )

    args = parser.parse_args()

    if args.command == "build-ir":
        build_ir_command(args)


if __name__ == "__main__":
    main()
