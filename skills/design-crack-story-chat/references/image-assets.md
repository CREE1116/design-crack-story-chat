# 이미지 호스팅 및 웹페이지 제작 (Image Hosting & Web Showcase)

## 목차

- [적용 범위와 기본 원칙](#적용-범위와-기본-원칙)
- [에셋 디렉터리 및 축(Axis) 설계](#에셋-디렉터리-및-축axis-설계)
- [Cloudflare Pages 호스팅 아키텍처](#cloudflare-pages-호스팅-아키텍처)
- [쇼케이스 웹페이지(index.html) 제작 및 템플릿](#쇼케이스-웹페이지indexhtml-제작-및-템플릿)
- [축 계약 검사 및 배포 도구](#축-계약-검사-및-배포-도구)
- [금지 패턴 및 체크리스트](#금지-패턴-및-체크리스트)

---

## 적용 범위와 기본 원칙

스토리챗은 외부 호스팅된 이미지를 마크다운 문법(`![](URL)`)으로 실시간 호출할 수 있습니다.

- **[image-output-rules.md](image-output-rules.md)**: 시스템 프롬프트에서 이미지를 **어떤 번호로 매핑하고 언제 출력할 것인가 (런타임 출력 제어)**
- **[image-assets.md](image-assets.md) (본 문서)**: 이미지를 **어떻게 폴더링하고, Cloudflare Pages로 호스팅하며, 웹 쇼케이스 갤러리를 구축할 것인가 (호스팅 & 웹 배포)**

> [!IMPORTANT]
> **이 스킬은 AI 이미지를 직접 생성하지 않습니다.** 그림을 그리는 도구(Midjourney, NAI, SD, 외주 등)는 제작자가 자유롭게 선택합니다. 스킬이 책임지는 것은 **폴더 구조의 무결성, 깨진 링크 방지, Cloudflare Pages 호스팅 및 웹 갤러리 배포**입니다.
> 
> 이미지는 항상 선택 사항입니다. **단 한 장의 이미지가 없어도 텍스트만으로 완벽히 플레이가 성립**해야 합니다.

---

## 에셋 디렉터리 및 축(Axis) 설계

에셋 목록을 프롬프트에 무한정 나열하지 않고, **4대 표준 카테고리 축**을 닫아 폴더를 구성합니다.

```text
my-story-assets/
├── index.html            # 작품 소개 및 인물별 일러스트 갤러리 웹페이지
├── 장소/                 # 배경 및 공간 이미지
│   ├── 1.png
│   ├── 2.png
│   └── 21.png
├── [인물명]/             # 캐릭터별 표정/상황 이미지 (인물당 5~7장)
│   ├── 1.png
│   ├── 2.png
│   └── 7.png
├── 몬스터/               # 적/괴수/메카닉 이미지
│   ├── 31.png
│   └── 32.png
└── 이벤트/               # 특수 컷씬/성애(19+) CG (키워드북 연동)
    ├── 1.png
    └── 101.png
```

- **상황 축 수**: 인물당 표정/상황은 5~7개 내외로 닫습니다. (예: `기본`, `진지`, `당황`, `부끄러움`, `전투`, `특수`)
- **부분 배포 전제**: 준비된 이미지가 10장뿐이어도 즉시 배포할 수 있으며, 없는 이미지는 프롬프트 규칙에 따라 자동으로 생략됩니다.

---

## Cloudflare Pages 호스팅 아키텍처

현재 실전 크랙 생태계에서는 **Cloudflare Pages**를 통한 웹페이지 + 이미지 동시 호스팅이 표준으로 사용됩니다.

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 한국(서울) 엣지 POP 0초대 로딩 : 통신사 차단/렉 완전 해결   │
│ 2. 무제한 대역폭 (무료 티어)      : 트래픽 비용 걱정 없음    │
│ 3. 무료 서브도메인 & 커스텀 도메인 : *.pages.dev / domain.com │
│ 4. Git Push 자동 무중단 배포      : 커밋 즉시 10초 만에 갱신 │
│ 5. 웹 쇼케이스 갤러리 일체화      : 브라우저 접속 시 도감 출력 │
└─────────────────────────────────────────────────────────────┘
```

### 배포 URL 형태
```markdown
# Cloudflare Pages 무료 도메인
{IMG} = https://<project-name>.pages.dev

# 개인 커스텀 도메인
{IMG} = https://domain.com/작품ID
```

---

## 쇼케이스 웹페이지(index.html) 제작 및 템플릿

단순히 이미지 파일만 올려두는 것이 아니라, 루트에 `index.html`을 배치하여 **작품 소개, 등장인물 도감(Roster), 일러스트 갤러리를 겸하는 반응형 다크 테마 웹페이지**를 동시에 운영합니다.

```html
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>작품명 — Asset Gallery & Roster</title>
  <style>
    body { background: #0f172a; color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 2rem; margin: 0; }
    h1 { color: #38bdf8; margin-bottom: 0.5rem; }
    .subtitle { color: #94a3b8; margin-bottom: 2rem; }
    h2 { color: #a855f7; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; margin-top: 2rem; }
    .grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.25rem; margin-top: 1rem; }
    .card { background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; text-align: center; }
    .card img { width: 100%; height: auto; display: block; background: #020617; }
    .card .info { padding: 0.75rem; font-size: 0.875rem; }
    .card .path { color: #38bdf8; font-family: monospace; font-size: 0.8rem; margin-top: 0.25rem; }
  </style>
</head>
<body>
  <h1>작품명 — 공식 에셋 갤러리</h1>
  <p class="subtitle">크랙 스토리챗에 실시간 연동되는 고해상도 공식 일러스트 라이브러리입니다.</p>

  <h2>장소 (Backgrounds)</h2>
  <div class="grid">
    <div class="card"><img src="장소/1.png" alt="에덴 광장"><div class="info">에덴 중앙광장<div class="path">장소/1.png</div></div></div>
    <div class="card"><img src="장소/21.png" alt="지상 폐허"><div class="info">지상 폐허 3구역<div class="path">장소/21.png</div></div></div>
  </div>

  <h2>주연 인물 (Characters)</h2>
  <div class="grid">
    <div class="card"><img src="주세은/1.png" alt="주세은 기본"><div class="info">주세은 (기본·단정)<div class="path">주세은/1.png</div></div></div>
    <div class="card"><img src="주세은/7.png" alt="주세은 무전"><div class="info">주세은 (통신·무전)<div class="path">주세은/7.png</div></div></div>
    <div class="card"><img src="세라/1.png" alt="세라 미소"><div class="info">세라 (기본·미소)<div class="path">세라/1.png</div></div></div>
  </div>
</body>
</html>
```

---

## 축 계약 검사 및 배포 도구

`tools/images/deploy.py` 도구를 사용하여 폴더 골격, 배치표, `index.html`을 한 번에 생성하고 무결성을 검사합니다.

```bash
# 1. 축 목록대로 빈 폴더, _배치표.md, index.html 자동 생성
python3 tools/images/deploy.py --scaffold --root ~/내이미지폴더

# 2. 그림을 폴더에 넣은 뒤 파일 이름 및 축 계약 검사
python3 tools/images/deploy.py --check --root ~/내이미지폴더
```

### 검사기가 잡는 오류
- **목록에 없는 파일명**: 오타로 인한 깨진 링크 방지
- **과도하게 무거운 파일**: 모바일 로딩 지연 방지

---

## 금지 패턴 및 체크리스트

1. **임의 ID 호스팅 사용 금지**: 업로드마다 무작위 해시 ID를 발급하는 호스팅은 조합 URL과 호환되지 않습니다.
2. **이미지 의존적 텍스트 작성 금지**: "위 그림과 같은 표정으로 말했다" 등 이미지가 안 보이면 이해 안 되는 지문 서술 금지.
3. **핫링크 차단 호스트 사용 금지**: 외부 마크다운 직접 참조를 차단하는 호스트 배제.
4. **오타 방치 금지**: 배포 전 `deploy.py --check`로 파일명 일치 여부 확인 필수.
