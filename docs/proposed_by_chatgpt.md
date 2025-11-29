## 1. 질문 정리

* IR은 DB 없이 **JSON 파일**로만 저장할 것.
* 같은 디렉토리에 있는 여러 JSONL(플랫폼별 export)을 **같은 세션**으로 취급하면 됨.
* 보통 세 플랫폼에 같은 질문을 복붙하지만, 가끔은 문구가 다를 수 있음.
* 답변 서두에 항상 “질문 정리”를 넣는 프롬프트 패턴이 있으므로, 나중에 LLM으로 해석하면 “같은 질문인지” 판별에 활용 가능.
* 지금은 **IR만 생성하는 프로젝트**를 만들고 싶고, 그에 대한:

  * 프로젝트 이름,
  * 프로젝트 설명,
  * 디자인(아키텍처),
  * 파일 구조
    를 포함한 README 수준의 설계를 원함.

---

## 2. 답변 요약

* 프로젝트 이름 제안: **ChatWeave**

  * 의미: 여러 LLM 대화를 “엮어서(weave)” 하나의 구조화된 IR로 만드는 도구.
* 설계 포인트:

  * 입력: 플랫폼별 JSONL 파일들 (디렉터리 단위로 하나의 세션).
  * 출력: 세 종류의 JSON IR 파일

    1. `ConversationIR` (플랫폼별 원본 대화)
    2. `QAUnitIR` (플랫폼 내 질문–답변 단위)
    3. `MultiModelSessionIR` (세션 내 여러 플랫폼 QA를 정렬/매핑)
  * Python 패키지 구조:

    * `chatweave/models/` 에 IR dataclass 정의
    * `chatweave/io/` 에 JSONL/JSON 로딩·저장
    * `chatweave/pipeline/` 에 `conversation → qa → session` 파이프라인
    * `chatweave/cli.py` 로 `chatweave build-ir <session-dir>` 같은 명령 제공
* 이 프로젝트는 “렌더링(MD/HTML)”을 하지 않고, **IR JSON만 생성**하는 도구로 명확히 한정.

---

## 3. 실제 답변 서술

### 3.1. 프로젝트 이름

* 1순위: **ChatWeave**

  * 여러 LLM(채팅) 로그를 한데 모아 “짠다(weave)”는 이미지와 잘 맞음.
  * IR 중심 프로젝트와도 의미가 잘 맞음.

* 후보(참고용):

  * `DialogMesh`, `PolyChatIR`, `PromptTrio`
  * 하지만 기억·의미·확장성을 고려하면 ChatWeave가 가장 무난.

이하 내용은 `README.md` 초안 수준으로 볼 수 있게 정리한다.

---

### 3.2. 프로젝트 개요 (Description)

#### 프로젝트 요약

**ChatWeave**는 여러 LLM 플랫폼(ChatGPT, Claude, Gemini 등)에서 export한 대화(JSONL)를 입력으로 받아,

1. 플랫폼별 원본 대화,
2. 질문–답변 단위,
3. 여러 플랫폼 간 “같은 질문”을 기준으로 정렬된 세션

을 모두 **IR(JSON)** 형태로 생성하는 Python 기반 도구이다.

* 저장소: 로컬 파일 시스템
* 스토리지: JSON (DB 없음)
* 목적: 나중에 Markdown/HTML/노트 시스템/분석 파이프라인에서 재사용 가능한 **중간 표현(Intermediate Representation)** 제공

#### Scope

* 하는 것:

  * JSONL 파싱 → 정규화 → IR(JSON) 생성
  * 단일 플랫폼 내부에서 QA 단위 추출
  * 디렉터리 단위(세션 단위)에서 여러 플랫폼 QA 간 매핑 정보 구조화
* 하지 않는 것:

  * Markdown / HTML / PDF / 노트 도구로의 변환
  * LLM을 직접 호출해서 자동 매칭/요약 (필요하면 별도 스크립트/프로젝트에서 이 IR을 사용)

---

### 3.3. 설계 개요 (Architecture / Design)

#### 3.3.1. 입력과 출력

* **입력**

  * 디렉터리 하나 = 하나의 세션
  * 그 안에:

    * `chatgpt.jsonl`
    * `claude.jsonl`
    * `gemini.jsonl`
    * ... 등 플랫폼별 export 파일
  * JSONL 포맷:

    * 1행: meta (`_meta`, `platform`, `url`, `exported_at`)
    * 2행+: 메시지 (`role`, `content`, `timestamp`)

