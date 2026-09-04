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
CORE_EXPECTED = {
    "prologue.md",
    "integrated-prompt-safe.md",
    "integrated-prompt-unsafe.md",
    "start-prompt.md",
}
VALID_KB_SETS = [
    {"keyword-book-safe.md", "keyword-book-unsafe.md"},
    {"keyword-book-safe.md", "keyword-book-unsafe.md", "keyword-book.md"},
    {"keyword-book.md", "keyword-book-unsafe.md"},
    {"keyword-book.md"},
]
# 크랙에 붙이지 않는 파생 제작 입력이 들어가는 유일한 하위 디렉터리.
DERIVED_DIR = "assets"
DERIVED_DIRS = {DERIVED_DIR, "start-sets", "departments"}
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


def validate(build: Path) -> bool:
    if not build.is_dir():
        print(f"FAIL {build}: build directory not found")
        return False

    # 점으로 시작하는 항목은 무시한다. macOS의 .DS_Store 처럼 OS가 만드는 파일이
    # 산출물 개수를 깨뜨리면 안 된다. check_project_layout.py 와 같은 규칙이다.
    entries = [e for e in build.iterdir() if not e.name.startswith(".")]
    names = {entry.name for entry in entries if entry.is_file()}
    
    # 코어 파일 누락 검사
    missing_core = sorted(CORE_EXPECTED - names)
    kb_files = {n for n in names if n.startswith("keyword-book") and n.endswith(".md")}
    
    # 키워드북 세트 일치 검사
    kb_valid = any(kb_files == valid_set for valid_set in VALID_KB_SETS)
    
    all_known = CORE_EXPECTED | kb_files
    extra = sorted(names - all_known)
    
    non_files = sorted(entry.name for entry in entries
                       if not entry.is_file() and entry.name not in DERIVED_DIRS)
    ok = True
    if missing_core:
        print(f"FAIL {build}: missing core artifacts: {', '.join(missing_core)}")
        ok = False
    if not kb_valid:
        print(f"FAIL {build}: invalid keyword book set: {sorted(kb_files)} (expected one of: {VALID_KB_SETS})")
        ok = False
    if extra:
        print(f"FAIL {build}: unexpected artifacts: {', '.join(extra)}")
        ok = False
    if non_files:
        print(f"FAIL {build}: unexpected directories/entries: {', '.join(non_files)}")
        ok = False
    if not ok:
        return False
    print(f"PASS {build}: valid final artifacts ({len(CORE_EXPECTED) + len(kb_files)} files: {', '.join(sorted(all_known))})")

    texts = {name: (build / name).read_text(encoding="utf-8") for name in CORE_EXPECTED}
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

    # Keyword-book validation moved to the crack-emu harness, which checks the
    # same authoring limits and additionally measures real three-slot behaviour
    # over actual turns:
    #   crack-emu --project <build> lint
    #   crack-emu --project <build> report
    if kb_files:
        print(f"SKIP keyword books ({len(kb_files)}): run `crack-emu --project "
              f"{build} lint` and `... report`")

    derived = build / DERIVED_DIR
    if derived.is_dir():
        known = {
            "image-prompts.md", "prompts.json", "prompts-nude.json", "story-description.md", "summary-comment.md",
            "build-stamp.json", "character-design.md", "scene-design.md",
            # 플레이어가 읽는 두 칸. 모델 프롬프트가 아니라 [시작 설정] 탭으로 간다.
            "play-guide.md", "recommended-replies.md",
            "preset-adult-poses.json", "preset-emotions.json", "preset-actions.json",
        }
        stray = sorted(p.name for p in derived.iterdir()
                       if p.is_file() and not p.name.startswith(".")
                       and p.name not in known
                       and not (p.name.startswith("preset-") and p.suffix == ".json"))
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
