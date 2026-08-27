#!/usr/bin/env python3
"""Check the derived image-prompt artifacts against their sources.

Image prompts are not authored material. They are compiled from `characters.md`
(appearance anchors) and from the axis lists the integrated prompt publishes, so
three things must agree at all times:

    characters.md  ─┐
                    ├─→  build/assets/prompts.json  ─→  disk folders
    integrated ─────┘         (axis lists)

Any disagreement produces links the model composes but nothing serves, and the
failure is silent during play. This checks the agreement mechanically.

Usage:
    check_image_assets.py PROJECT_DIR
    check_image_assets.py PROJECT_DIR --quiet
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):
    pass

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEADING_TAGS = 4   # 이만큼은 인물마다 달라야 썸네일에서 구분된다


def parse_roster(characters_md: str) -> set[str]:
    headings = re.findall(r"^##\s+(.+)$", characters_md, re.MULTILINE)
    roster: set[str] = set()
    for h in headings:
        m = re.search(r"`?char\.([a-z0-9-]+)`?", h)
        if m:
            roster.add(m.group(1))
            continue
        name_match = re.match(r"^([가-힣a-zA-Z0-9\s]+?)(?:\s*[「『·\(0-9]|$)", h.strip())
        if name_match:
            roster.add(name_match.group(1).strip())
    return roster


def validate(project: Path, quiet: bool = False) -> bool:
    chars_path = project / "characters.md"
    config_path = project / "build" / "assets" / "prompts.json"
    if not config_path.exists():
        if not quiet:
            print(f"SKIP {project}: 이미지 자산 없음 ({config_path.name} 미존재)")
        return True
    if not chars_path.exists():
        print(f"FAIL {project}: characters.md 가 없습니다")
        return False

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    roster = parse_roster(chars_path.read_text(encoding="utf-8"))
    people = cfg.get("characters", {})
    ok = True

    # 1. 명부 대조 — 한글명 및 슬러그 양방향 매핑
    people_map: dict[str, str] = {}
    for slug, obj in people.items():
        people_map[slug] = slug
        if isinstance(obj, dict) and "ko" in obj:
            people_map[obj["ko"]] = slug

    missing: list[str] = []
    matched_slugs: set[str] = set()
    for r in sorted(roster):
        if r in people_map:
            matched_slugs.add(people_map[r])
        elif r in people:
            matched_slugs.add(r)
        else:
            missing.append(r)

    orphan = sorted(set(people.keys()) - matched_slugs)
    if missing:
        ok = False
        print(f"FAIL 이미지 프롬프트 누락 {len(missing)}명: {', '.join(missing)}")
        print("     characters.md 에 있는 인물인데 이미지 프롬프트가 없습니다.")
    if orphan:
        ok = False
        print(f"FAIL 정체 불명 슬러그 {len(orphan)}개: {', '.join(orphan)}")
        print("     characters.md 에 없는 인물의 이미지 프롬프트입니다. 이름이 바뀌었을 수 있습니다.")

    # 2. 슬러그 형식
    bad = sorted(s for s in {*people, *cfg.get("situations", {}), *cfg.get("scenes", {}),
                             *cfg.get("backgrounds", {}), *cfg.get("monsters", {})}
                 if not SLUG.match(s))
    if bad:
        ok = False
        print(f"FAIL 슬러그 형식 위반: {', '.join(bad)}")
        print("     소문자·숫자·하이픈만 씁니다. URL과 폴더 이름이 되기 때문입니다.")

    # 3. 축 목록이 통합 프롬프트에 실려 있는가
    prompt_path = project / "build" / "integrated-prompt-safe.md"
    kb_path = project / "build" / "keyword-book.md"
    published = ""
    for path in (prompt_path, kb_path):
        if path.exists():
            published += path.read_text(encoding="utf-8")
    if published:
        for axis in ("situations", "scenes"):
            absent = sorted(s for s in cfg.get(axis, {}) if s not in published)
            if absent:
                ok = False
                print(f"FAIL {axis} 슬러그가 프롬프트에 없음: {', '.join(absent)}")
                print("     모델은 프롬프트에 실린 목록에서만 슬러그를 조합합니다.")
        unreachable = sorted(s for s in people if s not in published)
        if unreachable and not quiet:
            print(f"INFO 프롬프트에 없는 인물 슬러그 {len(unreachable)}개: "
                  f"{', '.join(unreachable[:6])}{' …' if len(unreachable) > 6 else ''}")
            print("     이 인물들의 이미지는 해당 키워드북 항목이 로드될 때만 부를 수 있습니다.")

    # 4. 시드 중복 — 같은 시드는 인물 간 유사도를 높인다
    seeds: dict[int, list[str]] = {}
    for slug, entry in people.items():
        seed = entry.get("seed")
        if seed is not None:
            seeds.setdefault(seed, []).append(slug)
    for seed, owners in sorted(seeds.items()):
        if len(owners) > 1:
            ok = False
            print(f"FAIL 시드 {seed} 중복: {', '.join(owners)}")

    # 5. 선두 태그 구별 — 식별 포인트는 앞에 와야 썸네일에서 산다
    leads: dict[str, list[str]] = {}
    for slug, entry in people.items():
        tags = [t.strip() for t in (entry.get("tags") or "").split(",") if t.strip()]
        if not tags:
            ok = False
            print(f"FAIL {slug}: tags 가 비어 있습니다")
            continue
        leads.setdefault(", ".join(tags[:LEADING_TAGS]).casefold(), []).append(slug)
    for lead, owners in leads.items():
        if len(owners) > 1:
            ok = False
            print(f"FAIL 선두 태그가 동일: {', '.join(owners)}")
            print(f"     «{lead}»")
            print(f"     앞 {LEADING_TAGS}개 태그는 인물마다 달라야 합니다. "
                  "뒤쪽 태그는 가중치가 낮아 썸네일 크기에서 묻힙니다.")

    if ok and not quiet:
        combos = len(people) * len(cfg.get("situations", {}))
        fixed = sum(len(cfg.get(k, {})) for k in ("scenes", "backgrounds", "monsters"))
        print(f"PASS 이미지 자산: 인물 {len(people)}명, 조합 {combos}장 + 고정 {fixed}장")
    return ok


def main() -> int:
    args = [a for a in sys.argv[1:] if a != "--quiet"]
    quiet = "--quiet" in sys.argv[1:]
    if len(args) != 1:
        print("usage: check_image_assets.py PROJECT_DIR [--quiet]", file=sys.stderr)
        return 2
    try:
        return 0 if validate(Path(args[0]), quiet) else 1
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL image asset validation: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
