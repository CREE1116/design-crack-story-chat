# NovelAI 정밀 프롬프트 엔지니어링 및 POV 지오메트리 가이드 (NovelAI Prompt Engineering & POV Geometry)

본 문서는 `novel-ai-image-skill`의 핵심 엔진인 **정밀 POV 카메라 지오메트리, NovelAI V4/V5 가중치 문법, 및 S/A 코드 단부루 공식 태그 사전**을 크랙 스토리챗 파이프라인에 전면 흡수·통합한 기술 명세서입니다.

---

## 목차
- [1. NovelAI V4/V5 가중치 문법 체계](#1-novelai-v4v5-가중치-문법-체계)
- [2. 정밀 1인칭 POV 카메라 & 시선 기하학](#2-정밀-1인칭-pov-카메라--시선-기하학)
- [3. 일반 상황코드(S01~S18) 공식 Danbooru 태그 사전](#3-일반-상황코드s01s18-공식-danbooru-태그-사전)
- [4. 성인 상황코드(A01~A15) 정밀 체위 기하학 사전](#4-성인-상황코드a01a15-정밀-체위-기하학-사전)
- [5. 3단 레이어 분리 컴파일 (Character + Pose + Scene)](#5-3단-레이어-분리-컴파일-character--pose--scene)

---

## 1. NovelAI V4/V5 가중치 문법 체계

NovelAI 최신 모델(V4, V5)은 소괄호 `((tag))` 대신 **숫자 기반 가중치 구문(`weight::tag::`)**을 지원합니다.

### 1) 가중치 계층 표준 (Weighting Hierarchy)
| 계층 | 가중치 범위 | 적용 대상 | 구체적 예시 |
|---|---|---|---|
| **코어 두상/포즈** | `1.35 ~ 1.50` | 캐릭터 얼굴/헤어 지문, 결정적 포즈 | `1.5::light green hair, bob cut straight hair, tsurime::` |
| **표정 오버라이드** | `1.50 ~ 1.80` | 베이스 눈매를 덮어쓰는 특수 표정 | `1.8::closed eyes::`, `1.5::smile, open mouth::` |
| **보조 디테일/소품** | `1.10 ~ 1.25` | 시그니처 장신구, 비대칭 소품 | `1.2::single silver hoop earring::` |
| **일반 묘사 태그** | `1.00` | 의상, 배경, 일반 신체 지표 | `small breasts`, `thigh gap`, `white vest` |
| **억제/약화 태그** | `-1.20 ~ -1.50` | 출력 확률을 낮추고 싶은 요소 | `-1.3::loose hair::` |

> [!WARNING]
> 지나치게 많은 태그에 가중치를 남발하거나 `2.0`을 초과하면 이미지 왜곡(Deep fried)이 발생합니다. 코어 두상(1.5)과 충돌 표정(1.8)에만 선별 적용합니다.

---

## 2. 정밀 1인칭 POV 카메라 & 시선 기하학

스토리챗 CG의 대다수는 **플레이어(ⓤ)의 1인칭 시점(POV)** 또는 **주인공을 정면으로 바라보는 대화 구도**입니다.

### 1) POV 카메라 8대 필수 필드
1. **시점 소유자 (Viewpoint Owner)**: 누구의 눈인가? (대부분 플레이어 ⓤ)
2. **소유자의 자세 (Owner Posture)**: 서 있음(`standing`), 앉아 있음(`sitting`), 누워 있음(`lying, on back`)
3. **카메라 앵글/높이 (Angle & Height)**:
   - 플레이어가 위에서 내려다볼 때: `from above, high angle` (상대는 `looking up`)
   - 플레이어가 아래에서 올려다볼 때: `from below, low angle` (상대는 `looking down`)
   - 동등한 눈높이 대화: `straight-on, eye level`
   - 측면 앵글: `from side, profile`
4. **시선 타겟 (Gaze Target)**:
   - 플레이어 카메라를 정면 응시: `looking at viewer`
   - 서로 마주봄 (2인 이상): `eye contact`
   - 접촉점/신체 부위를 내려다봄: `looking down, looking at another`
   - 부끄러워 시선 회피: `looking away, averted eyes`
   - 눈 감음: `closed eyes` (가중치 1.8 권장)
5. **POV 증거물 (POV Evidence)**:
   - 플레이어의 손이 화면에 등장: `pov hands`
   - 플레이어의 다리/하반신 등장: `pov legs`, `pov crotch`
   - 여성 시점: `female pov`, 남성 시점: `male pov`
6. **거리 및 화각 (Distance & Framing)**:
   - 대화 씬: `upper body, cowboy shot`
   - 감정 클로즈업: `close-up, face focus`
   - 전체 체위/행위 씬: `full body, wide shot`

---

## 3. 일반 상황코드(S01~S18) 공식 Danbooru 태그 사전

캐릭터의 베이스 프롬프트 뒤에 결합되는 **18종 감정·상황별 단부루 공식 태그 세트**입니다.

| 코드 | 상황명 | 공식 Danbooru 태그 조합 | 카메라/시선 가이드 |
|:---:|---|---|---|
| **S01** | 차분 | `calm, neutral expression, relaxed posture, looking at viewer` | 정면, 아이레벨 |
| **S02** | 호감 | `soft smile, gentle expression, slight blush, warm eyes, looking at viewer` | 정면, 부드러운 조명 |
| **S03** | 웃음 | `1.5::smile, open mouth, happy, joyful expression::, eye contact` | 활짝 웃는 입 오버라이드 |
| **S04** | 장난 | `smirk, playful smile, mischievous, 1.4::winking::, head tilt` | 윙크 또는 비대칭 미소 |
| **S05** | 애정 | `affectionate, loving expression, deep blush, shining eyes, head tilt, gazing at viewer` | 뺨 홍조, 반짝이는 눈 |
| **S06** | 부끄럼 | `embarrassed, shy, heavy blush, 1.5::looking away, averted eyes::, fidgeting` | 시선 회피, 강한 홍조 |
| **S07** | 놀람 | `1.5::surprised, wide eyes, parted lips::, gasping, stunned` | 크게 뜬 눈, 벌어진 입 |
| **S08** | 의심 | `skeptical, narrowed eyes, raised eyebrow, distrustful, scrutinizing gaze` | 가늘게 뜬 눈, 한쪽 눈썹 |
| **S09** | 짜증 | `annoyed, frowning, furrowed brow, pout, irritated expression, looking at viewer` | 찌푸린 미간, 뾰로통한 입 |
| **S10** | 경멸 | `1.5::contempt, looking down on viewer, cold stare, disgust, half-closed eyes::, from below` | 아래로 깔보는 시선 |
| **S11** | 분노 | `1.5::angry, furious, clenched teeth, glaring, intense gaze::, dramatic shadow` | 이를 악문 표정, 강렬한 눈빛 |
| **S12** | 결의 | `determined, resolute, fierce eyes, serious expression, firm mouth` | 다문 입, 다부진 결의 |
| **S13** | 슬픔 | `sad, melancholic, downcast eyes, trembling lips, teary eyes` | 처진 시선, 눈물 맺힘 |
| **S14** | 오열 | `1.6::crying, weeping, tears running down cheeks, sobbing, despair::, open mouth` | 흘러내리는 눈물, 오열 |
| **S15** | 불안 | `anxious, nervous, uneasy, sweating, biting lip, trembling` | 식은땀, 입술 깨물기 |
| **S16** | 공포 | `1.6::terrified, fear, dilated pupils, trembling, pale face::, shadow on face` | 풀린 동공, 창백한 안색 |
| **S17** | 피로 | `tired, exhausted, bags under eyes, sighing, slumped shoulders, lethargic` | 눈 밑 다크서클, 한숨 |
| **S18** | 입맞춤 | `1.8::kiss, kissing, closed eyes, touching lips::, intimate, profile, romantic lighting` | 1:1 밀착, 눈 감음 |

---

## 4. 성인 상황코드(A01~A15) 정밀 체위 기하학 사전

키워드북의 성애 연출 모듈(`성애_19금`)에서 동적 호출되는 **15종 성애 체위별 공식 기하학 태그 세트**입니다.

| 코드 | 체위명 | 공식 Danbooru 체위 및 기하학 태그 | 구도 및 POV 디테일 |
|:---:|---|---|---|
| **A01** | 정상위 | `missionary, lying on back, spread legs, looking up, eye contact, heavy blush, bed, pov, from above` | 위에서 내려다보는 시점 |
| **A02** | 후배위 | `doggystyle, all fours, arched back, looking back, heavy blush, from behind, bed, pov` | 뒤에서 바라보는 구도, 돌아보는 시선 |
| **A03** | 기승위 | `cowgirl position, straddling, sitting on partner, looking down, bouncing, hands on partner chest, pov, from below` | 아래에서 올려다보는 시점 |
| **A04** | 들박 | `suspended congress, standing sex, lifted, wrapping legs around waist, held in arms, pov, against wall` | 공중 리프팅, 다리 감기 |
| **A05** | 핸드잡 | `handjob, gripping, stroking, looking at viewer, heavy blush, pov hands` | 손동작 클로즈업, 정면 응시 |
| **A06** | 펠라 | `fellatio, oral, kneeling, looking up, saliva trail, eye contact, pov, from above` | 무릎 꿇고 올려다보는 시선 |
| **A07** | 딥쓰롯 | `deepthroat, throat bulge, tears in eyes, gagging, holding partner hair, pov` | 고난도 구강, 눈물 맺힘 |
| **A08** | 파이즈리 | `paizuri, breast smother, pressing breasts together, cleavage, looking up, heavy blush, pov` | 가슴 압착, 상단 응시 |
| **A09** | 풋잡 | `footjob, soles, rubbing, looking down on viewer, smug smile or heavy blush, pov, from below` | 발바닥 압착, 올려다봄 |
| **A10** | 커널링구스 | `cunnilingus, spread legs, arched back, grabbing bed sheets, head thrown back, pleasure face, pov` | 젖혀진 고개, 시트 쥐기 |
| **A11** | 핸드잡 & 가슴 | `handjob, sucking own nipple, multi-tasking, deep blush, looking at viewer, pov` | 복합 애무 |
| **A12** | 가슴 애무 | `breast sucking, fondling breasts, hands on breasts, head thrown back, pleasure face, pov hands` | 플레이어 손의 가슴 애무 |
| **A13** | 프렌치키스 | `french kiss, tongue out, tongue contact, saliva trail, open mouth, passionate, close-up` | 혀 얽힘, 타액선, 초근접 |
| **A14** | 필로우토크 | `pillow talk, lying in bed, side by side, bare shoulders, soft blanket, gentle smile, peaceful` | 사후 여운, 나른한 대화 |
| **A15** | 핑거링 | `fingering, hand between legs, trembling thighs, wet, parted lips, heavy blush, pov hands` | 허벅지 떨림, 플레이어 손 |

---

## 5. 3단 레이어 분리 컴파일 (Character + Pose + Scene)

NovelAI 이미지 렌더링 시 **불변 레이어와 가변 레이어**를 명확히 분리하여 프롬프트를 조립합니다.

$$\text{Final Prompt} = \mathbf{Layer\ 1 (Base\ Character)} + \mathbf{Layer\ 2 (Pose / Emotion)} + \mathbf{Layer\ 3 (Scene / Atmosphere)}$$

1. **Layer 1: 불변 캐릭터 베이스 (Character Fingerprint)**
   - `1girl, 22yo, 1.5::dark brown hair, high ponytail, swept bangs, kind brown eyes, tsurime::, small breasts, slender, narrow waist, thigh gap`
2. **Layer 2: 가변 포즈/상황 (S/A 코드 및 의상 샷)**
   - 예 (S02 호감): `soft smile, gentle expression, slight blush, looking at viewer, white medical vest with pouches, upper body`
   - 예 (A01 정상위): `missionary, lying on back, spread legs, looking up, eye contact, heavy blush, pov, from above`
3. **Layer 3: 씬 및 환경 조명 (Scene & Lighting)**
   - `modern clinic room, soft indoor lighting, bed, cozy atmosphere, high quality`

이 3단 구조를 통해 캐릭터의 고유 외형을 100% 보존하면서 상황에 맞는 수백 장의 바리에이션 이미지를 완벽하게 일관되게 생성할 수 있습니다.
