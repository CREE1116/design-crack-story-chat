#!/usr/bin/env bash
# 스토리챗 프로젝트 하나에 모든 검사를 돌린다.
#   ./scripts/validate.sh examples/hunter
set -uo pipefail

PROJ="${1:-examples/hunter}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
S="$ROOT/skills/design-crack-story-chat/scripts"
EMU="$ROOT/tools/crack-emu"
FAIL=0

run() { echo; echo "── $1"; shift; "$@" || FAIL=1; }

run "원본 대비 신선도"  python3 "$S/check_freshness.py" "$PROJ"
run "프로젝트 구조"     python3 "$S/check_project_layout.py" "$PROJ"
run "이름 규칙"         python3 "$S/check_naming.py" "$PROJ"
run "키워드북 · 슬롯 배치" env PYTHONPATH="$EMU" python3 -m crack_emulator \
      --project "$PROJ/build" lint
run "기호 정의"         python3 "$S/check_symbols.py" \
      "$PROJ/build/integrated-prompt-safe.md" "$PROJ/build/integrated-prompt-unsafe.md"

echo
echo "── 3슬롯 실측"
echo "   가상 씬 목록 시뮬레이션은 폐지했습니다. 실제 턴을 돌려서 측정하세요:"
echo "     PYTHONPATH=$EMU python3 -m crack_emulator --project $PROJ/build \\"
echo "       replay qa1 $EMU/scenarios/onboarding.txt"
echo "     PYTHONPATH=$EMU python3 -m crack_emulator --project $PROJ/build report"

echo
[ "$FAIL" -eq 0 ] && echo "전체 통과" || echo "실패 있음"
exit "$FAIL"
