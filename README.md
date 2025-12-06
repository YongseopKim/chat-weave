# ChatWeave

Multi-platform LLM conversation alignment and comparison toolkit.

여러 LLM 플랫폼(ChatGPT, Claude, Gemini, Grok)에서 export한 대화 로그(JSONL)를 입력으로 받아, 플랫폼 독립적인 **중간 표현(Intermediate Representation, IR)**을 생성하는 Python 도구입니다.

**현재 버전**: v0.4.0 (CLI 확장 및 플랫폼 추론 기능 추가)

## Features

- ✅ **JSONL 파싱**: ChatGPT, Claude, Gemini, Grok의 export 파일 지원
- ✅ **ConversationIR**: 플랫폼별 대화를 정규화된 IR로 변환
- ✅ **Query Hash**: 동일 질문 탐지를 위한 해시 생성
- ✅ **QAUnitIR**: Q&A 단위 추출 및 질문 요약 자동 추출
- ✅ **Heuristic Extractor**: ChatGPT/Gemini의 "질문 정리" 섹션 자동 파싱
- ✅ **MultiModelSessionIR**: 크로스 플랫폼 정렬 및 질문 매칭
- ✅ **Hash-based Matching**: 동일 질문 자동 그룹핑
- ✅ **Dependency Tracking**: 순차적 질문 의존성 추적
- ✅ **플랫폼 자동 추론**: metadata → 파일명 패턴 → 명시적 지정
- ✅ **유연한 입력**: 단일 파일, 여러 파일, 디렉토리 모두 지원
- ✅ **Progress 추적**: progress.json으로 실행 단계 기록
- ✅ **로깅 옵션**: 콘솔/파일 로깅, quiet 모드 지원
- ✅ **CLI 확장**: 다양한 입력 방식 및 옵션 지원
- ✅ **DB 불필요**: JSON 파일 기반 저장
- 🚧 **LLM Integration**: LLM 기반 질문 매칭 (v0.5 예정)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Session Directory                               │
│  (chatgpt.jsonl, claude.jsonl, gemini.jsonl, grok.jsonl)            │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    UnifiedParser                                     │
│  (모든 플랫폼 동일 JSONL 스키마 사용)                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 1: ConversationIR (플랫폼별)                       │
│  - meta: platform, url, exported_at                                  │
│  - messages: [id, role, timestamp, raw_content, normalized_content]  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 2: QAUnitIR (Q&A 단위 추출)                        │
│  - qa_units: [user_message_ids, assistant_message_ids]               │
│  - question_from_user, question_from_assistant_summary               │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Layer 3: MultiModelSessionIR (크로스 플랫폼 정렬)         │
│  - prompts: [canonical_prompt, per_platform mappings]                │
│  - depends_on, missing_context 추적                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      JSON Output Files                               │
│  ir/conversation-ir/, ir/qa-unit-ir/, ir/session-ir/                │
└─────────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
pip install chatweave
```

개발 모드:

```bash
git clone https://github.com/dragon/chat-weave.git
cd chat-weave

# 가상환경 생성 및 활성화
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate  # Windows

pip install -e ".[dev]"
```

## Usage

### CLI

**기본 사용:**
```bash
# 디렉토리 입력
chatweave build-ir ./examples/sample-session/

# 단일 파일 입력
chatweave build-ir ./chatgpt_export.jsonl

# 여러 파일 입력
chatweave build-ir chatgpt.jsonl claude.jsonl gemini.jsonl
```

**옵션:**
```bash
# 출력 디렉토리 지정
chatweave build-ir ./session/ --output ./ir/

# 작업 디렉토리 지정 (progress.json 위치)
chatweave build-ir ./session/ --working-dir ./tmp/

# 플랫폼 명시적 지정 (단일 파일만)
chatweave build-ir ./unknown.jsonl --platform chatgpt

