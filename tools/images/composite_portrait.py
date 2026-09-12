#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = ["rembg[cpu]>=2.0.60,<3", "pillow>=10", "scipy>=1.11"]
# ///
"""Two images in: local background removal, ivory outline, blurred background out.

Run: uv run composite_portrait.py character.webp background.webp
The first run downloads a segmentation model; source images stay local.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageFilter, ImageOps
from scipy import ndimage


def clean_mask(mask: Image.Image) -> Image.Image:
    values = np.asarray(mask.convert("L")).copy()
    labels, count = ndimage.label(values > 127)
    if not count:
        raise ValueError("No foreground detected; use --mask with a corrected mask.")
    areas = np.bincount(labels.ravel())
    keep = areas >= max(16, areas[1:].max() * 0.0005)
    keep[0] = False
    support = ndimage.binary_dilation(keep[labels], iterations=2)
    values[~support] = 0
    return Image.fromarray(values)


def compose(foreground: Image.Image, background: Image.Image,
            border: int, color: str, blur: float) -> Image.Image:
    backdrop = ImageOps.fit(background.convert("RGB"), foreground.size,
                             method=Image.Resampling.LANCZOS)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(blur)).convert("RGBA")
    if border:
        alpha = np.asarray(foreground.getchannel("A")) > 127
        outside = ndimage.distance_transform_edt(~alpha)
        outline = np.clip(border + 0.5 - outside, 0, 1)
        layer = Image.new("RGBA", foreground.size, ImageColor.getrgb(color) + (255,))
        layer.putalpha(Image.fromarray((outline * 255).astype("uint8")))
        backdrop = Image.alpha_composite(backdrop, layer)
    return Image.alpha_composite(backdrop, foreground)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("character", type=Path)
    parser.add_argument("background", type=Path)
    parser.add_argument("--out", type=Path, help="Default: character-composite.png")
    parser.add_argument("--mask", type=Path, help="Optional same-size grayscale mask; white=foreground")
    parser.add_argument("--model", default="isnet-anime", choices=["isnet-anime", "isnet-general-use", "u2net"])
    parser.add_argument("--border", type=int, help="Pixels; default 0.8%% of short side; 0 disables")
    parser.add_argument("--border-color", default="#fff8ec")
    parser.add_argument("--blur", type=float, help="Gaussian radius in pixels; default 0.6%% of short side")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    output = args.out or args.character.with_name(args.character.stem + "-composite.png")
    cutout_path = output.with_name(output.stem + "-cutout.png")
    if output.suffix.lower() not in {".png", ".webp"}:
        parser.error("Output must be PNG or WebP")
    for path in (output, cutout_path):
        if path.resolve() in {args.character.resolve(), args.background.resolve(),
                              args.mask.resolve() if args.mask else None}:
            parser.error("Output cannot replace an input")
        if path.exists() and not args.overwrite:
            parser.error(f"Output exists: {path}; choose another name or --overwrite")
    with Image.open(args.character) as source:
        foreground = ImageOps.exif_transpose(source).convert("RGBA")
    with Image.open(args.background) as source:
        background = ImageOps.exif_transpose(source).convert("RGB")
    border = args.border if args.border is not None else max(1, round(min(foreground.size) * .008))
    blur = args.blur if args.blur is not None else min(foreground.size) * .006
    if border < 0 or not np.isfinite(blur) or blur < 0:
        parser.error("Border and blur must be finite and nonnegative")
    ImageColor.getrgb(args.border_color)
    original_alpha = foreground.getchannel("A")
    if args.mask:
        with Image.open(args.mask) as source:
            mask = source.convert("L")
        if mask.size != foreground.size:
            parser.error("Mask must match character dimensions")
    elif original_alpha.getextrema()[0] < 255:
        mask = original_alpha
    else:
        from rembg import new_session, remove
        print(f"Removing background locally ({args.model})…", flush=True)
        session = new_session(args.model, providers=["CPUExecutionProvider"])
        mask = remove(foreground, session=session, only_mask=True)
    mask = clean_mask(mask)
    foreground.putalpha(Image.fromarray(np.minimum(np.asarray(mask), np.asarray(original_alpha))))
    result = compose(foreground, background, border, args.border_color, blur)
    output.parent.mkdir(parents=True, exist_ok=True)
    foreground.save(cutout_path)
    if output.suffix.lower() == ".webp":
        result.save(output, lossless=True)
    else:
        result.save(output)
    print(f"Composite: {output.resolve()}\nCutout: {cutout_path.resolve()}")


if __name__ == "__main__":
    main()
