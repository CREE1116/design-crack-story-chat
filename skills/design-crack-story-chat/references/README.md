# 레퍼런스 지도 (Reference Map)

레퍼런스를 전부 읽으면 컨텍스트가 남지 않는다. 이 문서는 **어떤 사실이 어느 파일 소유인지**만 알려준다. 작업 종류로 파일을 고르는 라우팅은 [SKILL.md](../SKILL.md)의 "Route the work"에 있다.

## 한 사실 = 한 소유 문서

같은 규칙이 두 파일에 적히면 한쪽만 고쳐진 채 둘 다 살아남고, 컴파일 때 어느 쪽이 맞는지 알 수 없게 된다. **사본을 만들지 말고 링크한다.** 이미 있는 규칙과 충돌하는 규칙을 쓰게 되면 둘 중 하나를 고친다.

작업 하나를 끝내기 위해 원리→문구→검증 문서를 계속 왕복하지 않게 한다. **서사 제어는 `narrative-control.md` 하나에 적용·커널·검증·근거를 함께 둔다.** 다른 문서는 링크만 둔다. 나머지 기존 분야의 소유권은 아래 표를 따른다.

| 층 | 소유 문서 | 담는 것 |
|---|---|---|
| 원리·효과 | `production-patterns.md` | 패턴이 왜 필요한가, 무엇을 막는가 |
| 실제 프롬프트 문구 | `crack-prompt-rules.md` | 통합 프롬프트에 그대로 들어갈 문장 |
| 조립된 완성 골격 | `system-prompt-presets.md` | 장르별로 슬롯을 채운 전체 프리셋 |
| 쓰는 법 | `prompt-writing.md` | 규칙을 어떻게 문장으로 만드나 (개별 규칙 사본 없음) |

## 소유권 표

| 사실 | 소유 문서 |
|---|---|
| 파일 구조, 두 원본의 경계, 빌드 산출물 계약 | `file-architecture.md` |
| 고정 하네스 서사제어 전체: 유저 속도·판정·커널·행동 검증·연구 | `narrative-control.md` |
| 기획·갈등 엔진·씬·분기·엔딩 | `story-craft.md` |
| 세계 시스템(등급·위협·성장·경제), 사건, 비밀, 인물 정의 틀 | `story-model.md` |
| 심리 생성 엔진(T0, 상태 슬롯, 생성 순서) | `character-generation.md` |
| 최소 인물 명부·戀/慾 열·화법 앵커·개별 상세 배치 | `character-personality.md` |
| 외형 지문, 헤어 3요소, 의상 색 결속, NAI 고정 비법 | `character-appearance-guide.md` |
| 배경·환경 프롬프트, 풍경화형 vs 인물배치형 | `scene-design-guide.md` |
| NAI 가중치 문법, POV 기하학, S01~S18 / A01~A15 태그 사전 | `novelai-prompt-engineering.md` |
| 이미지 프롬프트 작성: 외형·의상·감정·행동 분리, 얼굴 위주 감정 구도 | `image-prompt-authoring.md` |
| **문체·감각 서술, 문체 패치 블록** | `prose-style-guide.md` |
| 6중 잠금·부정편향·앵커링·나레이터 **문구** | `crack-prompt-rules.md` |
| 위 항목들의 **원리와 효과** | `production-patterns.md` |
| 장르별 완성 프리셋, 7,000자 예산 배분 | `system-prompt-presets.md` |
| 규칙 작성법, 네 경로 배치, 3단 계층, **역발상 5단계 파이프라인, 30대 보편 원칙** | `prompt-writing.md` |
| **공유 지식 앵커+고유 편차, 표 헤더 공유, 전역 기호·글자 수** | `semantic-compression.md` |
| **크랙 런타임 주입 파이프라인, 상단/하단 주입 위치** | `crack-internal-runtime.md` |
| **키워드북 3슬롯, 트리거 설계, 상시 강화 항목** | `keyword-book.md` |
| 단축어 3분류, 400자 규격, 표준 4종, 실사용 설계 규칙 10 | `shortcuts-guide.md` |
| HUD 8슬롯, 관계 이모지 매트릭스, 갱신·계승 | `status-window-guide.md` |
| 지문·대사 문법, 특수 채널, 미디어 호출, 금지 출력 | `output-contract.md` |
| SAFE/UNSAFE 델타와 불변식 | `content-variants.md` |
| 프롤로그 7단 줌인, 시작 프롬프트 4단 핫스타트 | `opening-design-guide.md` |
| 다중 시작 세트 디렉토리 규약 | `start-sets.md` |
| 대화 연속성, 첫 입력 프로필 파싱 | `conversation-continuity.md` |
| 이미지 에셋 구조, WebP, Cloudflare, 쇼케이스 | `image-assets.md` |
| 캐릭터 누끼, 배경 합성·보케, 배경 품질 일관성 | `image-compositing.md` |
| 프롬프트 내 이미지 출력 규칙, 성인 이미지 이관 | `image-output-rules.md` |
| 상세설명란·댓글 코멘트 작성 규격 | `story-description-guide.md` |
| **플레이 가이드, 추천 답변 3개** | `play-guide.md` |
| Playwright 자동 동기화 | `crack-auto-sync-guide.md` |
| 검수 체크리스트 전체 | `validation.md` |

