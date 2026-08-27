#!/usr/bin/env python3
"""Danbooru Tag & Wiki Search Tool for Crack Story Chat Asset Creation."""

from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
from pathlib import Path

# Search database paths: 1) local data, 2) novel-ai-image-skill, 3) user home
SEARCH_PATHS = [
    Path(__file__).resolve().parent / "data" / "wiki.sqlite3",
    Path("/Users/leejongmin/crack/novel-ai-image-skill/skills/novel-ai-image-skill/data/wiki.sqlite3"),
    Path.home() / "crack" / "novel-ai-image-skill" / "skills" / "novel-ai-image-skill" / "data" / "wiki.sqlite3",
]

TOKEN_RE = re.compile(r"[^\W_]+(?:[_'-][^\W_]+)*", re.UNICODE)


def find_database(custom_path: Path | None = None) -> Path | None:
    if custom_path and custom_path.is_file():
        return custom_path
    for p in SEARCH_PATHS:
        if p.is_file():
            return p
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="+", help="English tag names, concepts, or body keywords")
    parser.add_argument("--database", type=Path, default=None, help="Custom path to wiki.sqlite3")
    parser.add_argument("--limit", type=int, default=6, help="Maximum results per query")
    parser.add_argument("--body", action="store_true", help="Include full wiki description body")
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    return parser.parse_args()


def normalise(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", " ").split())


def fts_expression(query: str, operator: str) -> str:
    tokens = TOKEN_RE.findall(query.casefold().replace("_", " "))
    return f" {operator} ".join('"' + token.replace('"', '""') + '"' for token in tokens)


def row_to_dict(row: sqlite3.Row, include_body: bool) -> dict[str, object]:
    result: dict[str, object] = {
        "tag": row["tag"],
        "title": row["title"],
        "aliases": json.loads(row["aliases"]) if row["aliases"] else [],
        "category": row["category"],
        "match": row["match_type"],
        "snippet": row["snippet"],
    }
    if include_body:
        result["body"] = row["body"]
    return result


def search(connection: sqlite3.Connection, query: str, limit: int, include_body: bool) -> list[dict[str, object]]:
    exact = connection.execute(
        "SELECT tag, title, aliases, category, body, 'exact' AS match_type, "
        "substr(replace(replace(body, char(13), ' '), char(10), ' '), 1, 240) AS snippet "
        "FROM pages WHERE tag_norm = ? LIMIT ?",
        (normalise(query), limit),
    ).fetchall()
    rows = list(exact)
    seen = {row["tag"] for row in rows}
    remaining = limit - len(rows)
    if remaining <= 0:
        return [row_to_dict(row, include_body) for row in rows]

    for operator in ("AND", "OR"):
        expression = fts_expression(query, operator)
        if not expression:
            break
        found = connection.execute(
            "SELECT p.tag, p.title, p.aliases, p.category, p.body, "
            "'wiki' AS match_type, snippet(pages_fts, 3, '[', ']', ' … ', 24) AS snippet "
            "FROM pages_fts JOIN pages p ON p.id = pages_fts.rowid "
            "WHERE pages_fts MATCH ? ORDER BY bm25(pages_fts, 12.0, 8.0, 4.0, 1.0) LIMIT ?",
            (expression, max(limit * 3, 20)),
        ).fetchall()
        for row in found:
            if row["tag"] in seen:
                continue
            rows.append(row)
            seen.add(row["tag"])
            remaining -= 1
            if remaining == 0:
                break
        if remaining == 0 or found:
            break
    return [row_to_dict(row, include_body) for row in rows]


def main() -> int:
    args = parse_args()
    db_path = find_database(args.database)
    if not db_path:
        print(f"❌ 단부루 위키 데이터베이스(wiki.sqlite3)를 찾을 수 없습니다.")
        print(f"   탐색 경로: {[str(p) for p in SEARCH_PATHS]}")
        print(f"   novel-ai-image-skill이 설치되어 있거나 --database로 경로를 지정해주세요.")
        return 1

    connection = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    results = {query: search(connection, query, args.limit, args.body) for query in args.queries}
    connection.close()

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0

    print(f"🔍 단부루 태그 검색 결과 (DB: {db_path.name})\n" + "═" * 60)
    for query, items in results.items():
        print(f"\n📌 검색어: '{query}' ({len(items)}개 결과)")
        if not items:
            print("  (일치하는 태그 없음)")
            continue
        for item in items:
            match_badge = "⭐ [정확 일치]" if item["match"] == "exact" else "📖 [위키 검색]"
            aliases_str = f" (동의어: {', '.join(item['aliases'][:3])})" if item["aliases"] else ""
            print(f"  • {match_badge} {item['tag']}{aliases_str} [{item['category']}]")
            if item.get("snippet"):
                clean_snippet = re.sub(r"\s+", " ", str(item["snippet"])).strip()
                print(f"    └ 정의: {clean_snippet}")
            if args.body and item.get("body"):
                print(f"    └ 상세 본문:\n{item['body']}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
