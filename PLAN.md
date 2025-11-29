# ChatWeave Implementation Plan

## Part 1: 아키텍처 설계

### 1.1 IR 스키마 상세 설계

#### Layer 1: ConversationIR

플랫폼별 JSONL 파일 1개를 정규화한 구조.

```python
from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict
from datetime import datetime

Role = Literal["user", "assistant"]
Platform = Literal["chatgpt", "claude", "gemini"]

@dataclass
class MessageIR:
    """개별 메시지 단위"""
    id: str                         # "m0001" 형식
    index: int                      # 0-based 순서
    role: Role
    timestamp: datetime

    raw_content: str                # 원본 텍스트 (빈 문자열 허용)
    normalized_content: Optional[str]  # 정규화된 텍스트
    content_format: str = "markdown"

    # user 메시지인 경우에만 사용
    query_hash: Optional[str] = None

    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class ConversationIR:
    """플랫폼별 대화 전체"""
    schema: str = "conversation-ir/v1"
    platform: Platform
    conversation_id: str            # 파일명 또는 해시
    meta: Dict[str, object]         # url, exported_at 등
    messages: List[MessageIR]
```

**핵심 설계 결정:**
- `raw_content`: 원본 손실 없이 보존
- `normalized_content`: 공백/줄바꿈 정리된 버전
- `query_hash`: user 메시지의 정규화된 텍스트 해시 (동일 질문 탐지용)

---

#### Layer 2: QAUnitIR

하나의 ConversationIR에서 질문-답변 단위를 추출.

```python
@dataclass
class QAUnit:
    """질문-답변 한 쌍"""
    qa_id: str                      # "q0001" 형식
    platform: Platform
    conversation_id: str

    user_message_ids: List[str]     # 해당 user 메시지들
    assistant_message_ids: List[str] # 해당 assistant 메시지들

    # 질문 텍스트 후보
    question_from_user: Optional[str]
    question_from_assistant_summary: Optional[str]  # "질문 정리" 섹션 추출

    user_query_hash: Optional[str]
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class QAUnitIR:
    """플랫폼별 QA 묶음"""
    schema: str = "qa-unit-ir/v1"
    platform: Platform
    conversation_id: str
    qa_units: List[QAUnit]
```

**핵심 설계 결정:**
- `question_from_user`: 실제 user 입력
- `question_from_assistant_summary`: assistant 응답 초반의 "질문 정리" 부분
- Claude의 빈 user content 대응: `question_from_assistant_summary`로 의도 파악

---

#### Layer 3: MultiModelSessionIR

디렉토리 단위로 여러 플랫폼의 QAUnit을 "같은 질문" 기준으로 정렬.

```python
@dataclass
class PerPlatformQARef:
    """플랫폼별 QA 참조"""
    platform: Platform
    qa_id: str
    conversation_id: str

    prompt_text: Optional[str]      # 해당 플랫폼의 실제 질문 텍스트
    prompt_similarity: Optional[float] = None  # canonical과의 유사도 (0~1)

    missing_prompt: bool = False    # user content가 비어있는 경우
    missing_context: bool = False   # 의존하는 이전 QA가 없는 경우


@dataclass
class PromptGroup:
    """같은 질문에 대한 멀티플랫폼 그룹"""
    prompt_key: str                 # "p0001" 형식

    canonical_prompt: Dict[str, object]  # {"text": str, "language": str, "source": {...}}
    depends_on: List[str] = field(default_factory=list)  # 이전 질문 의존성

    per_platform: List[PerPlatformQARef] = field(default_factory=list)
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class MultiModelSessionIR:
    """세션 전체 정렬 정보"""
    schema: str = "multi-model-session-ir/v1"
    session_id: str                 # 디렉토리명
    platforms: List[Platform]
    conversations: List[Dict[str, str]]  # [{"platform":..., "conversation_id":...}]

    prompts: List[PromptGroup]
    meta: Dict[str, object] = field(default_factory=dict)
```

**핵심 설계 결정:**
- `canonical_prompt`: 대표 질문 (첫 번째 발견된 것 또는 LLM으로 합성)
- `prompt_similarity`: 나중에 embedding/LLM으로 계산
- `missing_context`: 맥락 의존성 추적 (follow-up 질문 처리)

---

### 1.2 파이프라인 설계

