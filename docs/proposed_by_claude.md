## 프로젝트 이름 후보

1. **chatweave** — 여러 챗을 엮는다는 의미
2. **multichat-ir** — 직관적, 기능 설명적
3. **chatalign** — 정렬/비교 기능 강조
4. **convmerge** — conversation merge
5. **trilog** — tri(3) + log, 세 플랫폼 대화 로그

추천: **chatweave** — 짧고, 기억하기 쉽고, 확장성 있는 이름 (3개 이상으로 늘어나도 어색하지 않음)

---

## README.md

```markdown
# chatweave

Multi-platform LLM conversation alignment and comparison toolkit.

여러 LLM 플랫폼(ChatGPT, Claude, Gemini)에 동일한 질문을 던지고, 각 플랫폼의 응답을 정렬·비교하기 위한 중간 표현(IR) 생성 도구.

## Features

- JSONL 형식의 대화 로그를 플랫폼별 IR로 파싱
- 동일 디렉토리 내 대화들을 하나의 세션으로 자동 그룹핑
- Assistant 응답에서 질문 요약 추출 → 플랫폼 간 질문 매칭
- JSON 기반 IR 출력 (DB 불필요)
- 플러그인 방식의 파서/추출기/매처 확장 구조

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Session Directory                        │
│  (chatgpt.jsonl, claude.jsonl, gemini.jsonl)                    │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Platform Parsers                            │
│  ChatGPTParser, ClaudeParser, GeminiParser                      │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Layer 1: ConversationIR (per platform)          │
│  - meta: platform, url, exported_at, source_path                │
│  - messages: [index, role, timestamp, raw_content]              │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Query Extractor                             │
│  LLMQueryExtractor, HeuristicQueryExtractor                     │
│  (assistant 응답 초반부에서 질문 요약 추출)                        │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Query Matcher                              │
│  LLMQueryMatcher, EmbeddingQueryMatcher, IndexBasedMatcher      │
│  (추출된 질문들을 의미적으로 그룹핑)                               │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                Layer 2: AlignedSessionIR                         │
│  - session_dir, conversation_ids                                │
│  - exchanges: [extracted_queries, mappings, canonical_query]    │
│  - unaligned: {platform: [message_indices]}                     │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      JSON Output Files                           │
│  conversations/{platform}.json, aligned.json                    │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
Input:  sessions/2025-11-29-rwa/chatgpt.jsonl
        sessions/2025-11-29-rwa/claude.jsonl
        sessions/2025-11-29-rwa/gemini.jsonl
                      │
                      ▼
Output: sessions/2025-11-29-rwa/.chatweave/
            ├── conversations/
            │   ├── chatgpt.json    # ConversationIR
            │   ├── claude.json     # ConversationIR
            │   └── gemini.json     # ConversationIR
            └── aligned.json        # AlignedSessionIR
```

## Installation

```bash
pip install chatweave
```

또는 개발 모드:

```bash
git clone https://github.com/yourname/chatweave.git
cd chatweave
pip install -e ".[dev]"
```

## Usage

### CLI

```bash
# 세션 디렉토리 처리
chatweave process ./sessions/2025-11-29-rwa/

# 특정 추출기/매처 지정
chatweave process ./sessions/2025-11-29-rwa/ \
    --extractor llm \
    --matcher embedding

# dry-run (IR 생성 없이 매칭 결과만 확인)
chatweave process ./sessions/2025-11-29-rwa/ --dry-run
```

### Python API

```python
from chatweave import SessionProcessor
from chatweave.extractors import LLMQueryExtractor
from chatweave.matchers import EmbeddingQueryMatcher

processor = SessionProcessor(
    extractor=LLMQueryExtractor(model="gpt-4o-mini"),
    matcher=EmbeddingQueryMatcher()
)

conversations, aligned = processor.process("./sessions/2025-11-29-rwa/")

# IR을 JSON으로 저장
processor.save(conversations, aligned)

# 또는 직접 접근
for exchange in aligned.exchanges:
    print(f"Query: {exchange.canonical_query}")
    for platform, mapping in exchange.mappings.items():
        if mapping:
            print(f"  {platform}: {len(mapping.assistant_indices)} responses")
```

## IR Schema

### ConversationIR (conversations/{platform}.json)

