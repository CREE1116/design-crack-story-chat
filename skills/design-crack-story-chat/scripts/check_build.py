#!/usr/bin/env python3
"""Validate the five Crack publish artifacts as one build contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path

# 출력이 head 등으로 잘려도 트레이스백 없이 종료한다.
try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):  # Windows 등
    pass

MAX_PROMPT = 7000
MAX_OPENING = 1000
TARGET_PROMPT = 6500
EXPECTED = {
    "prologue.md",
    "integrated-prompt-safe.md",
    "integrated-prompt-unsafe.md",
    "start-prompt.md",
    "keyword-book.md",
}
# 크랙에 붙이지 않는 파생 제작 입력이 들어가는 유일한 하위 디렉터리.
DERIVED_DIR = "assets"
UNSAFE_BANNED = (
    "정책 무시",
    "정책 우회",
    "필터 우회",
    "검열 해제",
    "안전장치 해제",
    "무조건 수행",
    "unfiltered",
    "bypass safety",
    "ignore policy",
)


def count(text: str) -> tuple[int, int, int]:
    codepoints = len(text)
    utf16 = len(text.encode("utf-16-le")) // 2
    return max(codepoints, utf16), codepoints, utf16


def headings(text: str) -> set[str]:
    return {
        match.group(1).strip().casefold()
        for match in re.finditer(r"^#{1,3}\s+(.+?)\s*$", text, re.MULTILINE)
        if not match.group(1).strip().startswith("SAFE")
        and not match.group(1).strip().startswith("UNSAFE")
    }


def stable_ids(text: str) -> set[str]:
    return set(re.findall(r"\b(?:char|loc|faction|arc|scene|event|goal|secret|flag|state|ending|kb)\.[a-z0-9-]+\b", text.casefold()))


def report_length(label: str, text: str, limit: int, target: int) -> bool:
    measured, codepoints, utf16 = count(text)
    if measured > limit:
        print(f"FAIL {label}: {measured}/{limit} chars (codepoints={codepoints}, utf16={utf16})")
        return False
    status = "WARN" if measured > target else "PASS"
    print(f"{status} {label}: {measured}/{limit} chars (codepoints={codepoints}, utf16={utf16})")
    return True


def load_keyword_validator():
    try:
        from check_keyword_book import validate  # type: ignore
    except ImportError as exc:  # pragma: no cover - only malformed installs hit this
        print(f"FAIL keyword validator import: {exc}")
        return None
    return validate


def validate(build: Path) -> bool:
    if not build.is_dir():
        print(f"FAIL {build}: build directory not found")
        return False

    # 점으로 시작하는 항목은 무시한다. macOS의 .DS_Store 처럼 OS가 만드는 파일이
    # 산출물 개수를 깨뜨리면 안 된다. check_project_layout.py 와 같은 규칙이다.
    entries = [e for e in build.iterdir() if not e.name.startswith(".")]
    names = {entry.name for entry in entries if entry.is_file()}
    extra = sorted(names - EXPECTED)
    missing = sorted(EXPECTED - names)
    # build/assets/ 는 크랙에 붙이지 않는 파생 제작 입력(이미지 프롬프트 등)의 자리다.
    # 다섯 개의 크랙 산출물과 달리 모델에게 실리지 않으므로 개수를 세지 않는다.
    non_files = sorted(entry.name for entry in entries
                       if not entry.is_file() and entry.name != DERIVED_DIR)
    ok = True
    if missing:
        print(f"FAIL {build}: missing artifacts: {', '.join(missing)}")
        ok = False
    if extra:
        print(f"FAIL {build}: unexpected artifacts: {', '.join(extra)}")
        ok = False
    if non_files:
        print(f"FAIL {build}: unexpected directories/entries: {', '.join(non_files)}")
        ok = False
    if not ok:
        return False
    print(f"PASS {build}: exactly {len(EXPECTED)} final artifacts")

    texts = {name: (build / name).read_text(encoding="utf-8") for name in EXPECTED}
    ok = report_length("prologue.md", texts["prologue.md"], MAX_OPENING, 900) and ok
    ok = report_length("start-prompt.md", texts["start-prompt.md"], MAX_OPENING, 900) and ok
    safe = texts["integrated-prompt-safe.md"]
    unsafe = texts["integrated-prompt-unsafe.md"]
    ok = report_length("integrated-prompt-safe.md", safe, MAX_PROMPT, TARGET_PROMPT) and ok
    ok = report_length("integrated-prompt-unsafe.md", unsafe, MAX_PROMPT, TARGET_PROMPT) and ok

    if not safe.strip() or not unsafe.strip():
        print("FAIL integrated prompts: both variants must be non-empty")
        ok = False
    if headings(safe) != headings(unsafe):
        print("FAIL integrated prompts: section headings drift between SAFE and UNSAFE")
        print(f"  SAFE-only: {sorted(headings(safe) - headings(unsafe))}")
        print(f"  UNSAFE-only: {sorted(headings(unsafe) - headings(safe))}")
        ok = False
    safe_ids = stable_ids(safe)
    unsafe_ids = stable_ids(unsafe)
    if safe_ids or unsafe_ids:
        if safe_ids != unsafe_ids:
            print("FAIL integrated prompts: stable IDs drift between SAFE and UNSAFE")
            print(f"  SAFE-only: {sorted(safe_ids - unsafe_ids)}")
            print(f"  UNSAFE-only: {sorted(unsafe_ids - safe_ids)}")
            ok = False
        else:
            print(f"PASS integrated prompts: shared stable IDs={len(safe_ids)}")
    for phrase in UNSAFE_BANNED:
        if phrase.casefold() in unsafe.casefold():
            print(f"FAIL integrated-prompt-unsafe.md: banned bypass phrase: {phrase}")
            ok = False

    validator = load_keyword_validator()
    if validator is not None:
        ok = validator(str(build / "keyword-book.md")) and ok

    derived = build / DERIVED_DIR
    if derived.is_dir():
        known = {"image-prompts.md", "prompts.json", "summary-comment.md", "build-stamp.json"}
        stray = sorted(p.name for p in derived.iterdir()
                       if p.is_file() and not p.name.startswith(".")
                       and p.name not in known)
        if stray:
            print(f"FAIL {derived}: 알 수 없는 파생물: {', '.join(stray)}")
            print("     파생물은 요약 코멘트와 이미지 프롬프트만 둡니다. "
                  "모델에 실릴 규칙은 다섯 산출물에만 넣습니다.")
            ok = False
        try:
            from check_image_assets import validate as validate_images  # type: ignore
            ok = validate_images(build.parent) and ok
        except ImportError as exc:
            print(f"WARN image asset validator import: {exc}")
    return ok


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_build.py BUILD_DIR", file=sys.stderr)
        return 2
    try:
        return 0 if validate(Path(sys.argv[1])) else 1
    except (OSError, UnicodeError) as exc:
        print(f"FAIL build validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