```
┌──────────────────┐
│   Session Dir    │
│ (*.jsonl files)  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────────────────────────┐
│   Stage 1        │     │  Platform Parsers                    │
│   JSONL →        │────▶│  - ChatGPTParser                     │
│   ConversationIR │     │  - ClaudeParser                      │
│                  │     │  - GeminiParser                      │
└────────┬─────────┘     └──────────────────────────────────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────────────────────────┐
│   Stage 2        │     │  Query Extractors                    │
│   ConversationIR │────▶│  - HeuristicQueryExtractor           │
│   → QAUnitIR     │     │  - LLMQueryExtractor (optional)      │
└────────┬─────────┘     └──────────────────────────────────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────────────────────────┐
│   Stage 3        │     │  Query Matchers                      │
│   QAUnitIR[]     │────▶│  - HashQueryMatcher                  │
│   → SessionIR    │     │  - LLMQueryMatcher (optional)        │
└──────────────────┘     └──────────────────────────────────────┘
```

#### Stage 1: JSONL → ConversationIR

```python
def build_conversation_ir(session_dir: Path) -> Dict[str, ConversationIR]:
    conversations = {}
    for jsonl_path in session_dir.glob("*.jsonl"):
        parser = get_parser_for_file(jsonl_path)
        conv = parser.parse(jsonl_path)
        conversations[conv.platform] = conv
    return conversations
```

#### Stage 2: ConversationIR → QAUnitIR

```python
def build_qa_ir(
    conversations: Dict[str, ConversationIR],
    extractor: QueryExtractor = HeuristicQueryExtractor()
) -> Dict[str, QAUnitIR]:
    qa_units = {}
    for platform, conv in conversations.items():
        units = extract_qa_units(conv, extractor)
        qa_units[platform] = QAUnitIR(
            platform=platform,
            conversation_id=conv.conversation_id,
            qa_units=units
        )
    return qa_units
```

#### Stage 3: QAUnitIR[] → MultiModelSessionIR

```python
def build_session_ir(
    qa_units: Dict[str, QAUnitIR],
    session_id: str,
    matcher: QueryMatcher = HashQueryMatcher()
) -> MultiModelSessionIR:
    # 1. 모든 QAUnit 수집
    all_units = collect_all_units(qa_units)

    # 2. 질문 매칭/그룹핑
    groups = matcher.match(all_units)

    # 3. PromptGroup 생성
    prompts = [create_prompt_group(g, i) for i, g in enumerate(groups)]

    return MultiModelSessionIR(
        session_id=session_id,
        platforms=list(qa_units.keys()),
        conversations=[...],
        prompts=prompts
    )
```

---

### 1.3 확장 포인트

#### Parser Extension

```python
from abc import ABC, abstractmethod

class ConversationParser(ABC):
    platform: str

    @abstractmethod
    def parse(self, jsonl_path: Path) -> ConversationIR:
        pass

# 새 플랫폼 추가
class PerplexityParser(ConversationParser):
    platform = "perplexity"

    def parse(self, jsonl_path: Path) -> ConversationIR:
        ...
```

#### Extractor Extension

```python
class QueryExtractor(ABC):
    @abstractmethod
    def extract(self, assistant_content: str) -> Optional[str]:
        """Assistant 응답에서 질문 요약 추출"""
        pass

class HeuristicQueryExtractor(QueryExtractor):
    """규칙 기반: "## 질문 정리" 패턴 매칭"""

class LLMQueryExtractor(QueryExtractor):
    """LLM 호출: "이 응답이 답하고 있는 질문은?"""""
```

#### Matcher Extension

```python
class QueryMatcher(ABC):
    @abstractmethod
    def match(self, units: List[QAUnit]) -> List[List[QAUnit]]:
        """QAUnit들을 같은 질문끼리 그룹핑"""
        pass

class HashQueryMatcher(QueryMatcher):
    """query_hash 동일성 기반 매칭"""

class LLMQueryMatcher(QueryMatcher):
    """LLM으로 의미적 유사도 판단"""

class EmbeddingQueryMatcher(QueryMatcher):
    """임베딩 벡터 클러스터링 기반"""
```

---

## Part 2: 구현 로드맵

### v0.1: Core Foundation

**목표**: 기본 파싱 및 ConversationIR 생성

**구현 항목**:
1. `chatweave/models/conversation.py`
   - MessageIR, ConversationIR dataclass
   - JSON serialization/deserialization

2. `chatweave/parsers/`
   - `base.py`: ConversationParser ABC
   - `chatgpt.py`: ChatGPT JSONL 파서
   - `claude.py`: Claude JSONL 파서
   - `gemini.py`: Gemini JSONL 파서