* **출력 (IR JSON 파일들)**
  (기본 디렉터리: 예시로 `./ir/`)

  1. `conversation-ir/`

     * `conversation-{platform}-{conversation_id}.json`
     * 각 JSONL → 1개의 `ConversationIR`
  2. `qa-unit-ir/`

     * `qa-{platform}-{conversation_id}.json`
     * 각 `ConversationIR` → 여러 `QAUnit` 묶음
  3. `session-ir/`

     * `session-{session_id}.json`
     * 디렉터리 내 여러 `QAUnitIR`를 모아 만든 `MultiModelSessionIR`

#### 3.3.2. 데이터 모델

요약만 적고, 세부는 간단히 나열한다.

1. **ConversationIR**

   * 단일 JSONL 파일 → 메시지 리스트

   * 필드:

     * `schema`: `"conversation-ir/v1"`
     * `platform`: `"chatgpt" | "claude" | "gemini"`
     * `conversation_id`: 파일명 또는 해시
     * `meta`: `{ "url": ..., "exported_at": ... }`
     * `messages`: `MessageIR[]`

   * `MessageIR`:

     * `id`: `"m0001"` 형식
     * `index`: 0-based
     * `role`: `"user" | "assistant"`
     * `timestamp`: ISO 8601 파싱 결과
     * `raw_content`: 원문 (빈 문자열 허용)
     * `normalized_content`: 정규화된 텍스트 (없으면 `null`)
     * `content_format`: 기본 `"markdown"`
     * `query_hash`: user 메시지인 경우 질문 텍스트 정규화 후 해시 (없으면 `null`)
     * `meta`: 확장용 딕셔너리

2. **QAUnitIR**

   * 하나의 `ConversationIR` 안에서 “질문–답변 단위”를 묶은 것

   * 필드:

     * `schema`: `"qa-unit-ir/v1"`
     * `platform`
     * `conversation_id`
     * `qa_units`: `QAUnit[]`

   * `QAUnit`:

     * `qa_id`: `"q0001"` 형식
     * `platform`
     * `conversation_id`
     * `user_message_ids`: `[ "m0001", ... ]`
     * `assistant_message_ids`: `[ "m0002", "m0003", ... ]`
     * `question_from_user`: user가 실제로 입력한 질문 텍스트 (정규화 버전)
     * `question_from_assistant_summary`: 첫 assistant 답변의 “질문 정리” 부분
     * `user_query_hash`: 해당 user 질문의 해시
     * `meta`: 확장용 딕셔너리

3. **MultiModelSessionIR**

   * 디렉터리(=세션) 단위에서, 여러 플랫폼의 QAUnit을 “같은 질문” 기준으로 정렬

   * 필드:

     * `schema`: `"multi-model-session-ir/v1"`
     * `session_id`: 디렉터리명 또는 해시
     * `platforms`: `["chatgpt", "claude", "gemini", ...]`
     * `conversations`: `[{"platform":..., "conversation_id":...}, ...]`
     * `prompts`: `PromptGroup[]`
     * `meta`: 세션 전체 메타 (예: 생성 시각, 버전 등)

   * `PromptGroup`:

     * `prompt_key`: `"p0001"` 형식
     * `canonical_prompt`:

       * `{ "text": str, "language": "en"|"ko"|..., "source": {"platform":..., "qa_id":...} }`
     * `depends_on`: `["p000x", ...]` (이 질문이 의존하는 이전 질문들)
     * `per_platform`: `PerPlatformQARef[]`
     * `meta`: 확장용

   * `PerPlatformQARef`:

     * `platform`
     * `qa_id`
     * `conversation_id`
     * `prompt_text`: 해당 플랫폼에서 실제 사용된 질문 텍스트 (user or assistant 요약)
     * `prompt_similarity`: canonical과의 유사도 (0~1, 없으면 `null`)
     * `missing_prompt`: Claude처럼 user content가 비었을 때 `true`
     * `missing_context`: `depends_on`을 만족하는 QA가 이 플랫폼에 없을 때 `true`

