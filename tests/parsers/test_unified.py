"""Tests for conversation parsers."""

import json
from pathlib import Path

import pytest

from chatweave.io.ir_writer import write_conversation_ir
from chatweave.parsers.unified import UnifiedParser


class TestUnifiedParser:
    """Tests for UnifiedParser."""

    def test_parse_chatgpt(self, chatgpt_jsonl):
        """Test parsing ChatGPT JSONL file."""
        parser = UnifiedParser()
        conversation_ir = parser.parse(chatgpt_jsonl)

        assert conversation_ir.platform == "chatgpt"
        assert conversation_ir.schema == "conversation-ir/v1"
        assert "chatgpt.com" in conversation_ir.meta.get("url", "")
        assert len(conversation_ir.messages) == 8  # 4 Q&A pairs

        # Check first message
        first_msg = conversation_ir.messages[0]
        assert first_msg.id == "m0000"
        assert first_msg.index == 0
        assert first_msg.role == "user"
        assert "claude code" in first_msg.raw_content.lower()
        assert first_msg.normalized_content is not None
        assert first_msg.query_hash is not None  # user message has hash

        # Check second message (assistant)
        second_msg = conversation_ir.messages[1]
        assert second_msg.role == "assistant"
        assert second_msg.query_hash is None  # assistant has no hash

    def test_parse_claude(self, claude_jsonl):
        """Test parsing Claude JSONL file."""
        parser = UnifiedParser()
        conversation_ir = parser.parse(claude_jsonl)

        assert conversation_ir.platform == "claude"
        assert "claude.ai" in conversation_ir.meta.get("url", "")
        assert len(conversation_ir.messages) == 8

    def test_parse_gemini(self, gemini_jsonl):
        """Test parsing Gemini JSONL file."""
        parser = UnifiedParser()
        conversation_ir = parser.parse(gemini_jsonl)

        assert conversation_ir.platform == "gemini"
        assert "gemini.google.com" in conversation_ir.meta.get("url", "")
        assert len(conversation_ir.messages) == 8

    def test_same_question_same_hash(self, chatgpt_jsonl, claude_jsonl):
        """Test that same questions across platforms have same hash."""
        parser = UnifiedParser()

        chatgpt_ir = parser.parse(chatgpt_jsonl)
        claude_ir = parser.parse(claude_jsonl)

        # First user message should be identical
        chatgpt_first_user = chatgpt_ir.messages[0]
        claude_first_user = claude_ir.messages[0]

        # Both should ask about "claude code 실행 중 node 관련 쓰레드"
        assert chatgpt_first_user.role == "user"
        assert claude_first_user.role == "user"

        # Since content is identical, hashes should match
        assert chatgpt_first_user.query_hash == claude_first_user.query_hash

    def test_write_and_read_ir(self, chatgpt_jsonl, temp_output_dir):
        """Test writing ConversationIR to JSON and reading it back."""
        parser = UnifiedParser()
        conversation_ir = parser.parse(chatgpt_jsonl)

        # Write to file
        output_path = write_conversation_ir(conversation_ir, temp_output_dir)

        assert output_path.exists()
        assert output_path.name.startswith("chatgpt_conv_")
        assert output_path.suffix == ".json"

        # Read back and verify
        with open(output_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["schema"] == "conversation-ir/v1"
        assert data["platform"] == "chatgpt"
        assert len(data["messages"]) == 8

        # Verify message structure
        first_msg = data["messages"][0]
        assert "id" in first_msg
        assert "role" in first_msg
        assert "timestamp" in first_msg
        assert "raw_content" in first_msg
        assert "normalized_content" in first_msg
        assert "query_hash" in first_msg

    def test_invalid_platform(self, tmp_path):
        """Test parsing file with invalid platform."""
        # Create invalid JSONL file
        invalid_jsonl = tmp_path / "invalid.jsonl"
        with open(invalid_jsonl, "w") as f:
            f.write('{"_meta":true,"platform":"invalid","url":"","exported_at":""}\n')
            f.write('{"role":"user","content":"test","timestamp":""}\n')

        parser = UnifiedParser()
        with pytest.raises(ValueError, match="Cannot infer platform"):
            parser.parse(invalid_jsonl)

    def test_missing_metadata(self, tmp_path):
        """Test parsing file without metadata line."""
        invalid_jsonl = tmp_path / "no_meta.jsonl"
        with open(invalid_jsonl, "w") as f:
            f.write('{"role":"user","content":"test","timestamp":""}\n')

        parser = UnifiedParser()
        with pytest.raises(ValueError, match="must be metadata"):
            parser.parse(invalid_jsonl)

    def test_all_platforms_parse_successfully(
        self, chatgpt_jsonl, claude_jsonl, gemini_jsonl, temp_output_dir
    ):
        """Integration test: parse all platforms and write IR files."""
        parser = UnifiedParser()

        for jsonl_path in [chatgpt_jsonl, claude_jsonl, gemini_jsonl]:
            conversation_ir = parser.parse(jsonl_path)
            output_path = write_conversation_ir(conversation_ir, temp_output_dir)

            assert output_path.exists()
            print(f"✓ {conversation_ir.platform}: {output_path}")
