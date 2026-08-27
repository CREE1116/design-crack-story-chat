# 이미지 자산 관리 및 Cloudflare Pages 배포 도구

스토리챗에 사용할 이미지는 제작자가 준비한 이미지를 WebP로 최적화하고, Cloudflare Pages에 호스팅하여 웹 쇼케이스 갤러리와 함께 서빙하는 파이프라인을 제공합니다.

---

## 1. 표준 디렉터리 스캐폴딩 및 웹 쇼케이스 생성

```bash
# prompts.json 설정을 기반으로 인물 번호화 디렉터리 및 웹 템플릿 자동 생성
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