> 중요: 이 레이어는 **정렬 정보만**을 갖는다. 실제 내용은 항상 아래 `ConversationIR`/`QAUnitIR`를 통해 접근.

---

### 3.4. 파이프라인 (논리적 흐름)

#### 단계 1: JSONL → ConversationIR

* 각 JSONL 파일에 대해:

  1. 1행 meta 파싱 → `meta` 필드로 저장
  2. 2행+ 메시지 → `MessageIR` 리스트 생성

     * `raw_content` 그대로
     * `normalized_content`는 간단한 정규화 (트리밍, 줄바꿈 통일 등)
     * user 메시지인 경우 `query_hash` 생성
* 결과를 `ir/conversation-ir/conversation-{platform}-{conversation_id}.json` 으로 저장

#### 단계 2: ConversationIR → QAUnitIR

* 메시지 리스트를 순회:

  * `role == "user"`를 만나면 새 `QAUnit` 시작
  * 그 뒤 연속된 `assistant` 메시지들을 같은 QAUnit에 묶음
* `question_from_user`:

  * user의 `normalized_content`
* `question_from_assistant_summary`:

  * 첫 assistant의 “1. 질문 정리” 영역을 파싱해서 저장 (정규식 or 나중에 LLM으로 정제)
* 결과를 `ir/qa-unit-ir/qa-{platform}-{conversation_id}.json` 으로 저장

#### 단계 3: QAUnitIR → MultiModelSessionIR (디렉터리 단위)

* 디렉터리에 포함된 모든 `QAUnitIR` 로딩
* “같은 질문인지” 판단 로직(초기 버전):

  1. `user_query_hash`가 동일한 QAUnit끼리 자동 그룹핑
  2. hash가 없는/다른 경우:

     * `question_from_user` + `question_from_assistant_summary`를 이용해
       나중에 LLM 또는 간단한 유사도(metric)로 수동/반자동 그룹핑
* 각 그룹을 하나의 `PromptGroup`으로 만들고:

  * `canonical_prompt.text`: 그룹 내에서 대표로 선택 (예: ChatGPT 버전, 또는 LLM으로 합성)
  * `per_platform`: 그룹에 속한 QAUnit들을 `PerPlatformQARef`로 매핑
  * `depends_on`: 나중에 수동/LLM으로 맥락 관계 지정 가능하게 리스트로 둠
* 결과를 `ir/session-ir/session-{session_id}.json` 으로 저장

---

### 3.5. 파일 구조 (File Structure)

예시:

```text
chatweave/
├── pyproject.toml            # 또는 setup.cfg / setup.py
├── README.md
├── chatweave/
│   ├── __init__.py
│   ├── cli.py                # `chatweave build-ir <session-dir>` 등
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── conversation.py   # ConversationIR, MessageIR dataclass
│   │   ├── qa_unit.py        # QAUnitIR, QAUnit
│   │   └── session.py        # MultiModelSessionIR, PromptGroup, PerPlatformQARef
│   │
│   ├── io/
│   │   ├── __init__.py
│   │   ├── jsonl_loader.py   # JSONL → raw dict list
│   │   ├── ir_writer.py      # IR dataclass → JSON 파일 저장
│   │   └── ir_reader.py      # JSON 파일 → IR dataclass 로딩
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── build_conversation_ir.py  # jsonl → ConversationIR
│   │   ├── build_qa_ir.py            # ConversationIR → QAUnitIR
│   │   └── build_session_ir.py       # 여러 QAUnitIR → MultiModelSessionIR
│   │
│   └── util/
│       ├── __init__.py
│       ├── text_normalization.py     # normalized_content, query_hash
│       └── similarity.py             # prompt_similarity 계산 (초기엔 stub)
│
├── tests/
│   ├── test_conversation_ir.py
│   ├── test_qa_ir.py
│   └── test_session_ir.py
│
└── examples/
    ├── sample-session/
    │   ├── chatgpt.jsonl
    │   ├── claude.jsonl
    │   └── gemini.jsonl
    └── expected-ir/
        ├── conversation-ir/
        ├── qa-unit-ir/
        └── session-ir/
```

---

이렇게 설계해 두면:

