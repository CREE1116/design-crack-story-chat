# crack-emu

크랙(Crack) 스토리챗 빌드를 **실제로 돌려보는** 에뮬레이터 겸 QA 하네스.

`build/` 디렉토리(`integrated-prompt-*.md`, `keyword-book*.md`, `prologue.md`,
`start-prompt.md`)를 파싱해 크랙과 같은 순서로 프롬프트를 조립하고, LLM에 보내고,
돌아온 응답을 그 빌드 자신의 출력 계약에 대조한다. 사람이 쓸 웹 UI와
에이전트가 쓸 JSON CLI를 같은 엔진 위에 올렸다.

## 왜

키워드북을 눈으로 읽어서는 알 수 없는 것들이 있다.

- `라임`이 `슬라임`의 부분문자열이라 프롤로그의 "거대 슬라임"이 라임 대리 항목을 발동시킨다
- 크랙은 턴당 3개만 로드하므로, 그 오발동이 **정작 그 턴에 필요한 항목의 슬롯을 뺏는다**
- 20턴을 돌려보면 한 번도 발동하지 않는 항목과 매 턴 발동하는 항목이 갈린다

이건 정적 검사로 안 나온다. 실제로 턴을 돌려야 나온다.

## 설치

```bash
pip install -e .        # 의존성: pyyaml 하나
crack-emu --help
```

설치 없이 쓰려면 `python3 -m crack_emulator` 로 대체 가능하다.

## 빠르게

```bash
B=~/crack/마왕성주식회사/build

crack-emu --project $B lint                 # 정적 점검: 길이, 충돌, 부분문자열 오탐, 슬롯 배치
crack-emu --project $B health               # 프로바이더 연결 확인
crack-emu --project $B serve                # 웹 UI (localhost:8765)

crack-emu --project $B turn s1 --input "라임 대리님 안녕하세요"
crack-emu --project $B replay s1 scenarios/onboarding.txt
crack-emu --project $B report               # 발동 로그 집계
```

## 웹 UI

`crack-emu --project <build> serve` 로 뜬다. 왼쪽에서 페르소나 본문과 유저노트를
직접 쓰고, 가운데서 대화하고, 오른쪽에서 그 턴의 계약 위반·발동 항목·드롭된 항목을
바로 본다. `프롬프트 보기` 는 방금 모델에 보낸 것을 블록 단위로 그대로 펼친다.

API 키는 서버 프로세스의 환경변수에 머무르며 브라우저로 내려가지 않는다.

## 크랙 재현 충실도

`spec/crack_spec.yaml` 이 동작 사양이고, 모든 항목에 근거 등급이 붙어 있다.

