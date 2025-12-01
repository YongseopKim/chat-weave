#!/usr/bin/env python3
"""
ChatWeave: 배치 IR 생성 스크립트

각 하위 디렉토리에서:
1. JSONL 파일들을 raw/ 디렉토리로 이동
2. ir/ 디렉토리 생성
3. Conversation IR 생성

Usage: python batch_build_ir.py <directory>
Example: python batch_build_ir.py ~/Downloads
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Tuple


class Colors:
    """ANSI color codes"""
    GREEN = '\033[0;32m'
    BLUE = '\033[0;34m'
    YELLOW = '\033[1;33m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color


def print_colored(message: str, color: str = Colors.NC):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")


def count_jsonl_files(directory: Path) -> int:
    """Count JSONL files in directory"""
    if not directory.exists():
        return 0
    return len(list(directory.glob("*.jsonl")))


def move_jsonl_files(source_dir: Path, target_dir: Path) -> int:
    """Move JSONL files from source to target directory"""
    moved = 0
    for jsonl_file in source_dir.glob("*.jsonl"):
        if jsonl_file.is_file():
            target_file = target_dir / jsonl_file.name
            jsonl_file.rename(target_file)
            print_colored(f"  → Moved: {jsonl_file.name}", Colors.GREEN)
            moved += 1
    return moved


def build_conversation_ir(raw_dir: Path, ir_dir: Path) -> bool:
    """Run chatweave build-ir command"""
    try:
        result = subprocess.run(
            [
                "chatweave",
                "build-ir",
                str(raw_dir),
                "--output",
                str(ir_dir),
                "--step",
                "conversation",
                "--quiet",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        print_colored(f"  Error: {e.stderr}", Colors.RED)
        return False
    except FileNotFoundError:
        print_colored("  Error: 'chatweave' command not found. Is it installed?", Colors.RED)
        return False


def process_directory(directory: Path) -> Tuple[bool, str]:
    """
    Process a single directory

    Returns:
        (success: bool, status: str)
        status can be: "success", "skipped", "failed"
    """
    dirname = directory.name
    timestamp = datetime.now().strftime("%H:%M:%S")

    print_colored(f"[{timestamp}] Processing: {dirname}", Colors.BLUE)

    # Define directories
    raw_dir = directory / "raw"
    ir_dir = directory / "ir"

    # Count JSONL files in root and raw/
    root_jsonl_count = count_jsonl_files(directory)
    raw_jsonl_count = count_jsonl_files(raw_dir)
    total_jsonl = root_jsonl_count + raw_jsonl_count

    # Skip if no JSONL files found
    if total_jsonl == 0:
        print_colored("  ⊘ No JSONL files found, skipping\n", Colors.YELLOW)
        return False, "skipped"

    # 1. Create/verify raw/ directory
    raw_dir.mkdir(exist_ok=True)
    print_colored("  ✓ Created/verified raw/ directory", Colors.GREEN)

    # 2. Move JSONL files if they are in root
    if root_jsonl_count > 0:
        print(f"  Found {root_jsonl_count} JSONL file(s) in root")
        moved = move_jsonl_files(directory, raw_dir)
        if moved > 0:
            print_colored(f"  ✓ Moved {moved} JSONL file(s) to raw/", Colors.GREEN)
    elif raw_jsonl_count > 0:
        print_colored(
            f"  ℹ Found {raw_jsonl_count} JSONL file(s) already in raw/ (skipping move)",
            Colors.BLUE
        )

    # 3. Create/verify ir/ directory
    ir_dir.mkdir(exist_ok=True)
    print_colored("  ✓ Created/verified ir/ directory", Colors.GREEN)

    # 4. Generate Conversation IR
    print_colored("  ⚙ Generating Conversation IR...", Colors.BLUE)

    if build_conversation_ir(raw_dir, ir_dir):
        print_colored("  ✓ Conversation IR generated successfully\n", Colors.GREEN)
        return True, "success"
    else:
        print_colored("  ✗ Failed to generate Conversation IR\n", Colors.RED)
        return False, "failed"


def main():
    parser = argparse.ArgumentParser(
        description="Process all subdirectories to build Conversation IR",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ~/Downloads
  %(prog)s /path/to/sessions

Each subdirectory will be processed as follows:
  1. Move JSONL files to subdirectory/raw/
  2. Create subdirectory/ir/
  3. Generate Conversation IR in subdirectory/ir/
"""
    )
    parser.add_argument(
        "directory",
        type=str,
        help="Target directory containing subdirectories with JSONL files"
    )

    args = parser.parse_args()

    # Validate target directory
    target_dir = Path(args.directory).expanduser().resolve()

    if not target_dir.exists():
        print_colored(f"Error: Directory not found: {target_dir}", Colors.RED)
        sys.exit(1)

    if not target_dir.is_dir():
        print_colored(f"Error: Not a directory: {target_dir}", Colors.RED)
        sys.exit(1)

    # Start processing
    print_colored("=== ChatWeave 일괄 처리 시작 ===", Colors.BLUE)
    print(f"Target directory: {target_dir}\n")

    # Counters
    processed = 0
    skipped = 0
    failed = 0

    # Process all subdirectories
    subdirs = sorted([d for d in target_dir.iterdir() if d.is_dir()])

    for subdir in subdirs:
        # Skip hidden directories
        if subdir.name.startswith('.'):
            continue

        success, status = process_directory(subdir)

        if status == "success":
            processed += 1
        elif status == "skipped":
            skipped += 1
        elif status == "failed":
            failed += 1

    # Print summary
    print_colored("=== 처리 완료 ===", Colors.BLUE)
    print_colored(f"  성공: {processed}개 디렉토리", Colors.GREEN)
    print_colored(f"  건너뜀: {skipped}개 디렉토리 (JSONL 없음)", Colors.YELLOW)
    if failed > 0:
        print_colored(f"  실패: {failed}개 디렉토리", Colors.RED)
    print()

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
