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


def field(text: str, name: str) -> str | None:
    match = re.search(rf"^- {re.escape(name)}:\s*(.*?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def body(text: str) -> str | None:
    match = re.search(
        r"^## (?:Entry text|입력 본문)\s*\n(.*?)(?=^## |\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None
    value = re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()
    return value


def parse_keywords(raw: str | None) -> list[str]:
    if raw is None or not raw.startswith("[") or not raw.endswith("]"):
        return []
    return [item.strip().strip("'\"`") for item in raw[1:-1].split(",") if item.strip()]


def split_entries(text: str) -> list[tuple[str, str]]:
    matches = list(re.finditer(r"^#\s+`?(kb\.[^`\s]+)`?.*$", text, re.MULTILINE))
    if not matches:
        return []
    entries: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        entries.append((match.group(1), text[match.start() : end]))
    return entries


def validate_entry(label: str, text: str) -> bool:
    errors: list[str] = []
    activation_setting = field(text, "activation_setting")
    activation_when = field(text, "activation_when")
    keywords = parse_keywords(field(text, "keywords"))
    entry = body(text)

    if not activation_setting or activation_setting.startswith("["):
        errors.append("activation_setting is required")
    if not activation_when or activation_when.startswith("["):
        errors.append("activation_when is required")
    if not 1 <= len(keywords) <= MAX_KEYWORDS:
        errors.append(f"keywords must contain 1..{MAX_KEYWORDS} items")
    if len({keyword.casefold() for keyword in keywords}) != len(keywords):
        errors.append("keywords contain duplicates")
    if not entry:
        errors.append("Entry text/입력 본문 is required")
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
        print(f"FAIL {label}: no # `kb.*` entry blocks found")
        return False
    ok = True
    seen_ids: set[str] = set()
    seen_keywords: dict[str, str] = {}
    for entry_id, entry_text in entries:
        if entry_id in seen_ids:
            print(f"FAIL {label}: duplicate entry id {entry_id}")
            ok = False
        seen_ids.add(entry_id)
        raw_keywords = parse_keywords(field(entry_text, "keywords"))
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
