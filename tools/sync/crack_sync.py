#!/usr/bin/env python3
"""Crack Story Chat Playwright Automation Sync Tool.

Automatically fills and synchronizes Crack story-chat project build artifacts
(prologue, start prompt, system prompt, keyword book, shortcuts, summary comment)
into the Crack web editor UI safely and reliably.

Keeps the browser open interactively so the user can inspect, draft-save, publish,
and hot-reload/re-inject whenever source files change.

Usage:
    # 1. First-time interactive login session capture
    python3 tools/sync/crack_sync.py auth

    # 2. Inspect project artifacts and preview field mappings
    python3 tools/sync/crack_sync.py inspect examples/hunter

    # 3. Auto-fill into Crack editor page and keep session open
    python3 tools/sync/crack_sync.py sync examples/hunter --url "https://crack.wrtn.ai/studio/..." --variant safe
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_AUTH_PATH = Path.home() / ".crack" / "auth_state.json"
DEFAULT_LOGIN_URL = "https://crack.wrtn.ai"


@dataclass
class KeywordEntry:
    title: str
    keywords: list[str]
    content: str


@dataclass
class ShortcutEntry:
    id: str
    name: str
    description: str
    prompt: str


@dataclass
class DepartmentStartSetting:
    dept_id: str
    title: str
    prologue: str
    start_prompt: str
    play_guide: str = ""
    replies: list[str] = field(default_factory=list)


@dataclass
class ProjectArtifacts:
    project_name: str
    title: str
    prologue: str
    start_prompt: str
    system_prompt: str
    keyword_entries: list[KeywordEntry] = field(default_factory=list)
    shortcuts: list[ShortcutEntry] = field(default_factory=list)
    departments: list[DepartmentStartSetting] = field(default_factory=list)
    summary_comment: str = ""
    story_description: str = ""
    short_summary: str = ""
    play_guide: str = ""
    replies: list[str] = field(default_factory=list)
    variant: str = "safe"
    # [등록] 탭 설정. story.md Core 의 선언만 담는다 — 선언하지 않은 항목은 건드리지 않는다.
    register: dict = field(default_factory=dict)


# ── 시작 세트 ────────────────────────────────────────────────────
# `start-sets/<id>/{meta.md,prologue.md,start-prompt.md}` 가 정본이고
# `departments/` 는 구버전 이름이다. 폴더를 만들면 그대로 잡히며,
# 어떤 프로젝트의 폴더 이름도 이 파일에 적지 않는다.
START_SET_DIRS = ("start-sets", "departments")

# 크랙 목록 카드의 한 줄 소개 한도. 상세설명(story-description.md)과 다른 필드다.
LOGLINE_MAX = 30
PROLOGUE_MAX = 1000
START_PROMPT_MAX = 1000
SYSTEM_PROMPT_MAX = 7000
ENTRY_MAX = 400
SHORTCUT_MAX = 400
PLAY_GUIDE_MAX = 500
REPLY_MAX_COUNT = 3

# UNSAFE 판을 같은 계정에 별도 작품으로 올릴 때 제목을 구분하기 위한 접미사.
# 핫리로드 경로가 여러 개라 로더 한 곳에서 붙인다.
TITLE_SUFFIX = ""

# [시작 설정] 탭의 칸은 위치로 찾지 않는다. 보이는 textarea 목록의 순서는
# 크랙 UI가 바뀌거나 세트를 추가할 때마다 흔들리고, 어긋나면 프롤로그가
# 시작 상황 칸에, 시작 프롬프트가 플레이 가이드 칸에 조용히 들어간다.
# 아래는 각 칸의 placeholder 에 실제로 들어 있는 문구다.
START_TAB_PLACEHOLDERS = {
    # 프롤로그 칸에는 placeholder 가 없다. 화면의 "자동 생성 기능을 활용하면…"
    # 문구는 옆 [자동 생성] 버튼의 도움말이지 이 칸의 속성이 아니다. 그래서
    # 프롤로그만 문구로 못 찾고, 시작 상황 칸을 앵커로 삼아 바로 앞 칸을 쓴다.
    "prologue": (),
    "start_prompt": ("사용자의 역할", "이야기가 시작되는"),
    "play_guide": ("사용자를 위한 가이드",),
    "reply": ("추천답변", "추천 답변"),
}

# 크랙이 허용하는 시작 세트 수. 3개가 차면 [설정 추가] 버튼이 사라진다.
MAX_START_SETS = 3


def crack_len(text: str) -> int:
    """크랙 한도 판정용 글자 수.

    이모지는 UTF-16 서로게이트 페어라 코드포인트로 세면 과소 측정된다. 둘 중
    큰 값을 쓰는 것은 scripts/check_prompt_length.py 와 같은 규칙이다.
    """
    return max(len(text), len(text.encode("utf-16-le")) // 2)


def parse_set_meta(folder: Path, index: int) -> dict:
    """meta.md 를 읽는다. 전부 선택 사항이며 없으면 폴더명과 디렉터리 순서를 쓴다."""
    fallback = re.sub(r"^\d+[_-]", "", folder.name)
    meta = {"title": fallback, "description": "", "default": False, "order": index, "enabled": True}
    path = folder / "meta.md"
    if not path.exists():
        return meta
    desc: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            if meta["title"] == fallback:
                meta["title"] = stripped.lstrip("#").strip() or fallback
            continue
        m = re.match(r"^-\s*(default|order|title|enabled)\s*:\s*(.+)$", stripped, re.IGNORECASE)
        if m:
            key, value = m.group(1).lower(), m.group(2).strip()
            if key == "default":
                meta["default"] = value.lower() in {"true", "yes", "1", "y"}
            elif key == "enabled":
                # 크랙 상한(3개)을 넘겨 기획한 루트를 지우지 않고 보류하는 스위치.
                # 원본은 그대로 두고 이번 판올림에서만 빼기 위한 것이다.
                meta["enabled"] = value.lower() in {"true", "yes", "1", "y"}
            elif key == "order":
                try:
                    meta["order"] = int(value)
                except ValueError:
                    pass
            else:
                meta["title"] = value
            continue
        if stripped:
            desc.append(stripped)
    meta["description"] = " ".join(desc).strip()
    return meta


def load_start_sets(project_dir: Path) -> list[DepartmentStartSetting]:
    """프롤로그와 첫 상황을 한 쌍으로 묶은 시작 세트를 모두 읽는다."""
    out: list[tuple[int, DepartmentStartSetting]] = []
    build_dir = project_dir if project_dir.name == "build" else (project_dir / "build")
    for dirname in START_SET_DIRS:
        candidates = [build_dir / dirname, project_dir / dirname]
        base = next((c for c in candidates if c.is_dir()), None)
        if base is None:
            continue
        for i, folder in enumerate(sorted(p for p in base.iterdir() if p.is_dir())):
            p_file, s_file = folder / "prologue.md", folder / "start-prompt.md"
            p_text = p_file.read_text(encoding="utf-8").strip() if p_file.exists() else ""
            s_text = s_file.read_text(encoding="utf-8").strip() if s_file.exists() else ""
            if not (p_text or s_text):
                continue
            # 세트마다 추천 답변을 다르게 줄 수 있다. 없으면 프로젝트 공통을 쓴다.
            r_file = folder / "recommended-replies.md"
            r_list: list[str] = []
            if r_file.exists():
                raw = r_file.read_text(encoding="utf-8").strip()
                r_list = [b.strip() for b in re.split(r"^---+$", raw, flags=re.MULTILINE) if b.strip()]
                r_list = r_list[:REPLY_MAX_COUNT]
            meta = parse_set_meta(folder, i)
            if not meta["enabled"]:
                print(f"   ⏸️ 시작 세트 '{meta['title']}' 는 meta.md 에서 보류 상태입니다 (enabled: false)")
                continue
            out.append((meta["order"], DepartmentStartSetting(
                dept_id=folder.name,
                title=meta["title"],
                prologue=p_text,
                start_prompt=s_text,
                replies=r_list,
            )))
        if out:
            break
    out.sort(key=lambda x: (x[0], x[1].dept_id))
    return [d for _, d in out]


def parse_keywords(raw: str | None) -> list[str]:
    if raw is None:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip("'\"`") for item in raw.split(",") if item.strip()]


def parse_keyword_body(text: str) -> str:
    # 1. ## Entry text / ## 내용 / ## 본문 헤딩
    match = re.search(
        r"^##\s+(?:Entry text|입력 본문|본문|내용)\s*\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if match:
        return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()

    # 2. - 내용: / - 본문:
    match = re.search(
        r"^-\s*(?:내용|본문|entry|body):\s*\n?(.*?)(?=^-\s*[a-zA-Z가-힣_]+:|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if match:
        return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()

    # 3. 키워드 줄 이후
    lines = text.splitlines()
    body_lines: list[str] = []
    found_kw = False
    for line in lines:
        if re.match(r"^-\s*(?:키워드|keywords?):", line, re.IGNORECASE):
            found_kw = True
            continue
        if found_kw:
            if re.match(r"^-\s*(?:activation|setting|when):", line, re.IGNORECASE):
                continue
            body_lines.append(line)
    if body_lines:
        content = "\n".join(body_lines)
        return re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL).strip()
    return ""


def parse_keyword_book(kb_text: str) -> tuple[list[KeywordEntry], list[ShortcutEntry]]:
    keyword_entries: list[KeywordEntry] = []
    shortcuts: list[ShortcutEntry] = []

    # 단축어 시작 지점 탐색
    sc_start_match = re.search(
        r"^#+\s*(?:Shortcuts?|단축어|Shortcut\s+`?[a-zA-Z0-9_-]+`?)\b",
        kb_text,
        flags=re.MULTILINE | re.IGNORECASE,
    )
    if sc_start_match:
        kb_part = kb_text[: sc_start_match.start()]
        shortcut_part = kb_text[sc_start_match.start() :]
    else:
        kb_part = kb_text
        shortcut_part = ""

    # 1. 키워드북 항목 파싱
    heading_matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", kb_part, re.MULTILINE))
    filtered_matches = []
    for m in heading_matches:
        t = m.group(2).strip()
        if re.match(r"^(?:등록 순서|3슬롯|Entry text|입력 본문|본문|내용|Shortcuts?|단축어)\b", t, re.IGNORECASE):
            continue
        filtered_matches.append(m)

    for i, match in enumerate(filtered_matches):
        start = match.start()
        end = filtered_matches[i + 1].start() if i + 1 < len(filtered_matches) else len(kb_part)
        block = kb_part[start:end]

        kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if kw_match:
            raw_title = match.group(2).strip()
            clean_title = re.sub(r"^`?kb\.[^`\s]+`?\s*—?\s*", "", raw_title)
            clean_title = re.sub(r"^[0-9]+\.\s*", "", clean_title).strip()
            keywords = parse_keywords(kw_match.group(1))
            content = parse_keyword_body(block)
            keyword_entries.append(KeywordEntry(title=clean_title, keywords=keywords, content=content))

    # 2. 단축어 파싱
    if shortcut_part:
        sc_headings = list(
            re.finditer(
                r"^#+\s+(?:Shortcut\s+`?([^`\n]+)`?|sc\.([a-zA-Z0-9_-]+)|([^#\n]+))$",
                shortcut_part,
                re.MULTILINE | re.IGNORECASE,
            )
        )
        valid_sc_matches = []
        for m in sc_headings:
            h_text = m.group(0).strip()
            if re.match(r"^#+\s*(?:Shortcuts?|단축어)(?:\s*\(.*?\))?\s*$", h_text, re.IGNORECASE):
                continue
            if re.search(r"^##\s+(?:Shortcut prompt|프롬프트|내용)\b", h_text, re.IGNORECASE):
                continue
            valid_sc_matches.append(m)

        for i, match in enumerate(valid_sc_matches):
            start = match.start()
            end = valid_sc_matches[i + 1].start() if i + 1 < len(valid_sc_matches) else len(shortcut_part)
            block = shortcut_part[start:end]

            sc_id = match.group(1) or match.group(2) or match.group(3) or "shortcut"
            sc_id = sc_id.strip()
            name_m = re.search(r"^-\s*(?:name|이름):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
            desc_m = re.search(r"^-\s*(?:description|설명):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)

            # Prompt can be under ## Shortcut prompt or - prompt: (supports multi-line bullets & code blocks)
            prompt_m = re.search(
                r"^##\s+(?:Shortcut prompt|프롬프트)\s*\n(.*?)(?=^#|\Z)",
                block,
                re.MULTILINE | re.DOTALL | re.IGNORECASE,
            )
            if not prompt_m:
                prompt_m = re.search(
                    r"^-\s*(?:prompt|프롬프트):\s*\n?(.*?)(?=^-\s*(?:name|이름|desc|description|설명):|^#|\Z)",
                    block,
                    re.MULTILINE | re.DOTALL | re.IGNORECASE,
                )

            name = (name_m.group(1).strip() if name_m else sc_id).lstrip("/")
            desc = desc_m.group(1).strip() if desc_m else ""
            prompt = prompt_m.group(1).strip() if prompt_m else ""
            shortcuts.append(ShortcutEntry(id=sc_id, name=name, description=desc, prompt=prompt))

    return keyword_entries, shortcuts


# ── [등록] 탭 설정 ─────────────────────────────────────────────────
# 선택지는 2026-09-16 크랙 에디터에서 실제로 펼쳐 본 목록이다. 크랙이 목록을
# 바꾸면 inspect 가 "없는 선택지" 로 알려주므로, 그때 여기와 가이드를 함께 고친다.
GENRE_OPTIONS = ("로맨스", "로판", "SF/판타지", "일상/현대", "무협", "시대", "BL", "GL", "2차 창작", "유틸리티", "기타")
TARGET_OPTIONS = ("남성향", "여성향", "전체")
CHAT_FORM_OPTIONS = ("1:1 롤플레잉", "시뮬레이션")
MAX_OUTPUT_OPTIONS = ("기본", "1.5x", "3x", "5x")
HASHTAG_MAX_COUNT = 10
DESCRIPTION_MAX = 1000  # [등록] 탭 상세 설명 textarea maxlength
HASHTAG_MAX_LEN = 10  # 입력칸 maxlength=10. 넘으면 칸이 조용히 잘라 먹는다.

REGISTER_FIELDS: tuple[tuple[str, str], ...] = (
    ("genre", r"Genre|장르"),
    ("target", r"Target|타겟"),
    ("chat_form", r"Chat form|Chat format|대화 형태"),
    ("mode", r"Recommended mode|권장 모드"),
    ("max_output", r"Max output|권장 최대 출력량"),
    ("hashtags", r"Hashtags|해시태그"),
    ("audience", r"Audience|이용자 층"),
)


def parse_register_settings(story_content: str) -> dict:
    """story.md Core 의 `- Genre:` 같은 선언을 [등록] 탭 설정으로 읽는다."""
    out: dict = {}
    for key, names in REGISTER_FIELDS:
        m = re.search(rf"^-\s*(?:{names}):\s*(.+)$", story_content, re.MULTILINE | re.IGNORECASE)
        if not m:
            continue
        value = m.group(1).strip()
        if key == "hashtags":
            parts = re.split(r"[,，]", value) if re.search(r"[,，]", value) else value.split()
            out[key] = [x.strip().lstrip("#").strip() for x in parts if x.strip().lstrip("#").strip()]
        else:
            out[key] = value
    return out


def register_violations(register: dict) -> list[str]:
    """선언값이 크랙 선택지·한도에 맞는지 센다. 틀린 값을 넣으면 에디터가 조용히 무시한다."""
    found: list[str] = []
    for key, options, label in (
        ("genre", GENRE_OPTIONS, "장르"),
        ("target", TARGET_OPTIONS, "타겟"),
        ("chat_form", CHAT_FORM_OPTIONS, "대화 형태"),
        ("max_output", MAX_OUTPUT_OPTIONS, "권장 최대 출력량"),
    ):
        if key in register and register[key] not in options:
            found.append(f"{label} '{register[key]}' 은 크랙 선택지에 없습니다 ({' · '.join(options)})")
    tags = register.get("hashtags") or []
    if len(tags) > HASHTAG_MAX_COUNT:
        found.append(f"해시태그 {len(tags)}개 (최대 {HASHTAG_MAX_COUNT}개)")
    for tag in tags:
        if crack_len(tag) > HASHTAG_MAX_LEN:
            found.append(f"해시태그 '{tag}' {crack_len(tag)}자 (한 개당 {HASHTAG_MAX_LEN}자)")
    return found


def load_project_artifacts(project_dir: Path, variant: str = "safe") -> ProjectArtifacts:
    build_dir = project_dir / "build"
    if not build_dir.exists():
        raise FileNotFoundError(f"Build directory not found in {project_dir}")

    prologue_path = build_dir / "prologue.md"
    start_prompt_path = build_dir / "start-prompt.md"
    sys_prompt_path = build_dir / f"integrated-prompt-{variant}.md"
    kb_variant_path = build_dir / f"keyword-book-{variant}.md"
    kb_path = kb_variant_path if kb_variant_path.exists() else (build_dir / "keyword-book.md")
    summary_path = build_dir / "assets" / "summary-comment.md"
    story_desc_path = build_dir / "assets" / "story-description.md"
    play_guide_path = build_dir / "assets" / "play-guide.md"
    replies_path = build_dir / "assets" / "recommended-replies.md"
    story_path = project_dir / "story.md"

    prologue = prologue_path.read_text(encoding="utf-8").strip() if prologue_path.exists() else ""
    start_prompt = start_prompt_path.read_text(encoding="utf-8").strip() if start_prompt_path.exists() else ""
    system_prompt = sys_prompt_path.read_text(encoding="utf-8").strip() if sys_prompt_path.exists() else ""
    kb_text = kb_path.read_text(encoding="utf-8").strip() if kb_path.exists() else ""
    summary_comment = summary_path.read_text(encoding="utf-8").strip() if summary_path.exists() else ""
    story_description = story_desc_path.read_text(encoding="utf-8").strip() if story_desc_path.exists() else ""
    play_guide = play_guide_path.read_text(encoding="utf-8").strip() if play_guide_path.exists() else ""
    # 추천 답변은 `---` 로 구분한 최대 3블록.
    replies: list[str] = []
    if replies_path.exists():
        raw = replies_path.read_text(encoding="utf-8").strip()
        replies = [b.strip() for b in re.split(r"^---+$", raw, flags=re.MULTILINE) if b.strip()]
        replies = replies[:REPLY_MAX_COUNT]

    # Title and short summary (Logline) extraction
    title = project_dir.name
    short_summary = ""
    register: dict = {}
    if story_path.exists():
        story_content = story_path.read_text(encoding="utf-8")
        register = parse_register_settings(story_content)
        title_tag = re.search(r"^-\s*Title:\s*(.+)$", story_content, re.MULTILINE | re.IGNORECASE)
        if title_tag:
            title = title_tag.group(1).strip()
        else:
            first_line = story_content.splitlines()[0]
            title_m = re.search(r"^#\s+(.+)$", first_line)
            if title_m and title_m.group(1).strip().lower() != "story":
                title = title_m.group(1).strip()
        # 성인 변형은 목록에서 구분돼야 한다. story.md 가 접미사를 선언하면
        # unsafe 빌드의 제목에만 붙인다. 선언이 없으면 두 변형이 같은 제목으로
        # 등록돼 어느 쪽이 성인판인지 카드만 보고 알 수 없다.
        suffix_tag = re.search(r"^-\s*Unsafe title suffix:\s*(.+)$",
                               story_content, re.MULTILINE | re.IGNORECASE)
        if variant == "unsafe" and suffix_tag:
            title = f"{title} {suffix_tag.group(1).strip()}".strip()

        # 1. 태그 우선 탐색: - Logline: / - 한줄소개: / - 한줄설명: / - Tagline: / - Premise:
        summary_m = re.search(
            r"^-\s*(?:Logline|한줄소개|한줄설명|Tagline|Premise|로그라인|소개):\s*(.+)$",
            story_content,
            re.MULTILINE | re.IGNORECASE,
        )
        if summary_m:
            short_summary = summary_m.group(1).strip()

    if not short_summary and story_description:
        # 2. story-description.md의 코멘트 첫 문단 추출
        comm_m = re.search(r"「제작자 코멘트」\s*\n+(.+?)(?:\n\n|\Z)", story_description, re.DOTALL)
        if comm_m:
            first_p = comm_m.group(1).strip().splitlines()[0]
            short_summary = first_p.strip()

    # 한도 초과는 조용히 자르지 않는다. inspect 가 위반으로 보고하고,
    # 작성자가 story.md 의 `- Logline:` 을 직접 줄이게 한다.

    keyword_entries, shortcuts = parse_keyword_book(kb_text)

    # 3. 시작 세트 로드 — references/start-sets.md 규약
    departments = load_start_sets(project_dir)

    return ProjectArtifacts(
        project_name=project_dir.name,
        title=title + TITLE_SUFFIX,
        prologue=prologue,
        start_prompt=start_prompt,
        system_prompt=system_prompt,
        keyword_entries=keyword_entries,
        shortcuts=shortcuts,
        departments=departments,
        summary_comment=summary_comment,
        story_description=story_description,
        short_summary=short_summary,
        play_guide=play_guide,
        replies=replies,
        variant=variant,
        register=register,
    )


def run_auth(login_url: str = DEFAULT_LOGIN_URL, auth_path: Path = DEFAULT_AUTH_PATH) -> int:
    """Launch interactive headed browser for the user to log in and save storage state."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다. 다음 명령어로 설치해 주세요:", file=sys.stderr)
        print("   uv run --with playwright python tools/sync/crack_sync.py ...", file=sys.stderr)
        print("   또는 pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    print("=" * 70)
    print("🔑 크랙(Crack) 1회 로그인 세션 캡처 모드")
    print("=" * 70)
    print(f"브라우저 창이 열리면 크랙 계정으로 로그인해 주세요.")
    print(f"로그인이 완료되면 콘솔에서 [Enter] 키를 누르면 세션이 저장됩니다.")
    print(f"저장 경로: {auth_path}")
    print("=" * 70)

    auth_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url)

        print("\n👉 브라우저 창에서 크랙 로그인을 완료해 주세요...")
        print("💡 로그인 상태가 감지되면 세션이 자동으로 `~/.crack/auth_state.json`에 영구 저장됩니다.")

        for _ in range(300):  # 최대 5분간 로그인 감지 대기
            try:
                if page.is_closed():
                    break
                cookies = context.cookies()
                if cookies and len(cookies) > 0:
                    auth_path.parent.mkdir(parents=True, exist_ok=True)
                    context.storage_state(path=str(auth_path))
                time.sleep(1)
            except Exception:
                break

        try:
            if not page.is_closed():
                context.storage_state(path=str(auth_path))
                print(f"\n✅ 로그인 세션이 성공적으로 저장되었습니다! ({auth_path})")
        except Exception:
            pass

    return 0