```json
{
  "schema_version": "1.0",
  "meta": {
    "platform": "claude",
    "url": "https://claude.ai/chat/...",
    "exported_at": "2025-11-29T10:00:00Z",
    "source_path": "claude.jsonl"
  },
  "messages": [
    {
      "index": 0,
      "role": "user",
      "timestamp": "2025-11-29T10:00:05Z",
      "raw_content": ""
    },
    {
      "index": 1,
      "role": "assistant",
      "timestamp": "2025-11-29T10:00:10Z",
      "raw_content": "## 질문 정리\n\nRWA 토큰화에 대해 질문하셨습니다...\n\n## 답변\n..."
    }
  ]
}
```

### AlignedSessionIR (aligned.json)

```json
{
  "schema_version": "1.0",
  "session_id": "2025-11-29-rwa",
  "session_dir": "./sessions/2025-11-29-rwa",
  "conversation_ids": [
    "chatgpt:chatgpt",
    "claude:claude",
    "gemini:gemini"
  ],
  "exchanges": [
    {
      "exchange_id": "ex000",
      "extracted_queries": [
        {
          "text": "RWA 토큰화란 무엇인가?",
          "source_platform": "chatgpt",
          "source_message_index": 1,
          "extraction_method": "llm"
        },
        {
          "text": "RWA 토큰화에 대해 설명해달라",
          "source_platform": "claude",
          "source_message_index": 1,
          "extraction_method": "llm"
        }
      ],
      "canonical_query": "RWA 토큰화란 무엇인가?",
      "mappings": {
        "chatgpt": {
          "user_indices": [0],
          "assistant_indices": [1],
          "context_complete": true
        },
        "claude": {
          "user_indices": [0],
          "assistant_indices": [1],
          "context_complete": true
        },
        "gemini": {
          "user_indices": [0],
          "assistant_indices": [1, 2],
          "context_complete": true
        }
      }
    }
  ],
  "unaligned": {
    "chatgpt": [],
    "claude": [],
    "gemini": [5, 6]
  }
}
```

## Project Structure

```
chatweave/
├── pyproject.toml
├── README.md
├── LICENSE
│
├── src/
│   └── chatweave/
│       ├── __init__.py
│       ├── cli.py                 # CLI entry point
│       ├── processor.py           # SessionProcessor
│       │
│       ├── ir/                    # IR definitions
│       │   ├── __init__.py
│       │   ├── conversation.py    # ConversationIR, Message, ConversationMeta
│       │   ├── aligned.py         # AlignedSessionIR, AlignedExchange, ...
│       │   └── serialization.py   # JSON encode/decode
│       │
│       ├── parsers/               # JSONL → ConversationIR
│       │   ├── __init__.py
│       │   ├── base.py            # ConversationParser ABC
│       │   ├── chatgpt.py
│       │   ├── claude.py
│       │   └── gemini.py
│       │
│       ├── extractors/            # Assistant 응답 → 질문 추출
│       │   ├── __init__.py
│       │   ├── base.py            # QueryExtractor ABC
│       │   ├── llm.py             # LLMQueryExtractor
│       │   └── heuristic.py       # HeuristicQueryExtractor
│       │
│       └── matchers/              # 질문 매칭/그룹핑
│           ├── __init__.py
│           ├── base.py            # QueryMatcher ABC
│           ├── llm.py             # LLMQueryMatcher
│           ├── embedding.py       # EmbeddingQueryMatcher
│           └── index.py           # IndexBasedMatcher
│
└── tests/
    ├── conftest.py
    ├── fixtures/                  # 테스트용 JSONL 샘플
    │   └── sample_session/
    │       ├── chatgpt.jsonl
    │       ├── claude.jsonl
    │       └── gemini.jsonl
    ├── test_parsers.py
    ├── test_extractors.py
    ├── test_matchers.py
    └── test_processor.py
```

## Extending

### Custom Parser (새 플랫폼 추가)

```python
from chatweave.parsers.base import ConversationParser
from chatweave.ir import ConversationIR

class PerplexityParser(ConversationParser):
    platform = "perplexity"

    def parse(self, jsonl_path: Path) -> ConversationIR:
        # 구현
        ...
```

### Custom Extractor

