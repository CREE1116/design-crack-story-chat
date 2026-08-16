#!/usr/bin/env python3
"""Simulate Crack's three-entry keyword-book load against realistic scenes.

Crack loads at most three keyword-book entries at once. Reviewing entries one
at a time never finds a collision; only enumerating scenes does.

Usage:
    check_kb_slots.py build/keyword-book.md scenes.txt
    check_kb_slots.py build/keyword-book.md --scene "길드 선택" --text "발할라와 아발론 부스"

Scene file format — one scene per non-empty line, comments start with '#':
    길드 선택: 발할라 아발론 에덴 바벨 부스를 둘러본다
    범람 초기: 게이트가 열리고 범람체가 쏟아진다

Entries are matched in registration order (file order). When more than three
match, the later ones are dropped: that is the failure the simulation reports.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

MAX_SLOTS = 3


def normalize(text: str) -> str:
    return re.sub(r"\s+", "", text).casefold()


def load_entries(path: Path) -> list[tuple[str, list[str]]]:
    text = path.read_text(encoding="utf-8")
    matches = list(re.finditer(r"^#\s+`?(kb\.[^`\s]+)`?.*$", text, re.MULTILINE))
    entries: list[tuple[str, list[str]]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        raw = re.search(r"^- keywords:\s*(\[.*?\])\s*$", block, re.MULTILINE)
        keywords: list[str] = []
        if raw:
            inner = raw.group(1)[1:-1]
            keywords = [k.strip().strip("'\"`") for k in inner.split(",") if k.strip()]
        entries.append((match.group(1), keywords))
    return entries


def load_scenes(args: list[str]) -> list[tuple[str, str]]:
    scenes: list[tuple[str, str]] = []
    index = 0
    while index < len(args):
        if args[index] == "--scene":
            label = args[index + 1]
            text = args[index + 3] if args[index + 2] == "--text" else ""
            scenes.append((label, text))
            index += 4
            continue
        for line in Path(args[index]).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            label, _, text = line.partition(":")
            scenes.append((label.strip(), text.strip() or label.strip()))
        index += 1
    return scenes


def simulate(entries: list[tuple[str, list[str]]], label: str, text: str) -> bool:
    haystack = normalize(text)
    hits = [
        entry_id
        for entry_id, keywords in entries
        if any(normalize(k) and normalize(k) in haystack for k in keywords)
    ]
    if len(hits) <= MAX_SLOTS:
        detail = ", ".join(hits) if hits else "(none)"
        print(f"PASS {label}: {len(hits)}/{MAX_SLOTS} — {detail}")
        return True
    loaded = ", ".join(hits[:MAX_SLOTS])
    dropped = ", ".join(hits[MAX_SLOTS:])
    print(f"FAIL {label}: {len(hits)}/{MAX_SLOTS} — loaded [{loaded}] DROPPED [{dropped}]")
    return False


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        return 2
    entries = load_entries(Path(sys.argv[1]))
    if not entries:
        print(f"FAIL {sys.argv[1]}: no # `kb.*` entry blocks found")
        return 1
    scenes = load_scenes(sys.argv[2:])
    if not scenes:
        print("FAIL: no scenes supplied")
        return 1
    print(f"# {len(entries)} entries, registration order: {', '.join(i for i, _ in entries)}\n")
    ok = True
    for label, text in scenes:
        ok = simulate(entries, label, text) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
