#!/usr/bin/env python3
"""Simulate Crack's three-entry keyword-book load against realistic scenes.

Crack loads at most three entries at once, and ties are broken by registration
order — earlier entries win. Reviewing entries one at a time never finds a
collision; only enumerating scenes does.

Usage:
    check_kb_slots.py build/keyword-book.md scenes.txt
    check_kb_slots.py build/keyword-book.md --scene "길드 선택" --text "발할라와 아발론 부스"
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


def parse_keywords(raw: str | None) -> list[str]:
    if raw is None:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip("'\"`") for item in raw.split(",") if item.strip()]


def load_entries(path: Path) -> list[tuple[str, list[str]]]:
    text = path.read_text(encoding="utf-8")
    heading_matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", text, re.MULTILINE))
    filtered_matches = []
    for m in heading_matches:
        title = m.group(2).strip()
        if re.match(r"^(?:Entry text|입력 본문|본문|내용|Shortcut)\b", title, re.IGNORECASE):
            continue
        filtered_matches.append(m)

    entries: list[tuple[str, list[str]]] = []
    for i, match in enumerate(filtered_matches):
        start = match.start()
        end = filtered_matches[i + 1].start() if i + 1 < len(filtered_matches) else len(text)
        block = text[start:end]

        kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if kw_match:
            raw_title = match.group(2).strip()
            kb_id_match = re.search(r"`?(kb\.[^`\s]+)`?", raw_title)
            if kb_id_match:
                entry_id = kb_id_match.group(1)
            else:
                entry_id = re.sub(r"^[0-9]+\.\s*", "", raw_title).strip()
            keywords = parse_keywords(kw_match.group(1))
            entries.append((entry_id, keywords))
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
        print(f"FAIL {sys.argv[1]}: no keyword-book entries found")
        return 1

    scenes = load_scenes(sys.argv[2:])
    if not scenes:
        print(f"FAIL {sys.argv[1]}: no scenes provided")
        return 1

    entry_ids = [eid for eid, _ in entries]
    matched_counts = {eid: 0 for eid in entry_ids}
    loaded_counts = {eid: 0 for eid in entry_ids}

    print(f"# {len(entries)} entries, {len(scenes)} scenes, {MAX_SLOTS} slots\n")
    print("## 장면별 로드")
    for label, text in scenes:
        scene_haystack = normalize(f"{label} {text}")
        hit = [eid for eid, kw in entries if matches(kw, scene_haystack)]
        loaded = hit[:MAX_SLOTS]
        dropped = hit[MAX_SLOTS:]

        for eid in hit:
            matched_counts[eid] += 1
        for eid in loaded:
            loaded_counts[eid] += 1

        status = "WARN" if dropped else "PASS"
        loaded_str = ", ".join(loaded) or "(없음)"
        dropped_str = f" DROPPED [{', '.join(dropped)}]" if dropped else ""
        print(f"{status} {label}: {len(loaded)}/{MAX_SLOTS} — {loaded_str}{dropped_str}")

    print("\n## 항목별 실제 로드율")
    for eid in entry_ids:
        m = matched_counts[eid]
        l = loaded_counts[eid]
        comment = ""
        if m == 0:
            comment = "  ← 이 장면 목록이 시험하지 않음. 목록을 늘리거나 항목이 불필요한지 볼 것"
        elif l == 0:
            comment = "  ← 걸린 1회 모두 밀림. 단독으로 걸리는 장면이 목록에 없거나 순서가 낮다"
        elif l < m:
            comment = f"  ← {m - l}회 밀림"
        print(f"  {eid:<22} 매칭 {m:>2}/{len(scenes):<2}  로드 {l:>2}/{len(scenes):<2}{comment}")

    print("\n## 사실상 상시 항목")
    always_on = [
        (eid, matched_counts[eid] / len(scenes), index)
        for index, (eid, _) in enumerate(entries)
        if matched_counts[eid] / len(scenes) >= ALWAYS_ON_RATE
    ]
    cutoff = int(len(entries) * (1 - BOTTOM_FRACTION))
    failed = False
    for eid, rate, index in always_on:
        if index < cutoff:
            print(
                f"FAIL {eid}: {rate:.0%} 매칭, 순서 {index + 1}번(상위 {index / len(entries):.0%}). "
                f"다른 항목을 밀어내므로 {cutoff + 1}번 이후로 내릴 것"
            )
            failed = True
        else:
            print(
                f"INFO {eid}: {rate:.0%} 매칭, 순서 {index + 1}번(하단). "
                f"채움형으로 동작한다 — 본문이 없어도 응답이 성립해야 한다"
            )
    if not always_on:
        print("PASS 70% 이상 매칭되는 항목 없음 (상시 항목 부재)")

    print("   (슬롯 초과는 설계 판단이 필요한 경고입니다. 통과 조건에 넣지 않습니다.)")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