def run_inspect(project_dir: Path, variant: str = "safe") -> int:
    """Inspect and print artifact contents mapped to Crack UI fields."""
    artifacts = load_project_artifacts(project_dir, variant=variant)

    print("=" * 75)
    print(f"📋 크랙 프로젝트 자동 동기화 데이터 검사: [{artifacts.title}] ({artifacts.variant.upper()})")
    print("=" * 75)
    print(f"1. 📖 프롤로그 (Prologue)           : {len(artifacts.prologue):,}자 / 1,000자")
    print(f"2. 🚀 시작 프롬프트 (Start Prompt)     : {len(artifacts.start_prompt):,}자 / 1,000자")
    if artifacts.departments:
        print(f"   🏢 부서별 시작 설정 (Departments) : 총 {len(artifacts.departments)}개 등록 예정")
        for i, d in enumerate(artifacts.departments, 1):
            print(f"      [{i:02d}] {d.title:<24} | 프롤로그 {len(d.prologue):,}자 | 시작상황 {len(d.start_prompt):,}자")
    print(f"3. 🧠 메인 시스템 프롬프트 ({artifacts.variant}) : {len(artifacts.system_prompt):,}자 / 7,000자")
    print(f"4. 📚 키워드북 항목 (Keyword Book)    : 총 {len(artifacts.keyword_entries)}개 등록 예정")
    for i, e in enumerate(artifacts.keyword_entries, 1):
        print(f"   [{i:02d}] {e.title:<18} | 키워드({len(e.keywords)}개): {', '.join(e.keywords):<22} | 본문 {len(e.content)}자")
    print(f"5. ⚡ 단축어 (Shortcuts)             : 총 {len(artifacts.shortcuts)}개 등록 예정")
    for i, sc in enumerate(artifacts.shortcuts, 1):
        print(f"   [{i:02d}] {sc.name} ({sc.id}) : {sc.description} | {len(sc.prompt)}자")
    desc_text = artifacts.story_description if artifacts.story_description else artifacts.summary_comment
    logline_len = len(artifacts.short_summary)
    logline_flag = "" if logline_len <= LOGLINE_MAX else f"  ⚠️ {LOGLINE_MAX}자 초과 — 크랙에서 잘립니다"
    print(f"6. 📝 작품 한 줄 소개 (Logline)     : '{artifacts.short_summary}' ({logline_len}자 / {LOGLINE_MAX}자){logline_flag}")
    print(f"7. 🌐 작품 상세 설명 (Description)   : {len(desc_text):,}자")
    pg = artifacts.play_guide
    pg_flag = "" if crack_len(pg) <= PLAY_GUIDE_MAX else f"  ⚠️ {PLAY_GUIDE_MAX}자 초과 — 크랙에서 잘립니다"
    print(f"8. 🎮 플레이 가이드 (Play Guide)     : {len(pg):,}자 / {PLAY_GUIDE_MAX}자" + ("  (없음 — 선택 항목)" if not pg else pg_flag))
    print(f"9. 💡 추천 답변 (Replies)           : {len(artifacts.replies)}개 / 최대 {REPLY_MAX_COUNT}개")
    for i, r in enumerate(artifacts.replies, 1):
        head = r.splitlines()[0][:38]
        print(f"   [{i}] {head}… ({len(r)}자)")
    reg = artifacts.register
    if reg:
        print("10. 🏷️ 등록 탭 설정 (story.md Core 선언)")
        for key, label in (("genre", "장르"), ("target", "타겟"), ("chat_form", "대화 형태"),
                           ("mode", "권장 모드"), ("max_output", "권장 최대 출력량")):
            if key in reg:
                print(f"   {label:<12}: {reg[key]}")
        if "hashtags" in reg:
            print(f"   해시태그     : {' '.join('#' + x for x in reg['hashtags'])} ({len(reg['hashtags'])}개 / {HASHTAG_MAX_COUNT}개)")
        if "audience" in reg:
            print(f"   이용자 층    : {reg['audience']} — 한 번 정하면 못 바꿔서 도구가 설정하지 않습니다")
    else:
        print("10. 🏷️ 등록 탭 설정                : (선언 없음 — 건드리지 않음)")
    print("=" * 75)

    # 한도를 출력만 하고 통과를 선언하면 검사기가 아니라 인쇄기다. 실제로 센다.
    violations: list[str] = []

    def check(label: str, text: str, cap: int) -> None:
        n = crack_len(text)
        if n > cap:
            violations.append(f"{label}: {n:,}자 / {cap:,}자 한도 ({n - cap:,}자 초과)")

    check("프롤로그", artifacts.prologue, PROLOGUE_MAX)
    check("시작 프롬프트", artifacts.start_prompt, START_PROMPT_MAX)
    check(f"메인 시스템 프롬프트({artifacts.variant})", artifacts.system_prompt, SYSTEM_PROMPT_MAX)
    check("한 줄 소개", artifacts.short_summary, LOGLINE_MAX)
    check("플레이 가이드", artifacts.play_guide, PLAY_GUIDE_MAX)
    for d in artifacts.departments:
        check(f"시작세트 '{d.title}' 프롤로그", d.prologue, PROLOGUE_MAX)
        check(f"시작세트 '{d.title}' 시작상황", d.start_prompt, START_PROMPT_MAX)
    for e in artifacts.keyword_entries:
        check(f"키워드북 '{e.title}' 본문", e.content, ENTRY_MAX)
        if not 1 <= len(e.keywords) <= 5:
            violations.append(f"키워드북 '{e.title}': 키워드 {len(e.keywords)}개 (1~5개만 허용)")
    for sc in artifacts.shortcuts:
        check(f"단축어 '{sc.name}' 프롬프트", sc.prompt, SHORTCUT_MAX)
    if len(artifacts.replies) > REPLY_MAX_COUNT:
        violations.append(f"추천 답변 {len(artifacts.replies)}개 (최대 {REPLY_MAX_COUNT}개)")
    check("상세 설명", artifacts.story_description, DESCRIPTION_MAX)
    violations.extend(register_violations(artifacts.register))
    if len(artifacts.departments) > MAX_START_SETS:
        violations.append(
            f"시작 세트 {len(artifacts.departments)}개 (크랙 상한 {MAX_START_SETS}개) — "
            f"초과분은 주입되지 않습니다")

    if violations:
        print(f"❌ 크랙 규격 위반 {len(violations)}건 — 이대로 주입하면 잘립니다:")
        for v in violations:
            print(f"   · {v}")
        print("=" * 75)
        return 1

    print("✨ 모든 산출물이 크랙 규격에 부합합니다. (글자 수는 UTF-16 code unit 기준)")
    return 0


