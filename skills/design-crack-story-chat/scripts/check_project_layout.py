#!/usr/bin/env python3
"""Validate the two-source Crack project layout and its optional five-file build."""

from __future__ import annotations

import sys
from pathlib import Path

from check_build import validate as validate_build

# 출력이 head 등으로 잘려도 트레이스백 없이 종료한다.
try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):  # Windows 등
    pass

SOURCES = {"story.md", "characters.md"}
BUILD = "build"


def visible_entries(root: Path) -> list[Path]:
    return [entry for entry in root.iterdir() if not entry.name.startswith(".")]


def validate(root: Path, require_build: bool = True) -> bool:
    if not root.is_dir():
        print(f"FAIL {root}: project directory not found")
        return False

    entries = visible_entries(root)
    names = {entry.name for entry in entries}
    missing = sorted(name for name in SOURCES if not (root / name).is_file())
    extras = sorted(names - SOURCES - {BUILD})
    ok = True
    if missing:
        print(f"FAIL {root}: missing authored source: {', '.join(missing)}")
        ok = False
    if extras:
        print(f"FAIL {root}: unexpected intermediate artifact: {', '.join(extras)}")
        ok = False

    build = root / BUILD
    if build.exists() and not build.is_dir():
        print(f"FAIL {root}: build must be a directory")
        ok = False
    if require_build and not build.is_dir():
        print(f"FAIL {root}: build directory not found")
        ok = False
    if not ok:
        return False

    print(f"PASS {root}: authored sources are exactly story.md + characters.md")
    if build.is_dir():
        return validate_build(build)
    print("PASS build: not required before first compilation")
    return True


def main() -> int:
    args = sys.argv[1:]
    allow_unbuilt = False
    if "--allow-unbuilt" in args:
        args.remove("--allow-unbuilt")
        allow_unbuilt = True
    if len(args) != 1:
        print("usage: check_project_layout.py STORY_CHAT_DIR [--allow-unbuilt]", file=sys.stderr)
        return 2
    try:
        return 0 if validate(Path(args[0]), require_build=not allow_unbuilt) else 1
    except (OSError, UnicodeError) as exc:
        print(f"FAIL project layout validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
