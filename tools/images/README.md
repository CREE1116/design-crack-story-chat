# 이미지 자산 관리 및 Cloudflare Pages 배포 도구

스토리챗에 사용할 이미지는 단부루 위키 기반의 **초정밀 캐릭터 시각 지문(Visual Fingerprint) 프롬프트**를 구성하고, 제작된 이미지를 WebP로 최적화하여 Cloudflare Pages 및 웹 쇼케이스 갤러리로 서빙하는 통합 툴체인을 제공합니다.

---

## 0. 단부루 공식 태그 검색 및 검증 (`search_tag.py`)

캐릭터의 체형, 헤어, 의상, 눈매 등의 태그를 단부루 2024 공식 위키 DB에서 실시간 검색합니다:

```bash
python3 search_tag.py "thigh gap" "high ponytail" "tactical vest"
```

---

## 0.1. 캐릭터 외형 베이스 프롬프트 컴파일러 (`compose_character.py`)

체형 및 신체 고유 디테일(가슴 볼륨, 근육/탄탄함, 골격 실루엣, 허벅지/골반/쇄골 등), 헤어 3요소(색상+스타일+기장), 의상 전 파츠 색상 결속을 자동 린팅하고 불변 베이스 프롬프트 및 UC(Undesired Content)를 생성합니다:

```bash
# 데모 실행 및 린팅 테스트
python3 compose_character.py --demo

# characters.md 파싱 및 검증
python3 compose_character.py --parse-md <작품>/characters.md
```

---

## 0.2. 배경 및 환경 프롬프트 컴파일러 (`compose_scene.py`)

풍경화형 단독 배경(Pure Scenery CG, 5대 앵커: no humans 락, 공간/건축, 조명/시간, 대기/날씨, 소품/랜드마크, 카메라)과 인물이 결합되는 결속용 배경(Staged Environment: 환경 바인딩, 지지대/가구, 인물 조명, 심도)을 자동 린팅하고 `scene-design.md`, NovelAI 일괄 생성 프리셋(`preset-backgrounds.json`), `prompts.json`을 생성합니다:

```bash
# 데모 실행 및 5대 앵커 린팅 테스트
python3 tools/images/compose_scene.py --demo

# story.md 기반 배경 장소 자동 파싱 및 명세서 생성
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-md <작품>/build/assets/scene-design.md

# NovelAI / WebUI 일괄 생성용 프리셋 JSON 내보내기
python3 tools/images/compose_scene.py --parse-story <작품>/story.md --output-preset <작품>/build/assets/preset-backgrounds.json

# 단일 씬 즉시 컴파일
python3 tools/images/compose_scene.py --name "마왕성 로비" --category indoor --arch "grand corporate lobby" --props "speed gate turnstiles" --lighting "volumetric ceiling lights"
```

---

## 0.3. 배경 이미지 크롭 및 순서 리네이밍 도구 (`crop_backgrounds.py`)

NovelAI 등에서 생성된 원본 이미지(1216x832, 1920x1080 등)를 크랙 스토리챗 상단 배경 표준 와이드 규격(`1024x400`, 2.56:1 비율)으로 Center Crop 및 고품질 Lanczos 리사이즈하고, 마크다운 배치표(`에셋_배치표.md`)나 프리셋 순서에 맞춰 넘버링(`bg01_장소명.webp` 또는 `a01.webp`)을 자동 부여합니다:

```bash
# 마크다운 배치표 기반으로 1024x400 크롭 및 bg01~bg25 네이밍 후 WebP 변환
python3 tools/images/crop_backgrounds.py \
  --src image-배경_원본 \
  --out image/배경 \
  --table image/에셋_배치표.md \
  --format webp

# 미리보기 (dry-run)
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out image/배경 --table image/에셋_배치표.md --dry-run

# preset-backgrounds.json 기반으로 순서 매핑
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out image/배경 --preset build/assets/preset-backgrounds.json

# 크랙 표준 scene/a01 스타일 및 PNG+WebP 동시 저장
python3 tools/images/crop_backgrounds.py --src image-배경_원본 --out deploy/scene --table image/에셋_배치표.md --style scene --format both
```

---

## 1. 표준 디렉터리 스캐폴딩 및 웹 쇼케이스 생성
python3 deploy.py --scaffold --config <작품>/build/assets/prompts.json --root ~/내이미지폴더
```

실행 시 다음 구조가 자동으로 준비됩니다:
```
~/내이미지폴더/
  index.html            인터랙티브 웹 쇼케이스 갤러리 (4대 탭, 모달 인스펙터, 19+ 토글)
  styles.css            반응형 다크 테마 및 애니메이션 스타일시트
  app.js                에셋 데이터 바인딩 및 실시간 검색/필터 스크립트
  _배치표.md            전체 에셋 체크리스트
  01/                   인물 01 디렉터리 (README.md 가이드 포함)
  02/                   인물 02 디렉터리
  scene/                배경 및 장소 디렉터리
  mob/                  몬스터 및 위협 디렉터리
  event/                특수 이벤트 CG 디렉터리
```

---

## 2. WebP 고압축 일괄 변환

기존 `.png`, `.jpg` 이미지를 한 번에 고효율 `.webp`로 변환합니다:

```bash
python3 deploy.py --convert-webp --root ~/내이미지폴더
```

* 원본 이미지를 유지하면서 동일한 위치에 초경량 `.webp` 파일을 자동 생성합니다.
* 크랙 런타임의 이미지 로딩 속도를 극대화하고 데이터 전송량을 대폭 절감합니다.

---

## 3. 에셋 정합성 검사

```bash
python3 deploy.py --check --root ~/내이미지폴더
```

* 인물별 `a01.webp` ~ `a06.webp` (Safe/일반) 및 `s01.webp` ~ `s06.webp` (NSFW/19+) 에셋 존재 여부를 검사합니다.

---

## 4. Cloudflare Pages 호스팅 배포

1. Cloudflare Dashboard ➡️ **Workers & Pages** ➡️ **Create application** ➡️ **Pages** 선택
2. GitHub 저장소 연동 또는 직접 `~/내이미지폴더` 업로드
3. 생성된 배포 URL (`https://<project-name>.pages.dev`)을 크랙 스토리챗 시스템 프롬프트의 `{IMG}` 매크로에 등록:
   ```text
   {IMG} = https://<project-name>.pages.dev
   ```
4. 크랙 프롬프트 내 호출:
   ```markdown
   ![]({IMG}/01/a01.webp)
   ```
