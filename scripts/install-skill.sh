#!/usr/bin/env bash
# 이 저장소의 스킬을 에이전트가 읽는 위치에 연결한다.
#   ./scripts/install-skill.sh            심볼릭 링크 (저장소를 고치면 바로 반영)
#   ./scripts/install-skill.sh --copy     사본 (저장소와 분리)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="design-crack-story-chat"
SRC="$ROOT/skills/$NAME"
MODE="${1:-link}"

for DEST in "$HOME/.claude/skills" "$HOME/.agents/skills"; do
  mkdir -p "$DEST"
  TARGET="$DEST/$NAME"
  [ -e "$TARGET" ] || [ -L "$TARGET" ] && rm -rf "$TARGET"
  if [ "$MODE" = "--copy" ]; then
    cp -R "$SRC" "$TARGET"; echo "복사: $TARGET"
  else
    ln -s "$SRC" "$TARGET"; echo "연결: $TARGET → $SRC"
  fi
done

echo
echo "확인: 에이전트에게 \"design-crack-story-chat 스킬 로딩해줘\" 라고 해보세요."
[ "$MODE" = "--copy" ] || echo "링크 방식이라 저장소를 고치면 즉시 반영됩니다."
