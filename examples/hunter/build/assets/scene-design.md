# 『각성의 밤』 공식 배경 및 환경 디자인 명세서 (Scene & Environment Specification)

본 문서는 스토리챗에 사용되는 **① 풍경화형 단독 배경(Pure Scenery CG)**과 **② 인물 결속용 배경(Staged Environment)**의 프롬프트 및 UC 명세서입니다.

---

## 📋 씬 및 장소 로스터 요약

| ID | 장소명 | 분류 | 핵심 공간/건축 테마 | 주요 시그니처 소품 |
|:---:|---|---|---|---|
| `scene/a01` | **각성자 관리국 등록홀** | indoor | modern government administration hall, sleek glass and marble interior, wide lobby | reception desks, holographic status boards, rows of waiting chairs, security gates |
| `scene/a02` | **발할라 길드 훈련장** | combat | massive underground combat arena, reinforced steel barricades, scorched stone flooring | holographic target projectors, heavy weapon racks, blast marks |

---

## [scene/a01] 각성자 관리국 등록홀
> 용도: **헌터 등록 및 등급 측정 대기 로비**

### 1. 🖼️ 풍경화형 단독 배경 (Pure Scenery CG)
무대 전체를 조망하고 공간의 깊이와 분위기를 전달하는 단독 씬 프롬프트입니다.

```text
[Prompt]
no humans, scenery, modern government administration hall, sleek glass and marble interior, wide lobby, reception desks, holographic status boards, rows of waiting chairs, security gates, bright cool white ceiling panel lighting, holographic terminal glow, formal clean atmosphere, bustling administrative area, wide angle, panoramic interior view

[UC (네거티브)]
1girl, 1boy, humans, character, person, lowres, bad anatomy, text, error, blurry, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark
```

### 2. 👥 인물 배치형 결속 배경 (Staged Character Environment)
캐릭터 포트레이트 및 상황 CG 생성 시 인물 베이스 태그 뒤에 결합되는 환경 프롬프트입니다.

```text
[Prompt 환경 결속부]
indoors, administration hall lobby, beside reception desk, holographic directory screen in background, clean overhead lighting, subtle screen backlight, depth of field, blurred background

[UC 환경 방어부]
white background, simple background, flat background, solid color background
```

---

## [scene/a02] 발할라 길드 훈련장
> 용도: **길드 지하 실전 대련 및 각성자 전투 평가장**

### 1. 🖼️ 풍경화형 단독 배경 (Pure Scenery CG)
무대 전체를 조망하고 공간의 깊이와 분위기를 전달하는 단독 씬 프롬프트입니다.

```text
[Prompt]
no humans, scenery, massive underground combat arena, reinforced steel barricades, scorched stone flooring, holographic target projectors, heavy weapon racks, blast marks, harsh overhead industrial floodlights, high contrast dramatic shadows, floating dust particles, smoky haze, wide shot, grand scale, atmospheric perspective

[UC (네거티브)]
1girl, 1boy, humans, character, person, lowres, bad anatomy, text, error, blurry, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark
```

### 2. 👥 인물 배치형 결속 배경 (Staged Character Environment)
캐릭터 포트레이트 및 상황 CG 생성 시 인물 베이스 태그 뒤에 결합되는 환경 프롬프트입니다.

```text
[Prompt 환경 결속부]
indoors, combat training arena, scorched stone floor, steel barricade in background, dramatic harsh key lighting, floating sparks, depth of field, blurred background

[UC 환경 방어부]
white background, simple background, flat background, solid color background
```

---
