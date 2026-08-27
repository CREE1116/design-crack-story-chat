#!/usr/bin/env python3
"""Validate Crack keyword-book authoring entries."""

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

MAX_KEYWORDS = 5
MAX_BODY = 400
TARGET_BODY = 360


def read(path: str) -> str:
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def parse_keywords(raw: str | None) -> list[str]:
    if raw is None:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        raw = raw[1:-1]
    return [item.strip().strip("'\"`") for item in raw.split(",") if item.strip()]


def body(text: str) -> str | None:
    # 1. ## Entry text / ## 내용 / ## 본문 헤딩 파싱
    match = re.search(
        r"^##\s+(?:Entry text|입력 본문|본문|내용)\s*\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if match:
        return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()

    # 2. - 내용: / - 본문: 파싱
    match = re.search(
        r"^-\s*(?:내용|본문|entry|body):\s*\n?(.*?)(?=^-\s*[a-zA-Z가-힣_]+:|\Z)",
        text,
        re.MULTILINE | re.DOTALL | re.IGNORECASE,
    )
    if match:
        return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()

    # 3. 키워드 줄 이후의 본문 파싱
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
    return None


def split_entries(text: str) -> list[tuple[str, str]]:
    # 모든 헤딩(#, ##, ###) 탐색 (하위 헤딩인 ## Entry text, ## 내용 등은 제외)
    heading_matches = list(re.finditer(r"^(#{1,3})\s+(.+)$", text, re.MULTILINE))
    filtered_matches = []
    for m in heading_matches:
        title = m.group(2).strip()
        if re.match(r"^(?:Entry text|입력 본문|본문|내용|Shortcut)\b", title, re.IGNORECASE):
            continue
        filtered_matches.append(m)

    entries: list[tuple[str, str]] = []
    for i, match in enumerate(filtered_matches):
        start = match.start()
        end = filtered_matches[i + 1].start() if i + 1 < len(filtered_matches) else len(text)
        block = text[start:end]

        # 블록 내에 키워드 정의가 있는지 확인
        kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", block, re.MULTILINE | re.IGNORECASE)
        if kw_match:
            raw_title = match.group(2).strip()
            kb_id_match = re.search(r"`?(kb\.[^`\s]+)`?", raw_title)
            if kb_id_match:
                entry_id = kb_id_match.group(1)
            else:
                entry_id = re.sub(r"^[0-9]+\.\s*", "", raw_title).strip()
            entries.append((entry_id, block))
    return entries


def validate_entry(label: str, text: str) -> bool:
    errors: list[str] = []
    kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", text, re.MULTILINE | re.IGNORECASE)
    keywords = parse_keywords(kw_match.group(1) if kw_match else None)
    entry = body(text)

    if not 1 <= len(keywords) <= MAX_KEYWORDS:
        errors.append(f"keywords must contain 1..{MAX_KEYWORDS} items (got {len(keywords)})")
    if len({keyword.casefold() for keyword in keywords}) != len(keywords):
        errors.append("keywords contain duplicates")
    if not entry:
        errors.append("Entry text/본문 is required")
        count = 0
    else:
        codepoints = len(entry)
        utf16 = len(entry.encode("utf-16-le")) // 2
        count = max(codepoints, utf16)
        if count > MAX_BODY:
            errors.append(f"entry text is {count}/{MAX_BODY} chars")

    if errors:
        print(f"FAIL {label}: " + "; ".join(errors))
        return False
    status = "WARN" if count > TARGET_BODY else "PASS"
    print(f"{status} {label}: keywords={len(keywords)}/5, body={count}/400")
    return True


def validate(path: str) -> bool:
    text = read(path)
    entries = split_entries(text)
    label = "stdin" if path == "-" else path
    if not entries:
        if re.search(r"^- entries:\s*\[\]\s*$", text, re.MULTILINE):
            print(f"PASS {label}: explicit empty keyword-book registry")
            return True
        print(f"FAIL {label}: no keyword-book entry blocks found")
        return False
    ok = True
    seen_ids: set[str] = set()
    seen_keywords: dict[str, str] = {}
    for entry_id, entry_text in entries:
        if entry_id in seen_ids:
            print(f"FAIL {label}: duplicate entry id/title {entry_id}")
            ok = False
        seen_ids.add(entry_id)
        kw_match = re.search(r"^-\s*(?:키워드|keywords?):\s*(.+)$", entry_text, re.MULTILINE | re.IGNORECASE)
        raw_keywords = parse_keywords(kw_match.group(1) if kw_match else None)
        for keyword in raw_keywords:
            normalized = re.sub(r"\s+", "", keyword).casefold()
            previous = seen_keywords.get(normalized)
            if previous and previous != entry_id:
                print(f"FAIL {label}: keyword collision {keyword!r} in {previous} and {entry_id}")
                ok = False
            seen_keywords[normalized] = entry_id
        ok = validate_entry(f"{label}#{entry_id}", entry_text) and ok
    return ok


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1:] == ["-"] and sys.stdin.isatty():
        print("usage: check_keyword_book.py ENTRY.md [...] | -", file=sys.stderr)
        return 2
    ok = True
    for path in sys.argv[1:]:
        try:
            ok = validate(path) and ok
        except OSError as exc:
            print(f"FAIL {path}: {exc}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
