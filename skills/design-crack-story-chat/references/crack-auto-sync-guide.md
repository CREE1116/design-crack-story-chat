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

## ⚡ 키워드북 20개 일괄 자동 주입 (No More 60-Click Pain!)

크랙 스토리 제작 시 가장 고통스러운 작업이 바로 **15~20개에 달하는 키워드북 항목을 수동으로 하나씩 복사-붙여넣기하는 일**입니다.

* ❌ **수동 입력 시**: [항목 추가] ➡️ 제목 복붙 ➡️ 키워드 태그 입력 ➡️ 본문 복붙 ➡️ [완료] 과정을 **20번 반복 (최소 60~80회 클릭 & 복붙 노가다)**
* ✅ **Playwright 자동 주입 시**: `build/keyword-book.md`를 파싱하여 **모든 항목을 3초 만에 1:1로 완벽 자동 등록**

---

## 🔄 브라우저 상주 & 대화형 핫리로드 (Interactive Session Loop)

주입이 완료된 후 **브라우저 창이 자동으로 닫히지 않고 계속 유지**됩니다!

```
===========================================================================
🎉 크랙 에디터에 모든 산출물이 성공적으로 자동 입력되었습니다!
💡 브라우저 창이 열려 있으므로 자유롭게 확인/임시저장/발행을 진행하실 수 있습니다.
===========================================================================
  [r] 로컬 산출물 다시 읽고 브라우저에 재주입 (Re-sync / Hot-reload)
  [v] SAFE ↔ UNSAFE 프롬프트 버전 전환 및 재주입
  [o] 크랙 에디터 페이지 새로고침 (Refresh Page)
  [q] 세션 종료 및 브라우저 닫기 (Quit)
===========================================================================
👉 명령을 입력하세요 [r(재주입) / v(버전전환) / o(새로고침) / q(종료)]:
```

### 💡 실전 활용 시나리오
1. **임시저장 & 육안 검토**: 자동 주입된 프롬프트와 19개 키워드북을 브라우저에서 스크롤하며 확인하고, 크랙의 [임시저장] 버튼을 누릅니다.
2. **설정 수정 후 1초 재입력 (`r`)**:
   - 로컬에서 `story.md`나 `keyword-book.md`의 키워드/설정을 수정합니다.
   - 터미널에서 `r`만 누르면 브라우저를 닫고 다시 열 필요 없이 **수정된 최신 내용이 브라우저 폼에 즉시 덮어씌워집니다.**
3. **SAFE ↔ UNSAFE 전환 (`v`)**:
   - `v`를 누르면 SAFE 버전과 UNSAFE 버전 시스템 프롬프트를 실시간으로 전환하여 주입합니다.

---

## 📋 자동 매핑 및 주입 필드 규격

| 크랙 에디터 입력 탭 | 소스 산출물 파일 | 제약 및 규격 |
|---|---|---|
| **프롤로그 (Prologue)** | `build/prologue.md` | ≤ 1,000자 |
| **시작 프롬프트 (Start Prompt)** | `build/start-prompt.md` | ≤ 1,000자 |
| **시스템 프롬프트 (System Prompt)** | `build/integrated-prompt-{safe/unsafe}.md` | ≤ 7,000자 (SAFE / UNSAFE 선택) |
| **키워드북 (Keyword Book)** | `build/keyword-book.md` (키워드북 섹션) | 항목별 제목 + 키워드 1~5개 + 본문 ≤ 400자 (15~20개 일괄) |
| **단축어 (Shortcuts)** | `build/keyword-book.md` (Shortcuts 섹션) | 이름 ≤ 10자 + 설명 ≤ 30자 + 프롬프트 ≤ 400자 |
| **작품 상세 설명 / 코멘트** | `build/assets/summary-comment.md` | 배너 링크 + 통계표 + 등장인물 소개 |

---

## ⚙️ CLI 명령어 레퍼런스

```bash
# 1. 크랙 1회 로그인 세션 저장
uv run --with playwright python tools/sync/crack_sync.py auth

# 2. 산출물 사전 검사
python3 tools/sync/crack_sync.py inspect examples/hunter

# 3. 크랙 에디터에 자동 주입 & 상주 루프 실행
uv run --with playwright python tools/sync/crack_sync.py sync examples/hunter \
  --url "https://crack.wrtn.ai/studio/projects/YOUR_PROJECT_ID" \
  --variant safe
```
