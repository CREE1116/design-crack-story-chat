#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["pillow>=10", "scipy>=1.11", "numpy>=1.26"]
# ///
"""Character name cards: chroma cutout on black, name and title beside it.

Run: uv run name_card.py cuts/ --meta cards.json --out cards/
Add --render (with playwright installed) to rasterise each SVG to WebP.

`--meta` is a JSON array; every entry needs `name` and `source`, and may add
`id`, `title`, `group`, `accent`:

    [{"id": "01", "name": "카르디아 벨하르트", "title": "제1천왕·총사령관",
      "group": "마왕군", "accent": "#a8564e", "source": "카르디아/차분.png"}]

`source` is relative to the cuts directory. Cuts shot on a chroma screen are
keyed by colour; anything else falls back to the segmentation model, so the
same card works for a plain-background render.
"""
from __future__ import annotations

import argparse
import base64
import importlib.util
import io
import json
import sys
import unicodedata as ud
from pathlib import Path

import numpy as np
from PIL import Image, ImageFont

NFC = lambda s: ud.normalize("NFC", s)
FALLBACK_FONTS = (
    "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
)
STACK = "'Apple SD Gothic Neo','Noto Sans KR',sans-serif"


def load_compositor():
    """Reuse the cutout pipeline rather than reimplementing the keying."""
    path = Path(__file__).with_name("composite_portrait.py")
    spec = importlib.util.spec_from_file_location("composite_portrait", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["composite_portrait"] = module
    spec.loader.exec_module(module)
    return module


def pick_font(explicit: str | None) -> ImageFont.FreeTypeFont | None:
    for candidate in filter(None, (explicit, *FALLBACK_FONTS)):
        try:
            return ImageFont.truetype(candidate, 40)
        except OSError:
            continue
    return None


def text_width(font: ImageFont.FreeTypeFont | None, text: str, size: int, tracking: float) -> float:
    """Measured width, so the figure is pushed aside by exactly what the type needs."""
    if not text:
        return 0.0
    if font is None:  # 대략치. 한글 1em, 그 밖은 절반으로 본다
        units = sum(1.0 if ud.east_asian_width(c) in "WF" else .5 for c in text)
        return units * size + max(0, len(text) - 1) * tracking
    sized = font.font_variant(size=size)
    return sized.getlength(text) + max(0, len(text) - 1) * tracking


def cutout(cp, path: Path, rim: int, rim_colour: str) -> Image.Image:
    with Image.open(path) as source:
        figure = source.convert("RGBA").copy()
    original = figure.getchannel("A")
    channel = cp.screen_channel(figure)
    if channel:
        mask = cp.chroma_mask(figure, channel)
    else:
        from rembg import new_session, remove
        session = new_session("isnet-anime", providers=["CPUExecutionProvider"])
        mask = remove(figure, session=session, only_mask=True)
    mask = cp.clean_mask(mask)
    mask = cp.shrink_mask(cp.smooth_alpha(mask, min(figure.size) * .002), 1)
    merged = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(original)))
    figure.putalpha(merged)
    if channel:
        index = 1 if channel == "green" else 2
        figure = cp.unmix(figure, merged, cp.screen_colour(figure, index))
    solid = cp.silhouette(figure.getchannel("A"), 1.5)
    figure.putalpha(Image.fromarray(np.where(solid, np.asarray(figure.getchannel("A")), 0).astype("uint8")))
    if rim <= 0:
        return figure
    # 검정 위에서 어두운 머리가 배경에 묻히지 않게 최소한의 테만 두른다
    rimmed = cp.compose(figure, Image.new("RGB", figure.size, (0, 0, 0)), rim, rim_colour, 0, solid)
    data = np.asarray(rimmed.convert("RGBA")).copy()
    data[..., 3] = np.where(data[..., :3].max(axis=2) < 8, 0, 255)
    return Image.fromarray(data, "RGBA")


