#!/usr/bin/env bash
# 배포용 .skill 파일을 만든다. -> dist/design-crack-story-chat.skill
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="design-crack-story-chat"
OUT="$ROOT/dist/$NAME.skill"

mkdir -p "$ROOT/dist"
rm -f "$OUT"
find "$ROOT/skills/$NAME" -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true
( cd "$ROOT/skills/$NAME" && zip -qr "$OUT" . -x '.DS_Store' '*/.DS_Store' )

echo "$OUT"
unzip -l "$OUT" | tail -3
