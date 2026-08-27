# 캐릭터 외형 초정밀 설계 가이드 (High-Precision Character Appearance Guide)

AI 이미지 생성 시 모델, 체크포인트, 시드가 바뀌어도 캐릭터의 외형과 정체성이 100% 동일하게 재현되도록 만드는 **시각적 지문(Visual Fingerprint) 설계 규격**입니다.

모호한 감성어(*"예쁜", "시크한", "잘생긴"*)를 배제하고, **체형, 헤어, 의상 색상, 안면, 비대칭 앵커**를 구체적이고 검증 가능한 시각 지표로 명시합니다.

---

## 목차
- [1. 캐릭터 외형 설계의 6대 핵심 축](#1-캐릭터-외형-설계의-6대-핵심-축)
- [2. 체형(Body Form) 4대 초고밀도 디테일](#2-체형body-form-4대-초고밀도-디테일)
- [3. 헤어(Hair) 3요소 필수 결속 공식](#3-헤어hair-3요소-필수-결속-공식)
- [4. 의상 전 파츠 색상 결속 원칙](#4-의상-전-파츠-색상-결속-원칙)
- [5. 안면·동공 및 제어된 비대칭성](#5-안면동공-및-제어된-비대칭성)
- [6. 단부루 태그 검색 도구 활용법](#6-단부루-태그-검색-도구-활용법)
- [7. 실전 작성 예시 및 프롬프트 컴파일](#7-실전-작성-예시-및-프롬프트-컴파일)

---

## 1. 캐릭터 외형 설계의 6대 핵심 축

```
[인물 시각적 지문 (Character Fingerprint) 6대 축]
1. 👤 체형 & 실루엣: 가슴 크기, 근육/체지방, 키/체구, 골반/허벅지 갭
2. 💇 헤어 3요소: 색상 + 형태/묶음/앞머리 + 기장
3. 🎨 의상 전 파츠 색상 결속: 모든 의상 조각에 1:1로 색상 명시
4. 👁️ 안면 & 동공: 눈매 각도, 동공 색상, 고유 표식(점/흉터)
5. ⚖️ 제어된 비대칭성: 좌우 불일치 식별 포인트 (단일 귀걸이, 숄더가드 등)
6. 🎒 시그니처 소지품: 1~2개의 고유 상징 물품 (안경, 특수 시계 등)
```

---

## 2. 체형 및 신체 디테일 (Body Form & Physical Details)

체형은 인물의 전체적인 실루엣과 인상을 결정하는 기본 뼈대입니다. 단순한 체급 표기(*"마름", "보통"*)를 넘어, **가슴 볼륨, 근육/탄탄함, 골격/실루엣, 신체 고유 디테일(허벅지 갭, 두꺼운 허벅지, 골반, 쇄골 등)**을 구체적인 시각 지표로 정의합니다.

| 분류 | 세부 설명 | 대표 단부루 태그 및 표현 |
|---|---|---|
| **가슴 볼륨** | 바스트 크기 및 볼륨감 명시 | `flat chest`, `small breasts`, `medium breasts`, `large breasts`, `huge breasts` |
| **근육/체지방** | 근육 선, 복근, 탄탄함 여부 | `toned`, `abs`, `muscular`, `biceps`, `athletic build`, `soft body`, `chubby` |
| **골격/실루엣** | 키, 전체 비율, 허리/몸매 라인 | `slender`, `skinny`, `petite`, `curvy`, `tall`, `short`, `narrow waist`, `hourglass figure` |
| **신체 고유 디테일** | 허벅지 형태, 갭, 골반, 쇄골, 팔다리 비율 | `thigh gap`, `thick thighs`, `wide hips`, `slim legs`, `prominent collarbone`, `long legs` |

> [!IMPORTANT]
> **신체 디테일 작성 원칙:**
> - 단순히 `"슬림한 몸매"` 대신 `slender, narrow waist, small breasts, thigh gap`처럼 구체적인 선과 볼륨, 고유 디테일을 결합합니다.
> - 전투형 인물은 `athletic build, toned, abs, medium breasts, thick thighs, prominent collarbone`과 같이 근육과 활동성, 골격 특징을 드러내는 조합을 부여합니다.
> - 허벅지 갭(`thigh gap`), 넓은 골반(`wide hips`), 두꺼운 허벅지(`thick thighs`), 쇄골(`collarbone`) 등은 캐릭터의 개성에 맞게 부여하는 핵심 신체 디테일입니다.

---

## 3. 헤어(Hair) 3요소 필수 결속 공식

헤어스타일은 인물 식별의 가장 큰 비중을 차지합니다. 반드시 **[색상 + 형태 + 길이]** 3요소가 하나의 세트로 결속되어야 합니다.

$$\text{헤어 태그} = [\text{색상}] + [\text{스타일/묶음/앞머리}] + [\text{기장}]$$

### 1. 3요소 구성표
1. **색상 (Color)**: `black hair`, `dark brown hair`, `silver hair`, `blonde hair`, `ash grey hair`, `crimson hair` 등
2. **형태 (Style & Bangs)**:
   - 묶음: `high ponytail`, `low ponytail`, `twin braids`, `side ponytail`, `half updo`, `messy bun`
   - 디테일: `loose strands at nape`, `sidelocks`, `ahoge`, `hair behind ear`
   - 앞머리: `blunt bangs`, `messy bangs`, `swept bangs`, `parted bangs`, `hair over one eye`
3. **길이 (Length)**: `short hair`, `medium hair`, `long hair`, `very long hair (reaching hips)`

### 2. 결속 예시
* ⭕ **올바른 예**: `dark brown hair in high ponytail, loose strands at nape, messy bangs, long hair`
* ❌ **잘못된 예**: `brown hair, ponytail` (묶음 높이, 잔머리, 앞머리, 기장 불명확 ➡️ 매번 다른 헤어 출력)

---

## 4. 의상 전 파츠 색상 결속 원칙

> [!CAUTION]
> **의상 색상 고립 금지 원칙:**
> 모델이 임의로 색을 칠하지 않도록, **상의, 하의, 이너, 아우터, 장갑, 양말, 신발 등 모든 의상 파츠에 색상 형용사를 직접 붙입니다.**

| 의상 부위 | 결속 규칙 | 구체적 태그 예시 |
|---|---|---|
| **아우터/조끼** | 색상 + 핏 + 특수 디테일 | `navy blue high-collar tactical vest`, `charcoal grey tailored coat` |
| **이너/상의** | 색상 + 옷깃/소매 형태 | `white button-up collared shirt`, `black tight sleeveless top` |
| **하의/바지/치마** | 색상 + 소재 + 형태 | `slate grey combat cargo pants`, `dark pleated mini skirt` |
| **벨트/홀스터** | 색상 + 버클/파우치 | `black leather belt with silver buckle, utility pouches` |
| **손/장갑** | 색상 + 장갑 형태 | `black fingerless leather gloves`, `white silk gloves` |
| **다리/양말** | 색상 + 기장 | `dark navy thighhighs`, `black sheer pantyhose`, `white ankle socks` |
| **신발/부츠** | 색상 + 굽/소재 | `dark brown steel-toed combat boots`, `black leather loafers` |

---

## 5. 안면, 두상, 귀 & 이목구비 초정밀 설계 (Face, Ears & Facial Features)

안면은 캐릭터의 감정과 인상을 지배하는 가장 핵심적인 영역입니다. 단순한 눈 색깔 표기를 넘어 **얼굴형, 귀, 눈매, 동공, 눈썹/속눈썹, 코/입, 피부/표식**을 세부적으로 정의합니다.

| 부위 | 세부 설계 항목 | 대표 단부루 태그 및 표현 |
|---|---|---|
| **얼굴형/턱선** | 윤곽선, 볼살, 턱 형태 | `oval face`, `round face, soft cheeks`, `sharp chin`, `pointed chin`, `defined angular jawline`, `chubby cheeks` |
| **귀 & 피어싱** | 귀 형태, 엘프귀/수인귀, 장식 | `human ears`, `pointed ears`, `animal ears`, `ear piercing`, `single earring on left ear`, `lobe piercing` |
| **눈매 각도/형태** | 눈매 기울기, 크기, 분위기 | `sharp almond eyes`, `round gentle eyes`, `tsurime` (올라간 눈), `tareme` (처진 눈), `sanpaku` (삼백안), `half-closed eyes` |
| **동공 & 홍채** | 색상, 오드아이, 광택 | `warm brown eyes`, `golden amber eyes`, `pale blue eyes`, `heterochromia (pale blue right eye, dark brown left eye)`, `glowing pupils` |
| **눈썹 & 속눈썹** | 굵기, 각도, 속눈썹 길이 | `slender arched eyebrows`, `thick eyebrows`, `thick furrowed eyebrows`, `long eyelashes`, `short eyebrows` |
| **코 & 입** | 콧대 높이, 입술 형태, 입 모양 | `small straight nose`, `prominent nose bridge`, `thin lips`, `parted lips`, `slight gentle smile`, `firm set mouth` |
| **피부 & 표식** | 피부톤, 홍조, 점, 흉터 | `fair skin, slight blush`, `pale skin`, `tanned weathered skin`, `mole under left eye`, `cross-shaped scar on cheek`, `freckles` |

---

## 5.1. 제어된 비대칭성 및 시그니처 소지품

### 1. 제어된 비대칭성 (Controlled Asymmetry)
한눈에 캐릭터를 식별할 수 있는 좌우 불일치 포인트를 최소 1개 부여합니다.
* `single silver hoop earring on left ear` (왼쪽 귀에만 찬 단일 링 귀걸이)
* `heavy steel pauldron on right shoulder only` (오른쪽 어깨에만 장착한 강철 견갑)
* `hair over right eye` (오른쪽 눈만 가린 비대칭 앞머리)
* `single fingerless glove on right hand` (한쪽 손에만 낀 장갑)

### 2. 시그니처 소지품 / 모티프 (Signature Item)
* `teal bio-scanner on belt pouch` (허리 파우치의 청록색 바이오 스캐너)
* `glowing orange heavy greatsword slung on back` (등에 멘 주황빛 대검)
* `thin rimless glasses held in hand` (손에 든 얇은 무테안경)

---

## 6. NAI V5 레퍼런스-프리(Reference-Free) 캐릭터 100% 고정 실전 비법

NovelAI V5는 **단부루 태그와 자연어 묘사의 이행률(Follow-rate)이 매우 높은 최신 모델**입니다. 이미지 레퍼런스(Reference Image)가 없는 환경에서도 프롬프트 구조화만으로 인물의 시각적 정체성을 100% 고정할 수 있는 6대 실전 테크닉입니다.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 🧠 [NAI V5 캐릭터 고정 6대 핵심 원칙]                                        │
│                                                                             │
│ 1. 👑 두상(Head)이 8할이다: [명도+색상] + [형태+결] + [앞머리] + [눈매+동공]    │
│    (1.5::light green hair, bob cut straight hair, swept bangs, green eyes, tsurime::)│
│                                                                             │
│ 2. 🛡️ 가슴/체형 앵커 필수: 아티스트 스타일에 따른 체형 흔들림 방지          │
│    (small breasts, medium breasts, flat chest 등 무조건 박아둘 것)          │
│                                                                             │
│ 3. 👗 의상 4단 자연어 덩어리: [색상] + [소재/질감] + [아이템] + [디테일/장식]│
│    (black cotton crop top with cross laced front, brown leather scout vest) │
│                                                                             │
│ 4. 📐 구도(Shot)별 하의 스마트 분기: 상반신(`upper body`) 샷은 하의 생략     │
│                                                                             │
│ 5. 🎭 표정 전환 시 눈/입 가중치 오버라이드: 충돌 태그는 `1.5~1.8::...::`로 억제│
│    (1.5::smile, open mouth, happy::, 1.8::closed eyes::)                    │
│                                                                             │
│ 6. 🎲 인물별 고유 시드(Seed) 고정: 시드 고정 없이는 위의 모든 것이 무효      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 1) 👑 두상(Head) 8할 고정 원칙 & 1.5 가중치 묶음

캐릭터 인상의 80%는 두상(헤어, 앞머리, 눈매, 동공)에서 결정됩니다.

1. **헤어 색상에 명도 접두사 필수 결속 (`light` / `dark`)**:
   - ❌ `green hair` (매 컷마다 연두색, 청록색, 짙은 녹색으로 색조 튐)
   - ⭕ `light green hair` 또는 `dark green hair` (명도를 확정하여 색조 흔들림 차단)
2. **헤어 형태 + 결(Texture) 결합**:
   - `bob cut straight hair` (단발 + 생머리 직모 결속)
   - `wavy hair in high ponytail` (웨이브 결 + 하이 포니테일)
   - `messy short hair` (더벅머리 숏컷)
3. **앞머리(Bangs) 필수 지정**:
   - 앞머리를 지정하지 않으면 AI가 매번 다른 이마/앞머리를 생성합니다.
   - `swept bangs` (옆으로 넘긴 앞머리), `blunt bangs` (일자 뱅), `parted bangs` (가르마 뱅), `messy bangs` (자연스러운 잔머리 뱅) 중 하나를 반드시 고정합니다.
4. **눈매 각도 + 동공 색상 결속**:
   - `green eyes, tsurime` (녹색 눈 + 날카롭게 올라간 고양이상 눈매)
   - `amber eyes, tareme` (호박색 눈 + 순한 처진 강아지상 눈매)
5. **두상 1.5 가중치 묶음 (`1.5::...::`)**:
   - 의상이나 배경에 밀려 두상이 왜곡되지 않도록 두상 파츠 전체를 1.5 가중치 구문으로 묶어 최우선 배치합니다.
   - `1.5::light green hair, bob cut straight hair, swept bangs, green eyes, tsurime::`

---

### 2) 🛡️ 가슴/체형 앵커 필수 ("가슴 태그는 웬만하면 넣어라")

* 아티스트 스타일 프리셋이나 상황 구도에 따라 가슴 및 체형 볼륨이 제멋대로 흔들립니다.
* 취향에 관계없이 `flat chest`, `small breasts`, `medium breasts`, `large breasts` 중 하나를 **고정용 등급 앵커**로 무조건 박아두어야 체형 편차가 잡힙니다.

---

### 3) 👗 의상 4단 자연어 결속 덩어리 ("옷은 자연어로 길게")

* 의상 태그를 `top, vest, skirt`처럼 단어로 툭툭 끊으면 AI가 색상과 디테일을 다른 부위에 섞어버립니다 (Color Bleeding).
* **[색상 + 소재/질감 + 아이템 + 디테일/장식]**의 4단 구조로 하나의 긴 자연어 덩어리를 만듭니다:
  * ⭕ `black cotton crop top with cross laced front` (검정 + 면 소재 + 크롭탑 + 전면 크로스 레이스)
  * ⭕ `brown leather scout vest with strap harness and small pouches` (갈색 + 가죽 소재 + 스카우트 조끼 + 스트랩 하네스 및 소형 파우치)
  * ⭕ `dark grey pleated wool skirt with white trim` (다크 그레이 + 플리츠 울 소재 + 스커트 + 화이트 라인 트리밍)

---

### 4) 📐 구도(Shot)별 하의/신발 스마트 분기

* **상반신(`upper body`) 샷**:
  * 하의(`skirt`, `pants`), 양말, 신발 태그를 **반드시 생략**합니다. 하의 태그가 남아 있으면 AI가 상반신 샷 구도를 깨고 화각을 아래로 넓히려 하거나 체형 비율이 왜곡됩니다.
* **카우보이/전신(`cowboy shot`, `full body`) 샷**:
  * 하의, 양말/스타킹, 신발 태그를 온전하게 포함합니다.

---

### 5) 🎭 표정(Expression) 전환 시 눈/입 가중치 오버라이드

* **순수 감정 표정**: `emotionless`, `calm`, `blush` 등은 베이스 외형과 충돌하지 않으므로 그대로 추가합니다.
* **눈/입을 변형하는 표정**: `closed eyes`(눈 감음), `winking`(윙크), `smile, open mouth`(활짝 웃음) 등은 베이스에 설정된 눈매(`tsurime`, `open eyes`)와 정면 충돌합니다.
* **해결책 (가중치 오버라이드)**:
  * 눈/입 변형 태그에 가중치(`1.5~1.8::...::`)를 주어 베이스 눈매를 눌러줍니다:
  ```text
  1.5::smile, open mouth, happy::, 1.8::closed eyes::
  ```

---

## 7. 단부루 태그 검색 도구 활용법

스킬 내 탑재된 `search_tag.py`를 실행하여 공식 단부루 위키의 태그명과 정의를 실시간으로 검색 및 검증할 수 있습니다.

```bash
# 1. 체형, 헤어, 의상 태그 검색
python3 tools/images/search_tag.py "thigh gap" "high ponytail" "tactical vest"

# 2. 상세 정의 및 위키 본문까지 포함해서 보기
python3 tools/images/search_tag.py "mating press" --body

# 3. JSON 구조화 출력
python3 tools/images/search_tag.py "sharp eyes" --json
```

---

## 8. 실전 작성 예시 및 프롬프트 컴파일

### `characters.md` 작성 예시 (서유진)
```markdown
### 서유진 (Seo Yu-jin)
- **성별/나이**: 여성 / 22세
- **체형/실루엣**: 162cm, 슬렌더 탄탄한 체형, 미디엄 바스트(`medium breasts`), 좁은 허리(`narrow waist`), 허벅지 갭(`thigh gap`), 슬림 레그(`slim legs`)
- **헤어**: 다크 브라운 하이 포니테일(`dark brown hair in high ponytail`), 목덜미 잔머리(`loose strands at nape`), 자연스러운 앞머리(`messy bangs`), 등 중간까지 오는 긴 기장(`long hair`)
- **안면/동공**: 상냥한 아몬드형 갈색 눈(`kind brown almond eyes`), 눈매(`tsurime`), 왼쪽 눈 밑 애교점(`mole under left eye`)
- **비대칭 앵커**: 왼쪽 귀에만 찬 은색 링 귀걸이(`single silver hoop earring on left ear`)
- **의상 (4단 자연어 결속 덩어리)**:
  - 아우터: 화이트&스카이블루 의료용 방탄 조끼(`white and light blue medical field vest with pouches`)
  - 이너: 네이비 블루 면소재 압축 셔츠(`navy blue cotton compression shirt`)
  - 하의 (전신 샷용): 다크 그레이 카고 팬츠(`dark grey tactical cargo pants`)
  - 손: 블랙 가죽 반장갑(`black fingerless leather gloves`)
  - 신발: 다크 브라운 경량 전술 부츠(`dark brown lightweight combat boots`)
- **시그니처 소지품**: 허리 파우치에 장착된 청록색 바이오 스캐너(`teal bio-scanner on belt pouch`)
```

### 컴파일된 최종 NAI V5 베이스 프롬프트 (Base Character Tag)
```text
1girl, young woman, 22yo, 1.5::dark brown hair, high ponytail, loose strands at nape, messy bangs, long hair, brown eyes, kind almond eyes, tsurime::, mole under left eye, single silver hoop earring on left ear, medium breasts, slender, narrow waist, thigh gap, white and light blue medical field vest with pouches, navy blue cotton compression shirt, black fingerless leather gloves, teal bio-scanner on belt pouch
```

---

## 8. 네거티브 프롬프트(UC / Undesired Content) 작성 원칙

UC(Undesired Content)는 **"절대 출력되지 말아야 할 불량 요소 및 캐릭터 외형 왜곡 방지 태그"**입니다.

### 1. 2단계 UC 결합 구조
1. **기본 품질 & 해부학 방어 (Quality & Anatomy Guards)**:
   ```text
   lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name
   ```
2. **인물 고유 외형 왜곡 방지 (Character Drift Exclusions)**:
   - 가슴 크기 왜곡 방지: `medium breasts` ➡️ UC: `large breasts, huge breasts, cleavage`
   - 헤어스타일 붕괴 방지: `high ponytail` ➡️ UC: `short hair, loose hair, twintails, twin braids`
   - 헤어 색상 왜곡 방지: `dark brown hair` ➡️ UC: `blonde hair, pink hair, blue hair, multi-colored hair`
   - 하의 왜곡 방지: `cargo pants` ➡️ UC: `skirt, dress, shorts`
   - 비대칭 장신구 왜곡 방지: `single silver hoop earring` ➡️ UC: `earrings, pair of earrings`

---

## 9. 공식 빌드 산출물: `build/assets/character-design.md`

컴파일러(`compose_character.py`)를 통해 프로젝트 빌드 시 `build/assets/character-design.md`가 자동 생성됩니다.

* **포함 내용**:
  * 📋 전체 캐릭터 비주얼 로스터 요약표
  * 👤 인물별 시각적 지문 6대 앵커
  * 🎯 컴파일된 불변 베이스 프롬프트 (Prompt)
  * 🚫 네거티브 프롬프트 (Undesired Content / UC)
  * 🔒 불변 유지(Do Not Vary) vs 변형 허용(Safe to Vary) 체크리스트