def dump_fields(page: Any, tag: str = "") -> None:
    """현재 화면의 입력 칸과 버튼을 그대로 찍는다.

    placeholder 를 추측해서 셀렉터를 쓰면 못 찾을 때 원인을 알 수 없다.
    이 덤프가 실물을 보여주므로 START_TAB_PLACEHOLDERS 를 사실에 맞춰 고칠 수 있다.
    """
    print(f"\n🔬 [필드 덤프{(' — ' + tag) if tag else ''}]")
    rows = page.evaluate("""() => {
        const vis = el => {
            const r = el.getBoundingClientRect();
            return r.width > 0 && r.height > 0;
        };
        const out = [];
        document.querySelectorAll("textarea, input, [contenteditable='true']").forEach(el => {
            if (!vis(el)) return;
            out.push({
                kind: "field",
                tag: el.tagName.toLowerCase(),
                placeholder: el.getAttribute("placeholder") || "",
                dataPlaceholder: el.getAttribute("data-placeholder") || "",
                ariaPlaceholder: el.getAttribute("aria-placeholder") || "",
                ariaLabel: el.getAttribute("aria-label") || "",
                name: el.getAttribute("name") || "",
                len: (el.value !== undefined ? (el.value || "") : (el.innerText || "")).length,
            });
        });
        document.querySelectorAll("button").forEach(el => {
            if (!vis(el)) return;
            const t = (el.innerText || "").trim();
            if (t) out.push({
                kind: "button",
                text: t.slice(0, 30),
                disabled: el.disabled || el.getAttribute("aria-disabled") === "true",
            });
        });
        // 저장을 막는 것은 대개 화면 어딘가의 빨간 문구다. 그것도 같이 찍는다.
        document.querySelectorAll("[role='alert'], [class*='error'], [class*='Error'], [class*='invalid']").forEach(el => {
            if (!vis(el)) return;
            const t = (el.innerText || "").trim();
            if (t && t.length < 200) out.push({kind: "alert", text: t});
        });
        return out;
    }""")
    for i, r in enumerate(rows):
        if r["kind"] == "field":
            hints = " | ".join(
                f"{k}={r[k]!r}" for k in
                ("placeholder", "dataPlaceholder", "ariaPlaceholder", "ariaLabel", "name")
                if r[k]
            )
            print(f"   [{i:02d}] <{r['tag']}> 내용{r['len']}자  {hints or '(식별 속성 없음)'}")
        elif r["kind"] == "alert":
            print(f"   [{i:02d}] ⛔ 화면 오류 문구: {r['text']!r}")
        else:
            flag = "  (비활성)" if r.get("disabled") else ""
            print(f"   [{i:02d}] <button> {r['text']!r}{flag}")
    print(f"   — 총 {len(rows)}개\n")


def placeholder_selector(needle: str) -> str:
    """안내 문구로 입력 칸을 찾는 셀렉터.

    크랙의 칸이 전부 `textarea[placeholder]` 인 것은 아니다. 리치 에디터는
    `contenteditable` 에 `data-placeholder` 를 쓰고, 일부는 `aria-placeholder`
    만 있다. 한 종류만 보면 그 칸은 조용히 비어 있는 채로 저장된다.
    """
    return ", ".join(
        f"{tag}:visible[{attr}*='{needle}']"
        for tag, attr in (
            ("textarea", "placeholder"),
            ("input", "placeholder"),
            ("div[contenteditable='true']", "data-placeholder"),
            ("div[contenteditable='true']", "aria-placeholder"),
            ("*", "aria-placeholder"),
        )
    )


def inject_replies(page: Any, replies: list, label: str = "") -> None:
    """현재 열려 있는 시작 세트 패널에 추천 답변을 넣는다.

    추천 답변은 **시작 세트마다 따로**다. 세트 루프가 끝난 뒤에 한 번만 넣으면
    그때 열려 있던 마지막 세트에만 들어가고, 기본 세트에는 아무것도 없다.
    실제로 그래서 "추천 답변이 안 들어갔다" 는 상태가 됐다.

    칸은 [추천 답변 추가] 를 눌러야 생긴다(`placeholder='추천 답변 N'`).
    채운 뒤 값 길이를 다시 읽어, 실제로 들어간 것만 성공이라고 말한다.
    """
    if not replies:
        return
    where = f" — {label}" if label else ""
    print(f"      📌 추천 답변 {len(replies)}개{where}")
    for i, reply in enumerate(replies[:REPLY_MAX_COUNT]):
        target = page.locator(f"textarea:visible[placeholder*='추천 답변 {i + 1}']").first
        if target.count() == 0:
            add_btn = page.locator(
                "button:visible:has-text('추천 답변 추가'), button:visible:has-text('추천답변 추가')"
            ).first
            if add_btn.count() > 0:
                add_btn.click()
                time.sleep(1.2)
                target = page.locator(f"textarea:visible[placeholder*='추천 답변 {i + 1}']").first
        if target.count() == 0:
            print(f"         ⚠️ 추천 답변 {i + 1} 칸을 만들지 못했습니다 — 건너뜁니다")
            continue
        fill_react_input(page, target, reply)
        time.sleep(0.4)
        try:
            got = len(target.input_value() or "")
        except Exception:
            got = -1
        if got == len(reply):
            print(f"         ✅ 추천 답변 {i + 1} ({got:,}자)")
        else:
            print(f"         ⚠️ 추천 답변 {i + 1} 넣은 뒤 {got}자 — 기대 {len(reply)}자")


def find_start_field(page: Any, field: str, index: int = 0) -> Any:
    """[시작 설정] 탭의 칸을 placeholder 문구로 찾는다.

    위치(`textarea[0]`, `[-1]`)로 찾으면 크랙이 칸을 하나 늘리거나 순서를
    바꾸는 순간 전 필드가 한 칸씩 밀려 조용히 잘못된 자리에 써진다. 실제로
    프롤로그가 시작 상황 칸에, 시작 프롬프트가 플레이 가이드 칸에 들어간
    적이 있다. 못 찾으면 아무 데나 쓰지 말고 None 을 돌려준다.
    """
    if field == "prologue":
        return find_prologue_field(page, index)
    for needle in START_TAB_PLACEHOLDERS[field]:
        loc = page.locator(placeholder_selector(needle))
        if loc.count() > index:
            return loc.nth(index)
    return None


def find_prologue_field(page: Any, index: int = 0) -> Any:
    """프롤로그 칸 — 시작 상황 칸 바로 앞의, placeholder 없는 textarea.

    이 칸만 식별 속성이 하나도 없어 문구로 찾을 수 없다. 순서를 세는 대신
    시작 상황 칸(placeholder 가 확실한 칸)을 앵커로 잡고 그 직전 칸을 고르므로,
    칸이 늘거나 순서가 바뀌어도 함께 움직인다.
    """
    idx = page.evaluate("""() => {
        const vis = el => { const r = el.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
        const tas = [...document.querySelectorAll("textarea")].filter(vis);
        const anchors = [];
        tas.forEach((el, i) => {
            const ph = el.getAttribute("placeholder") || "";
            if (ph.includes("사용자의 역할") || ph.includes("이야기가 시작되는")) anchors.push(i);
        });
        return anchors.map(i => {
            const prev = tas[i - 1];
            if (!prev) return -1;
            return (prev.getAttribute("placeholder") || "") ? -1 : i - 1;
        });
    }""")
    if not idx or index >= len(idx) or idx[index] < 0:
        return None
    return page.locator("textarea:visible").nth(idx[index])


def fill_start_field(page: Any, field: str, label: str, value: str, index: int = 0) -> bool:
    """placeholder 로 찾은 칸에만 쓴다. 못 찾으면 건너뛰고 경고한다."""
    if not value:
        return True
    target = find_start_field(page, field, index)
    if target is None:
        print(f"   ⚠️ [{label}] 칸을 찾지 못해 건너뜁니다 — 위치로 추정해 덮어쓰지 않습니다.")
        dump_fields(page, f"{label} 탐색 실패")
        return False
    fill_react_input(page, target, value)
    print(f"   ✅ [{label}] 주입 완료 ({len(value):,}자)")
    return True