def card_svg(entry: dict, href: str, shift: int, size: tuple[int, int],
             margin: int, accent: str, sizes: tuple[int, int, int]) -> str:
    width, height = size
    name_px, title_px, group_px = sizes
    # 이름을 공백에서 끊어 2행으로 둔다. 한 행으로 두면 조판 폭이 배로 늘고
    # 그만큼 인물을 더 밀어내야 해 얼굴이 화면 밖으로 나간다.
    lines = [part for part in NFC(entry["name"]).split(" ") if part]
    top = height // 2 - (len(lines) - 1) * (name_px + 10) // 2
    rows = "\n".join(
        f'  <text x="{margin}" y="{top + name_px // 2 + i * (name_px + 10)}" font-family="{STACK}"'
        f' font-size="{name_px}" font-weight="600" fill="#f4f2ee" letter-spacing="-1">{line}</text>'
        for i, line in enumerate(lines))
    title_y = top + name_px // 2 + (len(lines) - 1) * (name_px + 10) + title_px + 20
    return f"""<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink"
     width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <radialGradient id="glow" cx="0.68" cy="0.46" r="0.55">
      <stop offset="0%" stop-color="{accent}" stop-opacity="0.22"/>
      <stop offset="100%" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
  </defs>
  <rect width="{width}" height="{height}" fill="#08080a"/>
  <rect width="{width}" height="{height}" fill="url(#glow)"/>
  <image x="{shift}" y="0" width="{width}" height="{height}" xlink:href="{href}"/>
  <text x="{margin}" y="{top - name_px - 10}" font-family="{STACK}" font-size="{group_px}"
        font-weight="500" fill="#ffffff" fill-opacity="0.42" letter-spacing="5">{entry.get('group', '')}</text>
  <rect x="{margin}" y="{top - name_px + 12}" width="92" height="1" fill="{accent}" fill-opacity="0.85"/>
{rows}
  <text x="{margin}" y="{title_y}" font-family="{STACK}" font-size="{title_px}" font-weight="400"
        fill="#ffffff" fill-opacity="0.66" letter-spacing="2">{entry.get('title', '')}</text>
  <rect x="24.5" y="24.5" width="{width - 49}" height="{height - 49}" fill="none"
        stroke="#ffffff" stroke-opacity="0.07" stroke-width="1"/>
</svg>
"""


def render(svgs: list[Path], size: tuple[int, int], quality: int) -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Rendering needs playwright: uv run --with playwright …", file=sys.stderr)
        return 0
    width, height = size
    done = 0
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        for svg in svgs:
            page.goto(svg.resolve().as_uri())
            page.wait_for_timeout(200)
            shot = svg.with_suffix(".png")
            page.screenshot(path=str(shot), clip={"x": 0, "y": 0, "width": width, "height": height})
            with Image.open(shot) as image:
                image.convert("RGB").save(svg.with_suffix(".webp"), "WEBP", quality=quality, method=6)
            shot.unlink()
            done += 1
        browser.close()
    return done


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("cuts", type=Path, help="Directory the meta `source` paths are relative to")
    parser.add_argument("--meta", type=Path, required=True, help="JSON array of card entries")
    parser.add_argument("--out", type=Path, required=True, help="Directory for the SVGs")
    parser.add_argument("--size", default="1216x832", help="Card size WxH (default: 1216x832)")
    parser.add_argument("--accent", default="#a8564e", help="Fallback accent colour")
    parser.add_argument("--margin", type=int, default=96)
    parser.add_argument("--gutter", type=int, default=56, help="Gap kept between type and figure")
    parser.add_argument("--name-size", type=int, default=46)
    parser.add_argument("--title-size", type=int, default=21)
    parser.add_argument("--group-size", type=int, default=17)
    parser.add_argument("--rim", type=int, default=1, help="Thin outline on the cutout; 0 disables")
    parser.add_argument("--rim-color", default="#3c3c46")
    parser.add_argument("--font", help="TTF/OTF/TTC used only to measure type width")
    parser.add_argument("--render", action="store_true", help="Also rasterise to WebP")
    parser.add_argument("--quality", type=int, default=90)
    args = parser.parse_args()

    try:
        width, height = (int(v) for v in args.size.lower().split("x"))
    except ValueError:
        parser.error("--size must look like 1216x832")
    entries = json.loads(args.meta.read_text(encoding="utf-8"))
    if not isinstance(entries, list) or not entries:
        parser.error("--meta must be a non-empty JSON array")

    cp = load_compositor()
    font = pick_font(args.font)
    sizes = (args.name_size, args.title_size, args.group_size)
    args.out.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for index, entry in enumerate(entries, 1):
        for key in ("name", "source"):
            if not entry.get(key):
                parser.error(f"entry {index} is missing {key!r}")
        source = args.cuts / entry["source"]
        if not source.is_file():
            print(f"  missing cut, skipped: {source}", file=sys.stderr)
            continue
        figure = cutout(cp, source, args.rim, args.rim_color)
        widest = max([text_width(font, part, args.name_size, -1)
                      for part in NFC(entry["name"]).split(" ") if part]
                     + [text_width(font, entry.get("title", ""), args.title_size, 2),
                        text_width(font, entry.get("group", ""), args.group_size, 5)])
        box = figure.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
        shift = max(0, int(args.margin + widest + args.gutter) - (box[0] if box else 0))
        buffer = io.BytesIO()
        figure.save(buffer, "PNG")
        href = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()
        stem = "%s_%s" % (entry.get("id") or "%02d" % index, NFC(entry["name"]).replace(" ", "_"))
        target = args.out / f"{stem}.svg"
        target.write_text(card_svg(entry, href, shift, (width, height), args.margin,
                                   entry.get("accent") or args.accent, sizes), encoding="utf-8")
        written.append(target)
        print(f"  {stem}  type {widest:.0f}px  shift {shift}px")

    if not written:
        print("No cards written.", file=sys.stderr)
        return 1
    print(f"{len(written)} SVG → {args.out}")
    if args.render:
        print(f"{render(written, (width, height), args.quality)} WebP rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