```python
from chatweave.extractors.base import QueryExtractor

class RegexQueryExtractor(QueryExtractor):
    def extract(self, assistant_content: str) -> Optional[str]:
        # "## 질문" 섹션 파싱 등
        ...
```

### Custom Matcher

```python
from chatweave.matchers.base import QueryMatcher

class FuzzyMatcher(QueryMatcher):
    def match(self, queries: list[ExtractedQuery]) -> list[list[ExtractedQuery]]:
        # Levenshtein distance 기반 그룹핑
        ...
```

## Configuration

`chatweave.toml` (선택사항):

```toml
[extractor]
type = "llm"
model = "gpt-4o-mini"

[matcher]
type = "embedding"
model = "text-embedding-3-small"
threshold = 0.85

[output]
dir = ".chatweave"
```

## Roadmap

- [ ] v0.1: Core IR + Parsers (ChatGPT, Claude, Gemini)
- [ ] v0.2: LLM Query Extractor + Matcher
- [ ] v0.3: Embedding-based Matcher
- [ ] v0.4: CLI improvements, config file support
- [ ] v1.0: Stable IR schema, plugin system

## License

MIT
```

---

**맹점 체크:**
- 전제: "LLM 응답 초반에 질문 정리가 항상 있다" — 프롬프트 설정 없이 대화하면 추출 실패율 상승
- 이 설계가 틀릴 조건: JSONL 외 다른 입력 포맷(HTML export 등)이 필요해지면 파서 레이어 대폭 수정 필요

---

명확합니다. 최종안을 정리합니다.

---

## 최종 IR 설계

### 설계 원칙

1. **2계층 분리 유지**: ConversationIR (플랫폼별) → AlignedSessionIR (병합용)
2. **Session 식별**: 동일 디렉토리 = 동일 세션
3. **질문 매칭 전략**: assistant 응답 초반부에서 LLM이 정리한 질문을 추출 → 이를 기준으로 매칭
4. **출력 무관**: IR은 데이터 구조만 정의, 렌더링은 별도 레이어

### Layer 1: ConversationIR

```python
from dataclasses import dataclass, field
from typing import Literal, Optional
from datetime import datetime
from pathlib import Path

@dataclass
class ConversationMeta:
    platform: Literal["chatgpt", "claude", "gemini"]
    url: str
    exported_at: datetime
    source_path: Path  # 원본 JSONL 경로

@dataclass
class Message:
    index: int
    role: Literal["user", "assistant"]
    timestamp: datetime
    raw_content: str  # 빈 문자열 허용

@dataclass
class ConversationIR:
    meta: ConversationMeta
    messages: list[Message]

    @property
    def conversation_id(self) -> str:
        """플랫폼 + 파일명 기반 ID"""
        return f"{self.meta.platform}:{self.meta.source_path.stem}"
```

### Layer 2: AlignedSessionIR

```python
@dataclass
class ExtractedQuery:
    """assistant 응답 초반에서 추출한 질문 요약"""
    text: str
    source_platform: str
    source_message_index: int  # 해당 assistant 메시지의 index
    extraction_method: Literal["llm", "heuristic", "manual"]

@dataclass
class PlatformMapping:
    user_indices: list[int]
    assistant_indices: list[int]
    context_complete: bool = True

@dataclass
class AlignedExchange:
    exchange_id: str
    extracted_queries: list[ExtractedQuery]  # 플랫폼별로 추출된 질문들
    canonical_query: Optional[str] = None  # 대표 질문 (후처리로 설정 가능)
    mappings: dict[str, Optional[PlatformMapping]]

@dataclass
class AlignedSessionIR:
    session_dir: Path  # 세션 식별자 = 디렉토리 경로
    conversation_ids: list[str]  # 포함된 ConversationIR들의 ID
    exchanges: list[AlignedExchange]
    unaligned: dict[str, list[int]]  # platform → 매칭 안 된 message indices

    @property
    def session_id(self) -> str:
        return self.session_dir.name
```

### 질문 매칭 파이프라인

```python
from abc import ABC, abstractmethod

class QueryExtractor(ABC):
    """assistant 응답에서 질문 추출"""
    @abstractmethod
    def extract(self, assistant_content: str) -> Optional[str]:
        pass

