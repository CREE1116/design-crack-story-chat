# 크랙(Crack) 자동 입력 및 동기화 가이드 (Crack Playwright Auto-Sync Guide)

본 문서는 플레이라이트(Playwright) 브라우저 자동화 도구(`tools/sync/crack_sync.py`)를 사용하여 빌드 산출물(프롤로그, 시작 프롬프트, 시스템 프롬프트, 키워드북 19개 항목, 단축어, 상세 설명)을 **크랙(Crack) 웹 에디터에 1초 만에 안전하게 자동 입력하는 방법**을 안내합니다.

---

## 🎯 왜 비공식 API 대신 Playwright 브라우저 자동화인가?

1. **🛡️ 계정 안전성 (약관 위반 및 제재 방지)**:
   - 비공식 내부 API 직접 호출은 토큰 변조, WAF 봇 차단 및 계정 영구 정지(밴) 위험이 있습니다.
   - Playwright는 **사용자가 실제 로그인한 브라우저 세션 환경에서 사람이 입력하듯 폼을 채워주는 방식**이므로 가장 안전합니다.
2. **👀 실시간 시각적 검토 (Headed Mode)**:
   - 브라우저 창이 열린 상태로 필드가 채워지는 과정을 눈으로 확인할 수 있으며, 최종 "저장/발행" 버튼을 누르기 전에 작가가 직접 검토할 수 있습니다.
3. **⚡ 휴먼 에러 제로 (19개 키워드북 복붙 피로도 해소)**:
   - 19개에 달하는 키워드북 제목/키워드/본문, 단축어, 시스템 프롬프트를 일일이 손으로 복사-붙여넣기하는 고된 작업을 1회의 명령어로 끝냅니다.

---

## 🚀 빠른 시작 (3단계 워크플로우)

### 1단계: 의존성 준비 (최초 1회)
```bash
# Playwright 및 Chromium 브라우저 바이너리 설치
uv run --with playwright python -m playwright install chromium
```

### 2단계: 크랙 로그인 세션 1회 캡처
```bash
python3 tools/sync/crack_sync.py auth
# 또는 uv 사용 시:
uv run --with playwright python tools/sync/crack_sync.py auth
```
* 브라우저 창이 열리면 크랙(Crack)에 로그인합니다.
* 로그인이 완료된 후 터미널에서 `[Enter]`를 누르면 로그인 세션이 `~/.crack/auth_state.json`에 영구 저장됩니다.

### 3단계: 크랙 에디터에 자동 주입 (Sync)
```bash
# 1. 주입할 데이터 및 필드 매핑 미리보기
python3 tools/sync/crack_sync.py inspect examples/hunter

# 2. 크랙 에디터 페이지에 실제 자동 주입 실행
uv run --with playwright python tools/sync/crack_sync.py sync examples/hunter \
  --url "https://crack.wrtn.ai/studio/projects/YOUR_PROJECT_ID" \
  --variant safe
```

---

## 📋 자동 매핑 및 주입 필드 규격

| 크랙 에디터 입력 탭 | 소스 산출물 파일 | 제약 및 규격 |
|---|---|---|
| **프롤로그 (Prologue)** | `build/prologue.md` | ≤ 1,000자 |
| **시작 프롬프트 (Start Prompt)** | `build/start-prompt.md` | ≤ 1,000자 |
| **시스템 프롬프트 (System Prompt)** | `build/integrated-prompt-{safe/unsafe}.md` | ≤ 7,000자 (SAFE / UNSAFE 선택) |
| **키워드북 (Keyword Book)** | `build/keyword-book.md` (키워드북 섹션) | 항목별 제목 + 키워드 1~5개 + 본문 ≤ 400자 |
| **단축어 (Shortcuts)** | `build/keyword-book.md` (Shortcuts 섹션) | 이름 ≤ 10자 + 설명 ≤ 30자 + 프롬프트 ≤ 400자 |
| **작품 상세 설명 / 코멘트** | `build/assets/summary-comment.md` | 배너 링크 + 통계표 + 등장인물 소개 |

---

## ⚙️ CLI 명령어 및 옵션 레퍼런스

```bash
# 서브커맨드 목록
python3 tools/sync/crack_sync.py [auth | inspect | sync]

# 옵션:
# --variant [safe|unsafe] : 주입할 시스템 프롬프트 버전 선택 (기본값: safe)
# --url <URL>            : 크랙 스토리 에디터 URL (sync 필수)
# --dry-run              : 브라우저를 열지 않고 데이터 파싱만 검사
# --headless             : 백그라운드 브라우저 모드 실행
# --auto-submit          : 입력 완료 후 저장/발행 버튼까지 자동 클릭
```
