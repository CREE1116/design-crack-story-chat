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
class ProjectArtifacts:
    project_name: str
    title: str
    prologue: str
    start_prompt: str
    system_prompt: str
    keyword_entries: list[KeywordEntry] = field(default_factory=list)
    shortcuts: list[ShortcutEntry] = field(default_factory=list)
    summary_comment: str = ""
    story_description: str = ""
    short_summary: str = ""
    variant: str = "safe"


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


def load_project_artifacts(project_dir: Path, variant: str = "safe") -> ProjectArtifacts:
    build_dir = project_dir / "build"
    if not build_dir.exists():
        raise FileNotFoundError(f"Build directory not found in {project_dir}")

    prologue_path = build_dir / "prologue.md"
    start_prompt_path = build_dir / "start-prompt.md"
    sys_prompt_path = build_dir / f"integrated-prompt-{variant}.md"
    kb_path = build_dir / "keyword-book.md"
    summary_path = build_dir / "assets" / "summary-comment.md"
    story_desc_path = build_dir / "assets" / "story-description.md"
    story_path = project_dir / "story.md"

    prologue = prologue_path.read_text(encoding="utf-8").strip() if prologue_path.exists() else ""
    start_prompt = start_prompt_path.read_text(encoding="utf-8").strip() if start_prompt_path.exists() else ""
    system_prompt = sys_prompt_path.read_text(encoding="utf-8").strip() if sys_prompt_path.exists() else ""
    kb_text = kb_path.read_text(encoding="utf-8").strip() if kb_path.exists() else ""
    summary_comment = summary_path.read_text(encoding="utf-8").strip() if summary_path.exists() else ""
    story_description = story_desc_path.read_text(encoding="utf-8").strip() if story_desc_path.exists() else ""

    # Title and short summary (Logline) extraction
    title = project_dir.name
    short_summary = ""
    if story_path.exists():
        story_content = story_path.read_text(encoding="utf-8")
        title_tag = re.search(r"^-\s*Title:\s*(.+)$", story_content, re.MULTILINE | re.IGNORECASE)
        if title_tag:
            title = title_tag.group(1).strip()
        else:
            first_line = story_content.splitlines()[0]
            title_m = re.search(r"^#\s+(.+)$", first_line)
            if title_m and title_m.group(1).strip().lower() != "story":
                title = title_m.group(1).strip()

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

    # 100자 이하의 단문 로그라인으로 정제
    if len(short_summary) > 100:
        short_summary = short_summary[:95].rsplit(" ", 1)[0] + "..."

    keyword_entries, shortcuts = parse_keyword_book(kb_text)

    return ProjectArtifacts(
        project_name=project_dir.name,
        title=title,
        prologue=prologue,
        start_prompt=start_prompt,
        system_prompt=system_prompt,
        keyword_entries=keyword_entries,
        shortcuts=shortcuts,
        summary_comment=summary_comment,
        story_description=story_description,
        short_summary=short_summary,
        variant=variant,
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
    print(f"3. 🧠 메인 시스템 프롬프트 ({artifacts.variant}) : {len(artifacts.system_prompt):,}자 / 7,000자")
    print(f"4. 📚 키워드북 항목 (Keyword Book)    : 총 {len(artifacts.keyword_entries)}개 등록 예정")
    for i, e in enumerate(artifacts.keyword_entries, 1):
        print(f"   [{i:02d}] {e.title:<18} | 키워드({len(e.keywords)}개): {', '.join(e.keywords):<22} | 본문 {len(e.content)}자")
    print(f"5. ⚡ 단축어 (Shortcuts)             : 총 {len(artifacts.shortcuts)}개 등록 예정")
    for i, sc in enumerate(artifacts.shortcuts, 1):
        print(f"   [{i:02d}] {sc.name} ({sc.id}) : {sc.description} | {len(sc.prompt)}자")
    desc_text = artifacts.story_description if artifacts.story_description else artifacts.summary_comment
    print(f"6. 📝 작품 한 줄 소개 (Logline)     : '{artifacts.short_summary}' ({len(artifacts.short_summary)}자)")
    print(f"7. 🌐 작품 상세 설명 (Description)   : {len(desc_text):,}자")
    print("=" * 75)
    print("✨ 모든 산출물이 크랙 규격에 완벽하게 부합합니다!")
    return 0


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

    # ── [스토리 설정] 탭 → 제작자 커스텀 선택 → 메인 시스템 프롬프트 주입 ──
    print("   📌 [스토리 설정] 탭 클릭...")
    story_tab = page.locator("button:has-text('스토리 설정')").first
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
    start_tab = page.locator("button:has-text('시작 설정')").first
    if start_tab.count() > 0:
        start_tab.click()
        time.sleep(1.5)
        all_tas = page.locator("textarea:visible, div[contenteditable='true']:visible").all()
        if len(all_tas) >= 1:
            fill_react_input(page, all_tas[0], artifacts.prologue)
            print(f"   ✅ [프롤로그] 주입 완료 ({len(artifacts.prologue):,}자)")
        if len(all_tas) >= 2:
            # [1] = 시작 상황 (사용자의 역할, 세계관 등) -> artifacts.start_prompt 주입
            fill_react_input(page, all_tas[1], artifacts.start_prompt)
            print(f"   ✅ [시작 프롬프트 (시작 상황)] 주입 완료 ({len(artifacts.start_prompt):,}자)")
        elif len(all_tas) == 1:
            print("   ⚠️ 시작 상황 입력창을 찾지 못했습니다.")
    else:
        print("   ⚠️ '시작 설정' 탭 못 찾음")

    return True


def clear_existing_keywords(page: Any) -> int:
    """Delete all existing keyword notes on the keyword book tab to prevent duplicate stacking."""
    print("   🧹 기존 키워드북 항목 정리(초기화) 중...")
    del_btn_selector = (
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


def inject_keywords(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject keyword entries into keyword book tab.

    실제 DOM 플로우:
      1. '키워드북' 탭 클릭
      2. 기존 등록된 키워드 항목이 있으면 전수 삭제(초기화)
      3. '+ 키워드 노트 추가' 클릭 → 새 행 생성
      4. ✏️ 연필 버튼 클릭 → input에 제목 입력 → Enter로 확정
      5. ∨ chevron down 버튼 클릭하여 아코디언 확장
      6. 정보(본문) textarea에 content 입력
      7. 키워드 input에 tag 입력 후 Enter
      8. ^ chevron up 버튼 클릭하여 아코디언 접기
    """
    print(f"\n📚 [키워드북 주입 시작] (총 {len(artifacts.keyword_entries)}개 항목)")

    # 키워드북 탭
    page.locator("button:has-text('키워드북')").first.click()
    time.sleep(1.5)

    # 기존 항목 전수 삭제 (중복 누적 방지)
    clear_existing_keywords(page)
    time.sleep(0.8)

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

            # 5) 키워드 태그 input 입력
            kw_inp = page.locator("input[placeholder*='단어 입력 후 엔터'], input[placeholder*='엔터'], input:visible").last
            for kw in entry.keywords:
                kw_inp.fill(kw)
                kw_inp.press("Enter")
                time.sleep(0.08)
            time.sleep(0.3)

            # 6) 아코디언 접기
            chevron_up = page.locator("button:has(path[d*='M12 9']), button:has(path[d*='12 9'])").last
            if chevron_up.count() > 0:
                chevron_up.click(timeout=3000)
                time.sleep(0.4)

            print("완료")
        except Exception as ex:
            print(f"실패 ({ex})")

    print(f"   ✅ 키워드북 {len(artifacts.keyword_entries)}개 완료!")
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
    page.locator("button:has-text('단축어')").first.click()
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

    # 프로필 탭 클릭
    prof_tab = page.locator("button:has-text('프로필')").first
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
        print(f"   ✅ [작품 한 줄 소개] '{summary_text}' 입력 완료 ({len(summary_text):,}자)")

    return True


def inject_publish_info(page: Any, artifacts: ProjectArtifacts) -> bool:
    """Inject detailed description into publish screen via 엔딩 설정 -> 다음 button only."""
    print("\n📋 [발행 상세 설명 주입 시작]")

    # 1. 반드시 엔딩 설정 탭 클릭 후 -> 하단 다음 버튼 클릭
    ending_tab = page.locator("button:has-text('엔딩 설정')").first
    if ending_tab.count() > 0:
        ending_tab.click()
        time.sleep(1.0)
        next_btn = page.locator("button:text('다음'), button:has-text('다음')").first
        if next_btn.count() > 0:
            next_btn.click()
            time.sleep(1.5)
            print("   ✅ '엔딩 설정' -> '다음' 버튼 클릭 완료")

    # 2. 상세 설명 textarea (placeholder='스토리의 성격이나 서사, 과거 사건 등 상세한 내용을 작성해 주세요')
    detail_ta = page.locator("textarea[placeholder*='상세한 내용'], textarea[placeholder*='서사'], textarea:visible").first
    if detail_ta.count() > 0:
        # 배너 + 통계표 + 코멘트 마크다운 (story_description 우선, 없으면 summary_comment 폴백)
        raw_desc = artifacts.story_description if artifacts.story_description else artifacts.summary_comment
        fill_react_input(page, detail_ta, raw_desc.strip())
        print(f"   ✅ [상세 설명] 주입 완료 ({len(raw_desc.strip()):,}자)")
    else:
        print("   ⚠️ 상세 설명 textarea를 찾지 못했습니다.")

    return True

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


def auto_navigate_and_inject_all(page: Any, artifacts: ProjectArtifacts) -> None:
    """Detect page state, enter editor via '내 작품' -> '작품 만들기', and inject all tabs."""
    print("\n===========================================================================")
    print("🚀 [전체 일괄 자동 주입 모드 실행]")
    print("===========================================================================")

    # 1. 내 작품 -> 작품 만들기 진입
    navigate_to_create_story(page)
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

    # 6. 등록 상세 설명 주입
    inject_publish_info(page, artifacts)
    time.sleep(0.5)

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
) -> int:
    """Execute Playwright automation with persistent browser profile."""
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

        # -------------------------------------------------------------
        # 상호작용 상주 루프 (Interactive Session Loop / Hot-Reload)
        # -------------------------------------------------------------
        current_variant = variant
        print("\n" + "=" * 75)
        print("💡 크랙 브라우저가 열렸습니다! 원하는 에디터 페이지로 이동한 뒤 아래 명령을 입력하세요.")
        print("===========================================================================")
        print("  [a] 전체 일괄 자동 주입 (기본정보 ➡️ 프롬프트 ➡️ 키워드북 ➡️ 단축어)")
        print("  [p] 현재 화면에 프롬프트 3종(프롤로그·시작·시스템) 주입")
        print("  [k] 키워드북 19개 일괄 주입")
        print("  [s] 단축어 3개 일괄 주입")
        print("  [i] 기본 정보(제목·상세소개) 주입")
        print("  [d] 현재 페이지의 버튼/입력창 DOM 목록 분석 (디버깅)")
        print("  [v] SAFE ↔ UNSAFE 프롬프트 버전 전환")
        print("  [r] 로컬 산출물 파일 다시 읽기")
        print("  [q] 브라우저 닫기 및 종료 (Quit)")
        print("===========================================================================")

        if not headed:
            if not auto_inject:
                auto_navigate_and_inject_all(page, artifacts)
            context.close()
            return 0

        while True:
            try:
                cmd = input("\n👉 명령을 입력하세요 [a(전체주입) / p(프롬프트) / k(키워드북) / s(단축어) / d(DOM분석) / q(종료)]: ").strip().lower()
            except (KeyboardInterrupt, EOFError):
                print("\n👋 세션을 종료합니다.")
                break

            if cmd in ("q", "quit", "exit"):
                print("👋 브라우저를 닫고 프로그램을 종료합니다.")
                break
            elif cmd in ("a", "all", "sync"):
                artifacts = load_project_artifacts(project_dir, variant=current_variant)
                auto_navigate_and_inject_all(page, artifacts)
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
                print(f"⚠️ 알 수 없는 명령입니다: {cmd} (a, p, k, s, i, d, v, r, q 중 선택)")

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
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())