class LLMQueryExtractor(QueryExtractor):
    """LLM을 사용해 응답 초반부에서 정리된 질문 추출"""
    def extract(self, assistant_content: str) -> Optional[str]:
        # 구현: LLM API 호출하여 "이 응답이 답하고 있는 질문이 무엇인가?" 추출
        ...

class HeuristicQueryExtractor(QueryExtractor):
    """규칙 기반 추출 (fallback)"""
    def extract(self, assistant_content: str) -> Optional[str]:
        # 구현: "## 질문 정리", "질문:" 등 패턴 매칭
        ...

class QueryMatcher(ABC):
    """추출된 질문들 간 매칭"""
    @abstractmethod
    def match(self, queries: list[ExtractedQuery]) -> list[list[ExtractedQuery]]:
        """같은 질문끼리 그룹핑"""
        pass

class LLMQueryMatcher(QueryMatcher):
    """LLM으로 의미적 유사도 판단"""
    def match(self, queries: list[ExtractedQuery]) -> list[list[ExtractedQuery]]:
        ...

class EmbeddingQueryMatcher(QueryMatcher):
    """임베딩 기반 클러스터링"""
    def match(self, queries: list[ExtractedQuery]) -> list[list[ExtractedQuery]]:
        ...
```

### 확장 포인트

```python
# 새 플랫폼 추가
class ConversationParser(ABC):
    @abstractmethod
    def parse(self, jsonl_path: Path) -> ConversationIR:
        pass

class ChatGPTParser(ConversationParser): ...
class ClaudeParser(ConversationParser): ...
class GeminiParser(ConversationParser): ...
# 새 플랫폼: class NewPlatformParser(ConversationParser): ...

# 새 매칭 전략 추가
class IndexBasedMatcher(QueryMatcher): ...  # index fallback
class ManualMatcher(QueryMatcher): ...  # 수동 매핑 파일 로드

# 새 추출 전략 추가
class StructuredOutputExtractor(QueryExtractor): ...  # JSON 모드 등
```

### 디렉토리 구조 예시

```
sessions/
└── 2025-11-29-rwa-tokenization/   # session_id = "2025-11-29-rwa-tokenization"
    ├── chatgpt.jsonl
    ├── claude.jsonl
    └── gemini.jsonl
```

### 전체 흐름

```python
def build_session_ir(session_dir: Path) -> tuple[dict[str, ConversationIR], AlignedSessionIR]:
    # 1. 디렉토리 내 JSONL 파일들 파싱 → ConversationIR들
    conversations: dict[str, ConversationIR] = {}
    for jsonl_path in session_dir.glob("*.jsonl"):
        parser = get_parser_for_file(jsonl_path)
        conv = parser.parse(jsonl_path)
        conversations[conv.meta.platform] = conv

    # 2. 각 assistant 메시지에서 질문 추출
    extractor = LLMQueryExtractor()  # 또는 체인
    extracted: list[ExtractedQuery] = []
    for platform, conv in conversations.items():
        for msg in conv.messages:
            if msg.role == "assistant":
                query_text = extractor.extract(msg.raw_content)
                if query_text:
                    extracted.append(ExtractedQuery(
                        text=query_text,
                        source_platform=platform,
                        source_message_index=msg.index,
                        extraction_method="llm"
                    ))

    # 3. 추출된 질문들 매칭 → 그룹핑
    matcher = LLMQueryMatcher()
    groups = matcher.match(extracted)

    # 4. AlignedSessionIR 구성
    exchanges = []
    for i, group in enumerate(groups):
        mappings = build_mappings(group, conversations)
        exchanges.append(AlignedExchange(
            exchange_id=f"ex{i:03d}",
            extracted_queries=group,
            mappings=mappings
        ))

    aligned = AlignedSessionIR(
        session_dir=session_dir,
        conversation_ids=[c.conversation_id for c in conversations.values()],
        exchanges=exchanges,
        unaligned=find_unaligned(conversations, exchanges)
    )

    return conversations, aligned
```

---

**핵심 결정 변수:**
- LLM 추출/매칭 비용이 부담되면 → Heuristic + Embedding 조합으로 전환
- 추출 정확도가 낮으면 → 프롬프트 구조를 더 정형화하거나 manual fallback 추가
