---
name: design-crack-story-chat
description: Design, compile, or audit Crack interactive story chats from story.md and characters.md into platform-limited prompts and keyword books. Use for story/world design, psychologically generative characters, player agency, pacing and relationship control, long-session consistency, prompt compression, openings, and associated image/showcase production.
---

# 크랙 스토리챗 설계·컴파일

두 원본 `story.md`·`characters.md`에서 플레이 가능한 스토리챗과 플랫폼 규격의 프롬프트·키워드북을 만든다. **아래 핵심 기준을 적용하고, 요청에 맞는 첫 참조를 실제로 읽은 뒤 작업한다.** 링크 목록을 읽은 것을 참조 본문을 읽은 것으로 간주하지 않는다.

## 진입 즉시 적용할 기준

- **공유 지식+고유 차이.** MBTI·에니어그램·하십시오체·작가/장르 등 익숙한 앵커를 쓰고 작품 고유 사실·편차·필수 조건만 덧붙인다. 알려진 개념을 풀어 설명하거나 분석 항목 전부를 프롬프트 칸으로 만들지 않는다.
- **키워드북 발동·강도.** 직전 모델 발화+현재 유저 발화에서 키워드를 감지한다. 발동 항목은 메인 뒤에 주입되는 더 강한 추가 프롬프트이므로 설정뿐 아니라 상황별 행동·문체·연출도 제어한다. 현재 유저의 키워드는 이번 응답에, 이번 모델 출력의 키워드는 다음 응답에 반영된다. 3슬롯 탈락과 상시 기준의 누락을 고려한다.
- **메인=기준·색인, 키워드북=상황별 상세·지시.** 인물 명부는 `이름｜나이·성별·신분｜MBTI·에니어｜戀｜慾｜화법`을 출발점으로 불필요한 열을 지운다. `戀=연애적극성;慾=성적적극성`, 값은 `高/中/低`; 선제 표현 성향이지 호감·동의·거절 기준이 아니다. 외형·과거·욕망·능력 상세는 키워드북, 빠지면 연기가 틀어지는 핵심 제약만 메인에 남긴다.
- **세계관=평소의 사실과 작동 방식.** 시대·지역 앵커와 고유 전제, 사회·세력·지리·법칙·생활 중 필요한 것을 쓴다. 갈등·비밀·반전을 필수 칸으로 강제하지 않는다. 첫 사건은 시작 프롬프트에 분리한다.
- **ⓤ의 선택·속도 보존.** 행동·대사·생각·감정·결정을 대필하지 않는다. 빠른 고백·진전·돌파·시간 생략을 턴 수·단계·쿨다운으로 막지 않는다. 무근거 성공 보장도 실패·모욕·대가 추가도 피하고 현재 의사와 실제 세계 조건으로 결과를 낸다.
- **세계와 NPC가 먼저 움직일 수 있다.** 진행=의미 있는 상태 변화. 반복이면 기존 욕망·문제·행동 결과에서 변화를 낸다. 플롯·관계·긴장을 구분하고 모델 주도 급등만 근거·후속 반응으로 조절한다. 요청된 휴식·선택 대기·종료는 정체가 아니다.
- **정사·지식·상태를 구분.** 핵심 성격·화법은 유지하되 감정·관계·계획은 경험으로 갱신한다. NPC 발언≠세계 사실≠다른 NPC의 지식. 키워드북 조회≠등장·폭로·사건 성립. 누락된 기억·비밀을 창작하지 않는다.
- **하네스는 고정.** 사용 가능한 대화 문맥 외의 숨은 장부·정밀 카운터·JSON 상태·저장 API·영구 기억을 가정하지 않는다. HUD는 확인된 상태의 표시다. SAFE/UNSAFE는 표현 범위만 달리하며 정사·판정·주체성·외부 정책은 동일하다.

## 요청 → 바로 읽을 곳 → 꺼낼 지식

가장 가까운 행부터 시작한다. 복합 요청이면 관련 행을 함께 읽되, 문서 안의 링크를 전부 따라가지 않는다. **대표 뼈대는 기본값을 보여주는 예시이며, 기존 프로젝트를 무조건 그 형식으로 교체하는 명령은 아니다.**