* 지금은 **IR JSON만 생성**하는 순수한 Python 도구로 시작할 수 있고,
* 나중에:

  * LLM을 불러서 질문 그룹핑/요약을 더 잘 하거나,
  * 이 IR을 읽어서 Markdown/HTML/Obsidian 노트로 변환하는 별도 프로젝트를 붙이거나,
  * IR 위에 분석/통계/태깅 레이어를 올리기에도 구조가 충분히 유연하다.

---

## 1. 질문 정리

* Python으로 JSONL들을 파싱해서 **IR만** 만들고 싶다.
* 같은 디렉터리에 있는 `chatgpt.jsonl / claude.jsonl / gemini.jsonl` 등을 **같은 세션**으로 취급해도 된다.
* 같은 질문을 보통 복붙하지만, 가끔은 플랫폼별로 문구가 조금 달라질 수 있다.
* 답변의 초반에 항상 “질문 정리”를 하도록 프롬프트를 세팅했으니, **assistant 답변의 앞부분을 LLM으로 다시 해석하면 “같은 질문인지” 판별할 힌트가 된다.**
* IR은 나중에 Markdown/HTML을 뽑기 위한 **중간 표현**일 뿐, 지금 단계에서 출력 포맷은 신경 쓰지 않는다.
* 이 모든 조건을 반영해서, 확장성까지 고려한 **최종 IR 설계안을 정리해 달라**는 요청.

---

## 2. 답변 요약

* **레이어를 3개로 나누는 설계**를 제안한다.

  1. `ConversationIR` (플랫폼별, JSONL 1개 → IR 1개)

     * 원본 메시지 + 정규화된 텍스트 + user용 `query_hash`(옵션)만 가진 가장 기본 레이어.
  2. `QAUnitIR` (단일 플랫폼 안에서 “질문–답변 단위”로 묶은 레이어)

     * user/assistant 메시지 묶음 +
       user 질문 텍스트 + assistant의 “질문 정리” 부분을 **둘 다** 후보로 저장.
  3. `MultiModelSessionIR` (디렉터리 단위, 여러 플랫폼을 묶는 상위 레이어)

     * 같은 디렉터리에 있는 여러 `ConversationIR/QAUnitIR`를 모아서
       `prompt_key`별로 플랫폼별 QAUnit를 정렬.
     * 여기서 `canonical_prompt`(대표 질문), 플랫폼별 실제 질문 텍스트, 유사도, 맥락 의존성(`depends_on`, `missing_context`)만 추가.

* IR은 **전부 JSON 직렬화 가능한 구조**로 두고,
  출력(MD/HTML)은 완전히 별 단계로 분리한다.

---

## 3. 최종 IR 설계안

### 3.1. 전체 구조 개요

Python 기준으로 보면, 디렉터리 하나에서:

1. 각 `.jsonl` → `ConversationIR`
2. 각 `ConversationIR`에서 “질문–답변 묶음” → `QAUnitIR`
3. 디렉터리 안의 여러 `QAUnitIR`들을 모아
   “같은 질문”끼리 `prompt_key`로 묶은 → `MultiModelSessionIR`

이 3단계가 끝나면, 나중에:

* 플랫폼별 로그 / 모델 비교 / 요약 / 태깅 / 분석
  모두 이 IR 위에서 할 수 있다.

---

### 3.2. 레이어 1: ConversationIR (플랫폼별, JSONL → 1:1)

JSONL 파일 하나가 그대로 `ConversationIR` 하나가 된다.

#### 스키마 (개념적, Python 타입 느낌)

```python
from dataclasses import dataclass, field
from typing import Literal, Optional, List, Dict
from datetime import datetime

Role = Literal["user", "assistant"]
ContentFormat = Literal["markdown", "text", "html"]

@dataclass
class MessageIR:
    id: str                  # m0001, m0002 ...
    index: int               # 0-based
    role: Role
    timestamp: datetime

    raw_content: str         # JSONL의 content 원문 (빈 문자열 가능)
    normalized_content: Optional[str]  # 전처리/클리닝 후 텍스트, 없으면 None
    content_format: ContentFormat = "markdown"

    # user 메시지인 경우에만 의미 있음 (질문 해시)
    query_hash: Optional[str] = None

    # 확장용 메타
    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class ConversationIR:
    schema: str              # "conversation-ir/v1"
    platform: Literal["chatgpt", "claude", "gemini"]
    conversation_id: str     # 파일명, 해시 등
    meta: Dict[str, object]  # url, exported_at 등 JSONL 1행에서 가져온 것
    messages: List[MessageIR]
```

