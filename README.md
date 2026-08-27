# design-crack-story-chat

크랙(Crack) 스토리챗을 **설계·컴파일·검증**하는 에이전트 스킬입니다.

세계관과 인물을 두 개의 마크다운 파일에만 쓰면, 크랙의 각 입력란에 그대로 넣을 수 있는 **5개의 산출물**로 컴파일합니다. 제작자 커스텀 프롬프트 7,000자 상한과 키워드북 3슬롯 제한 같은 플랫폼 제약을 설계 단계에서부터 강제합니다.

Claude Code, Cowork, Codex 등 스킬을 읽는 에이전트에서 동작합니다.

---

## 왜 필요한가

크랙에 스토리챗을 올리려면 서로 다른 입력란 다섯 개를 채워야 하고, 각각 다른 제약이 걸립니다.

| 입력란 | 상한 | 로딩 방식 |
|---|---|---|
| 통합 프롬프트 (SAFE) | 7,000자 | 항상 |
| 통합 프롬프트 (UNSAFE) | 7,000자 | 항상 |
| 프롤로그 | 1,000자 | 최초 1회 |
| 시작 프롬프트 | 1,000자 | 도입부 |
| 키워드북 | 항목당 400자, 최대 20개 | 조건부, **동시 3개까지** |

여기에 더해 **파생 산출물** 두 종류가 `build/assets/`에 같이 나옵니다 — 목록에 붙일 요약 코멘트와 이미지 프롬프트. 크랙에 붙이는 것이 아니라 같은 원본에서 매번 다시 생성되는 제작 입력입니다.

여기서 사람이 반복해서 틀리는 지점이 정해져 있습니다.

- **상한이 토큰이 아니라 글자수입니다.** 토큰 절약 습관대로 영어로 쓰면 오히려 길어집니다. 한국어가 영어의 약 절반입니다.
- **응답 분량은 숫자가 아니라 첫 응답(오프닝)에 앵커링합니다.** 고정 글자수 제한 대신 오프닝 서술량을 기준선으로 동기화하고 특수씬(전투/19+) 분량 급상승을 차단합니다.
- **동시 로딩이 3개뿐입니다.** 키워드북은 로어 사전이 아니라 조건부 연출 프롬프트 조각(키스, 19+ 성애, 특수전투 등)으로 분리 운용합니다.
- **자율성은 6중 잠금하되 ⓒ(NPC)의 능동성을 허용합니다.** 유저의 대사·행동은 대리서술하지 않되, NPC와 세계가 먼저 치고 들어와 스토리가 멈추지 않고 굴러갑니다.
- **3단 입력 파싱을 지킵니다.** `[메타]` > `*지문/설정*` > `평문 대사` 계층과 `/OOC` 모드 전환으로 유저의 자유 설정을 100% 안전하게 수용합니다.
- **말투는 고정 예시가 아니라 4단 벡터로 동적 합성합니다.** `[성격키워드 + MBTI + 관계단계 + 상황맥락]` 조합으로 관계가 깊어질수록 어조가 자연스럽게 진화합니다.
- **상태창(HUD)은 8대 표준 슬롯과 코드블록으로 관리합니다.** 턴 간 연속성 계승과 상황 태깅(`🟢`, `⚔️`, `💋`, `♀🔞`)의 메모리 앵커 역할을 수행합니다.
- **위험도 기반 비대칭 압축을 적용합니다.** 사고 위험이 큰 주도권 규칙은 골든 예시를 포함해 확실히 잠그고, 데이터·스타일 규칙은 `｜`, `·` 구분자로 극압축합니다.

이 스킬은 위 제약을 문서로 설명하는 데 그치지 않고, **스크립트로 검사**하며 **100% 순수 프리셋 라이브러리**를 제공합니다.

---

## 설치

세 가지 방법이 있습니다. Claude Code 사용자는 방법 1, Claude Code 외 에이전트(Cowork, Codex 등)는 방법 2, 스킬 자체를 고쳐 쓸 사람은 방법 3을 고르세요.