def fill_react_input(page: Any, selector_or_locator: Any, value: str) -> bool:
    """Safely fill text into React-controlled input/textarea and trigger all change events."""
    try:
        if isinstance(selector_or_locator, str):
            loc = page.locator(selector_or_locator).first
        else:
            loc = selector_or_locator
        if loc.count() > 0:
            loc.scroll_into_view_if_needed(timeout=2000)
            loc.click(timeout=2000)
            loc.fill(value, timeout=3000)
            return True
    except Exception:
        pass

    # JavaScript dispatch fallback
    try:
        page.evaluate(
            """
            ([sel, val]) => {
                let el = typeof sel === 'string' ? document.querySelector(sel) : sel;
                if (el) {
                    el.focus();
                    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
                        const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                            window.HTMLInputElement.prototype, "value"
                        )?.set || Object.getOwnPropertyDescriptor(
                            window.HTMLTextAreaElement.prototype, "value"
                        )?.set;
                        if (nativeInputValueSetter) {
                            nativeInputValueSetter.call(el, val);
                        } else {
                            el.value = val;
                        }
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                        el.dispatchEvent(new Event('change', { bubbles: true }));
                    } else if (el.isContentEditable) {
                        el.innerText = val;
                        el.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                    return true;
                }
                return false;
            }
        """,
            [selector_or_locator if isinstance(selector_or_locator, str) else None, value],
        )
        return True
    except Exception:
        return False


def switch_tab(page: Any, tab_names: list[str]) -> bool:
    """Switch to a tab by searching for matching visible text."""
    for name in tab_names:
        try:
            locs = page.locator(
                f"button:visible:has-text('{name}'), div[role='tab']:visible:has-text('{name}'), a:visible:has-text('{name}'), span:visible:has-text('{name}')"
            )
            count = locs.count()
            for idx in range(count):
                el = locs.nth(idx)
                txt = el.inner_text().strip()
                if name in txt and len(txt) <= len(name) + 10:
                    el.click(timeout=2000)
                    time.sleep(0.8)
                    return True
        except Exception:
            continue
    return False


def dump_dom_summary(page: Any) -> None:
    """Print all visible buttons, tabs, inputs, and textareas for inspection."""
    print("\n🔍 --- [현재 페이지 DOM 요소 덤프] ---")
    print(f"URL: {page.url}")
    print(f"Title: {page.title()}")

    # Buttons
    buttons = page.locator("button:visible, div[role='button']:visible, a:visible").all_inner_texts()
    clean_btns = [b.strip().replace("\n", " ") for b in buttons if b.strip() and len(b.strip()) < 30]
    print(f"🔘 버튼/링크 ({len(clean_btns)}개): {', '.join(clean_btns[:20])}")

    # Inputs & Textareas
    inputs = page.locator("input:visible, textarea:visible:not([aria-hidden='true']):not([name='hiddenTextarea'])").all()
    print(f"📝 입력창 ({len(inputs)}개 발견):")
    for i, inp in enumerate(inputs, 1):
        tag = inp.evaluate("el => el.tagName.toLowerCase()")
        ph = inp.get_attribute("placeholder") or ""
        aria = inp.get_attribute("aria-label") or ""
        name = inp.get_attribute("name") or ""
        print(f"   [{i:02d}] <{tag}> placeholder='{ph}' aria-label='{aria}' name='{name}'")
    print("------------------------------------------\n")


