"""Generate sample MultiModelSessionIR from sample JSONL files."""

from pathlib import Path

from chatweave.io.ir_writer import write_session_ir
from chatweave.parsers.unified import UnifiedParser
from chatweave.pipeline.build_qa_ir import build_qa_ir
from chatweave.pipeline.build_session_ir import build_session_ir


def main():
    # Sample session directory
    sample_dir = Path(__file__).parent / "examples" / "sample-session"

    # Find all JSONL files
    jsonl_files = list(sample_dir.glob("*.jsonl"))
    print(f"Found {len(jsonl_files)} JSONL files:")
    for f in jsonl_files:
        print(f"  - {f.name}")

    # Parse and build QAUnitIR for each platform
    parser = UnifiedParser()
    qa_units = {}

    for jsonl_path in jsonl_files:
        print(f"\nParsing {jsonl_path.name}...")
        conversation_ir = parser.parse(jsonl_path)
        qa_ir = build_qa_ir(conversation_ir)
        qa_units[qa_ir.platform] = qa_ir
        print(f"  Platform: {qa_ir.platform}")
        print(f"  QA units: {len(qa_ir.qa_units)}")

    # Build SessionIR
    print("\nBuilding SessionIR...")
    session_ir = build_session_ir(qa_units, "sample-session")
    print(f"  Platforms: {session_ir.platforms}")
    print(f"  Prompt groups: {len(session_ir.prompts)}")

    # Write to file
    output_dir = Path(__file__).parent / "ir" / "session-ir"
    output_path = write_session_ir(session_ir, output_dir)
    print(f"\nSessionIR written to: {output_path}")

    # Display summary
    print("\n=== Summary ===")
    for i, prompt in enumerate(session_ir.prompts):
        print(f"\nPrompt {i} ({prompt.prompt_key}):")
        print(f"  Canonical: {prompt.canonical_prompt['text'][:60]}...")
        print(f"  Depends on: {prompt.depends_on}")
        print(f"  Platforms: {len(prompt.per_platform)}")
        for ref in prompt.per_platform:
            print(f"    - {ref.platform}: {ref.qa_id} (similarity: {ref.prompt_similarity})")


if __name__ == "__main__":
    main()