### 방법 1 — Claude Code 플러그인 마켓플레이스 (Claude Code 사용자 권장)

이 저장소가 곧 마켓플레이스입니다(`.claude-plugin/marketplace.json`). Claude Code 안에서,

```
/plugin marketplace add CREE1116/design-crack-story-chat
/plugin install design-crack-story-chat@design-crack-story-chat
```

버전을 올릴 때는 `/plugin marketplace update design-crack-story-chat` 로 마켓플레이스 메타데이터를 새로고침한 뒤 다시 install하면 최신본으로 교체됩니다.

### 방법 2 — `.skill` 파일 (Claude Code 외 에이전트)

[Releases](../../releases)에서 최신 `design-crack-story-chat.skill`을 내려받아, 사용 중인 에이전트의 스킬 추가 기능(파일 업로드 또는 스킬 폴더에 압축 해제)에 넣습니다. 파일 자체는 `skills/design-crack-story-chat/` 내용을 그대로 압축한 zip이라, 아카이브를 열어 원하는 스킬 디렉터리에 풀어 넣어도 동일하게 동작합니다.

release가 아직 없으면 직접 만들 수도 있습니다.

```bash
git clone https://github.com/CREE1116/design-crack-story-chat.git
cd design-crack-story-chat
./scripts/build-skill.sh            # dist/design-crack-story-chat.skill 생성
```

### 방법 3 — 저장소에서 설치 (스킬을 직접 고칠 사람)

```bash
git clone https://github.com/CREE1116/design-crack-story-chat.git
cd design-crack-story-chat
./scripts/install-skill.sh          # ~/.claude/skills, ~/.agents/skills 에 심볼릭 링크
```

링크 방식이라 저장소를 고치면 에이전트에 **즉시 반영**됩니다. 사본을 원하면 `--copy`를 주세요.

```bash
./scripts/install-skill.sh --copy
```

저장소에서 작업할 때의 규칙은 [CLAUDE.md](CLAUDE.md)에 있습니다.

### 설치 확인

방법에 상관없이, 에이전트에게 이렇게 물어보면 됩니다.

```
design-crack-story-chat 스킬 로딩해줘.
```

`SKILL.md`를 읽었다고 답하면 설치된 것입니다. 안 읽었다면 스킬 폴더 경로(`~/.claude/skills/design-crack-story-chat` 등)가 에이전트가 스킬을 찾는 위치와 일치하는지 확인하세요.

---

## 빠른 시작

스킬을 설치한 에이전트(Claude Code 등)를 프로젝트 폴더에서 열고 이렇게 시작합니다.

```
새 크랙 스토리챗을 만들거야. design-crack-story-chat 스킬 써서
story.md와 characters.md 틀부터 잡아줘.
```

에이전트가 `assets/story-chat-template/`의 틀을 복사해 두 파일을 만들어 줍니다. 이후 진행은 이렇습니다.

1. **경험 계약을 먼저 정합니다.** 로어부터 쓰면 반드시 다시 씁니다 — 전제, 플레이어 판타지, 핵심 루프, 약속, 자유 경계 다섯 개를 결정하지 않은 채 설정에 들어가지 마세요.
   ```
   전제는 "게이트가 열린 2047년 서울, 갓 각성한 무소속 헌터"야.
   경험 계약부터 잡고 갈등 엔진을 만들어줘. 로어는 아직 쓰지 마.
   ```