def inject_prompts(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject prologue, start prompt, and system prompt into editor."""
    print("\n🧠 [프롬프트 주입 시작] (" + artifacts.variant.upper() + ")")
    if not require_editor_tabs(page, "프롬프트"):
        return False

    # ── [스토리 설정] 탭 → 제작자 커스텀 선택 → 메인 시스템 프롬프트 주입 ──
    print("   📌 [스토리 설정] 탭 클릭...")
    story_tab = page.locator("a:visible:has-text('스토리 설정'), button:visible:has-text('스토리 설정'), div[role='tab']:visible:has-text('스토리 설정'), li:visible:has-text('스토리 설정')").first
    if story_tab.count() > 0:
        story_tab.click()
        time.sleep(1.5)

        tpl_btn = page.locator("button:has-text('기본 프롬프트'), button:has-text('프롬프트 템플릿')").first
        if tpl_btn.count() > 0:
            tpl_btn.click()
            time.sleep(0.8)
            custom_opt = page.locator(
                "div:text('제작자 커스텀'), li:text('제작자 커스텀'), [role='option']:has-text('제작자 커스텀')"
            ).first
            if custom_opt.count() > 0:
                custom_opt.click(timeout=5000)
                time.sleep(1.2)
                print("   ✅ [제작자 커스텀] 프롬프트 양식 전환 완료!")
            else:
                print("   ⚠️ '제작자 커스텀' 옵션 못 찾음")

        sys_ta = page.locator("textarea:visible, div[contenteditable='true']:visible").first
        if sys_ta.count() > 0:
            fill_react_input(page, sys_ta, artifacts.system_prompt)
            print(f"   ✅ [메인 시스템 프롬프트] 주입 완료 ({len(artifacts.system_prompt):,}자)")
        else:
            print("   ⚠️ 시스템 프롬프트 입력창 못 찾음")
    else:
        print("   ⚠️ '스토리 설정' 탭 못 찾음")

    # ── [시작 설정] 탭 → [0] 프롤로그 + [1] 시작 상황 (세계관/역할) 주입 ──
    print("   📌 [시작 설정] 탭 클릭...")
    start_tab = page.locator("a:visible:has-text('시작 설정'), button:visible:has-text('시작 설정'), div[role='tab']:visible:has-text('시작 설정'), li:visible:has-text('시작 설정')").first
    if start_tab.count() > 0:
        start_tab.click()
        time.sleep(1.5)

        if artifacts.departments:
            print(f"\n🏢 [다중 시작 설정 주입 시작] (총 {len(artifacts.departments)}개 시작 세트)")
            for idx, dept in enumerate(artifacts.departments):
                print(f"   [{idx+1}/{len(artifacts.departments)}] '{dept.title}'")
                # 갱신 실행이면 그 세트는 이미 탭으로 존재한다. 새로 추가하지 말고
                # 그 탭을 눌러 들어간다. 상한(3개)에 찬 뒤에는 [설정 추가] 버튼이
                # 사라지므로, 탭을 찾지 못할 때만 추가를 시도한다.
                existing_tab = page.locator(f"button:visible:has-text('{dept.title}')").first
                if existing_tab.count() > 0:
                    existing_tab.click()
                    time.sleep(1.2)
                elif idx > 0:
                    add_btn = page.locator("button:visible:has-text('설정 추가'), button:visible:has-text('+ 추가'), button:visible:has-text('시작 추가')").first
                    if add_btn.count() == 0:
                        # 세트가 상한(3개)에 차면 크랙이 [설정 추가] 버튼을 없앤다.
                        # 버튼 없이 계속하면 앞 세트를 덮어쓰므로 여기서 멈춘다.
                        print(f"   ❌ '설정 추가' 버튼이 없습니다 — 크랙의 시작 세트 상한은 {MAX_START_SETS}개입니다. "
                              f"남은 {len(artifacts.departments) - idx}개는 주입하지 않습니다(앞 세트 덮어쓰기 방지).")
                        dump_fields(page, "설정 추가 버튼 탐색 실패")
                        break
                    add_btn.click()
                    time.sleep(1.5)

                # 설정 이름(제목)
                title_inp = page.locator("input:visible[placeholder*='상황'], input:visible[placeholder*='등장인물'], input:visible[placeholder*='이름']").last
                if title_inp.count() > 0:
                    fill_react_input(page, title_inp, dept.title)

                # 각 칸은 placeholder 로 찾는다. 새로 추가된 패널이 마지막이므로
                # 같은 placeholder 가 여러 개면 마지막 것을 쓴다.
                for field, label, value in (
                    ("prologue", "프롤로그", dept.prologue),
                    ("start_prompt", "시작 상황", dept.start_prompt),
                    ("play_guide", "플레이 가이드", dept.play_guide or artifacts.play_guide),
                ):
                    if not value:
                        continue
                    loc = None
                    if field == "prologue":
                        loc = find_prologue_field(page, -1 if idx else 0)
                    else:
                        for needle in START_TAB_PLACEHOLDERS[field]:
                            cand = page.locator(placeholder_selector(needle))
                            if cand.count() > 0:
                                loc = cand.last
                                break
                    if loc is None:
                        print(f"      ⚠️ [{label}] 칸 못 찾음 — 건너뜁니다")
                        if idx == 0:
                            dump_fields(page, f"{label} 탐색 실패")
                        continue
                    fill_react_input(page, loc, value)
                    print(f"      ✅ [{label}] {len(value):,}자")
                inject_replies(page, dept.replies or artifacts.replies, dept.title)
                time.sleep(0.5)
            print(f"   ✅ 시작 세트 주입 완료")
        else:
            fill_start_field(page, "prologue", "프롤로그", artifacts.prologue)
            fill_start_field(page, "start_prompt", "시작 상황 (시작 프롬프트)", artifacts.start_prompt)
            fill_start_field(page, "play_guide", "플레이 가이드", artifacts.play_guide)
            inject_replies(page, artifacts.replies)

    else:
        print("   ⚠️ '시작 설정' 탭 못 찾음")

    return True


def cover_slot_empty(page: Any) -> bool:
    """대표 이미지 칸이 비었는지 본다.

    "이미지를 필수로 등록해주세요" 는 저장을 한 번 시도해야 뜬다. 그 문구만
    보고 판단하면 첫 주입에서 표지를 통째로 건너뛰고, 그러면 [다음] 이
    비활성이라 storyId 가 발급되지 않는다. 실제로 이 순서 때문에 신규 생성이
    매번 프로필 단계에서 멎었다.
    """
    if os.environ.get("CRACK_SYNC_THUMBNAIL_FORCE", "").strip() == "1":
        return True
    try:
        if page.locator(":text('이미지를 필수로 등록')").count() > 0:
            return True
    except Exception:
        pass
    try:
        if page.locator("button:visible:has-text('업로드')").count() == 0:
            return False  # 업로드 칸 자체가 없는 화면이면 대상이 아니다
        # 빈 상태 아바타와 카드 예시는 표지가 아니다. 이걸 세면 이미 올린 표지가
        # 있다고 오판해 업로드를 건너뛰고, 크랙이 저장을 거부한다.
        shown = page.eval_on_selector_all(
            "img",
            "els=>els.filter(e=>e.offsetParent&&e.naturalWidth>200)"
            ".map(e=>e.currentSrc||e.src)"
            ".filter(u=>!/graphics\\/empty|card_example|avatar_portrait/.test(u))")
        return not shown
    except Exception:
        return False


def require_editor_tabs(page: Any, what: str) -> bool:
    """storyId 가 없으면 탭이 열리지 않는다. 주입을 시도해도 전부 허공에 쌓인다."""
    try:
        url = page.url
    except Exception:
        return False
    if "storyId=" not in url:
        print(f"   ⛔ storyId 가 없어 [{what}] 주입을 건너뜁니다 — 프로필 단계가 끝나지 않았습니다.")
        return False
    return True


def ensure_required_basics(page: Any, artifacts: "ProjectArtifacts") -> None:
    """저장 전 필수 항목(제목·한 줄 소개)이 비어 있으면 채운다.

    크랙은 이 둘이 비면 [임시저장] 을 눌러도 조용히 거부한다. 화면에는
    "이름 * 2~30자 이내로 입력해 주세요" 같은 문구만 뜨고 버튼은 눌린 것처럼
    보이므로, 채워 넣지 않으면 저장한 줄 알고 작업을 잃는다.
    """
    # 대표 이미지가 비면 크랙이 저장을 거부한다. 화면에는 "이미지를 필수로
    # 등록해주세요" 만 뜨고 버튼은 눌린 것처럼 보이므로, 없으면 여기서 말한다.
    thumb = os.environ.get("CRACK_SYNC_THUMBNAIL", "").strip()
    if cover_slot_empty(page):
        if thumb and Path(thumb).is_file():
            # 숨은 input 에 직접 넣으면 미디어 탭 같은 엉뚱한 input 을 집을 수
            # 있다. [업로드] 를 눌러 뜨는 파일 선택창을 가로채는 편이 확실하다.
            # [업로드] 를 누르면 바로 파일창이 뜨지 않는다. "기기에서 가져오기 /
            # 라이브러리에서 가져오기" 를 고르는 모달이 한 단계 끼어 있고, 그걸
            # 안 넘기면 모달이 화면에 남아 [임시저장] 버튼까지 가린다.
            done = False
            try:
                up = page.locator("button:visible:has-text('업로드')").first
                if up.count() > 0:
                    up.click()
                    time.sleep(1.2)
                    # :text() 는 버튼 안쪽 글자 노드를 잡아 클릭해도 파일창이 안 열린다.
                    # 모달의 선택지는 제목·설명이 든 button 이므로 button 으로 집는다.
                    pick = page.locator("button:visible", has_text="기기에서 가져오기").first
                    if pick.count() == 0:
                        pick = page.locator("button:visible", has_text="내 기기").first
                    if pick.count() > 0:
                        with page.expect_file_chooser(timeout=6000) as fc:
                            pick.click()
                        fc.value.set_files(thumb)
                        # 파일을 고르면 크롭 모달이 뜬다. [자르기] 를 눌러야
                        # 확정되고, 안 누르면 모달이 남아 저장 버튼을 가린다.
                        time.sleep(2.0)
                        crop = page.locator(
                            "button:visible:has-text('자르기'), button:visible:has-text('적용'), "
                            "button:visible:has-text('확인'), button:visible:has-text('완료')"
                        ).first
                        if crop.count() > 0:
                            crop.click()
                            time.sleep(2.5)
                        done = True
                    else:
                        # 모달을 못 넘겼으면 반드시 닫는다. 열린 채 두면 이후
                        # 클릭이 전부 막힌다.
                        cancel = page.locator("button:visible:has-text('취소')").first
                        if cancel.count() > 0:
                            cancel.click()
                            time.sleep(0.6)
            except Exception:
                done = False
                try:
                    cancel = page.locator("button:visible:has-text('취소')").first
                    if cancel.count() > 0:
                        cancel.click()
                        time.sleep(0.6)
                except Exception:
                    pass
            if not done:
                file_inputs = page.locator("input[type='file']")
                if file_inputs.count() > 0:
                    try:
                        file_inputs.first.set_input_files(thumb)
                        done = True
                    except Exception as e:
                        print(f"   ⚠️ 대표 이미지 업로드 실패: {e}")
            if done:
                time.sleep(2.0)
                # "이미지를 필수로 등록해주세요" 는 안내문이라 등록 후에도 남는다.
                # 등록 여부는 저장 뒤 새로고침 검증으로 판정한다.
                print(f"   ↩️ 저장 전 [대표 이미지] 를 올렸습니다: {Path(thumb).name}")
            else:
                print("   ⚠️ 대표 이미지 업로드 경로를 찾지 못했습니다.")
        else:
            print("   ⛔ [대표 이미지] 가 비어 있습니다 — 크랙은 이게 없으면 저장을 거부합니다.")
            print("      CRACK_SYNC_THUMBNAIL=<이미지경로> 로 지정하거나 브라우저에서 직접 올리세요.")
            print("      규격: 1,080 x 1,620px 세로 비율 · 5MB 이하 · GIF 가능(움짤 표지)")

    checks = (
        ("스토리의 이름", "input", artifacts.title, "제목"),
        ("간단한 소개", "textarea", artifacts.short_summary or artifacts.title, "한 줄 소개"),
    )
    for needle, tag, value, label in checks:
        loc = page.locator(f"{tag}:visible[placeholder*='{needle}']")
        if loc.count() == 0 or not value:
            continue
        try:
            if (loc.first.input_value() or "").strip():
                continue
        except Exception:
            continue
        fill_react_input(page, loc.first, value)
        print(f"   ↩️ 저장 전 [{label}] 이 비어 있어 채웠습니다 ({len(value)}자)")


def save_crack_draft(page: Any, artifacts: Any = None) -> bool:
    """Safely click [임시저장 (Draft Save)] button and verify toast/save state.
    
    NEVER clicks [발행] (Publish) or final release buttons.
    """
    print("\n💾 [임시저장(Draft Save) 시도]...")
    if artifacts is not None:
        # 표지 칸은 [프로필] 탭에만 있다. 주입이 끝나면 화면은 보통 [등록] 탭이라
        # 여기서 검사하면 업로드 버튼이 없어 "대상 아님" 으로 판정하고 표지를
        # 건너뛴다. 신규 작품이 표지 없이 저장되던 원인이다. 먼저 프로필 탭을 연다.
        if os.environ.get("CRACK_SYNC_THUMBNAIL", "").strip():
            prof = (
                page.locator("button:visible, a:visible, [role='tab']:visible")
                .filter(has_text=re.compile(r"^\s*프로필\s*\*?\s*$"))
                .first
            )
            if prof.count() > 0:
                try:
                    prof.click()
                    time.sleep(3.0)
                except Exception:
                    pass
        ensure_required_basics(page, artifacts)
    draft_selectors = [
        "button:visible:has-text('임시저장')",
        "button:visible:has-text('임시 저장')",
        "div[role='button']:visible:has-text('임시저장')",
        "div[role='button']:visible:has-text('임시 저장')",
    ]
    
    btn = None
    for sel in draft_selectors:
        loc = page.locator(sel)
        if loc.count() > 0 and loc.first.is_visible():
            btn = loc.first
            break
            
    if btn:
        try:
            btn.scroll_into_view_if_needed(timeout=3000)
            btn.click(timeout=4000)
            # 토스트는 몇 초 만에 사라진다. 한 번만 보면 나타났다 사라진 사이를
            # 놓치고 실패로 오판한다. 짧은 간격으로 여러 번 본다.
            # 클릭했다는 사실은 저장됐다는 뜻이 아니다. 버튼이 눌려도 폼 검증에
            # 걸려 조용히 무시되는 경우가 있어, 저장 표시를 실제로 찾은 뒤에만
            # 성공이라고 말한다. 못 찾으면 미확인이라고 말하고 화면을 찍는다.
            # 근거는 '저장됐다고 쓰인 문구' 뿐이다. role=alert/status 는 관계없는
            # 라이브 영역에도 붙어 있어서, 그걸 근거로 삼으면 예전처럼 거짓 성공을
            # 낸다. 무엇을 보고 성공이라 판단했는지 함께 출력한다.
            hit = ""
            deadline = time.time() + 8.0
            while time.time() < deadline and not hit:
                for needle in ("저장되었", "저장 완료", "임시저장되었", "임시 저장되었", "저장했"):
                    loc = page.locator(f":text('{needle}')")
                    if loc.count() > 0:
                        try:
                            hit = loc.first.inner_text(timeout=1000).strip()[:60]
                        except Exception:
                            hit = needle
                        break
                if not hit:
                    time.sleep(0.4)
            if hit:
                print(f"   ✅ [임시저장] 완료 확인 — 화면 문구: {hit!r}")
                return True
            # 크랙이 토스트를 안 띄우는 경우가 있다. 그때는 새로고침해서 값이
            # 남아 있는지 보는 것이 유일하게 믿을 수 있는 근거다.
            try:
                # 주입이 끝나면 화면은 step=ending 에 있다. 거기서 새로고침하면
                # 제목 칸이 아예 없어 "저장 안 됨" 으로 잘못 판정한다. 제목이
                # 있는 프로필 단계로 되돌린 뒤에 확인한다.
                verify_url = page.url.split("&step=")[0]
                page.goto(verify_url, wait_until="domcontentloaded", timeout=20000)
                time.sleep(3.5)
                name_inp = page.locator("input:visible[placeholder*='스토리의 이름']").first
                saved = ""
                if name_inp.count() > 0:
                    saved = (name_inp.input_value() or "").strip()
                if saved:
                    print(f"   ✅ [임시저장] 완료 확인 — 새로고침 후에도 제목이 남아 있음: {saved!r}")
                    return True
                print("   ⚠️ 새로고침하니 제목이 비어 있습니다 — 저장되지 않았습니다.")
            except Exception as e:
                print(f"   ⚠️ 새로고침 검증 실패: {e}")
            print("   ⚠️ [임시저장] 버튼은 눌렀지만 저장 표시를 확인하지 못했습니다.")
            shot = os.environ.get("CRACK_SYNC_SHOT")
            if shot:
                try:
                    page.screenshot(path=shot, full_page=True)
                    print(f"      화면을 저장했습니다: {shot}")
                except Exception as e:
                    print(f"      화면 저장 실패: {e}")
            print("      크랙이 필수 항목 미입력 등으로 저장을 거부했을 수 있습니다. 브라우저 화면을 확인하세요.")
            dump_fields(page, "임시저장 확인 실패")
            return False
        except Exception as e:
            print(f"   ⚠️ [임시저장] 버튼 클릭 실패: {e}")
            shot = os.environ.get("CRACK_SYNC_SHOT")
            if shot:
                try:
                    page.screenshot(path=shot, full_page=True)
                    print(f"      화면을 저장했습니다: {shot}")
                except Exception:
                    pass
            return False
    else:
        print("   ℹ️ 화면에서 '임시저장' 버튼을 찾지 못했습니다. (자동 저장이거나 에디터 헤더에 위치)")
        return False


def clear_existing_keywords(page: Any) -> int:
    """Delete all existing keyword notes on the keyword book tab to prevent duplicate stacking."""
    print("   🧹 기존 키워드북 항목 정리(초기화) 중...")
    # 실측: 키워드 행마다 [펼치기 m5.64…][연필 M16.05…][휴지통 M15.44…] 세 버튼이
    # 반복된다. 예전 목록에는 휴지통 path 가 하나도 없어 삭제가 0개로 끝났고,
    # 그 상태로 다시 싱크하면 이미 20개가 차 있어 [키워드 노트 추가] 가
    # disabled 라 한 건도 못 넣는다.
    del_btn_selector = (
        "button:visible:has(path[d^='M15.44']), "
        "button:visible:has(path[d*='M6 19']), "
        "button:visible:has(path[d*='19 7']), "
        "button:visible:has(path[d*='M16 9']), "
        "button:visible:has(path[d*='trash']), "
        "button:visible:has(path[d*='M19 4']), "
        "button:visible:has-text('삭제'), "
        "button:visible[aria-label*='삭제'], "
        "button:visible[title*='삭제']"
    )

    deleted = 0
    # 최대 50개 항목까지 순차 삭제
    for _ in range(50):
        # 1. 화면에 보이는 삭제 버튼 탐색
        del_btns = page.locator(del_btn_selector)
        if del_btns.count() == 0:
            # 혹시 점 3개(더보기) 메뉴 안에 삭제가 있는지 확인
            more_btns = page.locator("button:visible:has(path[d*='M12 8']), button:visible:has(path[d*='M5 12'])")
            if more_btns.count() > 0:
                try:
                    more_btns.first.click(timeout=1500)
                    time.sleep(0.3)
                    del_menu = page.locator("div[role='menuitem']:has-text('삭제'), button:has-text('삭제'), li:has-text('삭제')").first
                    if del_menu.count() > 0 and del_menu.is_visible():
                        del_menu.click(timeout=2000)
                        time.sleep(0.4)
                    else:
                        break
                except Exception:
                    break
            else:
                break
        else:
            try:
                del_btns.first.click(timeout=2500)
                time.sleep(0.4)
            except Exception:
                break

        # 2. 삭제 확인 모달(Dialog) 처리
        modal_del = page.locator("div[role='dialog'] button:has-text('삭제'), div[role='dialog'] button:has-text('확인')").first
        if modal_del.count() > 0 and modal_del.is_visible():
            try:
                modal_del.click(timeout=2000)
                time.sleep(0.4)
            except Exception:
                pass

        deleted += 1
        time.sleep(0.3)

    if deleted > 0:
        print(f"   ✅ 기존 등록된 키워드 {deleted}개 삭제 완료 (초기화)")
    else:
        print("   ℹ️ 기존 등록된 키워드 없음")
    return deleted


KEYWORD_ENTRY_CAP = 20  # 실측: 21번째부터 [키워드 노트 추가] 가 disabled 로 바뀐다


def inject_keywords(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject keyword entries into keyword book tab.

    실제 DOM 플로우:
      1. '키워드북' 탭 클릭
      2. 기존 등록된 키워드 항목이 있으면 전수 삭제(초기화)
      3. '+ 키워드 노트 추가' 클릭 → 새 행 생성
      4. ✏️ 연필 버튼 클릭 → input에 제목 입력 → Enter로 확정
      5. ∨ chevron down 버튼 클릭하여 아코디언 확장
      6. 정보(본문) textarea에 content 입력
      7. 키워드 input에 tag 입력 후 Enter (기존 태그 정리 및 React 호환)
      8. ^ chevron up 버튼 클릭하여 아코디언 접기
    """
    total = len(artifacts.keyword_entries)
    print(f"\n📚 [키워드북 주입 시작] (총 {total}개 항목)")
    if total > KEYWORD_ENTRY_CAP:
        print(f"   ⚠️ 크랙 키워드북 상한은 {KEYWORD_ENTRY_CAP}개입니다 — 뒤의 {total - KEYWORD_ENTRY_CAP}개는 등록되지 않습니다.")
        print("      항목을 합치거나 덜 쓰이는 것을 빼고 다시 실행하세요.")

    # 키워드북 탭
    if not require_editor_tabs(page, "키워드북"):
        return False
    if not switch_tab(page, ["키워드북"]):
        # 예전에는 여기서 30초 타임아웃 예외가 그대로 터져 나와 세션이 통째로
        # 죽었다. 못 찾으면 화면을 덤프하고 조용히 물러난다.
        print("   ⛔ '키워드북' 탭을 찾지 못했습니다.")
        dump_fields(page, "키워드북 탭 없음")
        return False
    time.sleep(1.5)

    # 기존 항목 전수 삭제 (중복 누적 방지)
    clear_existing_keywords(page)
    time.sleep(0.8)

    added = 0
    failed: list[str] = []
    capped = False
    for i, entry in enumerate(artifacts.keyword_entries, 1):
        print(
            f"   [{i:02d}/{len(artifacts.keyword_entries):02d}] '{entry.title}' "
            f"(키워드 {len(entry.keywords)}개, 본문 {len(entry.content)}자)...",
            end=" ", flush=True,
        )
        try:
            # 1) 키워드 노트 추가 버튼 클릭
            add_btn = page.locator(
                "button:has-text('키워드 노트 추가'), button:has-text('+ 키워드 노트 추가'), button:has-text('노트 추가'), button:has-text('키워드 추가'), button:has-text('+ 추가')"
            ).first
            if add_btn.count() > 0:
                add_btn.scroll_into_view_if_needed(timeout=3000)
                if not add_btn.is_enabled():
                    # 상한에 걸리면 버튼이 disabled 로 바뀐다. 그대로 클릭하면
                    # 5초 타임아웃이 항목마다 반복되며 원인도 드러나지 않는다.
                    print(f"상한 도달 — [키워드 노트 추가] 비활성 (등록 {added}개에서 멈춤)")
                    capped = True
                    break
                add_btn.click(timeout=5000)
            time.sleep(1.0)

            # 2) ✏️ 연필 버튼 클릭하여 제목 변경
            pencil_btn = page.locator("button:has(path[d*='M16.05']), button:has(path[d*='M16.0']), button:has-text('수정')").last
            if pencil_btn.count() > 0:
                pencil_btn.click(timeout=5000)
            time.sleep(0.5)

            title_inp = page.locator("input:visible").first
            fill_react_input(page, title_inp, entry.title)
            time.sleep(0.3)
            title_inp.press("Enter")
            time.sleep(0.6)

            # 3) ∨ chevron down 버튼 클릭하여 아코디언 확장
            chevron_btn = page.locator("button:has(path[d*='M12 15']), button:has(path[d*='12 15']), button:has(path[d*='M7.41'])").last
            if chevron_btn.count() > 0:
                chevron_btn.click(timeout=5000)
            else:
                row = page.locator(f"div:has(p:has-text('{entry.title}'))").first
                if row.count() > 0:
                    row.locator("button").last.click(timeout=5000)
            time.sleep(0.8)

            # 4) 정보 (본문) textarea 입력
            info_ta = page.locator("textarea[placeholder*='엘다리스'], textarea[placeholder*='정보'], textarea:visible").last
            fill_react_input(page, info_ta, entry.content)
            time.sleep(0.3)

            # 5) 키워드 태그 input 입력 (각 태그별 focus, fill, Enter 후 잔류 텍스트 방지)
            kw_inp = page.locator("input[placeholder*='단어 입력 후 엔터'], input[placeholder*='엔터'], input:visible").last
            for kw in entry.keywords:
                kw_str = str(kw).strip()
                if not kw_str:
                    continue
                try:
                    kw_inp.click(timeout=2000)
                    time.sleep(0.05)
                    kw_inp.fill(kw_str)
                    time.sleep(0.05)
                    kw_inp.press("Enter")
                    time.sleep(0.12)
                except Exception:
                    # Fallback fill
                    fill_react_input(page, kw_inp, kw_str)
                    kw_inp.press("Enter")
                    time.sleep(0.12)
            time.sleep(0.3)

            # 6) 아코디언 접기
            chevron_up = page.locator("button:has(path[d*='M12 9']), button:has(path[d*='12 9'])").last
            if chevron_up.count() > 0:
                chevron_up.click(timeout=3000)
                time.sleep(0.4)

            print("완료")
            added += 1
        except Exception as ex:
            failed.append(entry.title)
            print(f"실패 ({ex})")

    # 예전에는 시도한 개수를 그대로 "완료" 로 찍어서, 상한에 걸려 빠진 항목이
    # 있어도 성공으로 보고했다. 실제로 들어간 것만 센다.
    if capped:
        print(f"   ⛔ 키워드북 상한({KEYWORD_ENTRY_CAP}개)에 걸려 {added}개만 등록됐습니다.")
        remaining = [e.title for e in artifacts.keyword_entries[added:]]
        if remaining:
            print(f"      누락: {', '.join(remaining)}")
        return False
    if failed:
        print(f"   ⚠️ 키워드북 {added}/{len(artifacts.keyword_entries)}개 등록 — 실패: {', '.join(failed)}")
        return False
    print(f"   ✅ 키워드북 {added}개 완료!")
    return True


def clear_existing_shortcuts(page: Any) -> int:
    """Delete existing custom shortcuts to prevent duplication upon re-sync."""
    print("   🧹 기존 단축어 항목 정리 중...")
    del_selector = (
        "button:visible:has(path[d*='M6 19']), "
        "button:visible:has(path[d*='19 7']), "
        "button:visible:has(path[d*='M16 9']), "
        "button:visible:has(path[d*='trash']), "
        "button:visible:has-text('삭제'), "
        "button:visible[aria-label*='삭제']"
    )
    deleted = 0
    for _ in range(30):
        del_btns = page.locator(del_selector)
        if del_btns.count() == 0:
            break
        try:
            del_btns.first.click(timeout=2000)
            time.sleep(0.3)
            modal_del = page.locator("div[role='dialog'] button:has-text('삭제'), div[role='dialog'] button:has-text('확인')").first
            if modal_del.count() > 0 and modal_del.is_visible():
                modal_del.click(timeout=1500)
                time.sleep(0.3)
            deleted += 1
        except Exception:
            break

    if deleted > 0:
        print(f"   ✅ 기존 단축어 {deleted}개 삭제 완료")
    return deleted


def inject_shortcuts(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject shortcuts into shortcuts tab.

    실제 DOM 플로우:
      1. '단축어' 탭 클릭
      2. 기존 단축어 정리 (중복 방지)
      3. '+ 단축어 추가' 버튼 클릭 → 드롭다운 펼침
      4. '신규 추가' (div/li, button 아님) 클릭 → 인라인 폼 생성
      5. INPUT[0]=단축어이름, INPUT[1]=설명, TEXTAREA=프롬프트 직접 채우기
      6. 별도 저장 버튼 없음 (저장은 탭 전환/완료 시 자동)
    """
    print(f"\n⚡ [단축어 주입 시작] (총 {len(artifacts.shortcuts)}개 항목)")

    # 단축어 탭
    page.locator("a:visible:has-text('단축어'), button:visible:has-text('단축어'), div[role='tab']:visible:has-text('단축어'), li:visible:has-text('단축어')").first.click()
    time.sleep(1.2)

    # 기존 단축어 정리
    clear_existing_shortcuts(page)
    time.sleep(0.5)

    for i, sc in enumerate(artifacts.shortcuts, 1):
        print(f"   [{i:02d}/{len(artifacts.shortcuts):02d}] '{sc.name}' ({sc.id})...", end=" ", flush=True)
        try:
            # 1) '+ 단축어 추가' 버튼 클릭 → 드롭다운 펼침
            add_btn = page.locator("button:has-text('단축어 추가')").first
            add_btn.click(timeout=5000)
            time.sleep(0.8)

            # 2) '신규 추가' 항목 클릭 (div/li, not button)
            new_item = page.get_by_text("신규 추가", exact=True).first
            if new_item.count() == 0:
                new_item = page.locator("text='신규 추가'").first
            new_item.click(timeout=5000)
            time.sleep(1.2)

            # 3) 인라인 폼 직접 채우기 (모달 없음)
            name_inp = page.locator("input[placeholder*='시점전환'], input[placeholder*='단축어 이름']").last
            if name_inp.count() == 0:
                name_inp = page.locator("input:visible").last
            fill_react_input(page, name_inp, sc.name)
            time.sleep(0.15)

            desc_inp = page.locator("input[placeholder*='용도'], input[placeholder*='설명해주세요']").last
            if desc_inp.count() == 0:
                desc_inp = page.locator("input:visible").nth(-2)
            fill_react_input(page, desc_inp, sc.description)
            time.sleep(0.15)

            prompt_ta = page.locator("textarea[placeholder*='프롬프트'], textarea[placeholder*='자동 주입']").last
            if prompt_ta.count() == 0:
                prompt_ta = page.locator("textarea:visible").last
            fill_react_input(page, prompt_ta, sc.prompt)
            time.sleep(0.2)

            print("완료")
        except Exception as ex:
            print(f"실패 ({ex})")

    print("   ✅ 단축어 주입 프로세스 완료!")
    return True


def inject_basic_info(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject title and short summary into 프로필 tab."""
    print("\n📝 [기본 정보 (프로필) 주입 시작]")
    if not require_editor_tabs(page, "기본 정보"):
        return False

    # 프로필 탭 클릭
    prof_tab = page.locator("a:visible:has-text('프로필'), button:visible:has-text('프로필'), div[role='tab']:visible:has-text('프로필'), li:visible:has-text('프로필')").first
    if prof_tab.count() > 0:
        prof_tab.click()
        time.sleep(1.0)

    # 작품 이름 입력 (placeholder='스토리의 이름을 입력해 주세요')
    title_inp = page.locator("input:visible[placeholder*='이름'], input:visible[placeholder*='제목'], input:visible").first
    if title_inp.count() > 0:
        fill_react_input(page, title_inp, artifacts.title)
        print(f"   ✅ [작품 제목] '{artifacts.title}' 입력 완료")

    # 작품 소개 / 한 줄 설명 (placeholder='간단한 소개를 입력해 주세요')
    desc_ta = page.locator("textarea:visible[placeholder*='소개'], textarea:visible[placeholder*='설명'], textarea:visible, div[contenteditable='true']:visible").first
    if desc_ta.count() > 0:
        summary_text = artifacts.short_summary if artifacts.short_summary else artifacts.title
        fill_react_input(page, desc_ta, summary_text)
        print(f"   ✅ [작품 한 줄 소개] '{summary_text}' 입력 완료 ({len(summary_text):,}자 / {LOGLINE_MAX}자)")
        if len(summary_text) > LOGLINE_MAX:
            print(f"   ⚠️ 한 줄 소개가 {LOGLINE_MAX}자를 넘습니다 — 목록 카드에서 잘립니다. story.md 의 '- Logline:' 을 줄이세요.")

    return True


def open_register_tab(page: Any) -> bool:
    """탭 줄 맨 끝의 [등록] 탭(step=register)을 연다.

    상단의 [등록하기] 버튼은 발행 흐름이라 절대 누르지 않는다. 좁은 창에서는
    탭이 가려지므로, 못 찾으면 URL 의 step 만 register 로 바꿔 같은 작품에 머문다.
    """
    if page.locator("textarea[placeholder*='상세한 내용']").count() > 0:
        return True
    tab = (
        page.locator("button:visible, a:visible, [role='tab']:visible")
        .filter(has_text=re.compile(r"^\s*등록\s*\*?\s*$"))
        .first
    )
    if tab.count() > 0:
        tab.click()
    else:
        url = page.url
        if "storyId=" not in url:
            print("   ⛔ storyId 가 없어 [등록] 탭을 열 수 없습니다.")
            return False
        target = re.sub(r"([?&]step=)[^&]*", r"\1register", url) if "step=" in url else url + "&step=register"
        page.goto(target, wait_until="domcontentloaded", timeout=60000)
    time.sleep(3.0)
    return page.locator("textarea[placeholder*='상세한 내용']").count() > 0


def inject_publish_info(page: Any, artifacts: ProjectArtifacts) -> bool:
    """[등록] 탭의 상세 설명 textarea 에 story-description 을 넣는다.

    상세 설명은 엔딩 설정 뒤 [다음] 이 아니라 [등록] 탭에 있다. 저장은 이후
    [임시저장] 으로 반영된다.
    """
    print("\n📋 [상세 설명 주입 시작]")
    raw_desc = (artifacts.story_description or artifacts.summary_comment or "").strip()
    if not raw_desc:
        print("   ⚠️ story-description.md 가 비어 있어 건너뜁니다.")
        return False
    if crack_len(raw_desc) > DESCRIPTION_MAX:
        print(f"   ⚠️ 상세 설명이 {DESCRIPTION_MAX:,}자를 넘습니다 ({crack_len(raw_desc):,}자) — 크랙이 잘라냅니다.")
    if not open_register_tab(page):
        print("   ⚠️ [등록] 탭에서 상세 설명 textarea를 찾지 못했습니다.")
        return False
    detail_ta = page.locator("textarea[placeholder*='상세한 내용'], textarea[placeholder*='스토리의 성격']").first
    fill_react_input(page, detail_ta, raw_desc)
    time.sleep(0.5)
    got = detail_ta.input_value()
    if got.strip() == raw_desc:
        print(f"   ✅ [상세 설명] 주입 완료 ({len(raw_desc):,}자) — [등록] 탭")
    else:
        print(f"   ⚠️ [상세 설명] 값이 다르게 들어갔습니다 ({len(got):,}자 / 기대 {len(raw_desc):,}자)")
    return True


def _mark_register_block(page: Any, heading: str, needle: str) -> str | None:
    """제목 글자(`장르 설정` 등)에서 위로 올라가 needle 을 품은 가장 가까운 칸을 표시한다.

    이 탭의 칸들은 data-slot 구조가 제각각이라 공통 컨테이너 선택자가 없다.
    제목에서 출발하면 크랙이 칸 순서를 바꿔도 엉뚱한 콤보박스를 잡지 않는다.
    """
    token = "crk-" + re.sub(r"\W", "", heading)
    found = page.evaluate(
        r"""([h, needle, tok]) => {
            const s = [...document.querySelectorAll('p,span,label')]
              .find(e => e.children.length === 0 && e.innerText.trim() === h);
            if (!s) return false;
            let el = s;
            for (let i = 0; i < 8 && el; i++) {
              el = el.parentElement;
              if (!el) break;
              const hit = needle.startsWith('text:') ? el.innerText.includes(needle.slice(5)) : !!el.querySelector(needle);
              if (hit) { el.setAttribute('data-crack-sync', tok); return true; }
            }
            return false;
        }""",
        [heading, needle, token],
    )
    return f"[data-crack-sync='{token}']" if found else None


_FIRST_LEAF_JS = r"""(el) => {
    const leaves = [...el.querySelectorAll('*')].filter(x => x.children.length === 0)
      .map(x => (x.innerText || x.textContent || '').trim()).filter(Boolean);
    return leaves.length ? leaves[0] : (el.innerText || '').trim();
}"""


def _select_register_combobox(page: Any, heading: str, value: str, label: str) -> bool:
    """콤보박스를 열어 첫 줄 글자가 value 와 같은 선택지를 고르고, 닫힌 뒤 다시 읽어 확인한다.

    선택지 안에는 설명·가격 줄이 붙어 있어(`하이퍼챗 1.0` + `102개` + 설명) 전체 글자로
    맞추면 `슈퍼챗 2` 가 `슈퍼챗 2.5` 에 걸린다. 첫 줄만 정확히 비교한다.
    """
    blk = _mark_register_block(page, heading, "[role='combobox']")
    if not blk:
        print(f"   ⚠️ [{label}] 칸을 찾지 못했습니다.")
        return False
    box = page.locator(blk).locator("[role='combobox']").first
    if box.evaluate(_FIRST_LEAF_JS) == value:
        print(f"   ✅ [{label}] 이미 '{value}'")
        return True
    box.scroll_into_view_if_needed()
    box.click()
    time.sleep(1.2)
    names = page.locator("[role='option']").evaluate_all(
        "(os) => os.filter(o => o.offsetParent).map(o => { const l=[...o.querySelectorAll('*')].filter(x=>x.children.length===0).map(x=>(x.innerText || x.textContent || '').trim()).filter(Boolean); return l.length ? l[0] : (o.innerText || '').trim(); })"
    )
    if value not in names:
        page.keyboard.press("Escape")
        print(f"   ⚠️ [{label}] '{value}' 선택지가 없습니다. 현재 선택지: {' · '.join(names)}")
        return False
    page.locator("[role='option']:visible").nth(names.index(value)).click()
    time.sleep(1.0)
    got = box.evaluate(_FIRST_LEAF_JS)
    if got == value:
        print(f"   ✅ [{label}] '{value}' 선택")
        return True
    print(f"   ⚠️ [{label}] '{value}' 를 골랐지만 칸에는 '{got}' 로 보입니다.")
    return False


def _set_register_max_output(page: Any, value: str) -> bool:
    blk = _mark_register_block(page, "권장 최대 출력량", "text:5x")
    if not blk:
        print("   ⚠️ [권장 최대 출력량] 칸을 찾지 못했습니다.")
        return False
    area = page.locator(blk)
    bulk = area.get_by_text("일괄 설정", exact=True)
    if bulk.count() > 0:
        try:
            bulk.first.click()
            time.sleep(0.5)
        except Exception:
            pass
    choice = area.get_by_text(value, exact=True)
    if choice.count() == 0:
        print(f"   ⚠️ [권장 최대 출력량] '{value}' 선택지를 찾지 못했습니다.")
        return False
    choice.first.click()
    time.sleep(0.6)
    print(f"   ✅ [권장 최대 출력량] '{value}' 클릭 (일괄 설정)")
    return True


def _set_register_hashtags(page: Any, tags: list[str]) -> bool:
    blk = _mark_register_block(page, "해시태그", "input[type='text']")
    if not blk:
        print("   ⚠️ [해시태그] 칸을 찾지 못했습니다.")
        return False
    area = page.locator(blk)
    read_chips = lambda: [x.strip().lstrip("#") for x in area.locator("span:has(> button) > span").all_inner_texts()]
    want = tags[:HASHTAG_MAX_COUNT]
    if read_chips() == want:
        print(f"   ✅ [해시태그] 이미 같음 ({len(want)}개)")
        return True
    # 기존 칩은 전부 지우고 선언 순서대로 다시 넣는다. 일부만 맞추면 순서가 섞인다.
    for _ in range(HASHTAG_MAX_COUNT + 2):
        dels = area.locator("span:has(> button) > button")
        if dels.count() == 0:
            break
        dels.first.click()
        time.sleep(0.3)
    inp = area.locator("input[type='text']").first
    for tag in want:
        inp.click()
        inp.fill(tag)
        inp.press("Enter")
        time.sleep(0.4)
    got = read_chips()
    if got == want:
        print(f"   ✅ [해시태그] {' '.join('#' + x for x in got)} ({len(got)}개)")
        return True
    print(f"   ⚠️ [해시태그] 기대 {want} / 실제 {got}")
    return False


def inject_register_settings(page: Any, artifacts: ProjectArtifacts) -> bool:
    """story.md 에 선언된 [등록] 탭 설정만 반영한다. 선언이 없으면 아무것도 바꾸지 않는다.

    이용자 층은 크랙이 "한번 설정하면 변경할 수 없어요" 라고 못박은 항목이라
    잘못 넣으면 되돌릴 수 없다. 도구는 설정하지 않고 알리기만 한다.
    """
    reg = artifacts.register
    print("\n🏷️ [등록 탭 설정 주입 시작]")
    if not reg:
        print("   ℹ️ story.md 에 등록 설정 선언이 없어 건너뜁니다 (- Genre: / - Target: / - Chat form: / - Hashtags: …).")
        return True
    for problem in register_violations(reg):
        print(f"   ⚠️ {problem}")
    if not open_register_tab(page):
        print("   ⚠️ [등록] 탭을 열지 못했습니다.")
        return False
    ok = True
    for key, heading, label in (("genre", "장르 설정", "장르"), ("target", "타겟 설정", "타겟"),
                                ("chat_form", "대화 형태 설정", "대화 형태"), ("mode", "권장 모드", "권장 모드")):
        if key in reg:
            ok = _select_register_combobox(page, heading, reg[key], label) and ok
    if "max_output" in reg:
        ok = _set_register_max_output(page, reg["max_output"]) and ok
    if "hashtags" in reg:
        ok = _set_register_hashtags(page, reg["hashtags"]) and ok
    if "audience" in reg:
        print(f"   ℹ️ [이용자 층] 선언값 '{reg['audience']}' — 크랙에서 한 번 정하면 바꿀 수 없어 도구가 설정하지 않습니다. 필요하면 브라우저에서 직접 고르세요.")
    return ok


def navigate_to_create_story(page: Any) -> bool:
    """Safely navigate from https://crack.wrtn.ai to '내 작품' -> '작품 만들기'."""
    print("\n🧭 [에디터 진입 탐색 시작]")

    # Check if already inside editor
    has_editor = (
        page.locator(
            "button:visible:has-text('프롬프트'), button:visible:has-text('키워드북'), div[role='tab']:visible:has-text('프롬프트')"
        ).count()
        > 0
    )
    if has_editor:
        print("   ✅ 이미 에디터 화면에 진입되어 있습니다.")
        return True

    # 1. '내 작품' 메뉴 찾아서 클릭
    print("   🔍 1단계: '내 작품' 메뉴 탐색 중...")
    my_works = page.locator(
        "button:visible:has-text('내 작품'), a:visible:has-text('내 작품'), div[role='tab']:visible:has-text('내 작품'), span:visible:has-text('내 작품')"
    )
    if my_works.count() > 0:
        try:
            my_works.first.click()
            time.sleep(1.5)
            print("   ✅ '내 작품' 메뉴 클릭 완료")
        except Exception:
            pass

    # 2. '작품 만들기' 버튼 찾아서 클릭
    print("   🔍 2단계: '작품 만들기' 버튼 탐색 중...")
    create_btn = page.locator(
        "button:visible:has-text('작품 만들기'), a:visible:has-text('작품 만들기'), button:visible:has-text('새 작품'), div[role='button']:visible:has-text('작품 만들기')"
    )
    if create_btn.count() > 0:
        try:
            create_btn.first.click()
            time.sleep(1.5)
            print("   ✅ '작품 만들기' 버튼 클릭 완료")
        except Exception as e:
            print(f"   ⚠️ '작품 만들기' 클릭 실패: {e}")

    # 3. '스토리' 선택 클릭
    print("   🔍 3단계: '스토리' 타입 선택 중...")
    story_btn = page.locator(
        "button:visible:has-text('스토리'), div[role='button']:visible:has-text('스토리'), a:visible:has-text('스토리'), p:visible:has-text('스토리')"
    )
    if story_btn.count() > 0:
        try:
            for idx in range(story_btn.count()):
                el = story_btn.nth(idx)
                txt = el.inner_text().strip()
                if "스토리" in txt and len(txt) < 25:
                    el.click(timeout=2000)
                    time.sleep(2.5)
                    print("   ✅ '스토리' 선택 완료 -> 에디터 진입!")
                    return True
        except Exception:
            pass

    return True


def complete_profile_step(page: Any, artifacts: "ProjectArtifacts") -> bool:
    """프로필 단계를 채우고 [다음] 을 눌러 storyId 를 발급받는다.

    이 단계를 건너뛰면 작품 레코드가 생기지 않는다. 값만 채워 넣고 [임시저장]
    을 눌러도 저장할 대상이 없어 조용히 실패하며, 화면상으로는 눌린 것처럼
    보인다. 실제로 이 누락 때문에 주입한 작업이 통째로 사라졌다.
    """
    print("\n🧾 [프로필 단계 — storyId 발급]")
    ensure_required_basics(page, artifacts)
    nxt = page.locator("button:visible:has-text('다음')").first
    # URL 의 storyId 를 발급 완료로 보면 안 된다. 생성 단계에서는 레코드가 생기기
    # 전에도 임시 storyId 가 붙어 있어서, 그걸 믿고 프로필을 건너뛰면 작품이
    # 만들어지지 않은 채 주입만 쌓이고 저장할 때 "스토리를 찾을 수 없습니다" 가 난다.
    # [다음] 이 아직 화면에 있으면 프로필 단계가 끝나지 않은 것이다.
    if nxt.count() == 0:
        if "storyId=" in page.url:
            print(f"   ✅ 프로필 단계 완료 — {page.url}")
            return True
        # 예전에는 여기서 True 를 돌려주고 계속 진행했다. 그러면 탭이 없는
        # 화면에 주입을 시작해 '탭 못 찾음' 경고만 쌓다가 키워드북에서
        # 타임아웃으로 죽었다. 없으면 없다고 말하고 멈춘다.
        print("   ⛔ [다음] 버튼도 없고 storyId 도 없습니다 — 프로필 단계가 끝나지 않았습니다.")
        dump_fields(page, "프로필 미완료")
        return False
    print("   ℹ️ [다음] 이 남아 있어 프로필 단계를 진행합니다.")
    for attempt in (1, 2):
        try:
            nxt.click()
        except Exception as e:
            print(f"   ⚠️ [다음] 클릭 실패 ({attempt}회): {e}")
        time.sleep(4.0)
        if "storyId=" in page.url:
            print(f"   ✅ storyId 발급됨 — {page.url}")
            return True
    print("   ⛔ [다음] 을 눌렀지만 storyId 가 생기지 않았습니다.")
    dump_fields(page, "storyId 발급 실패")
    return False


def auto_navigate_and_inject_all(page: Any, artifacts: ProjectArtifacts) -> None:
    """Detect page state, enter editor via '내 작품' -> '작품 만들기', and inject all tabs."""
    print("\n===========================================================================")
    print("🚀 [전체 일괄 자동 주입 모드 실행]")
    print("===========================================================================")

    # 1. 내 작품 -> 작품 만들기 진입
    navigate_to_create_story(page)
    time.sleep(1)

    # 1.5 프로필 단계를 끝내야 storyId 가 나온다. 이게 없으면 이후 주입은
    # 저장되지 않는 세션에 쌓이고, 새로고침하는 순간 전부 사라진다.
    if not complete_profile_step(page, artifacts):
        print("\n⛔ 프로필 단계가 끝나지 않아 이후 주입을 중단합니다.")
        print("   스토리 설정·시작 설정·키워드북 탭은 storyId 가 발급돼야 열립니다.")
        print("   제목·한 줄 소개·대표 이미지를 채우고 [다음] 을 누른 뒤 다시 실행하세요.")
        print("   대표 이미지는 CRACK_SYNC_THUMBNAIL=<1080x1620 이미지> 로 지정할 수 있습니다.")
        return
    time.sleep(1)

    # 2. 기본 정보 주입
    inject_basic_info(page, artifacts)
    time.sleep(0.5)

    # 3. 프롬프트 3종 주입
    inject_prompts(page, artifacts)
    time.sleep(0.5)

    # 4. 키워드북 주입
    inject_keywords(page, artifacts)
    time.sleep(0.5)

    # 5. 단축어 주입
    inject_shortcuts(page, artifacts)
    time.sleep(0.5)

    # 6. [등록] 탭: 상세 설명 + 장르·타겟·대화 형태·권장 모드·출력량·해시태그
    inject_publish_info(page, artifacts)
    inject_register_settings(page, artifacts)
    time.sleep(0.5)

    # 신규 생성 모드에서 이 주소를 안 찍으면, 다음에 같은 작품을 다시 싱크할
    # 방법이 없어 매번 새 작품이 하나씩 늘어난다.
    try:
        print(f"\n🔗 이 작품의 에디터 주소: {page.url}")
        print("   다음부터는 `--url '위 주소'` 로 같은 작품을 갱신하세요.")
    except Exception:
        pass
    print("\n🎉 모든 산출물 주입 완료! 브라우저 창에서 검토 후 [임시저장] 또는 [발행]을 진행하세요.")


DEFAULT_PROFILE_DIR = Path.home() / ".crack" / "profile"
DEFAULT_LOGIN_URL = "https://crack.wrtn.ai"


def run_auth(login_url: str = DEFAULT_LOGIN_URL, profile_dir: Path = DEFAULT_PROFILE_DIR) -> int:
    """Launch persistent browser profile for 1-time login."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다.", file=sys.stderr)
        return 1

    profile_dir.mkdir(parents=True, exist_ok=True)
    print("=" * 70)
    print(f"🔑 크랙(Crack) 영구 브라우저 프로필 로그인 모드")
    print(f"저장 경로: {profile_dir}")
    print("브라우저 창에서 로그인하시면 이후 모든 실행에서 로그인이 영구 유지됩니다.")
    print("=" * 70)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=False,
            slow_mo=50,
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(login_url)

        print("\n👉 브라우저 창에서 크랙 로그인을 완료해 주세요...")
        print("💡 로그인이 끝나면 언제든 브라우저를 닫거나 콘솔에서 [Enter]를 누르시면 됩니다.")

        try:
            input("\n👉 로그인을 완료한 후 여기서 [Enter]를 누르세요...")
        except (KeyboardInterrupt, EOFError):
            pass

        print(f"\n✅ 로그인 프로필이 영구 저장되었습니다! ({profile_dir})")
        context.close()

    return 0


def run_sync(
    project_dir: Path,
    target_url: str,
    variant: str = "safe",
    profile_dir: Path = DEFAULT_PROFILE_DIR,
    headed: bool = True,
    dry_run: bool = False,
    auto_inject: bool = False,
    auto_submit: bool = False,
    title_suffix: str = "",
) -> int:
    """Execute Playwright automation with persistent browser profile."""
    global TITLE_SUFFIX
    TITLE_SUFFIX = title_suffix
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다.", file=sys.stderr)
        return 1

    artifacts = load_project_artifacts(project_dir, variant=variant)
    profile_dir.mkdir(parents=True, exist_ok=True)

    is_existing_project = "projects/" in target_url
    print("=" * 75)
    print(f"🚀 크랙 스튜디오 자동 입력 도구 실행: {artifacts.title} ({variant.upper()})")
    if is_existing_project:
        print(f"🔗 실행 모드: [기존 프로젝트 로드 & 재주입] (URL: {target_url})")
    else:
        print("🔗 실행 모드: [신규 스토리 생성] (URL 생략 시 크랙 스튜디오에서 자동 신규 생성)")
    print(f"📝 한 줄 소개: '{artifacts.short_summary}' ({len(artifacts.short_summary)}자)")
    print(f"🖥️ 헤디드 브라우저: {'켜짐 (영구 상주 모드)' if headed else '백그라운드 (Headless)'}")
    print(f"📁 브라우저 프로필: {profile_dir} (영구 로그인 유지)")
    print("=" * 75)

    if dry_run:
        print("🔍 [DRY-RUN] 실제 주입 없이 검사만 완료하고 종료합니다.")
        return run_inspect(project_dir, variant=variant)

    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=not headed,
            slow_mo=50,
        )
        page = context.pages[0] if context.pages else context.new_page()

        print("🌐 크랙 페이지 로딩 중...")
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"⚠️ 페이지 로드 경고: {e}")

        time.sleep(1)

        # 신규 생성 모드인 경우 자동으로 '내 작품' -> '작품 만들기' -> '스토리' 진입
        if not is_existing_project:
            navigate_to_create_story(page)
            time.sleep(1)

        # --auto 플래그 지정 시 즉시 주입 실행
        if auto_inject:
            print("\n⚡ [--auto 플래그 감지] 즉시 전체 자동 주입을 실행합니다...")
            time.sleep(1.5)
            auto_navigate_and_inject_all(page, artifacts)
        # --auto-submit 은 --auto 없이도 동작해야 한다. 저장만 다시 시도하고
        # 싶을 때가 있고, 가둬 두면 플래그를 줬는데 아무 일도 안 일어난다.
        if auto_submit:
            time.sleep(1.5)
            save_crack_draft(page, artifacts)

        # -------------------------------------------------------------
        # 상호작용 상주 루프 (Interactive Session Loop / Hot-Reload)
        # -------------------------------------------------------------
        current_variant = variant
        print("\n" + "=" * 75)
        print("💡 크랙 브라우저가 열렸습니다! 원하는 에디터 페이지로 이동한 뒤 아래 명령을 입력하세요.")
        print("===========================================================================")
        print("  [a] 전체 일괄 자동 주입 (기본정보 ➡️ 프롬프트 ➡️ 키워드북 ➡️ 단축어)")
        print("  [w] 임시저장(Draft Save) 실행")
        print("  [p] 현재 화면에 프롬프트 3종(프롤로그·시작·시스템) 주입")
        print("  [k] 키워드북 일괄 주입")
        print("  [s] 단축어 일괄 주입")
        print("  [i] 기본 정보(제목·한 줄 소개) 주입")
        print("  [g] [등록] 탭 주입 (상세 설명·장르·타겟·대화 형태·권장 모드·출력량·해시태그)")
        print("  [d] 현재 페이지의 버튼/입력창 DOM 목록 분석 (디버깅)")
        print("  [v] SAFE ↔ UNSAFE 프롬프트 버전 전환")
        print("  [r] 로컬 산출물 파일 다시 읽기")
        print("  [q] 브라우저 닫기 및 종료 (Quit)")
        print("===========================================================================")

        if not headed:
            if not auto_inject:
                auto_navigate_and_inject_all(page, artifacts)
            if auto_submit:
                time.sleep(1.5)
                save_crack_draft(page, artifacts)
            context.close()
            return 0

        while True:
            try:
                cmd = input("\n👉 명령을 입력하세요 [a(전체주입) / w(임시저장) / p(프롬프트) / k(키워드북) / s(단축어) / d(DOM분석) / q(종료)]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n👋 세션을 종료합니다.")
                break

            if cmd in ("q", "quit", "exit"):
                print("👋 브라우저를 닫고 프로그램을 종료합니다.")
                break
            elif cmd in ("w", "save", "draft"):
                save_crack_draft(page, artifacts)
            elif cmd in ("a", "all", "sync"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                auto_navigate_and_inject_all(page, artifacts)
                if auto_submit:
                    time.sleep(1.5)
                    save_crack_draft(page, artifacts)
            elif cmd in ("p", "prompt", "prompts"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                inject_prompts(page, artifacts)
            elif cmd in ("k", "keyword", "keywords", "kb"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                inject_keywords(page, artifacts)
            elif cmd in ("s", "shortcut", "shortcuts", "sc"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                inject_shortcuts(page, artifacts)
            elif cmd in ("i", "info", "basic"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                inject_basic_info(page, artifacts)
            elif cmd in ("g", "reg", "publish", "detail"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                inject_publish_info(page, artifacts)
                inject_register_settings(page, artifacts)
            elif cmd in ("d", "dom", "debug", "inspect"):
                dump_dom_summary(page)
            elif cmd in ("r", "reload"):
                print(f"\n🔄 로컬 산출물을 다시 파싱했습니다 ({current_variant.upper()})")
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
            elif cmd in ("v", "variant"):
                current_variant = "unsafe" if current_variant == "safe" else "safe"
                print(f"\n🔀 시스템 프롬프트 버전을 [{current_variant.upper()}]로 전환했습니다.")
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
            elif not cmd:
                continue
            else:
                print(f"⚠️ 알 수 없는 명령입니다: {cmd} (a, w, p, k, s, i, g, d, v, r, q 중 선택)")

        context.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Crack Story Chat Playwright Automation Sync Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # auth
    auth_parser = subparsers.add_parser("auth", help="Interactive 1-time login session capture")
    auth_parser.add_argument("--url", default=DEFAULT_LOGIN_URL, help="Login page URL")
    auth_parser.add_argument("--profile-dir", default=DEFAULT_PROFILE_DIR, type=Path, help="Browser profile dir path")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect and preview artifact field mapping")
    inspect_parser.add_argument("project", type=Path, help="Project directory path (e.g. examples/hunter)")
    inspect_parser.add_argument("--variant", choices=["safe", "unsafe"], default="safe", help="Prompt variant")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Auto-fill artifacts into Crack editor page and keep open")
    sync_parser.add_argument("project", type=Path, help="Project directory path (e.g. examples/hunter)")
    sync_parser.add_argument("--url", default=DEFAULT_LOGIN_URL, help="Crack story editor URL")
    sync_parser.add_argument("--variant", choices=["safe", "unsafe"], default="safe", help="Prompt variant (safe/unsafe)")
    sync_parser.add_argument("--profile-dir", default=DEFAULT_PROFILE_DIR, type=Path, help="Browser profile dir path")
    sync_parser.add_argument("--headless", action="store_true", help="Run in headless mode (default is headed)")
    sync_parser.add_argument("--dry-run", action="store_true", help="Inspect without opening browser")
    sync_parser.add_argument("--auto", action="store_true", help="Automatically inject upon start")
    sync_parser.add_argument("--auto-submit", action="store_true", help="Automatically click save/submit button")
    sync_parser.add_argument("--title-suffix", default="",
                             help="제목 뒤에 붙일 문자열. UNSAFE 판을 별도 작품으로 임시저장할 때 쓴다 (예: --title-suffix ' U')")

    args = parser.parse_args()

    if args.command == "auth":
        return run_auth(login_url=args.url, profile_dir=args.profile_dir)
    elif args.command == "inspect":
        return run_inspect(project_dir=args.project, variant=args.variant)
    elif args.command == "sync":
        return run_sync(
            project_dir=args.project,
            target_url=args.url,
            variant=args.variant,
            profile_dir=args.profile_dir,
            headed=not args.headless,
            dry_run=args.dry_run,
            auto_inject=args.auto,
            auto_submit=args.auto_submit,
            title_suffix=args.title_suffix,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())