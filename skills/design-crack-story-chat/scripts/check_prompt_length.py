#!/usr/bin/env python3
"""Check a final Crack prompt against its character budget."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# 출력이 head 등으로 잘려도 트레이스백 없이 종료한다.
try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):  # Windows 등
    pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Count the final prompt text and enforce the Crack limit."
    )
    parser.add_argument(
        "paths",
        nargs="+",
        help="One or more files, or '-' alone to read stdin",
    )
    parser.add_argument(
        "--require-single",
        action="store_true",
        help="Require exactly one final publish artifact",
    )
    parser.add_argument("--limit", type=int, default=7000)
    parser.add_argument("--target", type=int, default=6500)
    return parser.parse_args()


def read_text(paths: list[str]) -> str:
    if paths == ["-"]:
        return sys.stdin.read()
    if "-" in paths:
        raise ValueError("'-' must be used alone")
    return "\n".join(Path(path).read_text(encoding="utf-8") for path in paths)


def main() -> int:
    args = parse_args()
    if args.limit < 1 or args.target < 1 or args.target > args.limit:
        print("error: require 0 < target <= limit", file=sys.stderr)
        return 2
    if args.require_single and len(args.paths) != 1:
        print(
            "error: --require-single expects exactly one publish artifact",
            file=sys.stderr,
        )
        return 2

    try:
        text = read_text(args.paths)
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    codepoints = len(text)
    utf16_units = len(text.encode("utf-16-le")) // 2
    count = max(codepoints, utf16_units)
    remaining = args.limit - count
    if count > args.limit:
        print(
            f"FAIL {count}/{args.limit} budget chars ({-remaining} over; "
            f"codepoints={codepoints}, utf16={utf16_units})"
        )
        return 1
    if count > args.target:
        print(
            f"WARN {count}/{args.limit} budget chars ({remaining} remaining; "
            f"target {args.target}; codepoints={codepoints}, utf16={utf16_units})"
        )
        return 0

    print(
        f"PASS {count}/{args.limit} budget chars ({remaining} remaining; "
        f"codepoints={codepoints}, utf16={utf16_units})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
