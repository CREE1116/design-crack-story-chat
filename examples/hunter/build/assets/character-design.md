# 『각성의 밤』 공식 캐릭터 비주얼 디자인 명세서 (Character Visual Design Specification)

본 문서는 AI 이미지 생성 시 모델, 체크포인트, 시드가 바뀌어도 캐릭터의 외형과 정체성이 100% 동일하게 재현되도록 정의된 **시각적 지문(Visual Fingerprint) 및 공식 프롬프트/UC 명세서**입니다.

---

## 📋 캐릭터 비주얼 로스터 요약

| 번호 | 인물명 | 성별/나이 | 헤어 시그니처 | 핵심 의상 & 배색 | 체형/이목구비 지표 |
|:---:|---|---|---|---|---|
| `01` | **심가을 (Shim Gae-ul)** | 1girl/young woman, 24yo | dark brown hair, neat low ponytail, parted bangs | navy blue administrative tailored blazer | slender, narrow waist, intelligent almond eyes, warm brown eyes |
| `02` | **하무진 (Ha Mu-jin)** | 1boy/mature male, 35yo | black hair, undercut, slicked back, short beard | dark crimson sleeveless leather duster coat | tall, towering build, sharp menacing gaze, deep-set eyes, golden amber eyes |

---

## [01] 심가을 (Shim Gae-ul)
> 역할: **각성자 관리국 등록과 선임 주임**

### 1. 시각적 지문 6대 앵커 (Visual Fingerprint)
- **👤 체형 & 실루엣**: `slender, narrow waist`, `slender build`, `medium breasts`, `thigh gap, slim legs`
- **💇 헤어 3요소**: `dark brown hair` (색상) + `neat low ponytail, parted bangs` (형태) + `medium hair` (기장)
- **👁️ 안면, 두상 & 이목구비**:
  - 얼굴형/턱선: `oval face, soft cheeks`
  - 피부톤/혈색: `fair skin`
  - 귀 형태: `human ears`
  - 눈매 각도: `intelligent almond eyes`
  - 동공 색상: `warm brown eyes`
  - 눈썹/속눈썹: `neat slender eyebrows, long eyelashes`
  - 코/입: `small straight nose, gentle smile`
- **⚖️ 제어된 비대칭성**: `thin silver rimless glasses`
- **🎨 의상 전 파츠 색상 결속**:
  - 아우터/조끼: `navy blue administrative tailored blazer`
  - 이너/상의: `white collared blouse`
  - 하의: `charcoal pencil skirt`
  - 양말/스타킹: `black sheer pantyhose`
  - 신발: `black low-heel pumps`
- **🎒 시그니처 소지품**: `digital tablet clipboard in hand`

### 2. 컴파일된 불변 베이스 프롬프트 (Prompt)
```text
1girl, young woman, 24yo, slender, narrow waist, slender build, medium breasts, thigh gap, slim legs, dark brown hair, neat low ponytail, parted bangs, medium hair, oval face, soft cheeks, fair skin, human ears, warm brown eyes, intelligent almond eyes, neat slender eyebrows, long eyelashes, small straight nose, gentle smile, thin silver rimless glasses, navy blue administrative tailored blazer, white collared blouse, charcoal pencil skirt, black sheer pantyhose, black low-heel pumps, digital tablet clipboard in hand
```

### 3. 네거티브 프롬프트 (Undesired Content / UC)
```text
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, large breasts, huge breasts, gigantic breasts, cleavage, short hair, loose hair, twintails, twin braids, blonde hair, pink hair, blue hair, green hair, multi-colored hair, animal ears, cat ears, dog ears, fox ears, pointy ears, elf ears, pants, cargo pants
```

### 4. 불변 유지(Do Not Vary) vs 변형 허용(Safe to Vary)
| 불변 고정 항목 (Do Not Vary) | 표정/상황별 변형 가능 항목 (Safe to Vary) |
|---|---|
| 헤어 색상/스타일 (`dark brown hair`, `neat low ponytail, parted bangs`), 안면 표식 (``), 의상 배색 (`navy blue administrative tailored blazer`) | 표정 (smile, serious, combat focus), 시선 각도 (looking at viewer, looking away), 조명/날씨 |

---

## [02] 하무진 (Ha Mu-jin)
> 역할: **발할라 길드 마스터 · 1급 각성자**

### 1. 시각적 지문 6대 앵커 (Visual Fingerprint)
- **👤 체형 & 실루엣**: `tall, towering build`, `heavily muscular, broad shoulders, massive abs`, ``, `thick legs, prominent collarbone`
- **💇 헤어 3요소**: `black hair` (색상) + `undercut, slicked back, short beard` (형태) + `short hair` (기장)
- **👁️ 안면, 두상 & 이목구비**:
  - 얼굴형/턱선: `defined angular jawline, strong square chin`
  - 피부톤/혈색: `tanned weathered skin`
  - 귀 형태: `human ears`
  - 눈매 각도: `sharp menacing gaze, deep-set eyes`
  - 동공 색상: `golden amber eyes`
  - 눈썹/속눈썹: `thick furrowed eyebrows`
  - 코/입: `straight prominent nose bridge, firm set mouth`
  - 고유 표식(점/흉터): `cross-shaped scar on right cheek`
- **⚖️ 제어된 비대칭성**: `heavy steel pauldron on right shoulder only`
- **🎨 의상 전 파츠 색상 결속**:
  - 아우터/조끼: `dark crimson sleeveless leather duster coat`
  - 이너/상의: `black torn combat tank top`
  - 하의: `charcoal combat pants with reinforced knee pads`
  - 장갑: `dark brown fingerless reinforced brawler gloves`
  - 신발: `heavy black combat boots with steel plates`
- **🎒 시그니처 소지품**: `glowing orange heavy greatsword slung on back`

### 2. 컴파일된 불변 베이스 프롬프트 (Prompt)
```text
1boy, mature male, 35yo, tall, towering build, heavily muscular, broad shoulders, massive abs, thick legs, prominent collarbone, black hair, undercut, slicked back, short beard, short hair, defined angular jawline, strong square chin, tanned weathered skin, human ears, golden amber eyes, sharp menacing gaze, deep-set eyes, thick furrowed eyebrows, straight prominent nose bridge, firm set mouth, cross-shaped scar on right cheek, heavy steel pauldron on right shoulder only, dark crimson sleeveless leather duster coat, black torn combat tank top, charcoal combat pants with reinforced knee pads, dark brown fingerless reinforced brawler gloves, heavy black combat boots with steel plates, glowing orange heavy greatsword slung on back
```

### 3. 네거티브 프롬프트 (Undesired Content / UC)
```text
lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, artist name, long hair, ponytail, braid, blonde hair, pink hair, blue hair, green hair, multi-colored hair, animal ears, cat ears, dog ears, fox ears, pointy ears, elf ears, skirt, dress, shorts
```

### 4. 불변 유지(Do Not Vary) vs 변형 허용(Safe to Vary)
| 불변 고정 항목 (Do Not Vary) | 표정/상황별 변형 가능 항목 (Safe to Vary) |
|---|---|
| 헤어 색상/스타일 (`black hair`, `undercut, slicked back, short beard`), 안면 표식 (`cross-shaped scar on right cheek`), 의상 배색 (`dark crimson sleeveless leather duster coat`) | 표정 (smile, serious, combat focus), 시선 각도 (looking at viewer, looking away), 조명/날씨 |

---