| 등급 | 뜻 |
|---|---|
| `OBSERVED` | 유저가 프롬프트 추출로 역공학한 결과 (dcinside 뤼튼갤 #961451). 작성자 본인이 "순서를 맹신하지 말라"고 단서를 달았다 |
| `SKILL` | design-crack-story-chat 스킬이 이미 갖고 있던 규칙 (3슬롯 상한 등) |
| `USER-REPORTED` | 제작자가 알려준 동작 |
| `UNVERIFIED` | 근거 없음. 합리적 추정값이며 실측으로 교체할 자리 |
| `EXTENSION` | 크랙에 있는지 불명. `fidelity: crack` 에서는 강제로 꺼진다 |

**벡터 임베딩 검색은 일부러 구현하지 않았다.** 크랙이 그렇게 동작한다는 근거가
없고, 넣는 순간 QA 대상이 크랙이 아니게 된다. 장기기억은 텍스트 기반이며 기본값은
`recent`, 어휘 매칭(BM25)은 선택 사항이다.

조립 순서(관측):

```
# {페르소나} Information → 메인프롬프트 → 스탯 정의 → ## keyword output
→ [최근 사건 타임라인](요약 4) → [캐릭터 관계도](5) → [System Message]
→ ───── 대화 이력 ─────
→ [User Message] → ## Additional Information & Rules
     [Story State] · <system_note> · <knowledge_base> · <recalled_history>(3)
→ [Roleplay Response]
```

키워드북이 대화 이력 **아래**에 붙는 것이 핵심이다. 최근성 우선순위가 가장 높은
자리이고, 그래서 메인 프롬프트보다 세게 먹는다.

## 검사 항목

`lint` — 모델 호출 없음:

| 규칙 | 내용 |
|---|---|
| `entry_too_long` / `entry_near_limit` | 400자 상한, 360자 권장 |
| `entry_keyword_overflow` | 키워드 5개 상한 |
| `keyword_collision` | 같은 키워드가 두 항목에 |
| `keyword_substring_hazard` | 키워드가 다른 낱말에 묻혀 오발동 (조사 결합은 정상으로 간주) |
| `priority_module_low` | 19금·키스 등 우선 모듈이 3슬롯 밖에 등록됨 |
| `always_on_trigger` | 상태창 고정 항목명을 트리거로 씀 → 슬롯 1개 영구 점유 |
| `prologue_unknown_number` | 프롤로그 이미지가 명부에 없는 인물번호 참조 |

`turn` / `replay` — 응답을 출력 계약에 대조:

| 규칙 | 심각도 |
|---|---|
| `user_impersonation` | critical — `{{user}} \| "..."` 출력 |
| `meta_leak` | critical — `<knowledge_base>` 등 내부 구조 노출 |
| `user_echo` | error — 지문에서 유저 대사 재인용 |
| `notation_leak` | error — ⓤ/ⓒ 노출 |
| `hud_missing` / `hud_field_missing` | 상태창 누락·항목 결손 |
| `image_unknown_character` / `image_unknown_situation` / `image_restricted_code` / `image_bad_host` | 이미지 계약 위반 |
| `numbered_choices` / `choice_prompt` | 선택지 유도 |
| `narration_italic` / `dialogue_format` | 서술 형식 |
| `length_drift` | 분량 드리프트 |

`report` — 누적 발동 로그 집계:

| 규칙 | 내용 |
|---|---|
| `slot_overflow` | 매칭이 3슬롯을 넘겨 항목이 드롭된 턴 |
| `entry_never_fired` | N턴 동안 한 번도 안 걸린 항목 |
| `entry_always_fired` | 매 턴 걸리는 항목 → 메인 프롬프트로 옮길 후보 |
| `high_match_entry_registered_high` | 자주 걸리면서 상단에 등록 → 남의 슬롯을 뺏음 |

## 프로바이더

전부 OpenAI 호환 `/chat/completions`. `spec/crack_spec.yaml` 의 `providers` 에서
`base_url` 과 키 환경변수만 바꾼다.

| 이름 | 비고 |
|---|---|
| `ollama` | 로컬. 키 불필요. 모델 컨텍스트가 작으면 7,000자 프롬프트가 안 들어가니 `num_ctx` 를 키운 모델을 쓸 것 |
| `openrouter` | `OPENROUTER_API_KEY`. `:free` 모델은 상위 풀 429가 잦다 |
| `gemini` | `GEMINI_API_KEY`. 무료 할당량 사용 가능 |
| `openai` | `OPENAI_API_KEY` |
| `echo` | 모델 없이 배관과 QA 규칙만 검증 |
| `agent` | 외부 API 호출 없이 **모델(에이전트) 또는 사용자가 직접 생성한 응답 텍스트를 주입**해 세션 턴에 기록하고 출력 계약 QA 및 키워드북 활성화를 검증하는 자가 루프 모드 |

### 모델 자가 응답 모드 (`agent`)

외부 LLM API(OpenAI/Gemini 등)를 쓰지 않고, **에이전트(LLM 자신)가 직접 캐릭터로서 응답을 작성해 에뮬레이터에 검증받는 루프**입니다:

- **CLI 사용 시**: `crack-emu turn <세션> --input "..." --reply "..."` 또는 `--reply-file "..."` 로 주입.

## 에이전트 연동

모든 하위 명령이 `--json` 으로 단일 JSON 객체를 낸다. 종료 코드는
`0` 통과, `1` 위반 발견, `2` 하네스 오류.

```bash
crack-emu --project $B --json replay qa1 scenarios/lock-probe.txt > result.json
```

`replay` 결과에는 턴별 응답, 발동·드롭된 키워드북 항목, 계약 위반 목록,
규칙별 집계가 들어간다. 위반이 있으면 종료 코드 1이므로 CI에 그대로 걸 수 있다.

전역 플래그는 하위 명령 앞뒤 어디에 써도 된다.

## 발동 로그

턴마다 `<store>/../logs/<session>.jsonl` 에 한 줄씩 쌓인다. 발동 항목, 매칭된
키워드, 매칭이 일어난 위치(직전 턴인지 이번 입력인지), 드롭된 항목, 프롬프트
길이, 그 턴의 위반 목록. `report` 가 이걸 읽는다.

## 테스트

```bash
python3 tests/test_harness.py
```

검사기를 믿기 전에 반드시 실패해야 하는 입력을 먹여 실제로 실패하는지 볼 것.
조용히 전부 통과하는 검사기는 탐색을 일찍 끝내 버린다.
