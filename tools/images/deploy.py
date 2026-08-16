#!/usr/bin/env python3
"""생성한 이미지를 전용 깃헙 저장소로 배포하고 {IMG} 주소를 만들어 준다.

프롬프트의 이미지 규칙은 축의 **닫힌 목록**을 전제한다. 모델이 목록에 없는
슬러그를 만들면 전부 깨진 링크가 되므로, 배포 시점이 그 계약을 마지막으로
검사할 수 있는 지점이다. 이 스크립트는 올리기 전에 먼저 검사한다.

기대하는 폴더 구조:

    <루트>/<인물>/<상황>.png
    <루트>/scene/<장면>.png
    <루트>/bg/<배경>.png
    <루트>/mob/<위협>.png

사용:
    python deploy.py --check                 검사만, 업로드 없음
    python deploy.py --dry-run               할 일만 출력
    python deploy.py --create                저장소가 없으면 만들고 배포
    python deploy.py                         배포
    python deploy.py --tag v2                태그를 찍어 캐시 지연 없이 배포
    python deploy.py --verify                배포 후 주소가 실제로 열리는지 확인

prompts.json의 deploy 절에서 기본값을 읽는다.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

try:
    from signal import SIGPIPE, SIG_DFL, signal as _signal
    _signal(SIGPIPE, SIG_DFL)
except (ImportError, ValueError, OSError):
    pass

HERE = Path(__file__).resolve().parent


def resolve_config(explicit: str | None) -> Path:
    """설정 파일을 찾는다: --config → $CRACK_PROMPTS → ./prompts.json.

    이미지 프롬프트는 작품의 파생 산출물이므로 `<작품>/build/assets/prompts.json`
    에 있다. 도구는 특정 작품에 묶이지 않고 그 경로를 받아 쓴다.
    """
    for candidate in (explicit, os.environ.get("CRACK_PROMPTS"), "prompts.json"):
        if candidate and Path(candidate).is_file():
            return Path(candidate).resolve()
    sys.exit(
        "설정 파일을 찾을 수 없습니다.\n"
        "  --config <작품>/build/assets/prompts.json 를 주거나\n"
        "  환경변수 CRACK_PROMPTS 를 설정하거나\n"
        "  현재 폴더에 prompts.json 을 두세요."
    )


EXT = ".png"
# 축 이름 → 저장소 안의 디렉터리. 인물은 슬러그 자체가 디렉터리라 별도 처리.
FIXED_AXES = {"scenes": "scene", "backgrounds": "bg", "monsters": "mob"}
MAX_FILE_MB = 20        # jsDelivr 파일 상한보다 훨씬 보수적으로 잡는다
WARN_FILE_MB = 2        # 스토리챗 삽화로는 이 이상이면 대개 과하다


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if check and result.returncode:
        sys.exit(f"실패: {' '.join(cmd)}\n{result.stderr.strip()}")
    return result.stdout.strip()


def load_config(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def expected(cfg: dict) -> dict[str, set[str]]:
    """축 목록에서 있어야 할 상대 경로 집합을 만든다."""
    want: dict[str, set[str]] = {}
    people = list(cfg.get("characters", {}))
    situations = list(cfg.get("situations", {}))
    want["인물"] = {f"{p}/{s}{EXT}" for p in people for s in situations}
    for key, folder in FIXED_AXES.items():
        want[folder] = {f"{folder}/{name}{EXT}" for name in cfg.get(key, {})}
    return want


def scan(root: Path) -> set[str]:
    return {
        str(p.relative_to(root)).replace("\\", "/")
        for p in root.rglob("*")
        if p.is_file() and not p.name.startswith(".") and p.suffix.lower() == EXT
    }


def audit(cfg: dict, root: Path) -> tuple[bool, set[str]]:
    """닫힌 목록 대비 검사. (통과여부, 올릴 파일 집합)을 돌려준다."""
    want = expected(cfg)
    all_want = set().union(*want.values())
    found = scan(root)

    unknown = sorted(found - all_want)
    ok = True

    print(f"## 커버리지  ({root})")
    for label, paths in want.items():
        have = len(paths & found)
        total = len(paths)
        mark = "" if have == total else f"  ← {total - have}장 없음"
        print(f"  {label:<8} {have:>3}/{total}{mark}")

    if unknown:
        ok = False
        print(f"\n## 목록에 없는 파일 {len(unknown)}개 — 슬러그 오타이거나 축 목록이 낡았다")
        for path in unknown[:20]:
            print(f"  X {path}")
        if len(unknown) > 20:
            print(f"  … 외 {len(unknown) - 20}개")
        print("  프롬프트의 축 목록에 없는 슬러그는 모델이 부를 수 없다.")
        print("  파일명을 고치거나 prompts.json의 축에 추가하고 통합 프롬프트도 갱신할 것.")

    heavy, huge = [], []
    for rel in sorted(found & all_want):
        mb = (root / rel).stat().st_size / 1_048_576
        if mb > MAX_FILE_MB:
            huge.append((rel, mb))
        elif mb > WARN_FILE_MB:
            heavy.append((rel, mb))
    if huge:
        ok = False
        print(f"\n## 너무 큰 파일 {len(huge)}개 (>{MAX_FILE_MB}MB)")
        for rel, mb in huge[:10]:
            print(f"  X {rel}  {mb:.1f}MB")
    if heavy:
        print(f"\n## 무거운 파일 {len(heavy)}개 (>{WARN_FILE_MB}MB) — 줄이는 편이 좋다")
        for rel, mb in heavy[:5]:
            print(f"  ? {rel}  {mb:.1f}MB")

    if not found:
        ok = False
        print("\n올릴 이미지가 없습니다.")

    return ok, found & all_want


def label(entry: dict | None, slug: str) -> str:
    return (entry or {}).get("ko") or slug


def size_of(entry: dict | None) -> str:
    size = (entry or {}).get("size")
    return f"{size[0]}×{size[1]}" if isinstance(size, list) and len(size) == 2 else "—"


def scaffold(cfg: dict, root: Path) -> int:
    """축 목록대로 빈 폴더와 배치표를 만든다.

    축은 컴파일 시점에 이미 닫혀 있으므로, 어떤 파일이 어디에 들어가야 하는지는
    그림을 그리기 전에 전부 정해져 있다. 사람이 폴더 이름을 손으로 만들면
    반드시 오타가 나고, 오타는 조용한 깨진 링크가 된다.
    """
    people = cfg.get("characters", {})
    situations = cfg.get("situations", {})
    found = scan(root) if root.is_dir() else set()
    lines = [
        "# 이미지 배치표",
        "",
        "`deploy.py --scaffold`가 생성한다. 아래 경로에 그림을 넣으면 된다.",
        "**파일 이름은 통합 프롬프트의 축 목록과 정확히 같아야 한다.** 한 글자만 달라도",
        "모델이 부를 수 없는 주소가 되고, 플레이 중에는 이미지가 그냥 안 뜨는 것으로만 보인다.",
        "",
        "전부 채울 필요는 없다. 없는 조합은 그 자리만 생략되도록 프롬프트가 규정한다.",
        "",
    ]
    made = 0

    def table(rows: list[tuple[str, str, str]]) -> None:
        lines.append("| 파일 | 내용 | 크기 | 상태 |")
        lines.append("|---|---|---|---|")
        for path, what, size in rows:
            mark = "있음" if path in found else "비어 있음"
            lines.append(f"| `{path}` | {what} | {size} | {mark} |")
        lines.append("")

    lines.append(f"## 인물 × 상황 — {len(people) * len(situations)}장")
    lines.append("")
    for slug, entry in people.items():
        folder = root / slug
        folder.mkdir(parents=True, exist_ok=True)
        made += 1
        lines.append(f"### `{slug}` — {label(entry, slug)}")
        lines.append("")
        rows = [(f"{slug}/{s}{EXT}", label(sv, s), size_of(sv)) for s, sv in situations.items()]
        table(rows)
        (folder / "README.md").write_text(
            f"# `{slug}` — {label(entry, slug)}\n\n"
            + "\n".join(f"- `{s}{EXT}` — {label(sv, s)} ({size_of(sv)})"
                        for s, sv in situations.items())
            + "\n\n파일 이름을 바꾸지 마세요. 통합 프롬프트의 상황 축과 같아야 합니다.\n",
            encoding="utf-8")

    for key, folder_name in FIXED_AXES.items():
        entries = cfg.get(key, {})
        if not entries:
            continue
        folder = root / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        made += 1
        lines.append(f"## `{folder_name}` — {len(entries)}장")
        lines.append("")
        table([(f"{folder_name}/{n}{EXT}", label(v, n), size_of(v)) for n, v in entries.items()])
        (folder / "README.md").write_text(
            f"# `{folder_name}`\n\n"
            + "\n".join(f"- `{n}{EXT}` — {label(v, n)} ({size_of(v)})" for n, v in entries.items())
            + "\n\n파일 이름을 바꾸지 마세요. 통합 프롬프트의 축 목록과 같아야 합니다.\n",
            encoding="utf-8")

    (root / "_배치표.md").write_text("\n".join(lines), encoding="utf-8")
    total = len(people) * len(situations) + sum(len(cfg.get(k, {})) for k in FIXED_AXES)
    print(f"폴더 {made}개, 자리 {total}개를 준비했습니다: {root}")
    print(f"  목록: {root / '_배치표.md'}")
    print(f"  이미 채워진 자리: {len(found)}개")
    print("\n  그림을 넣은 뒤 `python deploy.py --check` 로 이름을 확인하세요.")
    return 0


def base_url(repo: str, ref: str) -> str:
    return f"https://cdn.jsdelivr.net/gh/{repo}@{ref}"


def publish(cfg: dict, root: Path, files: set[str], args) -> str:
    repo = args.repo or cfg.get("deploy", {}).get("repo")
    if not repo or "/" not in repo:
        sys.exit("대상 저장소를 지정하세요: --repo owner/name (또는 prompts.json의 deploy.repo)")
    if not shutil.which("gh"):
        sys.exit("gh가 필요합니다: brew install gh")

    work = Path.cwd() / ".deploy-work"
    if work.exists():
        shutil.rmtree(work)

    exists = subprocess.run(["gh", "repo", "view", repo],
                            capture_output=True, text=True).returncode == 0
    if not exists:
        if not args.create:
            sys.exit(f"저장소가 없습니다: {repo}\n  --create 를 주면 공개 저장소로 만듭니다.")
        print(f"▸ 저장소 생성 {repo} (public — jsDelivr는 공개 저장소만 서빙합니다)")
        if not args.dry_run:
            run(["gh", "repo", "create", repo, "--public",
                 "--description", "크랙 스토리챗 이미지 자산"])

    print(f"▸ 파일 {len(files)}개 준비")
    if args.dry_run:
        print("  dry-run 이므로 아무것도 올리지 않습니다.")
        return base_url(repo, args.tag or cfg.get("deploy", {}).get("ref", "main"))

    if exists:
        run(["gh", "repo", "clone", repo, str(work), "--", "--depth", "1"])
        for stale in work.rglob("*"):
            if stale.is_file() and stale.suffix.lower() == EXT:
                stale.unlink()
    else:
        work.mkdir(parents=True)
        run(["git", "init", "-q", "-b", "main"], cwd=work)
        run(["git", "remote", "add", "origin", f"https://github.com/{repo}.git"], cwd=work)

    for rel in sorted(files):
        dest = work / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / rel, dest)
    (work / "README.md").write_text(
        "# 이미지 자산\n\n크랙 스토리챗용. `deploy.py`가 생성하므로 직접 수정하지 마세요.\n"
        f"\n주소 형태: `{base_url(repo, 'main')}/<인물>/<상황>.png`\n",
        encoding="utf-8")

    run(["git", "add", "-A"], cwd=work)
    if run(["git", "status", "--porcelain"], cwd=work):
        run(["git", "commit", "-qm", f"이미지 {len(files)}장 배포"], cwd=work)
        run(["git", "push", "-q", "-u", "origin", "main", "--force"], cwd=work)
        print("▸ 푸시 완료")
    else:
        print("▸ 변경 없음")

    ref = cfg.get("deploy", {}).get("ref", "main")
    if args.tag:
        run(["git", "tag", "-f", args.tag], cwd=work)
        run(["git", "push", "-q", "-f", "origin", args.tag], cwd=work)
        ref = args.tag
        print(f"▸ 태그 {args.tag} 푸시")

    shutil.rmtree(work, ignore_errors=True)
    return base_url(repo, ref)


def verify(url_base: str, files: set[str]) -> bool:
    sample = sorted(files)[:5]
    print(f"\n## 주소 확인 ({len(sample)}개 표본)")
    ok = True
    for rel in sample:
        url = f"{url_base}/{rel}"
        try:
            request = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(request, timeout=15) as response:
                print(f"  OK  {response.status}  {url}")
        except urllib.error.HTTPError as exc:
            ok = False
            print(f"  X   {exc.code}  {url}")
        except OSError as exc:
            ok = False
            print(f"  X   {exc}  {url}")
    if not ok:
        print("  jsDelivr는 첫 요청 시 원본을 가져오므로 푸시 직후 잠깐 404가 날 수 있습니다.")
        print("  1~2분 뒤 다시 확인하세요.")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="이미지 자산을 깃헙+jsDelivr로 배포한다")
    ap.add_argument("--config", help="prompts.json 경로 (기본: $CRACK_PROMPTS 또는 ./prompts.json)")
    ap.add_argument("--root", help="이미지 루트 (기본: 현재 폴더의 output_dir)")
    ap.add_argument("--repo", help="대상 저장소 owner/name")
    ap.add_argument("--create", action="store_true", help="저장소가 없으면 공개로 생성")
    ap.add_argument("--tag", help="이 태그를 찍고 주소에 사용 (캐시 지연 없음)")
    ap.add_argument("--scaffold", action="store_true",
                    help="축 목록대로 빈 폴더와 배치표를 만든다 (그림 넣기 전에 실행)")
    ap.add_argument("--check", action="store_true", help="검사만 하고 종료")
    ap.add_argument("--dry-run", action="store_true", help="업로드 없이 계획만 출력")
    ap.add_argument("--verify", action="store_true", help="배포 후 주소가 열리는지 확인")
    args = ap.parse_args()

    config_path = resolve_config(args.config)
    cfg = load_config(config_path)
    root = Path(args.root or Path.cwd() / cfg.get("config", {}).get("output_dir", "out"))

    if args.scaffold:
        root.mkdir(parents=True, exist_ok=True)
        return scaffold(cfg, root)

    if not root.is_dir():
        sys.exit(f"이미지 폴더가 없습니다: {root}\n  먼저 `python deploy.py --scaffold` 를 실행하세요.")

    ok, files = audit(cfg, root)
    if not ok:
        print("\n검사 실패 — 위 문제를 고치고 다시 실행하세요.")
        return 1
    if args.check:
        print(f"\n검사 통과 — 올릴 파일 {len(files)}개.")
        return 0

    url = publish(cfg, root, files, args)

    print(f"\n## 통합 프롬프트에 넣을 값")
    print(f"  {{IMG}} = {url}")
    print(f"\n  예: ![]({url}/ju-habin/normal.png)")
    print("\n  통합 프롬프트의 `{IMG}`를 위 주소로 치환하거나, 자리표시자를 그대로 두고")
    print("  크랙 UI에서 치환하세요. 축 목록은 프롬프트와 반드시 일치해야 합니다.")

    if args.tag:
        print(f"\n  태그 {args.tag} 를 썼으므로 이 주소는 영구 캐시됩니다.")
    else:
        print("\n  브랜치 주소는 jsDelivr가 최대 12시간 캐시합니다. 이미지를 갈아끼운 뒤")
        print("  즉시 반영하려면 --tag v2 처럼 새 태그를 쓰세요.")

    if args.verify and not args.dry_run:
        return 0 if verify(url, files) else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
