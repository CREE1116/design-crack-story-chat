#!/usr/bin/env python3
"""배경 이미지 일괄 크롭·크기 변경·선택적 장소 배지·파일명 변환.

Pillow 필요. --dry-run으로 매칭과 출력 경로를 확인한다.
기본 1024x400은 변경 가능한 작업 기본값이며 플랫폼 강제 규격이 아니다.
JSON은 배열 또는 backgrounds/scenes/poses 배열을 지원한다.
각 항목: name 필수, code/source 선택. source는 원본 폴더 바로 아래의 파일명.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    sys.exit("Pillow 라이브러리가 필요합니다: pip install Pillow")


def nfc(text: str) -> str:
    """Normalize unicode to NFC (fixes macOS NFD jamo decomposition)."""
    return unicodedata.normalize("NFC", text).strip()


@dataclass
class BackgroundTarget:
    index: int
    code: str                  # e.g. 'bg01', 'a01', '01'
    name: str                  # e.g. '본관 로비'
    filename_clean: str        # e.g. '본관_로비'
    source: str | None = None
    matched_src: Path | None = None


def parse_table_order(table_path: Path) -> list[BackgroundTarget]:
    """Parse background order and names from markdown asset placement table."""
    if not table_path.exists():
        print(f"❌ 배치표 파일을 찾을 수 없습니다: {table_path}", file=sys.stderr)
        return []

    text = nfc(table_path.read_text(encoding="utf-8"))
    targets: list[BackgroundTarget] = []

    bg_section_match = re.search(
        r"(?:^#{2,4}\s*[^\n]*(?:배경|scene|scenery|장소|공간)[^\n]*\n)([\s\S]*?)(?=\n#{2,4}\s|\Z)",
        text,
        re.MULTILINE | re.IGNORECASE
    )
    search_text = bg_section_match.group(1) if bg_section_match else text

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
        clean_name = re.sub(r"[^\w\s-]", "", name).strip()
        clean_file_slug = re.sub(r"[\s/]+", "_", clean_name)

        targets.append(BackgroundTarget(
            index=idx,
            code=cid,
            name=name,
            filename_clean=clean_file_slug
        ))
        idx += 1

    return targets


def parse_preset_order(preset_path: Path) -> list[BackgroundTarget]:
    """Parse background order from preset-backgrounds.json / scenes.json."""
    if not preset_path.exists():
        print(f"❌ 프리셋 파일을 찾을 수 없습니다: {preset_path}", file=sys.stderr)
        return []

    data = json.loads(preset_path.read_text(encoding="utf-8"))
    targets: list[BackgroundTarget] = []

    poses = data if isinstance(data, list) else next((data[k] for k in ("backgrounds", "scenes", "poses") if k in data), [])
    if not isinstance(poses, list):
        raise ValueError("JSON 목록은 배열이어야 합니다")
    for idx, item in enumerate(poses, 1):
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"].strip():
            raise ValueError("각 JSON 항목에는 비어 있지 않은 name이 필요합니다")
        name = nfc(item.get("name", f"배경_{idx:02d}"))
        clean_name = re.sub(r"[^\w\s-]", "", name).strip()
        clean_file_slug = re.sub(r"[\s/]+", "_", clean_name)
        targets.append(BackgroundTarget(
            index=idx,
            code=nfc(str(item.get("code", f"bg{idx:02d}"))),
            source=item.get("source"),
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
        if target.source:
            candidates = [p for p in unmatched_src if nfc(p.name) == nfc(target.source)]
        else:
            code = re.compile(r"(?<![a-z0-9])" + re.escape(target.code.casefold()) + r"(?![a-z0-9])")
            candidates = [p for p in unmatched_src if code.search(nfc(p.stem).casefold())]
            if not candidates:
                tokens = set(re.findall(r"\w+", target.name.casefold()))
                scores = [(len(tokens & set(re.findall(r"\w+", nfc(p.stem).casefold()))), p) for p in unmatched_src]
                best = max((score for score, _ in scores), default=0)
                candidates = [p for score, p in scores if best and score == best]
        if len(candidates) != 1:
            raise ValueError(f"{target.name}: 원본 매칭 {len(candidates)}개. JSON source로 파일명을 지정하세요")
        target.matched_src = candidates[0]
        unmatched_src.remove(candidates[0])
    return targets


def smart_crop_and_resize(
    img: Image.Image,
    target_w: int = 1024,
    target_h: int = 400,
    anchor: Literal["center", "top", "bottom", "left", "right"] = "center"
) -> Image.Image:
    """Crop image to target aspect ratio and resize using high-quality Lanczos resampling."""
    src_w, src_h = img.size
    target_ratio = target_w / target_h
    src_ratio = src_w / src_h

    if abs(src_ratio - target_ratio) < 1e-4:
        crop_box = (0, 0, src_w, src_h)
    elif src_ratio < target_ratio:
        crop_h = max(1, int(src_w / target_ratio))
        if anchor == "top":
            y = 0
        elif anchor == "bottom":
            y = src_h - crop_h
        else:
            y = (src_h - crop_h) // 2
        crop_box = (0, y, src_w, y + crop_h)
    else:
        crop_w = max(1, int(src_h * target_ratio))
        if anchor == "left":
            x = 0
        elif anchor == "right":
            x = src_w - crop_w
        else:
            x = (src_w - crop_w) // 2
        crop_box = (x, 0, x + crop_w, src_h)

    cropped = img.crop(crop_box)
    return cropped.resize((target_w, target_h), Image.Resampling.LANCZOS)


def find_korean_font(preferred_size: int = 18):
    """Find the best available Korean sans-serif font across macOS/Linux/Windows."""
    candidates = [
        ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 4),  # macOS Apple SD Gothic Neo SemiBold
        ("/System/Library/Fonts/AppleSDGothicNeo.ttc", 0),  # macOS Regular
        ("/Library/Fonts/Pretendard-SemiBold.otf", None),
        ("/Library/Fonts/Pretendard-Medium.otf", None),
        ("/Library/Fonts/NanumGothicBold.ttf", None),
        ("/Library/Fonts/NanumGothic.ttf", None),
        ("C:\\Windows\\Fonts\\malgun.ttf", None),        # Windows Malgun Gothic
        ("C:\\Windows\\Fonts\\malgunbd.ttf", None),
        ("/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf", None),
        ("/usr/share/fonts/truetype/nanum/NanumGothic.ttf", None),
    ]

    for path_str, idx in candidates:
        if os.path.exists(path_str):
            try:
                if idx is not None:
                    return ImageFont.truetype(path_str, preferred_size, index=idx)
                return ImageFont.truetype(path_str, preferred_size)
            except Exception:
                pass

    try:
        return ImageFont.load_default()
    except Exception:
        return None


def add_location_badge_aa(
    img: Image.Image,
    location_name: str,
    font_size: int = 18,
    scale: int = 4,
    font_path: Path | None = None
) -> Image.Image:
    """Overlay a sleek dark-glass pill badge with red status dot and location text."""
    base = img.convert("RGBA")
    w, h = base.size

    # Format location name: convert parentheses into elegant middle dot
    display_name = re.sub(r"\s*\(([^)]+)\)", r" · \1", location_name).strip()

    sw, sh = w * scale, h * scale

    font = ImageFont.truetype(str(font_path), font_size * scale) if font_path else find_korean_font(preferred_size=font_size * scale)
    if font is None:
        return base

    bbox = font.getbbox(display_name)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]

    pill_h = 35 * scale
    radius = pill_h / 2.0

    margin_left = 28 * scale
    margin_bottom = 22 * scale

    x0 = margin_left
    y1 = sh - margin_bottom
    y0 = y1 - pill_h

    red_dot_x = x0 + 19.5 * scale
    red_dot_y = y0 + radius
    red_dot_r = 4.0 * scale

    text_x = red_dot_x + 13.5 * scale
    text_y = y0 + (pill_h - text_h) / 2.0 - bbox[1]

    pill_w = (text_x + text_w + 18 * scale) - x0
    x1 = x0 + pill_w
    if x1 > sw - margin_left or y0 < 0:
        raise ValueError("배지가 이미지 범위를 넘습니다. --font-size를 줄이거나 --no-badge를 사용하세요")

    badge_hires = Image.new("RGBA", (sw, sh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(badge_hires)

    # Dark translucent pill background & subtle border
    draw.rounded_rectangle(
        [x0, y0, x1, y1],
        radius=radius,
        fill=(24, 30, 44, 225),
        outline=(150, 165, 185, 140),
        width=max(1, int(1.0 * scale))
    )

    # Coral red status dot
    draw.ellipse(
        [red_dot_x - red_dot_r, red_dot_y - red_dot_r, red_dot_x + red_dot_r, red_dot_y + red_dot_r],
        fill=(235, 75, 75, 255)
    )

    # Crisp white typography
    draw.text((text_x, text_y), display_name, font=font, fill=(255, 255, 255, 255))

    badge_layer = badge_hires.resize((w, h), Image.Resampling.LANCZOS)
    return Image.alpha_composite(base, badge_layer)


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
    badge: bool = True,
    dry_run: bool = False,
    naming: str | None = None,
    font_path: Path | None = None,
    font_size: int = 18,
    overwrite: bool = False
) -> int:
    if target_w <= 0 or target_h <= 0 or not 1 <= quality <= 100 or font_size <= 0:
        raise ValueError("크기·글꼴 크기는 양수, 품질은 1~100이어야 합니다")
    for config in (table_path, preset_path, font_path):
        if config and not config.is_file():
            raise ValueError(f"파일을 찾을 수 없습니다: {config}")
    if not src_dir.is_dir():
        print(f"❌ 원본 폴더를 찾을 수 없습니다: {src_dir}", file=sys.stderr)
        return 1

    src_files = [
        p for p in src_dir.iterdir()
        if p.is_file() and p.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp")
    ]
    if not src_files:
        print(f"❌ 원본 폴더({src_dir})에 이미지 파일이 없습니다.", file=sys.stderr)
        return 1

    print(f"📂 원본 이미지 {len(src_files)}개 발견 ({src_dir})")

    targets: list[BackgroundTarget] = []
    if table_path and table_path.exists():
        targets = parse_table_order(table_path)
        print(f"📋 배치표({table_path.name})에서 배경 목록 {len(targets)}개 로드")
    elif preset_path and preset_path.exists():
        targets = parse_preset_order(preset_path)
        print(f"📋 프리셋({preset_path.name})에서 배경 목록 {len(targets)}개 로드")
    else:
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

    if not targets:
        raise ValueError("처리할 항목이 없습니다")
    planned = []
    used = set()
    for t in targets:
        template = naming or {"scene": "a{index:02d}", "clean": "{index:02d}_{name}", "bg": "{code}_{name}"}[style]
        stem = template.format(index=t.index, code=t.code, name=t.filename_clean, stem=nfc(t.matched_src.stem))
        if not stem or stem in (".", "..") or any(c in stem for c in "/\\\0"):
            raise ValueError(f"출력 파일명은 단일 이름이어야 합니다: {stem!r}")
        paths = [out_dir / f"{stem}.{ext}" for ext in (["webp", "png"] if format_opt == "both" else [format_opt])]
        for dest in paths:
            key = nfc(str(dest.resolve())).casefold()
            if key in used or dest.resolve() in [x.resolve() for x in src_files]:
                raise ValueError(f"출력 충돌 또는 원본 덮어쓰기: {dest}")
            if dest.exists() and not overwrite:
                raise ValueError(f"기존 파일: {dest}; 덮어쓰려면 --overwrite")
            used.add(key)
        planned.append((t, stem))
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    badge_status = "적용 (좌측 하단 캡슐 뱃지)" if badge else "미적용"
    print(f"\n⚙️ 작업 설정: 규격 {target_w}x{target_h} ({anchor} 크롭), 배경 이름 뱃지: {badge_status}, 출력 포맷: {format_opt.upper()}")
    print("-" * 75)

    success_count = 0
    for t, out_stem in planned:
        badge_info = f" [뱃지: {t.name}]" if badge else ""
        print(f"✂️ [{t.code}] {t.matched_src.name} ➡️ {out_stem}{badge_info}")

        if dry_run:
            success_count += 1
            continue

        try:
            with Image.open(t.matched_src) as source_img:
                img = ImageOps.exif_transpose(source_img).convert("RGBA")
                if img.mode not in ("RGB", "RGBA"):
                    img = img.convert("RGBA" if "A" in img.mode else "RGB")

                processed = smart_crop_and_resize(img, target_w, target_h, anchor)

                if badge and t.name:
                    processed = add_location_badge_aa(processed, t.name, font_size=font_size, font_path=font_path)

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
    return 0 if success_count == len(targets) else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--src", type=Path, required=True, help="Source images directory (e.g. image-배경_원본)")
    parser.add_argument("--out", type=Path, required=True, help="Output directory (e.g. image/배경 or deploy/scene)")
    config = parser.add_mutually_exclusive_group()
    config.add_argument("--table", type=Path, help="Asset table path (e.g. image/에셋_배치표.md)")
    config.add_argument("--preset", type=Path, help="Preset backgrounds JSON (e.g. build/assets/preset-backgrounds.json)")
    parser.add_argument("--size", type=str, default="1024x400", help="Target size WxH (default: 1024x400)")
    parser.add_argument("--anchor", choices=["center", "top", "bottom", "left", "right"], default="center", help="Crop anchor (default: center)")
    parser.add_argument("--style", choices=["bg", "scene", "clean"], default="bg", help="Naming style: bg (bg01_name), scene (a01), clean (01_name)")
    parser.add_argument("--format", choices=["webp", "png", "both"], default="webp", help="Output format (default: webp)")
    parser.add_argument("--quality", type=int, default=90, help="WebP quality 1-100 (default: 90)")
    parser.add_argument("--no-badge", dest="badge", action="store_false", default=True, help="Do not stamp location UI pill badge")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without writing files")

    parser.add_argument("--naming", help="확장자 없는 이름 템플릿: {index:02d}, {code}, {name}, {stem}")
    parser.add_argument("--font", type=Path, help="배지 TTF/OTF/TTC 글꼴 경로")
    parser.add_argument("--font-size", type=int, default=18)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

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
        badge=args.badge,
        dry_run=args.dry_run, naming=args.naming, font_path=args.font,
        font_size=args.font_size, overwrite=args.overwrite
    )


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(f"오류: {exc}", file=sys.stderr)
        raise SystemExit(1)
