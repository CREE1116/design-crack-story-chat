#!/usr/bin/env python3
"""Reject retired dotted character/source namespaces in a story-chat project."""

from __future__ import annotations

import re
import sys
from pathlib import Path

FORBIDDEN = re.compile(r"\b(?:char|canon)\.[A-Za-z0-9_-]+", re.IGNORECASE)
SCAN_DIRS = ("build",)
SCAN_FILES = ("story.md", "characters.md")


def files(root: Path):
    for name in SCAN_FILES:
        path = root / name
        if path.is_file():
            yield path
    for dirname in SCAN_DIRS:
        directory = root / dirname
        if directory.is_dir():
            yield from (p for p in directory.rglob("*.md") if p.is_file())


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_naming.py STORY_CHAT_DIR", file=sys.stderr)
        return 2
    root = Path(sys.argv[1])
    found = False
    for path in files(root):
        text = path.read_text(encoding="utf-8")
        for match in FORBIDDEN.finditer(text):
            found = True
            line = text.count("\n", 0, match.start()) + 1
            print(f"FAIL {path}:{line}: retired dotted namespace {match.group(0)!r}")
    if found:
        return 1
    print(f"PASS {root}: no retired dotted character/source namespaces")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
