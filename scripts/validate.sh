#!/usr/bin/env bash
# 스토리챗 프로젝트 하나에 모든 검사를 돌린다.
#   ./scripts/validate.sh examples/hunter
set -uo pipefail

PROJ="${1:-examples/hunter}"
S="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/skills/design-crack-story-chat/scripts"
FAIL=0

run() { echo; echo "── $1"; shift; "$@" || FAIL=1; }

run "프로젝트 구조"   python3 "$S/check_project_layout.py" "$PROJ"
run "키워드북 형식"   python3 "$S/check_keyword_book.py" "$PROJ/build/keyword-book.md"
run "기호 정의"       python3 "$S/check_symbols.py" \
      "$PROJ/build/integrated-prompt-safe.md" "$PROJ/build/integrated-prompt-unsafe.md"

if [ -f "$PROJ/.assets/kb-scenes.txt" ]; then
  echo; echo "── 3슬롯 시뮬레이션"
  python3 "$S/check_kb_slots.py" "$PROJ/build/keyword-book.md" "$PROJ/.assets/kb-scenes.txt" || true
  echo "   (슬롯 초과는 설계 판단이 필요한 경고입니다. 통과 조건에 넣지 않습니다.)"
fi

echo
[ "$FAIL" -eq 0 ] && echo "전체 통과" || echo "실패 있음"
exit "$FAIL"