| 요청·증상 | 첫 참조와 읽을 범위 | 바로 사용할 것 |
|---|---|---|
| “통짜/기본 뼈대”, 전체 메인 재작성, 새 작품의 프롬프트 형태 | [system-prompt-presets.md](references/system-prompt-presets.md) §1 기본 뼈대 | 세계관·명부·서사제어·문체·출력의 완결된 골격. 장르 예시는 필요할 때만. |
| 진행 정체/과속, 부정편향, 관계 반복, NPC 수동성, 캐릭터 희석 | [narrative-control.md](references/narrative-control.md) 운영 규칙·커널·검증 문항 | 판정→발동→개입→제약. 사용자 주도 속도와 모델 주도 개입의 구분. |
| 세계관·작품 기획 | [story-model.md](references/story-model.md) World canon·해당 world systems; [story-craft.md](references/story-craft.md) 체험·사건 설계 | 일상 기준·가능한 행동·조건부 사건. 세계 설명과 예정 줄거리 분리. |
| 캐릭터 만들기/수정 | [character-personality.md](references/character-personality.md) 명부·유형·표현; 깊은 설계는 [character-generation.md](references/character-generation.md) | 짧은 공유 지식 앵커+고유 편차. 심리 분석과 메인 수록량 분리. |
| 키워드북 작성/분리, 미발동·슬롯 충돌 | [keyword-book.md](references/keyword-book.md) §1~6 | 메인과 경계→본문→호출→등록 예시→3슬롯→검증의 전체 작성 흐름. |
| 문체·말투·서술 개선 | [prose-style-guide.md](references/prose-style-guide.md) 앵커·필요한 교정 항목 | 문체 앵커+편차; 장르와 무관한 문장 규칙 남발 방지. |
| 압축·7천 자 맞추기 | [semantic-compression.md](references/semantic-compression.md) 공유 지식·압축 루프 | 중복 제거→앵커/표/기호→의미 복원 확인→실측. |
| 프롤로그·첫 입력·시작 장면 | [opening-design-guide.md](references/opening-design-guide.md); 프로필 처리는 [conversation-continuity.md](references/conversation-continuity.md) | 최초 상황과 개인화 처리, 플레이어에게 넘길 행동 공간. |
| 최종 빌드·SAFE/UNSAFE | [crack-prompt-rules.md](references/crack-prompt-rules.md) → [content-variants.md](references/content-variants.md) → [output-contract.md](references/output-contract.md) | 플랫폼 계약·변형 차이·실제 출력 형식. 기본 뼈대가 필요하면 첫 행 병행. |
| 검사·완성 판정 | [validation.md](references/validation.md); 서사 변경은 narrative-control 검증 문항 병행 | 구조·분량·계약 검사와 행동 검증의 구분. |

참조를 읽고 **현재 수정할 규칙·설정·산출물에 반영**한다. 배경 연구는 근거 확인·연구 요청일 때 읽는다. [전체 참조 지도](references/README.md)는 위 경로로 찾지 못한 경우의 색인이며 기본 선행 독서가 아니다.

## 프로젝트 작업 시 적용할 계약

부분 수정은 해당 범위만 수행한다. 전체 제작 요청일 때 아래 흐름을 끝까지 적용한다.