2. **세계관을 씁니다.** `story.md` 하나에 전부 — 등급 체계, 위협 분류, 성장 체계, 세력 경제까지. 능력물·생존물·직업물·경쟁물이라면 인물보다 세계 시스템을 먼저 잡습니다.
3. **인물을 씁니다.** `characters.md` 하나에 전부 — 외형·말투·능력·관계를 인물마다. 여기 없는 이름은 컴파일 시 모델이 지어냅니다.
4. **컴파일합니다.** 에이전트가 두 원본에서 5개 산출물(SAFE/UNSAFE 통합 프롬프트, 프롤로그, 시작 프롬프트, 키워드북)과 파생 산출물(요약 코멘트, 이미지 프롬프트)을 `build/`에 뽑습니다.
5. **검증합니다.**
   ```bash
   ./scripts/validate.sh <프로젝트 경로>
   ```
   글자수 상한, 정의 없는 기호, 3슬롯 충돌, 원본 대비 신선도를 스크립트 8개가 잡습니다. 실패하면 그대로 크랙에 올리지 않습니다.
6. **크랙에 붙여넣습니다.** 통합 프롬프트(SAFE/UNSAFE)·프롤로그·시작 프롬프트는 해당 입력란에 그대로 복사합니다. 키워드북만 UI에서 항목별로 등록합니다(한 번에 최대 3개까지 동시 로딩되므로 등록 후 장면을 나열해 충돌을 확인하세요).
7. **플레이하며 고칩니다.** 원본(`story.md`/`characters.md`)을 고쳤다면 4~5단계를 반드시 다시 돕니다. `check_freshness.py`가 재컴파일을 잊은 상태를 잡아줍니다.

원본은 딱 두 개입니다. 매니페스트, 상태 파일, 출력 계약 파일, 키워드북 소스 같은 중간 계층을 만들지 않습니다. 사실 하나에 주인 하나입니다.

전체 흐름을 처음부터 끝까지 따라가는 문서는 **[docs/usage.md](docs/usage.md)** 입니다. 막히면 **[docs/troubleshooting.md](docs/troubleshooting.md)** 를 먼저 보세요.

---

## 저장소 구조

```
skills/design-crack-story-chat/   스킬 본체
  SKILL.md                        진입점 — 워크플로와 라우팅
  references/                     주제별 상세 문서 18개 (프리셋, 상태창, 오프닝, 출력 규약, 이미지 출력 룰 포함)
  scripts/                        검증 스크립트 8개
  assets/story-chat-template/     story.md · characters.md 틀

examples/hunter/                  실제 작동하는 예제 (한국 헌터물, 인물 15명)
  story.md · characters.md        원본 2개
  build/                          컴파일된 크랙 산출물 5개
    assets/                       파생 산출물 — 요약 코멘트, 이미지 프롬프트
  .assets/                        손으로 쓴 픽스처 (슬롯 시뮬레이션 장면)

tools/images/                     이미지 자산 정리·배포
  deploy.py                       폴더 골격 생성, 축 계약 검사, 깃헙+jsDelivr 배포

docs/                             문서
scripts/                          릴리스 빌드, 전체 검증
```

---

## 검증 스크립트

전부 표준 라이브러리만 씁니다. 의존성이 없습니다.

| 스크립트 | 잡는 것 |
|---|---|
| `check_project_layout.py` | 원본 2개 + 산출물 5개 구조 |
| `check_build.py` | 산출물별 글자수 상한 |
| `check_prompt_length.py` | 개별 파일 글자수 (코드포인트·UTF-16 둘 다) |
| `check_keyword_book.py` | 항목 형식, 400자, 키워드 1~5개, 중복 |
| `check_symbols.py` | **정의 없이 쓰인 기호·이모지** |
| `check_kb_slots.py` | **장면별 3슬롯 초과 시뮬레이션** |
| `check_freshness.py` | **원본을 고치고 재컴파일 안 한 상태** |
| `check_image_assets.py` | 인물 명부와 이미지 프롬프트 대조, 선두 태그 구별 |

한 번에 돌리려면,

```bash
./scripts/validate.sh examples/hunter
```

이 저장소는 GitHub Actions에서 푸시할 때마다 예제 프로젝트로 위 검사를 전부 돌립니다. 스크립트가 실제로 동작한다는 증거이자, 예제가 항상 유효하다는 보증입니다.

