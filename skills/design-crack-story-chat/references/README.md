# 레퍼런스 지도 (Reference Map)

레퍼런스는 29개다. 전부 읽으면 컨텍스트가 남지 않는다. 이 문서는 **어떤 사실이 어느 파일 소유인지**만 알려준다. 작업 종류로 파일을 고르는 라우팅은 [SKILL.md](../SKILL.md)의 "Route the work"에 있다.

## 한 사실 = 한 소유 문서

같은 규칙이 두 파일에 적히면 한쪽만 고쳐진 채 둘 다 살아남고, 컴파일 때 어느 쪽이 맞는지 알 수 없게 된다. **사본을 만들지 말고 링크한다.** 이미 있는 규칙과 충돌하는 규칙을 쓰게 되면 둘 중 하나를 고친다.

한 주제를 여러 파일이 다루는 정당한 경우는 하나뿐이다 — **원리(왜)와 실제 문구(무엇을 붙여넣나)의 분리**. 이때도 각각 소유자가 다르다.

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
| 기획·갈등 엔진·씬·분기·엔딩 | `story-craft.md` |
| 세계 시스템(등급·위협·성장·경제), 사건, 비밀, 인물 정의 틀 | `story-model.md` |
| 심리 생성 엔진(T0, 상태 슬롯, 생성 순서) | `character-generation.md` |
| 성격 10슬롯, **동적 4단 말투 합성**, 역린, 관계 단계별 어조 | `character-personality.md` |
| 외형 지문, 헤어 3요소, 의상 색 결속, NAI 고정 비법 | `character-appearance-guide.md` |
| 배경·환경 프롬프트, 풍경화형 vs 인물배치형 | `scene-design-guide.md` |
| NAI 가중치 문법, POV 기하학, S01~S18 / A01~A15 태그 사전 | `novelai-prompt-engineering.md` |
| **문체·감각 서술, 문체 패치 블록** | `prose-style-guide.md` |
| 6중 잠금·능동성·부정편향·앵커링·나레이터 **문구** | `crack-prompt-rules.md` |
| 위 항목들의 **원리와 효과** | `production-patterns.md` |
| 장르별 완성 프리셋, 7,000자 예산 배분 | `system-prompt-presets.md` |
| 규칙 작성법, 네 경로 배치, 3단 계층 | `prompt-writing.md` |
| **압축 루프 4단계, 전역 기호표, 산출물별 글자 수 타겟** | `semantic-compression.md` |
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
| 프롬프트 내 이미지 출력 규칙, 성인 이미지 이관 | `image-output-rules.md` |
| 상세설명란·댓글 코멘트 작성 규격 | `story-description-guide.md` |
| **플레이 가이드, 추천 답변 3개** | `play-guide.md` |
| Playwright 자동 동기화 | `crack-auto-sync-guide.md` |
| 검수 체크리스트 전체 | `validation.md` |

## 자주 헷갈리는 경계

- **문체를 어디에 넣나** → 배치 표는 `prose-style-guide.md` §5-3, 상시 항목 성립 조건은 `keyword-book.md` 팁 8, 주입 위치의 근거는 `crack-internal-runtime.md`.
- **글자 수 숫자** → 전부 `semantic-compression.md` §4 소유. 다른 문서의 숫자는 인용이다.
- **말투** → 설계는 `character-personality.md`, 프롬프트 한 줄은 `crack-prompt-rules.md`, 서술 문체는 `prose-style-guide.md`. 셋은 다른 것이다.
- **키워드북 항목 순서** → 우선 모듈은 최상단(`keyword-book.md` 팁 3), 상시 항목은 최하단(팁 8). 검사는 `crack-emu lint` / `report`.
- **HUD** → 규격은 `status-window-guide.md`, 출력 문법과 생략 조건은 `output-contract.md`.
- **플레이어가 읽는 글 3종** → 한 줄 소개(30자)·상세설명·고정 댓글은 `story-description-guide.md` §0, 시작 전 안내판과 추천 답변은 `play-guide.md`. 다섯 칸 전부 다른 필드다.
- **단축어** → 키워드북과 같은 파일에 담기지만 소유 문서는 `shortcuts-guide.md`. `keyword-book.md` 에는 사본을 두지 않는다.

## 작업별 최소 로드 묶음

읽을 파일을 고를 때 이 묶음보다 넓히지 않는다.

| 하려는 일 | 로드 |
|---|---|
| 새 작품 처음 설계 | `story-craft` → `story-model` → `character-generation` → `file-architecture` |
| 통합 프롬프트 컴파일 | `crack-prompt-rules` → `semantic-compression` → `content-variants` → `output-contract` |
| 키워드북 설계·수정 | `keyword-book` → `crack-internal-runtime` |
| 오프닝 손보기 | `opening-design-guide` → `output-contract` |
| 문체만 고치기 | `prose-style-guide` (필요 시 `keyword-book` 팁 8) |
| 인물 추가 | `character-generation` → `character-personality` → `character-appearance-guide` → `image-assets` |
| 이미지 프롬프트 | `novelai-prompt-engineering` → `character-appearance-guide` → `scene-design-guide` |
| 검수·릴리스 | `validation` → `story-description-guide` → `play-guide` → `crack-auto-sync-guide` |