1. **기존 상태 확인.** 두 원본과 관련 변경을 먼저 읽는다. 빌드 직접 수정이 있으면 재생성 전 의도를 확인하고 유효한 정사를 원본에 반영해 보존한다.
2. **원본 소유권.** `story.md`=세계·ⓤ 고정 역할·시스템·사건·오프닝·로어 후보. `characters.md`=인물 정체성·심리·관계·지식·능력·외형·상세 후보. 저작 원본은 이 둘뿐이다. 중간 프롬프트 원본·세 번째 기억 파일을 만들지 않는다. 필요 ID는 하이픈형, 표시 이름과 구분하고 점으로 나눈 개발용 네임스페이스는 쓰지 않는다.
3. **수록 위치.** 상시 기준→통합본, 최초 입력/개인화→시작 프롬프트, 조건부 상세→키워드북, 사용자 명시 호출 기능→단축어. 성격 분석을 모두 메인에 싣지 않으며 상시 문체·서사제어를 키워드 호출에 의존시키지 않는다. 최종 프롬프트에는 참조 링크 대신 실제 실행 문구를 펼친다.
4. **산출물 5종.** `build/prologue.md`, `build/integrated-prompt-safe.md`, `build/integrated-prompt-unsafe.md`, `build/start-prompt.md`, `build/keyword-book.md`. 키워드북은 필요하면 `keyword-book-safe.md`·`keyword-book-unsafe.md` 쌍으로 대신한다. 비어도 키워드북 산출물은 유지한다. 두 변형은 같은 정사에서 함께 컴파일하며 성인 전용 지침·A코드는 unsafe 키워드북에만 둔다.
5. **독립 분량 측정.** 통합본 각 ≤7,000자; 프롤로그·시작 각 ≤1,000자; 키워드 본문 각 ≤400자·키워드 1~5개·활성 설정/조건 명시. 코드포인트와 UTF-16 중 큰 값으로 검사한다. 평상시 의도된 조회 0~2항목+여유 1슬롯; 4개 동시 주입에 의존하지 않는다. 짧고 충분하면 예산을 채우지 않는다.
6. **개인화·가시 출력.** 개인 프로필은 시작 프롬프트가 자유 입력을 받아 해석하고 외부 입력 폼을 재출력하지 않는다. 개인화 값을 통합본에 고정하지 않는다. 숨은 지침은 압축 가능하지만 플레이어에게 보이는 문장은 자연스럽게 쓴다.
7. **검증·재생성.** 원본 수정 후 관련 빌드를 재생성하고 validation의 해당 검사를 실행한다. 컴파일 완료 후에만 `scripts/check_freshness.py <project> --stamp`로 원본 해시를 기록한다. 정적 검사 통과를 실제 진행감·장기 일관성 검증으로 보고하지 않는다.

## 해당 요청이 있을 때만 여는 확장 지식

| 작업 | 직접 참조 |
|---|---|
| HUD·공개 상태 표시 | [status-window-guide.md](references/status-window-guide.md) |
| 복수 시작 설정·단축어 | [start-sets.md](references/start-sets.md), [shortcuts-guide.md](references/shortcuts-guide.md) |
| 외형·장면 이미지 설계 | [character-appearance-guide.md](references/character-appearance-guide.md), [scene-design-guide.md](references/scene-design-guide.md) |
| 이미지 프롬프트·감정 프리셋·NovelAI | [image-prompt-authoring.md](references/image-prompt-authoring.md)를 먼저 읽는다. 감정은 얼굴 클로즈업, 행동은 보조. POV 상세는 [novelai-prompt-engineering.md](references/novelai-prompt-engineering.md). |
| 배경 크롭·장소명 배지·일괄 리네이밍 | [image-assets.md](references/image-assets.md) 배경 크롭 파이프라인 → `tools/images/crop_backgrounds.py` (`--help`로 옵션 확인) |
| 이미지 자산·호스팅·쇼케이스 | [image-assets.md](references/image-assets.md), [image-output-rules.md](references/image-output-rules.md) |
| 소개문·플레이 안내 | [story-description-guide.md](references/story-description-guide.md), [play-guide.md](references/play-guide.md) |
| 에디터 등록·동기화 | [crack-auto-sync-guide.md](references/crack-auto-sync-guide.md) |
| 파일 구조 변경·신규 프로젝트 파일 | [file-architecture.md](references/file-architecture.md), [starter assets](assets/story-chat-template) |

전체 제작의 소개문·요약 코멘트·자산 설정은 `build/assets/`에 둔다. 서사 규칙 수정만으로 이미지 제작·호스팅·에디터 동기화를 시작하지 않는다.

## 스킬 유지보수·결과 보고

한 작업의 실행 규칙·예시·검증은 가까이 모으고 연구 설명은 뒤에 둔다. 플랫폼 계약·관찰 결과·설계 판단을 구분한다. 규칙을 교체하면 충돌하는 참조·예시도 갱신하며 새 규칙만 덧붙이지 않는다. 결과에는 바뀐 동작과 파일, 수행한 검사, 컴파일 시 실측 분량, 실제 플레이 검증 여부를 적는다.
