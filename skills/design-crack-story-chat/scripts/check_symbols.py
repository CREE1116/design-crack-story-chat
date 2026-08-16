#!/usr/bin/env python3
"""Audit a compiled prompt for meaning-bearing symbols used without a definition.

A compact rule dialect only works if every symbol carrying assigned meaning is
defined before first use. Authors reliably define the symbol they just invented
and forget the fifteen they have been using for hours.

A symbol counts as defined when it appears in the legend section, or is glossed
anywhere in the document by one of these patterns:

    ⌛=응답 번호          symbol immediately followed by '='
    😐중립                symbol immediately followed by a Hangul/Latin gloss
    `━` 구분선            symbol inside backticks (mentioned rather than used)

Usage:
    check_symbols.py build/integrated-prompt-safe.md
    check_symbols.py build/*.md --legend "# 표기"
    check_symbols.py build/*.md --strict      # layout glyphs also required

Exit status is non-zero when an operator or emoji is used but never defined.
"""

from __future__ import annotations

import re
import sys
import unicodedata

# 출력이 head 등으로 잘려도 트레이스백 없이 종료한다.
try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):  # Windows 등
    pass

# Carry assigned meaning; must be defined.
OPERATORS = set("ⓤⓒⓝⓐ→←↑↓⇒≤≥±×÷·|｜/※≠≈")

# Visual scaffolding; reported for review but never fatal unless --strict.
LAYOUT = set("━─│┃▸▪▶◆◇○●•…★☆♂♀§¶")


def is_emoji(char: str) -> bool:
    point = ord(char)
    if point < 0x2190:
        return False
    if 0x1F000 <= point <= 0x1FAFF:
        return True
    return unicodedata.category(char) == "So" and char not in LAYOUT


def classify(char: str) -> str | None:
    if char in OPERATORS:
        return "operator"
    if char in LAYOUT:
        return "layout"
    if is_emoji(char):
        return "emoji"
    return None


def used_symbols(text: str) -> dict[str, str]:
    return {c: kind for c in set(text) if (kind := classify(c))}


def split_legend(text: str, heading: str) -> tuple[str, int]:
    match = re.search(rf"^{re.escape(heading)}\s*$", text, re.MULTILINE)
    if not match:
        return "", -1
    rest = text[match.end() :]
    following = re.search(r"^#{1,2} ", rest, re.MULTILINE)
    end = match.end() + (following.start() if following else len(rest))
    return text[match.start() : end], match.start()


def glossed(text: str, symbol: str, kind: str) -> bool:
    """A symbol is glossed by an explicit definition, a backticked mention, or —
    for emoji only — membership in a scale list such as `😐중립 🙂호의 😄친밀`.

    Adjacency to Hangul alone is deliberately NOT accepted: a Korean particle
    following a symbol (`ⓝ는`, `/수형`) is indistinguishable from a gloss and
    silently suppresses real findings.
    """
    escaped = re.escape(symbol)
    if re.search(rf"{escaped}\s*=", text):
        return True
    if any(symbol in span for span in re.findall(r"`([^`\n]{1,40})`", text)):
        return True  # mentioned inside an inline code span, e.g. `←근거`
    # Closed-set declaration on the right of a short term: 날씨=☀️🌤️☁️🌧️❄️ 중 1개
    for term, rhs in re.findall(r"([^\s=]{1,8})=([^.\n]{1,60})", text):
        if symbol in rhs and symbol not in term:
            return True
    if kind != "emoji":
        return False
    for line in text.splitlines():
        if symbol not in line:
            continue
        pairs = [m for m in re.finditer(r"(\S)[가-힣]{2,}", line) if is_emoji(m.group(1))]
        if len(pairs) >= 3 and any(m.group(1) == symbol for m in pairs):
            return True
    return False


def line_of(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def audit(path: str, heading: str, strict: bool) -> bool:
    text = open(path, encoding="utf-8").read()
    legend, legend_at = split_legend(text, heading)
    if legend_at < 0:
        print(f"FAIL {path}: no legend section titled {heading!r}")
        return False

    body = text[:legend_at] + text[legend_at + len(legend) :]
    in_legend = set(legend)
    ok = True

    buckets: dict[str, list[str]] = {"operator": [], "emoji": [], "layout": []}
    for symbol, kind in sorted(used_symbols(body).items()):
        if symbol in in_legend or glossed(text, symbol, kind):
            continue
        buckets[kind].append(symbol)

    for kind in ("operator", "emoji"):
        if buckets[kind]:
            ok = False
            detail = ", ".join(f"{s!r}×{body.count(s)}" for s in buckets[kind])
            print(f"FAIL {path}: {kind} used but undefined — {detail}")
    if buckets["layout"]:
        detail = ", ".join(f"{s!r}×{body.count(s)}" for s in buckets["layout"])
        label = "FAIL" if strict else "INFO"
        if strict:
            ok = False
        print(f"{label} {path}: layout glyph undefined — {detail}")

    for symbol in sorted(s for s in in_legend if classify(s)):
        first = text.find(symbol)
        if 0 <= first < legend_at:
            ok = False
            print(f"FAIL {path}: {symbol!r} used at line {line_of(text, first)} "
                  f"before legend at line {line_of(text, legend_at)}")
        elif symbol not in body:
            print(f"WARN {path}: {symbol!r} defined in legend but never used")

    if ok:
        defined = sum(1 for s in in_legend if classify(s))
        print(f"PASS {path}: {defined} legend symbols, all used symbols defined before use")
    return ok


def main() -> int:
    args = sys.argv[1:]
    heading = "# 표기"
    strict = False
    if "--strict" in args:
        args.remove("--strict")
        strict = True
    if "--legend" in args:
        at = args.index("--legend")
        heading = args[at + 1]
        del args[at : at + 2]
    if not args:
        print(__doc__, file=sys.stderr)
        return 2
    ok = True
    for path in args:
        try:
            ok = audit(path, heading, strict) and ok
        except OSError as exc:
            print(f"FAIL {path}: {exc}")
            ok = False
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
