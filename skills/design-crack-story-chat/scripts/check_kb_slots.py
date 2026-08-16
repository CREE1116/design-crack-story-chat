#!/usr/bin/env python3
"""Simulate Crack's three-entry keyword-book load against realistic scenes.

Crack loads at most three entries at once, and ties are broken by registration
order — earlier entries win. Reviewing entries one at a time never finds a
collision; only enumerating scenes does.

Usage:
    check_kb_slots.py build/keyword-book.md scenes.txt
    check_kb_slots.py build/keyword-book.md --scene "길드 선택" --text "발할라와 아발론 부스"

Scene file format — one scene per non-empty line, comments start with '#':
    길드 선택: 발할라 아발론 에덴 바벨 부스를 둘러본다.
    범람 초기: 게이트가 열리고 범람체가 쏟아진다.

Write scene text the way it would really appear, punctuation included, or
entries keyed on common characters will not be exercised.

Reports three things:
  1. per-scene load — which entries win the three slots, which are dropped;
  2. per-entry load rate — how often an entry actually occupies a slot, not
     merely matches. An entry that matches often and never loads is dead;
  3. effectively-always-on entries — those matching most scenes. Used
     deliberately (a low-priority filler that soaks up leftover slots) this is
     a real technique; used by accident it starves every conditional entry.

Only (3) can fail the run. Slot overflow and load rate are reported for human
judgement: whether a dropped entry matters depends on whether the integrated
prompt still carries what that scene needs, which no script can know.
"""

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

MAX_SLOTS = 3
ALWAYS_ON_RATE = 0.7   # match rate at or above which an entry is "effectively always-on"
BOTTOM_FRACTION = 0.25  # such entries belong in the last quarter of the order


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


def matches(keywords: list[str], haystack: str) -> bool:
    return any(normalize(k) and normalize(k) in haystack for k in keywords)


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

    order = {entry_id: rank for rank, (entry_id, _) in enumerate(entries)}
    matched = {entry_id: 0 for entry_id, _ in entries}
    loaded = {entry_id: 0 for entry_id, _ in entries}
    ok = True

    print(f"# {len(entries)} entries, {len(scenes)} scenes, {MAX_SLOTS} slots\n")
    print("## 장면별 로드")
    for label, text in scenes:
        haystack = normalize(text)
        hits = [e for e, kws in entries if matches(kws, haystack)]
        for entry_id in hits:
            matched[entry_id] += 1
        for entry_id in hits[:MAX_SLOTS]:
            loaded[entry_id] += 1
        if len(hits) <= MAX_SLOTS:
            print(f"PASS {label}: {len(hits)}/{MAX_SLOTS} — {', '.join(hits) or '(none)'}")
        else:
            print(f"WARN {label}: {len(hits)}/{MAX_SLOTS} — "
                  f"loaded [{', '.join(hits[:MAX_SLOTS])}] "
                  f"DROPPED [{', '.join(hits[MAX_SLOTS:])}]")

    total = len(scenes)
    print("\n## 항목별 실제 로드율")
    for entry_id, _ in entries:
        m, l = matched[entry_id], loaded[entry_id]
        note = ""
        if not m:
            note = "  ← 이 장면 목록이 시험하지 않음. 목록을 늘리거나 항목이 불필요한지 볼 것"
        elif not l:
            note = f"  ← 걸린 {m}회 모두 밀림. 단독으로 걸리는 장면이 목록에 없거나 순서가 낮다"
        elif l < m:
            note = f"  ← {m - l}회 밀림"
        print(f"  {entry_id:<22} 매칭 {m}/{total}  로드 {l}/{total}{note}")

    hot = [e for e, _ in entries if matched[e] / total >= ALWAYS_ON_RATE]
    if hot:
        print("\n## 사실상 상시 항목")
        cutoff = len(entries) * (1 - BOTTOM_FRACTION)
        for entry_id in hot:
            rate = matched[entry_id] / total
            if order[entry_id] < cutoff:
                ok = False
                print(f"FAIL {entry_id}: {rate:.0%} 매칭인데 등록 순서 {order[entry_id] + 1}번. "
                      f"위쪽에 있으면 조건부 항목을 모두 굶긴다. 맨 아래로 내릴 것")
            else:
                print(f"INFO {entry_id}: {rate:.0%} 매칭, 순서 {order[entry_id] + 1}번(하단). "
                      f"채움형으로 동작한다 — 본문이 없어도 응답이 성립해야 한다")
        if len(hot) >= MAX_SLOTS:
            ok = False
            print(f"FAIL 사실상 상시 항목이 {len(hot)}개다. {MAX_SLOTS}슬롯을 전부 점유해 "
                  f"키워드북의 조건부 기능이 죽는다. 1~2개로 줄일 것")

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