3. `chatweave/io/`
   - `jsonl_loader.py`: JSONL 파일 읽기
   - `ir_writer.py`: IR JSON 저장

4. `chatweave/util/`
   - `text_normalization.py`: 텍스트 정규화
   - `hashing.py`: query_hash 생성

5. `tests/`
   - 샘플 JSONL fixtures
   - 파서 단위 테스트

**산출물**:
- `ir/conversation-ir/` 디렉토리에 플랫폼별 JSON 생성

---

### v0.2: QA Extraction

**목표**: QAUnitIR 생성 및 질문 추출

**구현 항목**:
1. `chatweave/models/qa_unit.py`
   - QAUnit, QAUnitIR dataclass

2. `chatweave/extractors/`
   - `base.py`: QueryExtractor ABC
   - `heuristic.py`: 규칙 기반 추출기
     - "## 질문 정리", "## 1. 질문" 등 패턴 매칭

3. `chatweave/pipeline/build_qa_ir.py`
   - ConversationIR → QAUnitIR 변환 로직

4. `tests/test_extractors.py`

**산출물**:
- `ir/qa-unit-ir/` 디렉토리에 플랫폼별 JSON 생성

---

### v0.3: Session Alignment

**목표**: MultiModelSessionIR 생성 및 기본 매칭

**구현 항목**:
1. `chatweave/models/session.py`
   - PerPlatformQARef, PromptGroup, MultiModelSessionIR dataclass

2. `chatweave/matchers/`
   - `base.py`: QueryMatcher ABC
   - `hash.py`: query_hash 기반 매칭기

3. `chatweave/pipeline/build_session_ir.py`
   - QAUnitIR[] → MultiModelSessionIR 변환 로직

4. `tests/test_matchers.py`

**산출물**:
- `ir/session-ir/` 디렉토리에 세션 JSON 생성

---

### v0.4: LLM Integration

**목표**: LLM 기반 질문 추출/매칭 (선택적)

**구현 항목**:
1. `chatweave/extractors/llm.py`
   - OpenAI/Anthropic API 호출
   - 프롬프트: "이 Assistant 응답이 답하고 있는 질문을 한 문장으로 요약하세요"

2. `chatweave/matchers/llm.py`
   - 질문 쌍 유사도 판단
   - 프롬프트: "두 질문이 같은 의도인지 판단하세요"

3. `chatweave/matchers/embedding.py` (optional)
   - 임베딩 기반 클러스터링

4. 설정 파일 (`chatweave.toml`)
   ```toml
   [extractor]
   type = "llm"  # or "heuristic"
   model = "gpt-4o-mini"

   [matcher]
   type = "hash"  # or "llm", "embedding"
   ```

---

### v1.0: CLI & Polish

**목표**: CLI 완성 및 안정화

**구현 항목**:
1. `chatweave/cli.py`
   ```bash
   chatweave build-ir <session-dir> [--output DIR] [--dry-run]
   chatweave validate <ir-file>
   chatweave info <session-dir>
   ```

2. `chatweave/processor.py`
   - SessionProcessor 클래스 (통합 파이프라인)

3. `pyproject.toml`
   - Entry points 설정
   - Dependencies

4. 문서화
   - README.md 최종화
   - 사용 예제

5. CI/CD
   - GitHub Actions
   - pytest + coverage

---

## 부록: 엣지 케이스 처리

### A. Claude 빈 User Content

**문제**: Claude export에서 user content가 빈 문자열인 경우

**해결**:
1. `raw_content = ""`로 보존
2. `question_from_assistant_summary`로 의도 추출
3. `PerPlatformQARef.missing_prompt = True` 표시

### B. 질문 매칭 실패

**문제**: query_hash가 다르고 LLM도 낮은 신뢰도

**해결**:
1. `PromptGroup.meta.confidence_score` 필드 추가
2. 낮은 점수는 수동 확인 대상으로 표시
3. 추후 `user_overrides.json`으로 수동 매핑 지원

### C. Follow-up 질문

**문제**: "위에서 말한 것 중 X에 대해 더 설명해줘"

**해결**:
1. `PromptGroup.depends_on`에 이전 prompt_key 기록
2. `missing_context = True`: 이 플랫폼에 해당 이전 QA가 없음

---

## 다음 단계

v0.1부터 순차적으로 구현을 시작합니다.

첫 번째 구현 대상:
1. `chatweave/models/conversation.py` - IR dataclass 정의
2. `chatweave/parsers/base.py` - Parser ABC
3. 샘플 JSONL 파일로 테스트
