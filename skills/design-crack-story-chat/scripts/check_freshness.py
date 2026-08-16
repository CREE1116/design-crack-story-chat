#!/usr/bin/env python3
"""원본이 바뀌었는데 산출물이 안 따라왔는지 검사한다.

산출물은 두 원본에서 매번 다시 생성한다는 것이 이 프로젝트의 규칙이지만,
사람이 `characters.md`를 고치고 컴파일을 잊는 일은 반드시 생긴다. 그리고
그 상태는 겉으로 아무 신호도 내지 않는다 — 빌드는 여전히 모든 검사를
통과하고, 크랙에 올라간 프롬프트만 조용히 옛날 인물을 연기한다.

섹션 단위로 지문을 남겨두고 비교하므로, 무엇이 바뀌었고 그래서 어느
산출물을 다시 봐야 하는지까지 알려준다.

사용:
    check_freshness.py PROJECT --stamp    컴파일 직후 현재 상태를 기록
    check_freshness.py PROJECT            기록 이후 바뀐 것이 있는지 검사
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):
    pass

SOURCES = ("story.md", "characters.md")
STAMP = Path("build") / "assets" / "build-stamp.json"

# 바뀐 섹션 제목 → 다시 봐야 할 산출물. 순서대로 처음 맞는 것을 쓴다.
ROUTES: tuple[tuple[str, str], ...] = (
    (r"appearance|외형|식별", "build/assets/image-prompts.md · prompts.json (외형 앵커의 단일 출처)"),
    (r"prologue|프롤로그|opening|오프닝|opening material|첫 상황|시작", "build/prologue.md · build/start-prompt.md"),
    (r"^char\.|인물|character", "통합본 현장 인물 씨앗 · 해당 키워드북 항목 · 이미지 프롬프트"),
    (r"등급|tier|위협|threat|범람체|성장|경제|세계|world|hard rule|법칙", "통합본 세계 법칙 · 관련 키워드북 항목"),
    (r"관계|relationship|이벤트|event|진행|arc", "통합본 진행·관계"),
    (r"길드|faction|조직|협회", "통합본 세력 요약 · 해당 키워드북 항목"),
    (r"kb\.|키워드|lore candidate", "build/keyword-book.md"),
)


def sections(text: str) -> dict[str, str]:
    """`#`~`###` 제목 단위로 쪼개 제목→지문 사전을 만든다."""
    marks = list(re.finditer(r"^(#{1,3})\s+(.+?)\s*$", text, re.MULTILINE))
    out: dict[str, str] = {}
    if not marks:
        return {"(전체)": hashlib.sha256(text.encode()).hexdigest()[:16]}
    for index, mark in enumerate(marks):
        end = marks[index + 1].start() if index + 1 < len(marks) else len(text)
        title = re.sub(r"[`*]", "", mark.group(2)).strip()
        body = text[mark.end():end]
        key = title
        suffix = 2
        while key in out:
            key, suffix = f"{title} ({suffix})", suffix + 1
        out[key] = hashlib.sha256(body.encode()).hexdigest()[:16]
    return out


def snapshot(project: Path) -> dict:
    data: dict[str, dict[str, str]] = {}
    for name in SOURCES:
        path = project / name
        if path.exists():
            data[name] = sections(path.read_text(encoding="utf-8"))
    return data


def route_for(title: str) -> str:
    low = title.casefold()
    for pattern, target in ROUTES:
        if re.search(pattern, low):
            return target
    return "관련 산출물을 직접 판단할 것"


def write_stamp(project: Path) -> int:
    path = project / STAMP
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot(project), ensure_ascii=False, indent=1) + "\n",
                    encoding="utf-8")
    total = sum(len(v) for v in snapshot(project).values())
    print(f"기록했습니다: {path}  (섹션 {total}개)")
    return 0


def compare(project: Path) -> int:
    path = project / STAMP
    if not path.exists():
        print(f"기록이 없습니다: {path}")
        print("  컴파일 직후 `check_freshness.py <작품> --stamp` 로 기준을 남기세요.")
        return 0
    old = json.loads(path.read_text(encoding="utf-8"))
    new = snapshot(project)

    stale = False
    for name in SOURCES:
        before, after = old.get(name, {}), new.get(name, {})
        if not before and not after:
            continue
        changed = sorted(t for t in before.keys() & after.keys() if before[t] != after[t])
        added = sorted(after.keys() - before.keys())
        removed = sorted(before.keys() - after.keys())
        if not (changed or added or removed):
            print(f"PASS {name}: 변경 없음")
            continue
        stale = True
        print(f"STALE {name}: 수정 {len(changed)} · 추가 {len(added)} · 삭제 {len(removed)}")
        for title in added:
            print(f"  + {title}")
            print(f"      → {route_for(title)}")
        for title in removed:
            print(f"  - {title}")
            print(f"      → {route_for(title)}  (참조가 남아 있는지 확인)")
        for title in changed:
            print(f"  ~ {title}")
            print(f"      → {route_for(title)}")

    if stale:
        print("\n산출물이 원본보다 낡았습니다. 다시 컴파일하고 `--stamp` 로 기준을 갱신하세요.")
        print("빌드 파일을 직접 고치지 마세요 — 그 순간 두 번째 원본이 됩니다.")
        return 1
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 1:
        print("usage: check_freshness.py PROJECT_DIR [--stamp]", file=sys.stderr)
        return 2
    project = Path(args[0])
    if not project.is_dir():
        print(f"FAIL {project}: 작품 폴더가 없습니다")
        return 1
    try:
        return write_stamp(project) if "--stamp" in sys.argv[1:] else compare(project)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"FAIL freshness check: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
