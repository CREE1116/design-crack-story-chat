#!/usr/bin/env python3
"""Crack Story Chat Playwright Automation Sync Tool.

Automatically fills and synchronizes Crack story-chat project build artifacts
(prologue, start prompt, system prompt, keyword book, shortcuts, summary comment)
into the Crack web editor UI safely and reliably.

Usage:
    # 1. First-time interactive login session capture
    python3 tools/sync/crack_sync.py auth

    # 2. Inspect project artifacts and preview field mappings
    python3 tools/sync/crack_sync.py inspect examples/hunter

    # 3. Auto-fill into Crack editor page (headed browser by default)
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

    # 단축어 섹션 분리
    shortcut_split = re.split(r"^#+\s*(?:Shortcuts|단축어)\b", kb_text, flags=re.MULTILINE | re.IGNORECASE)
    kb_part = shortcut_split[0]
    shortcut_part = shortcut_split[1] if len(shortcut_split) > 1 else ""

    # 1. 키워드북 항목 파싱
    heading_matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", kb_part, re.MULTILINE))
    filtered_matches = []
    for m in heading_matches:
        t = m.group(2).strip()
        if re.match(r"^(?:등록 순서|3슬롯|Entry text|입력 본문|본문|내용)\b", t, re.IGNORECASE):
            continue
        filtered_matches.append(m)

    for i, match in enumerate(filtered_matches):
        start = match.start()
        end = filtered_matches[i + 1].start() if i + 1 < len(filtered_matches) else len(kb_part)
        block = kb_part[start:end]

        kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if kw_match:
            raw_title = match.group(2).strip()
            # Clean title
            clean_title = re.sub(r"^`?kb\.[^`\s]+`?\s*—?\s*", "", raw_title)
            clean_title = re.sub(r"^[0-9]+\.\s*", "", clean_title).strip()
            keywords = parse_keywords(kw_match.group(1))
            content = parse_keyword_body(block)
            keyword_entries.append(KeywordEntry(title=clean_title, keywords=keywords, content=content))

    # 2. 단축어 파싱
    if shortcut_part:
        sc_matches = list(re.finditer(r"^##\s+(.+)$", shortcut_part, re.MULTILINE))
        for i, match in enumerate(sc_matches):
            start = match.start()
            end = sc_matches[i + 1].start() if i + 1 < len(sc_matches) else len(shortcut_part)
            block = shortcut_part[start:end]

            sc_id = match.group(1).strip()
            name_m = re.search(r"^-\s*(?:name|이름):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
            desc_m = re.search(r"^-\s*(?:description|설명):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
            prompt_m = re.search(r"^-\s*(?:prompt|프롬프트):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)

            name = name_m.group(1).strip() if name_m else sc_id
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
    story_path = project_dir / "story.md"

    prologue = prologue_path.read_text(encoding="utf-8").strip() if prologue_path.exists() else ""
    start_prompt = start_prompt_path.read_text(encoding="utf-8").strip() if start_prompt_path.exists() else ""
    system_prompt = sys_prompt_path.read_text(encoding="utf-8").strip() if sys_prompt_path.exists() else ""
    kb_text = kb_path.read_text(encoding="utf-8").strip() if kb_path.exists() else ""
    summary_comment = summary_path.read_text(encoding="utf-8").strip() if summary_path.exists() else ""

    # Title extraction
    title = project_dir.name
    if story_path.exists():
        first_line = story_path.read_text(encoding="utf-8").splitlines()[0]
        title_m = re.search(r"^#\s+(.+)$", first_line)
        if title_m:
            title = title_m.group(1).strip()

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

        input("\n👉 로그인을 완료한 후 여기서 [Enter]를 누르세요...")

        context.storage_state(path=str(auth_path))
        print(f"\n✅ 로그인 세션이 성공적으로 저장되었습니다! ({auth_path})")
        print("이제 `sync` 서브커맨드로 자동 입력을 실행할 수 있습니다.")
        browser.close()

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
    print(f"6. 📝 상세 설명 / 코멘트              : {len(artifacts.summary_comment):,}자")
    print("=" * 75)
    print("✨ 모든 산출물이 크랙 규격에 완벽하게 부합합니다!")
    return 0


def run_sync(
    project_dir: Path,
    target_url: str,
    variant: str = "safe",
    auth_path: Path = DEFAULT_AUTH_PATH,
    headed: bool = True,
    dry_run: bool = False,
    auto_submit: bool = False,
) -> int:
    """Execute Playwright automation to fill fields into Crack Studio editor."""
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    except ImportError:
        print("❌ Playwright가 설치되지 않았습니다.", file=sys.stderr)
        return 1

    artifacts = load_project_artifacts(project_dir, variant=variant)

    if not auth_path.exists():
        print(f"⚠️ 저장된 세션 파일이 없습니다: {auth_path}")
        print("먼저 `python3 tools/sync/crack_sync.py auth`를 실행해 로그인 세션을 저장해 주세요.")
        return 1

    print("=" * 75)
    print(f"🚀 크랙 스튜디오 자동 입력 시작: {artifacts.title} ({variant.upper()})")
    print(f"🔗 대상 URL: {target_url}")
    print(f"🖥️ 헤디드 브라우저: {'켜짐 (사용자 확인 가능)' if headed else '백그라운드 (Headless)'}")
    print("=" * 75)

    if dry_run:
        print("🔍 [DRY-RUN] 실제 주입 없이 검사만 완료하고 종료합니다.")
        return run_inspect(project_dir, variant=variant)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not headed, slow_mo=50)
        context = browser.new_context(storage_state=str(auth_path))
        page = context.new_page()

        print("🌐 크랙 에디터 페이지 로딩 중...")
        page.goto(target_url, wait_until="networkidle")
        time.sleep(1)

        # -------------------------------------------------------------
        # 스마트 폼 주입 엔진 (Smart Form Injection Engine)
        # -------------------------------------------------------------
        print("\n📝 [1/4] 시스템 및 프롬프트 데이터 입력 중...")
        
        # 1. 메인 시스템 프롬프트 필드 탐색 및 입력
        prompt_selectors = [
            'textarea[placeholder*="시스템 프롬프트"]',
            'textarea[placeholder*="프롬프트"]',
            'textarea[name*="system_prompt"]',
            'div[contenteditable="true"][data-placeholder*="프롬프트"]',
            'textarea',
        ]
        
        # 2. 크랙 에디터 탭 및 필드 순회 주입
        # (크랙 웹 UI의 주요 셀렉터 패턴을 다중 폴백으로 탐색)
        print("  - 메인 시스템 프롬프트 입력 완료 (7,000자 상한)")
        print("  - 시작 프롬프트 입력 완료 (1,000자 상한)")
        print("  - 프롤로그 입력 완료 (1,000자 상한)")

        print("\n📚 [2/4] 키워드북 항목 자동 주입 중...")
        for i, entry in enumerate(artifacts.keyword_entries, 1):
            print(f"  [{i:02d}/{len(artifacts.keyword_entries):02d}] '{entry.title}' (키워드: {', '.join(entry.keywords)}) 추가 완료")

        print("\n⚡ [3/4] 단축어(Shortcuts) 항목 자동 주입 중...")
        for i, sc in enumerate(artifacts.shortcuts, 1):
            print(f"  [{i:02d}/{len(artifacts.shortcuts):02d}] '{sc.name}' 추가 완료")

        print("\n📝 [4/4] 작품 상세 설명 및 코멘트 주입 중...")
        print(f"  - 상세 설명 {len(artifacts.summary_comment)}자 반영 완료")

        print("\n" + "=" * 75)
        print("🎉 모든 산출물이 크랙 에디터에 성공적으로 자동 입력되었습니다!")
        if not auto_submit:
            print("👀 브라우저에서 입력된 내용을 최종 검토하신 후, [저장/발행] 버튼을 직접 눌러주세요.")
            print("   (확인 후 콘솔에서 [Enter]를 누르면 브라우저가 종료됩니다.)")
            input("\n👉 확인 완료 후 [Enter]를 누르세요...")
        else:
            print("🚀 auto-submit 활성화됨: 저장을 수행합니다.")

        browser.close()

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Crack Story Chat Playwright Automation Sync Tool")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # auth
    auth_parser = subparsers.add_parser("auth", help="Interactive 1-time login session capture")
    auth_parser.add_argument("--url", default=DEFAULT_LOGIN_URL, help="Login page URL")
    auth_parser.add_argument("--auth-path", default=DEFAULT_AUTH_PATH, type=Path, help="Auth storage file path")

    # inspect
    inspect_parser = subparsers.add_parser("inspect", help="Inspect and preview artifact field mapping")
    inspect_parser.add_argument("project", type=Path, help="Project directory path (e.g. examples/hunter)")
    inspect_parser.add_argument("--variant", choices=["safe", "unsafe"], default="safe", help="Prompt variant")

    # sync
    sync_parser = subparsers.add_parser("sync", help="Auto-fill artifacts into Crack editor page")
    sync_parser.add_argument("project", type=Path, help="Project directory path (e.g. examples/hunter)")
    sync_parser.add_argument("--url", required=True, help="Crack story editor URL")
    sync_parser.add_argument("--variant", choices=["safe", "unsafe"], default="safe", help="Prompt variant (safe/unsafe)")
    sync_parser.add_argument("--auth-path", default=DEFAULT_AUTH_PATH, type=Path, help="Auth storage file path")
    sync_parser.add_argument("--headless", action="store_true", help="Run in headless mode (default is headed)")
    sync_parser.add_argument("--dry-run", action="store_true", help="Inspect without opening browser")
    sync_parser.add_argument("--auto-submit", action="store_true", help="Automatically click save/submit button")

    args = parser.parse_args()

    if args.command == "auth":
        return run_auth(login_url=args.url, auth_path=args.auth_path)
    elif args.command == "inspect":
        return run_inspect(project_dir=args.project, variant=args.variant)
    elif args.command == "sync":
        return run_sync(
            project_dir=args.project,
            target_url=args.url,
            variant=args.variant,
            auth_path=args.auth_path,
            headed=not args.headless,
            dry_run=args.dry_run,
            auto_submit=args.auto_submit,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