# 처리 단계 선택
chatweave build-ir ./session/ --step conversation  # ConversationIR만 생성
chatweave build-ir ./session/ --step qa            # QAUnitIR까지 생성
chatweave build-ir ./session/ --step session       # SessionIR까지 생성 (기본값)

# 로그 파일 저장
chatweave build-ir ./session/ --log-file ./chatweave.log

# 미리보기 (파일 작성 안 함)
chatweave build-ir ./session/ --dry-run

# 상세 출력
chatweave build-ir ./session/ --verbose

# 조용한 모드 (stdout 억제)
chatweave build-ir ./session/ --quiet
```

**플랫폼 추론:**

CLI는 다음 우선순위로 플랫폼을 추론합니다:
1. `--platform` 옵션 (최우선)
2. JSONL metadata의 `platform` 필드
3. 파일명 패턴 (`chatgpt_*.jsonl`, `claude_*.jsonl`, `gemini_*.jsonl`, `grok_*.jsonl`)

추론 실패 시 에러 메시지를 표시합니다.

### Python API

```python
from pathlib import Path
from chatweave.parsers.unified import UnifiedParser
from chatweave.io.ir_writer import write_conversation_ir

# JSONL 파일 파싱
parser = UnifiedParser()
conversation_ir = parser.parse(Path("examples/sample-session/chatgpt_20251129T114242.jsonl"))

# IR JSON 파일로 저장
output_dir = Path("ir/conversation-ir")
output_path = write_conversation_ir(conversation_ir, output_dir)
print(f"Generated: {output_path}")

# IR 데이터 접근
print(f"Platform: {conversation_ir.platform}")
print(f"Messages: {len(conversation_ir.messages)}")

for msg in conversation_ir.messages:
    if msg.role == "user":
        print(f"User: {msg.raw_content[:50]}...")
        print(f"Hash: {msg.query_hash}")
