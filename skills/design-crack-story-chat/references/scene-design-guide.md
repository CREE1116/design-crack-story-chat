# 배경 및 환경 프롬프트 설계 가이드 (Scene & Environment Design Guide)

스토리챗에 사용되는 배경은 크게 **① 풍경화처럼 그려지는 단독 배경(Pure Scenery CG)**과 **② 인물이 머물고 상호작용하는 결속용 배경(Staged Environment)**의 2가지 종류로 분리하여 설계합니다.

---

## 목차
- [1. 배경 프롬프트의 2대 갈래](#1-배경-프롬프트의-2대-갈래)
- [2. 풍경화형 단독 배경 설계 규격 (Pure Scenery CG)](#2-풍경화형-단독-배경-설계-규격-pure-scenery-cg)
- [3. 인물 배치형 결속 배경 설계 규격 (Staged Environment)](#3-인물-배치형-결속-배경-설계-규격-staged-environment)
- [4. 배경 UC(Undesired Content) 분리 규칙](#4-배경-ucundesired-content-분리-규칙)
- [5. 공식 빌드 산출물: scene-design.md](#5-공식-빌드-산출물-scene-designmd)
- [6. 실전 작성 예시](#6-실전-작성-예시)

---

## 1. 배경 프롬프트의 2대 갈래

```
[배경 프롬프트 2대 유형]
1. 🖼️ 풍경화형 단독 배경 (Pure Scenery / Landscape CG)
   • 목적: 공간 이동, 씬 전환, 세션 오프닝 등 세계관의 웅장한 무대 전체를 조망
   • 묘사 특징: 원근감, 건축미, 파노라마, 날씨, 빛의 산란, 랜드마크 중심의 '풍경화' 구도
   • 핵심 태그: no humans, scenery, landscape, wide angle, volumetric lighting, atmospheric perspective
   • 파일명: scene/a01.webp, scene/a02.webp 등

2. 👥 인물 배치형 결속 배경 (Staged Character Environment)
   • 목적: 캐릭터 포트레이트(01/a01.webp) 및 상황 CG 생성 시 인물 베이스 태그 뒤에 결합
   • 묘사 특징: 인물이 서 있거나 앉아 있을 만한 인간 스케일의 중경(Mid-ground) 가구/지지대 및 심도
   • 핵심 태그: indoors/outdoors, [방/거리 유형], [가구/소품 상호작용], depth of field, blurred background, rim lighting
   • 결합 형태: [캐릭터 불변 베이스 태그] + [결속용 배경 태그]
```

---

## 2. 풍경화형 단독 배경 설계 규격 (Pure Scenery CG)

단독 배경은 인물이 없는 상태에서 **하나의 완성된 풍경화/매트 페인팅**처럼 연출되어야 합니다.

```
[풍경화형 단독 배경 5대 앵커]
1. 🚫 인물 배제 락: no humans, scenery
2. 🏛️ 공간 스케일 & 건축: wide panoramic view, grand architecture, high ceiling, futuristic skyscrapers
3. 💡 시간대 & 조명 효과: golden hour, volumetric sunbeams, neon glow reflections, dim dramatic shadows
4. 🌫️ 대기 & 날씨 연출: atmospheric haze, light dust particles, rainy overcast, floating embers
5. 🎨 랜드마크 & 환경 소품: rows of empty control terminals, central fountain, towering obelisk
```

---

## 3. 인물 배치형 결속 배경 설계 규격 (Staged Environment)

결속용 배경은 **"그 공간 안에 인물이 자연스럽게 서 있거나 앉아 있을 만한 생활/전투 구도"**를 제공합니다. 인물을 가리거나 시선을 뺏지 않도록 피사계 심도와 조명 결속을 지원합니다.

```
[인물 결속용 배경 4대 앵커]
1. 🚪 공간 환경 바인딩: indoors, medical clinic room, cozy coffee shop, ruined battlefield
2. 🪑 인물 지지대 & 가구 (Anchors): leaning against concrete wall, seated on leather sofa, beside hospital bed
3. 💡 인물 지향 조명: rim lighting from window, cool blue screen glow on subject, soft ambient backlight
4. 📷 피사계 심도 (Depth): depth of field, blurred background, bokeh, medium shot
```

---

## 4. 배경 UC(Undesired Content) 분리 규칙

| 배경 종류 | 필수 네거티브(UC) 방어 항목 |
|---|---|
| **풍경화 단독 배경 (`Pure Scenery`)** | `1girl, 1boy, humans, character, person, bad architecture, blurry, lowres, text, watermark` *(인물 태그 일체 배제)* |
| **인물 결속 배경 (`In-Scene`)** | `white background, simple background, flat background, solid color background` *(단색 배경화 방지)* |

---

## 5. 공식 빌드 산출물: `build/assets/scene-design.md`

컴파일러 도구(`tools/images/compose_scene.py`)를 통해 프로젝트 빌드 시 `build/assets/scene-design.md`가 자동 생성됩니다.

```bash
# story.md 기반 배경 장소 자동 파싱 및 공식 명세서 컴파일
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-md <작품>/build/assets/scene-design.md

# NovelAI / WebUI 일괄 생성용 프리셋 동시 출력
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-preset <작품>/build/assets/preset-backgrounds.json
```

* **포함 내용**:
  * 📋 전체 씬/장소 로스터 요약표
  * 🖼️ 장소별 풍경화 단독 프롬프트 및 UC
  * 👥 장소별 인물 결속용 환경 프롬프트 및 UC
  * 💡 조명 및 앵글 매칭 가이드

---

## 6. 실전 작성 예시

### 예시 1: 중앙 의무 치료실 (`scene/a01`)

#### ① 풍경화 단독 배경 (Pure Scenery CG)
```text
[Prompt]:
no humans, scenery, hospital infirmary, modern high-tech medical clinic, interior, rows of empty medical beds with crisp white sheets, glowing green vital monitors, IV drip stands, stainless steel medical carts, volumetric pale blue fluorescent ceiling lighting, sterile quiet atmosphere, wide angle, panoramic view

[UC]:
1girl, 1boy, humans, character, person, lowres, bad anatomy, text, watermark, blurry
```

#### ② 인물 결속용 배경 (의무관 등 인물 결합 시)
```text
[Prompt 환경 결속부]:
indoors, medical clinic infirmary, beside hospital bed, vital monitor glowing in background, soft rim lighting from overhead lamps, depth of field, blurred background

[UC 환경 방어부]:
white background, simple background, flat background, solid color background
```

---

### 예시 2: 발할라 길드 훈련장 (`scene/a02`)

#### ① 풍경화 단독 배경 (Pure Scenery CG)
```text
[Prompt]:
no humans, scenery, massive underground combat arena, reinforced steel barricades, scorched stone flooring, holographic target projectors, floating dust particles, harsh overhead industrial floodlights, grand scale, atmospheric perspective, wide shot

[UC]:
1girl, 1boy, humans, character, person, lowres, bad anatomy, text, watermark, blurry
```

#### ② 인물 결속용 배경 (하무진 등 인물 결합 시)
```text
[Prompt 환경 결속부]:
indoors, combat training arena, scorched stone floor, steel barricade in background, dramatic harsh key lighting, floating sparks, depth of field, blurred background

[UC 환경 방어부]:
white background, simple background, flat background, solid color background
```