## 자주 헷갈리는 경계

- **문체를 어디에 넣나** → 배치 표는 `prose-style-guide.md` §5-3, 상시 항목 성립 조건은 `keyword-book.md` §5, 주입 위치의 근거는 `crack-internal-runtime.md`.
- **글자 수 숫자** → 전부 `semantic-compression.md` §4 소유. 다른 문서의 숫자는 인용이다.
- **말투** → 설계는 `character-personality.md`, 프롬프트 한 줄은 `crack-prompt-rules.md`, 서술 문체는 `prose-style-guide.md`. 셋은 다른 것이다.
- **키워드북 항목 순서** → 누락 비용에 따라 정렬하며 선택적 상시 보강은 최하단(`keyword-book.md` §5). 검사는 `crack-emu lint` / `report`.
- **HUD** → 규격은 `status-window-guide.md`, 출력 문법과 생략 조건은 `output-contract.md`.
- **플레이어가 읽는 글 3종** → 한 줄 소개(30자)·상세설명·고정 댓글은 `story-description-guide.md` §0, 시작 전 안내판과 추천 답변은 `play-guide.md`. 다섯 칸 전부 다른 필드다.
- **단축어** → 키워드북과 같은 파일에 담기지만 소유 문서는 `shortcuts-guide.md`. `keyword-book.md` 에는 사본을 두지 않는다.

## 작업별 최소 로드 묶음

읽을 파일을 고를 때 이 묶음보다 넓히지 않는다.

| 하려는 일 | 로드 |
|---|---|
| 새 작품 처음 설계 | `story-craft` → `story-model` → `character-generation` → `file-architecture` |
| 진행·관계·NPC 능동성 개선 | `narrative-control` (인물 슬롯 수정 시에만 `character-generation`) |
| 통합 프롬프트 컴파일 | `crack-prompt-rules` → `narrative-control` → `content-variants` → `output-contract` (길이 초과 시 `semantic-compression`) |
| 키워드북 설계·수정 | `keyword-book` → `crack-internal-runtime` |
| 오프닝 손보기 | `opening-design-guide` → `output-contract` |
| 문체만 고치기 | `prose-style-guide` (필요 시 `keyword-book` §5) |
| 인물 추가 | `character-generation` → `character-personality` → `character-appearance-guide` → `image-assets` |
| 이미지 프롬프트 | `novelai-prompt-engineering` → `character-appearance-guide` → `scene-design-guide` |
| 검수·릴리스 | `validation` → `story-description-guide` → `play-guide` → `crack-auto-sync-guide` |