```

## IR Schema

### Layer 1: ConversationIR

플랫폼별 JSONL 파일 1개 → ConversationIR 1개

```json
{
  "schema": "conversation-ir/v1",
  "platform": "claude",
  "conversation_id": "claude-abc123",
  "meta": {
    "url": "https://claude.ai/chat/...",
    "exported_at": "2025-11-29T10:00:00Z"
  },
  "messages": [
    {
      "id": "m0001",
      "index": 0,
      "role": "user",
      "timestamp": "2025-11-29T10:00:05Z",
      "raw_content": "RWA 토큰화에 대해 설명해줘",
      "normalized_content": "RWA 토큰화에 대해 설명해줘",
      "query_hash": "a1b2c3d4..."
    }
  ]
}
```

### Layer 2: QAUnitIR

ConversationIR에서 질문-답변 단위를 추출

```json
{
  "schema": "qa-unit-ir/v1",
  "platform": "claude",
  "conversation_id": "claude-abc123",
  "qa_units": [
    {
      "qa_id": "q0001",
      "user_message_ids": ["m0001"],
      "assistant_message_ids": ["m0002"],
      "question_from_user": "RWA 토큰화에 대해 설명해줘",
      "question_from_assistant_summary": "RWA(Real World Asset) 토큰화의 정의와 작동 방식에 대한 질문",
      "user_query_hash": "a1b2c3d4..."
    }
  ]
}
```

### Layer 3: MultiModelSessionIR

디렉토리 내 모든 플랫폼의 QAUnit을 "같은 질문" 기준으로 정렬

```json
{
  "schema": "multi-model-session-ir/v1",
  "session_id": "2025-11-29-topic",
  "platforms": ["chatgpt", "claude", "gemini"],
  "prompts": [
    {
      "prompt_key": "p0001",
      "canonical_prompt": {
        "text": "RWA 토큰화란 무엇인가?",
        "language": "ko",
        "source": { "platform": "chatgpt", "qa_id": "q0001" }
      },
      "depends_on": [],
      "per_platform": [
        {
          "platform": "chatgpt",
          "qa_id": "q0001",
          "prompt_similarity": 1.0,
          "missing_prompt": false
        },
        {
          "platform": "claude",
          "qa_id": "q0001",
          "prompt_similarity": 0.95,
          "missing_prompt": false
        }
      ]
    }
  ]
}
```

## Project Structure

```
chatweave/
├── pyproject.toml
├── README.md
│
├── chatweave/
│   ├── __init__.py
│   ├── cli.py                    # CLI entry point
│   │
│   ├── models/                   # IR dataclass 정의
│   │   ├── __init__.py
│   │   ├── conversation.py       # ConversationIR, MessageIR
│   │   ├── qa_unit.py            # QAUnitIR, QAUnit
│   │   └── session.py            # MultiModelSessionIR, PromptGroup
│   │
│   ├── io/                       # 파일 I/O
│   │   ├── __init__.py
│   │   ├── jsonl_loader.py       # JSONL 파일 읽기
│   │   └── ir_writer.py          # IR → JSON 저장
│   │
│   ├── parsers/                  # 플랫폼 파서
│   │   ├── __init__.py
│   │   ├── base.py               # ConversationParser ABC
│   │   └── unified.py            # UnifiedParser (모든 플랫폼 지원)
│   │
│   ├── pipeline/                 # IR 생성 파이프라인
│   │   ├── __init__.py
│   │   ├── build_qa_ir.py        # ConversationIR → QAUnitIR
│   │   └── build_session_ir.py   # QAUnitIR[] → MultiModelSessionIR
│   │
│   ├── extractors/               # 질문 추출기
│   │   ├── __init__.py
│   │   ├── base.py               # QueryExtractor ABC
│   │   └── heuristic.py          # 규칙 기반 질문 추출
│   │
│   ├── matchers/                 # 질문 매칭기
│   │   ├── __init__.py
│   │   ├── base.py               # QueryMatcher ABC
│   │   └── hash.py               # Hash 기반 질문 매칭
│   │
│   └── util/
│       ├── __init__.py
│       ├── text_normalization.py # 텍스트 정규화
│       ├── hashing.py            # Query hash 생성
│       ├── platform_inference.py # 플랫폼 자동 추론
│       ├── logging_config.py     # 로깅 설정
│       └── progress.py           # Progress 추적
│
├── tests/
│   ├── conftest.py
│   ├── models/
│   │   ├── test_conversation.py
│   │   ├── test_qa_unit.py
│   │   └── test_session.py
│   ├── util/
│   │   ├── test_text_normalization.py
│   │   ├── test_hashing.py
│   │   ├── test_platform_inference.py
│   │   └── test_progress.py
│   ├── io/
│   │   ├── test_jsonl_loader.py
│   │   └── test_ir_writer.py
│   ├── parsers/
│   │   └── test_unified.py
│   ├── pipeline/
│   │   ├── test_build_qa_ir.py
│   │   └── test_build_session_ir.py
│   ├── extractors/
│   │   └── test_heuristic.py
│   └── matchers/
│       └── test_hash.py
│
├── ir/                           # 생성된 IR 출력
│   ├── conversation-ir/
│   ├── qa-unit-ir/
│   └── session-ir/
│
└── examples/
    └── sample-session/
        ├── chatgpt_20251129T114242.jsonl
        ├── claude_20251129T114247.jsonl
        ├── gemini_20251129T114250.jsonl
        └── grok_20251206T133524.jsonl
```

## Scope

### 하는 것

- JSONL 파싱 → 정규화 → IR(JSON) 생성
- 플랫폼 내 QA 단위 추출
- 디렉토리 단위 멀티 플랫폼 QA 매핑/정렬

### 하지 않는 것

- Markdown / HTML / PDF 렌더링
- LLM API 직접 호출로 자동 요약 (IR 위에 별도 프로젝트에서 구현)
- 데이터베이스 저장

## License

MIT