포인트:

* **원본 손실 없음**: `raw_content`에 JSONL 그대로.
* `normalized_content`는 공백/줄바꿈 정리, 마크다운 클리닝 등을 한 값. 필요 없으면 그냥 `raw_content` 복사.
* user 메시지에만 `query_hash`(정규화 후 md5 등)를 넣어 두면,
  나중에 “복붙한 질문”은 해시로 빠르게 매칭할 수 있다.
* Claude에서 `content == ""`인 user:

  * `raw_content=""`, `normalized_content=None`, `query_hash=None` 그대로 둔다.

---

### 3.3. 레이어 2: QAUnitIR (플랫폼 내 “질문–답변 단위”)

한 플랫폼의 긴 대화를, 나중에 비교/요약/태깅하기 좋게 **QA 단위**로 쪼개는 레이어.

#### 스키마

```python
@dataclass
class QAUnit:
    qa_id: str                          # q0001, q0002 ...
    platform: Literal["chatgpt", "claude", "gemini"]
    conversation_id: str                # 소속 ConversationIR의 id

    # 이 QA를 구성하는 메시지들 (id 참조)
    user_message_ids: List[str]         # 보통 1개, 여러 개도 허용
    assistant_message_ids: List[str]    # 보통 1개, multiple chunk도 허용

    # 질문 텍스트 후보들
    # 1) 실제 user가 입력한 텍스트 (여러 줄일 수 있음)
    question_from_user: Optional[str]

    # 2) assistant 답변 초반부 "질문 정리"를 잘라낸 것 (당신 프롬프트 패턴에 기반)
    question_from_assistant_summary: Optional[str]

    # 해시/벡터 등 나중에 쓸 수 있는 피처
    user_query_hash: Optional[str]      # ConversationIR.messages[*].query_hash 중 하나
    meta: Dict[str, object] = field(default_factory=dict)
```

그리고 이를 감싸는 컨테이너:

```python
@dataclass
class QAUnitIR:
    schema: str = "qa-unit-ir/v1"
    platform: Literal["chatgpt", "claude", "gemini"]
    conversation_id: str
    qa_units: List[QAUnit]
```

생성 로직(개략):

* `ConversationIR.messages`를 순회하면서:

  * `role == "user"`가 나오면 새 QAUnit 시작.
  * 그 다음 이어지는 `assistant`들(연속 구간)을 같은 QAUnit의 `assistant_message_ids`로 묶음.
* `question_from_user`:

  * 해당 user 메시지들의 `normalized_content`를 합치거나 첫 user만 사용.
* `question_from_assistant_summary`:

  * 첫 assistant 메시지에서 “1. 질문 정리” 섹션만 잘라서 넣어두고,
  * 나중에 LLM을 이용해 정제/요약할 수 있음.

이 레이어는 **아직 멀티모델 병합 안 함**.
그냥 “플랫폼 내의 QA 리스트”일 뿐이다.

---

### 3.4. 레이어 3: MultiModelSessionIR (디렉터리 단위, 멀티모델 정렬)

같은 디렉터리에 있는 여러 플랫폼의 `QAUnitIR`를 모아서,
“사람 기준으로 같은 질문”끼리 묶는 레이어.

디렉터리 이름이 곧 하나의 **session**이라고 보면 된다.

#### 스키마

