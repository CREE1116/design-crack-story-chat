#!/usr/bin/env bash
# 이 저장소를 다른 환경으로 옮길 때 쓸 타르볼을 만든다.
#   ./scripts/pack-repo.sh                  ../skill-repo.tar.gz 생성
#   ./scripts/pack-repo.sh /경로/이름.tar.gz
#
# `.git` 을 넣지 않는다. 넣으면 받는 쪽에서 푼 순간 그쪽 `.git` 이 통째로
# 교체되어 remote 설정이 사라지고 히스토리가 타르볼 시점으로 되감긴다.
# 받는 쪽이 이미 푸시한 커밋도 같이 사라지는데, 파일만 보면 멀쩡해 보여서
# 다음 푸시 때까지 아무도 모른다. 실제로 두 번 발생했다.
#
# 커밋을 옮기고 싶으면 타르볼이 아니라 원격을 쓴다 — 만든 쪽에서 push,
# 받는 쪽에서 pull. 타르볼은 작업 파일을 옮기는 용도로만 쓴다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NAME="$(basename "$ROOT")"
OUT="${1:-$ROOT/../${NAME}.tar.gz}"

cd "$ROOT/.."
tar czf "$OUT" \
  --exclude="$NAME/.git" \
  --exclude="$NAME/.DS_Store" \
  --exclude=".DS_Store" \
  --exclude="__pycache__" \
  "$NAME"

echo "생성: $OUT"
echo "  $(tar tzf "$OUT" | wc -l | tr -d ' ')개 항목, .git 제외"

if tar tzf "$OUT" | grep -q "/\.git/"; then
  echo "FAIL: .git 이 들어갔다"; exit 1
fi
echo "확인: .git 없음"