> **검증 스크립트에는 반드시 음성 대조를 먹이세요.** 통과했다고 보고하는 검사기를 믿기 전에, 실패해야 마땅한 입력을 넣어 실제로 실패하는지 확인합니다. 모든 것을 조용히 통과시키는 검사기는 없는 것보다 나쁩니다. 탐색을 끝내버리기 때문입니다.

---

## 예제

`examples/hunter/`는 장식이 아니라 실제로 플레이 가능한 완성품입니다.

- 게이트·각성자 소재의 한국 헌터물
- 인물 15명 (협회 2 + 4대 길드 각 3 + 필드 요원)
- 4단계 등급 체계, 범람체 6종 분류, 이중축 성장 체계
- 키워드북 19개 항목(심화·명부·조회·채움 4유형), 통합 프롬프트 6,877 / 6,961자
- 이미지 프롬프트 108장 분량 (인물 15 × 상황 6 + 장면·배경·범람체 18)

컴파일 결과가 어떤 밀도로 나와야 하는지 보려면 [`examples/hunter/build/integrated-prompt-safe.md`](examples/hunter/build/integrated-prompt-safe.md)를 먼저 읽으세요.

---

## 이미지 호스팅 및 웹 쇼케이스

스토리챗은 외부 호스팅 이미지를 `![]({IMG}/카테고리/번호.png)` 형태로 조합해 실시간 호출할 수 있습니다.

**이미지를 직접 생성하는 기능은 없습니다.** 대신 **Cloudflare Pages를 통한 초고속 호스팅(서울 엣지 0초대 로딩 & 무제한 트래픽)** 및 **웹 쇼케이스 갤러리(`index.html`) 자동 생성**을 지원합니다.

```bash
export CRACK_PROMPTS=examples/hunter/build/assets/prompts.json
cd tools/images

python3 deploy.py --scaffold --root ~/내이미지폴더   # 폴더, _배치표.md, index.html(웹 갤러리) 자동 생성
python3 deploy.py --check    --root ~/내이미지폴더   # 파일 이름이 축 목록과 맞는지 검사
```

- `--scaffold`가 인물·장면별 폴더와 **Cloudflare Pages 배포용 웹 갤러리(`index.html`)**를 자동 생성합니다.
- `deploy.py --check`가 배포 전 **축 목록과 파일명이 정확히 일치하는지 검사**하여 깨진 링크를 100% 방지합니다.

자세한 내용은 [docs/image-assets.md](docs/image-assets.md)에 있습니다.

---

## 문서

- [사용법](docs/usage.md) — 처음부터 끝까지 따라하기
- [산출물 5종](docs/artifacts.md) — 각 입력란에 무엇이 들어가고 왜 그런지
- [검증](docs/validation.md) — 스크립트 사용법과 흔한 실패
- [이미지 자산](docs/image-assets.md) — 프롬프트 설계와 배치 생성
- [자주 겪는 문제](docs/troubleshooting.md) — 상태창이 안 뜬다, 메타 발언이 샌다 등

---

## 확인되지 않은 것

정직하게 적어둡니다. 아래는 크랙 UI에서 직접 확인해야 하며 이 저장소가 보증하지 않습니다.

- 상태창 코드펜스 안의 들여쓰기(`ㅤ` U+3164) 렌더링
- 이모지 렌더링
- 마크다운 외부 이미지(`![](url)`) 로딩 여부
- 키워드북 `activation_setting`의 실제 선택지 문자열

플랫폼 동작을 추측해서 규칙을 만들지 않는 것이 이 스킬의 원칙입니다. 확인되지 않은 것은 확인되지 않았다고 표시합니다.

---

## 라이선스

[MIT](LICENSE)

`examples/hunter/`의 세계관·인물 설정은 이 스킬의 사용 예시로 함께 배포됩니다. 자유롭게 참고하고 개조하세요.