```python
@dataclass
class PerPlatformQARef:
    platform: Literal["chatgpt", "claude", "gemini"]
    qa_id: str                        # 해당 플랫폼 QAUnit.qa_id
    conversation_id: str

    # 실제 그 플랫폼에서 쓰인 질문 텍스트 (있으면)
    prompt_text: Optional[str]        # question_from_user or question_from_assistant_summary
    prompt_similarity: Optional[float] = None  # canonical과의 유사도 (0~1)

    missing_prompt: bool = False      # Claude처럼 user content 비어있는 케이스
    missing_context: bool = False     # 이 질문이 의존하는 앞선 QA가 이 플랫폼에 없음


@dataclass
class PromptGroup:
    prompt_key: str                   # p0001, p0002 ...

    # 이 질문을 대표하는 표현 (canonical)
    canonical_prompt: Dict[str, object]  # { "text": str, "language": "en/ko", "source": {...} }

    # 맥락 의존 관계 (이 prompt가 어떤 이전 prompt에 의존하는지)
    depends_on: List[str] = field(default_factory=list)   # ["p0001", ...]

    # 플랫폼별 QA 참조들
    per_platform: List[PerPlatformQARef] = field(default_factory=list)

    meta: Dict[str, object] = field(default_factory=dict)


@dataclass
class MultiModelSessionIR:
    schema: str = "multi-model-session-ir/v1"
    session_id: str                   # 디렉터리명, 해시 등
    platforms: List[Literal["chatgpt", "claude", "gemini"]]

    # 이 세션에 포함된 모든 Conversation/QAUnit 레퍼런스 (필요하면)
    conversations: List[Dict[str, str]]  # [{ "platform":..., "conversation_id":... }, ...]

    prompts: List[PromptGroup]
    meta: Dict[str, object] = field(default_factory=dict)
```

핵심:

* `PromptGroup`이 “사람 기준으로 같은 질문”의 단위.

  * `canonical_prompt.text`: 이 질문을 대표하는 문장.

    * ChatGPT/Claude/Gemini 중 하나에서 가져오거나,
    * 나중에 LLM으로 `question_from_*`들을 융합해서 만들어도 됨.
* `PerPlatformQARef`:

  * 각 플랫폼에서 이 질문에 해당하는 `QAUnit`가 뭔지 연결.
  * `prompt_text`: 해당 플랫폼에서 실제로 입력/요약된 질문 문장.
  * `prompt_similarity`: canonical과의 유사도(나중에 LLM/임베딩/간단한 문자열 유사도로 채울 수 있음).
  * `missing_prompt`: Claude 빈 user 등.
  * `missing_context`: 이 질문이 `depends_on`에 있는 이전 질문에 의존하지만,
    이 플랫폼에는 그 이전 QA가 존재하지 않을 때 `True`.

이 레이어는 **오직 정렬/매핑 정보만 가진다.**
실제 텍스트는 전부 아래 `ConversationIR` / `QAUnitIR`에 있고,
여기서는 “뭘 누구와 비교하는지”만 정의한다.

---

### 3.5. Python에서의 처리 흐름 (IR만 생성)

IR만 만든다는 전제하에서의 파이프라인은 대략 이렇게 정리된다.

1. **JSONL → ConversationIR (파일 단위)**

   * 디렉터리 내의 `*.jsonl` 모두 읽어서 각각 변환.
   * 메시지 id / index / timestamp / raw/normalized / query_hash 세팅.

2. **ConversationIR → QAUnitIR (플랫폼/파일 단위)**

   * 각 `ConversationIR.messages`를 순회하며 QAUnit 묶기.
   * `question_from_user` / `question_from_assistant_summary` 채우기.
   * 결과를 JSON 등으로 저장.

3. **디렉터리 단위 MultiModelSessionIR 생성**

   * 디렉터리 안의 모든 `QAUnitIR`를 로딩.
   * “같은 질문” 그룹핑 로직은 단계적으로 갈 수 있다:

     * 1단계: `query_hash`가 완전히 동일한 user 질문끼리는 자동 매칭.
     * 2단계: 서로 다른 hash지만, LLM/임베딩으로 비교해서
       `question_from_user` + `question_from_assistant_summary`를 보고 사람이/LLM이 `prompt_key` 할당.
   * 이렇게 얻은 그룹들을 `PromptGroup` 리스트로 만들고,
     `MultiModelSessionIR`로 직렬화.

4. **여기까지가 “IR 생성 단계”의 끝**

   * 이 구조만 있으면, 그 다음부터는:

     * 플랫폼별 로그 MD 생성
     * 모델 비교 테이블 생성
     * 요약/태깅/스코어링
   * 전부 **별도 모듈**에서 이 IR을 입력으로 사용하게 만들 수 있다.

---

요약하면:

* 지금 해야 하는 건 “이 구조대로 JSON(or dataclass)만 만들고 저장하는 것”까지.
* 출력은 전혀 신경 쓰지 않고,
* `ConversationIR → QAUnitIR → MultiModelSessionIR` 3층 구조만 잘 잡아두면,
  나중에 확장(LLM 기반 정렬/요약/분석)을 아무 제약 없이 얹을 수 있다.
