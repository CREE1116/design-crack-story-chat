#!/usr/bin/env python3
"""Smart Background Cropper & Auto-Renamer for Crack Story Chat.

1. ✂️ Smart Crop & Resize:
   Crops any source image (e.g. NovelAI 1216x832 landscape, 1920x1080) to Crack
   standard wide banner ratio (default 1024x400) using center/top/bottom anchor
   and high-quality Lanczos resampling.

2. 🏷️ Intelligent Matching & Auto-Renaming:
   Reads asset placement table (e.g. 에셋_배치표.md), preset-backgrounds.json, or
   directory order, normalizes NFC/NFD Korean characters, and outputs cleanly
   sequenced filenames (e.g. bg01_마왕성_로비_결계_게이트.webp or scene/a01.webp).

3. 🚀 WebP / PNG multi-format batch generation.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    from PIL import Image
except ImportError:
    sys.exit("Pillow 라이브러리가 필요합니다: pip install Pillow")


def nfc(text: str) -> str:
    """Normalize unicode to NFC (fixes macOS NFD jamo decomposition)."""
    return unicodedata.normalize("NFC", text).strip()


@dataclass
class BackgroundTarget:
    index: int
    code: str                  # e.g. 'bg01', 'a01', '01'
    name: str                  # e.g. '마왕성 로비 (결계 게이트)'
    filename_clean: str        # e.g. '마왕성_로비_결계_게이트'
    matched_src: Path | None = None


def parse_table_order(table_path: Path) -> list[BackgroundTarget]:
    """Parse background order and names from markdown asset placement table."""
    if not table_path.exists():
        print(f"❌ 배치표 파일을 찾을 수 없습니다: {table_path}", file=sys.stderr)
        return []

    text = nfc(table_path.read_text(encoding="utf-8"))
    targets: list[BackgroundTarget] = []

    # 1. Try to find a section specifically for backgrounds (배경, Scene, etc.)
    bg_section_match = re.search(
        r"(?:^#{2,4}\s*[^\n]*(?:배경|scene|scenery|장소|공간)[^\n]*\n)([\s\S]*?)(?=\n#{2,4}\s|\Z)",
        text,
        re.MULTILINE | re.IGNORECASE
    )
    search_text = bg_section_match.group(1) if bg_section_match else text

    # Match rows like: | **bg01** | 마왕성 로비 (결계 게이트) | `bg01_...png` |
    rows = re.findall(
        r"^\|\s*`?\*?\*?([a-zA-Z0-9_/.-]+)\*?\*?`?\s*\|\s*`?\*?\*?([^|]+?)\*?\*?`?\s*\|",
        search_text,
        re.MULTILINE
    )

    idx = 1
    for cid_raw, name_raw in rows:
        cid = nfc(cid_raw).strip("*` ").lower()
        name = nfc(name_raw).strip("*` ")

        if cid in ("코드", "id", "번호", "---", ":---:", ":---", ""):
            continue
        # Filter for background codes or keywords
        if not (cid.startswith("bg") or cid.startswith("scene")) and not any(
            k in name for k in ("실", "홀", "룸", "방", "거리", "길", "사옥", "게이트", "던전", "라운지", "광장", "연구실", "본부", "주방", "포장마차", "테라스", "로비")
        ):
            continue

        clean_name = re.sub(r"[^\w\s-]", "", name).strip()
        clean_file_slug = re.sub(r"[\s/]+", "_", clean_name)

        targets.append(BackgroundTarget(
            index=idx,
            code=cid if cid.startswith("bg") else f"bg{idx:02d}",
            name=name,
            filename_clean=clean_file_slug
        ))
        idx += 1

    return targets


def parse_preset_order(preset_path: Path) -> list[BackgroundTarget]:
    """Parse background order from preset-backgrounds.json."""
    if not preset_path.exists():
        print(f"❌ 프리셋 파일을 찾을 수 없습니다: {preset_path}", file=sys.stderr)
        return []

    data = json.loads(preset_path.read_text(encoding="utf-8"))
    targets: list[BackgroundTarget] = []

    poses = data.get("poses", [])
    for idx, item in enumerate(poses, 1):
        name = nfc(item.get("name", f"배경_{idx:02d}"))
        clean_name = re.sub(r"[^\w\s-]", "", name).strip()
        clean_file_slug = re.sub(r"[\s/]+", "_", clean_name)
        targets.append(BackgroundTarget(
            index=idx,
            code=f"bg{idx:02d}",
            name=name,
            filename_clean=clean_file_slug
        ))

    return targets


def match_sources_to_targets(
    src_files: list[Path],
    targets: list[BackgroundTarget]
) -> list[BackgroundTarget]:
    """Fuzzy match source images to target specs using normalized name tokens."""
    unmatched_src = list(src_files)

    for target in targets:
        # 1. Exact match on clean filename
        target_tokens = set(re.findall(r"[가-힣a-zA-Z0-9]+", target.name))

        best_match = None
        best_score = 0

        for src in unmatched_src:
            src_name = nfc(src.stem)
            src_tokens = set(re.findall(r"[가-힣a-zA-Z0-9]+", src_name))

            # If code matches (e.g. bg01 in filename)
            if target.code in src_name.lower():
                best_match = src
                break

            # Token overlap score
            overlap = len(target_tokens.intersection(src_tokens))
            if overlap > best_score:
                best_score = overlap
                best_match = src

        if best_match and (best_score >= 1 or target.code in nfc(best_match.stem).lower()):
            target.matched_src = best_match
            unmatched_src.remove(best_match)

    return targets


def smart_crop_and_resize(
    img: Image.Image,
    target_w: int = 1024,
    target_h: int = 400,
    anchor: Literal["center", "top", "bottom"] = "center"
) -> Image.Image:
    """Crop image to target aspect ratio and resize using high-quality Lanczos resampling."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) < 1e-4:
        # Already same aspect ratio
        crop_box = (0, 0, src_w, src_h)
    elif src_ratio < target_ratio:
        # Source is taller than target: crop height
        crop_h = int(src_w / target_ratio)
        if anchor == "top":
            y = 0
        elif anchor == "bottom":
            y = src_h - crop_h
        else:  # center
            y = (src_h - crop_h) // 2
        crop_box = (0, y, src_w, y + crop_h)
    else:
        # Source is wider than target: crop width
        crop_w = int(src_h * target_ratio)
        if anchor == "left":
            x = 0
        elif anchor == "right":
            x = src_w - crop_w
        else:  # center
            x = (src_w - crop_w) // 2
        crop_box = (x, 0, x + crop_w, src_h)

    cropped = img.crop(crop_box)
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def process_backgrounds(
    src_dir: Path,
    out_dir: Path,
    table_path: Path | None = None,
    preset_path: Path | None = None,
    target_w: int = 1024,
    target_h: int = 400,
    anchor: str = "center",
    style: str = "bg",         # 'bg' (bg01_name), 'scene' (a01), 'clean' (01_name)
    format_opt: str = "webp",  # 'webp', 'png', 'both'
    quality: int = 90,
    dry_run: bool = False
) -> int:
    if not src_dir.exists():
        print(f"❌ 원본 폴더를 찾을 수 없습니다: {src_dir}", file=sys.stderr)
        return 1

    # Find all source images
    src_files = [
        p for p in src_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    ]
    if not src_files:
        print(f"❌ 원본 폴더({src_dir})에 이미지 파일이 없습니다.", file=sys.stderr)
        return 1

    print(f"📂 원본 이미지 {len(src_files)}개 발견 ({src_dir})")

    # Determine targets
    targets: list[BackgroundTarget] = []
    if table_path and table_path.exists():
        targets = parse_table_order(table_path)
        print(f"📋 배치표({table_path.name})에서 배경 목록 {len(targets)}개 로드")
    elif preset_path and preset_path.exists():
        targets = parse_preset_order(preset_path)
        print(f"📋 프리셋({preset_path.name})에서 배경 목록 {len(targets)}개 로드")
    else:
        # Fallback: Sort src_files alphabetically
        for idx, src in enumerate(sorted(src_files, key=lambda p: nfc(p.name)), 1):
            stem = nfc(src.stem)
            clean_stem = re.sub(r"^bg\d+_", "", stem)
            targets.append(BackgroundTarget(
                index=idx,
                code=f"bg{idx:02d}",
                name=clean_stem,
                filename_clean=clean_stem,
                matched_src=src
            ))

    if table_path or preset_path:
        targets = match_sources_to_targets(src_files, targets)

    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n⚙️ 작업 설정: 규격 {target_w}x{target_h} ({anchor} 크롭), 출력 포맷: {format_opt.upper()}")
    print("-" * 75)

    success_count = 0
    for t in targets:
        if not t.matched_src or not t.matched_src.exists():
            print(f"⚠️ [{t.code}] {t.name} -> 일치하는 원본 파일을 찾지 못했습니다.")
            continue

        # Generate output filename based on style
        if style == "scene":
            out_stem = f"a{t.index:02d}"
        elif style == "clean":
            out_stem = f"{t.index:02d}_{t.filename_clean}"
        else:  # default 'bg'
            out_stem = f"{t.code}_{t.filename_clean}"

        print(f"✂️ [{t.code}] {t.matched_src.name} ➡️ {out_stem}")

        if dry_run:
            success_count += 1
            continue

        try:
            with Image.open(t.matched_src) as img:
                # Convert to RGB/RGBA
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.mode else "RGB")

                processed = smart_crop_and_resize(img, target_w, target_h, anchor)

                if format_opt in ("webp", "both"):
                    out_webp = out_dir / f"{out_stem}.webp"
                    processed.save(out_webp, "WEBP", quality=quality, method=6)

                if format_opt in ("png", "both"):
                    out_png = out_dir / f"{out_stem}.png"
                    processed.save(out_png, "PNG", optimize=True)

                success_count += 1
        except Exception as e:
            print(f"  ❌ 변환 실패 ({t.matched_src.name}): {e}", file=sys.stderr)

    print("-" * 75)
    action_verb = "계획 완료" if dry_run else "저장 완료"
    print(f"🎉 총 {success_count}/{len(targets)}개 배경 이미지 크롭 및 리네이밍 {action_verb} ({out_dir})\n")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, required=True, help="Source images directory (e.g. image-배경_원본)")
    parser.add_argument("--out", type=Path, required=True, help="Output directory (e.g. image/배경 or deploy/scene)")
    parser.add_argument("--table", type=Path, help="Asset table path (e.g. image/에셋_배치표.md)")
    parser.add_argument("--preset", type=Path, help="Preset backgrounds JSON (e.g. build/assets/preset-backgrounds.json)")
    parser.add_argument("--size", type=str, default="1024x400", help="Target size WxH (default: 1024x400)")
    parser.add_argument("--anchor", choices=["center", "top", "bottom"], default="center", help="Crop anchor (default: center)")
    parser.add_argument("--style", choices=["bg", "scene", "clean"], default="bg", help="Naming style: bg (bg01_name), scene (a01), clean (01_name)")
    parser.add_argument("--format", choices=["webp", "png", "both"], default="webp", help="Output format (default: webp)")
    parser.add_argument("--quality", type=int, default=90, help="WebP quality 1-100 (default: 90)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    args = parser.parse_args()

    # Parse target size
    m = re.match(r"^(\d+)[xX](\d+)$", args.size.strip())
    if not m:
        sys.exit(f"❌ 잘못된 크기 형식입니다: {args.size} (예: 1024x400)")
    target_w, target_h = int(m.group(1)), int(m.group(2))

    return process_backgrounds(
        src_dir=args.src,
        out_dir=args.out,
        table_path=args.table,
        preset_path=args.preset,
        target_w=target_w,
        target_h=target_h,
        anchor=args.anchor,
        style=args.style,
        format_opt=args.format,
        quality=args.quality,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    raise SystemExit(main())
