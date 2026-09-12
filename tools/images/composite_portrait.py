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


def alpha_is_cutout(alpha: "Image.Image") -> bool:
    """Does this alpha channel actually carry a cutout?

    Generators such as NovelAI write RGBA PNGs whose alpha is opaque
    everywhere except for a few anti-aliased pixels. Testing only the minimum
    value mistakes that for a real cutout, so segmentation is skipped and the
    composite comes out identical to the input, green screen and all. Require
    a real share of transparent pixels instead.
    """
    counts = alpha.histogram()
    total = sum(counts)
    if not total:
        return False
    return sum(counts[:128]) >= total * 0.01


def shrink_mask(mask: Image.Image, pixels: float) -> Image.Image:
    """Pull the cutout edge inwards by a pixel or two.

    The outermost boundary pixels are a blend of subject and chroma screen, so
    recolouring them only turns green into olive and the rim stays visible.
    Dropping that sliver removes the fringe; a hair's width is a cheap trade.
    """
    step = int(round(pixels))
    if step <= 0:
        return mask
    values = np.asarray(mask.convert("L"))
    size = 2 * step + 1
    return Image.fromarray(ndimage.grey_erosion(values, size=(size, size)))


def smooth_alpha(mask: Image.Image, radius: float) -> Image.Image:
    """Round off pixel stair-steps so the outline reads as a drawn line.

    A colour key follows the pixel grid exactly, and the border is traced from
    that alpha, so every jagged pixel becomes a visible notch in the outline.
    Blur then re-steepen: the edge stays crisp, only the staircase goes.
    """
    if radius <= 0:
        return mask
    blurred = mask.convert("L").filter(ImageFilter.GaussianBlur(radius))
    values = np.asarray(blurred).astype(np.float32)
    return Image.fromarray(np.clip((values - 128) * 2.2 + 128, 0, 255).astype("uint8"))


def despill(image: Image.Image, alpha: Image.Image, band: float) -> Image.Image:
    """Pull chroma-key colour out of the cutout edge.

    A green or blue screen bleeds into semi-transparent hair and cloth, so the
    cutout keeps a coloured rim that is obvious against a new background. Only
    the pixels within `band` of the alpha boundary are touched, and only where
    one channel genuinely overshoots the other two, so green eyes or blue cloth
    inside the subject survive.
    """
    if band <= 0:
        return image
    data = np.asarray(image.convert("RGBA")).astype(np.int16)
    # 경계의 반투명 픽셀이 색이 가장 심하게 물리는 자리다. alpha>127 로 잡으면
    # 그 구간이 빠져 머리카락 끝의 초록 테가 그대로 남는다.
    kept = np.asarray(alpha) > 0
    rim = kept & (ndimage.distance_transform_edt(kept) <= band)
    if not rim.any():
        return image
    for channel in (1, 2):  # green screen, then blue
        others = [data[..., c] for c in (0, 1, 2) if c != channel]
        limit = np.maximum(others[0], others[1])
        hit = rim & ((data[..., channel] - limit) > 4)
        data[..., channel] = np.where(hit, limit, data[..., channel])
    return Image.fromarray(np.clip(data, 0, 255).astype("uint8"), "RGBA")


def channel_excess(image: Image.Image, index: int) -> "np.ndarray":
    """How far one channel overshoots the brighter of the other two."""
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    rest = [rgb[..., c] for c in range(3) if c != index]
    return rgb[..., index] - np.maximum(rest[0], rest[1])


def screen_level(image: Image.Image, index: int) -> float | None:
    """How strongly the screen colour reads, or None if there is no screen.

    A fixed cutoff does not survive real batches: the same green backdrop comes
    out vivid in one run and muted in the next, and a cutoff tuned to the vivid
    one silently rejects the muted one. Read the level off the image and
    require a clear gap between screen and subject instead.
    """
    excess = channel_excess(image, index)
    high = float(np.percentile(excess, 90))
    base = float(np.percentile(excess, 40))
    if high < 15 or high - base < 12:
        return None
    return high


def screen_channel(image: Image.Image) -> str | None:
    """Is this shot on a chroma screen, and which one?

    Judged over the whole frame, not the border ring: in a close-up the hair
    and shoulders run off the edge, so the ring is subject, not backdrop.
    """
    for name, index in (("green", 1), ("blue", 2)):
        if screen_level(image, index) is not None:
            return name
    return None


def chroma_mask(image: Image.Image, channel: str) -> Image.Image:
    """Key the screen out by colour instead of segmenting the subject.

    A segmentation model treats the subject as one solid shape, so the gaps
    between hair strands come out filled and the screen shows through nowhere.
    Those gaps are literally screen-coloured, so keying on colour keeps them
    open and follows fine strands that no mask predictor resolves.
    """
    index = 1 if channel == "green" else 2
    excess = channel_excess(image, index)
    level = screen_level(image, index)
    if level is None:
        raise ValueError("Chroma screen too weak to key")
    # 손가락 사이나 머리 틈의 스크린은 그림자가 얹혀 색이 흐려진다. 경사 구간이
    # 높으면 그 자리가 반투명 초록으로 남아 새 배경 위에서 그대로 보인다.
    low, high = level * .15, level * .45
    keep = np.clip((high - excess) / (high - low), 0, 1)
    return Image.fromarray((keep * 255).astype("uint8"))


def screen_colour(image: Image.Image, index: int) -> "np.ndarray":
    """Average colour of the chroma screen itself."""
    excess = channel_excess(image, index)
    level = screen_level(image, index)
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    pick = excess >= (level or 0) * .8
    if not pick.any():
        pick = excess >= np.percentile(excess, 95)
    return np.median(rgb[pick], axis=0)


def unmix(image: Image.Image, alpha: Image.Image, screen: "np.ndarray") -> Image.Image:
    """Subtract the screen out of partly transparent pixels.

    A soft hair edge is subject and screen mixed in one pixel, so pressing the
    green channel down only shifts the fringe to olive. Solving the mix for the
    subject removes it: colour = subject*a + screen*(1-a), so divide it back
    out. Fully opaque pixels are untouched.
    """
    rgb = np.asarray(image.convert("RGB")).astype(np.float32)
    a = (np.asarray(alpha).astype(np.float32) / 255.0)[..., None]
    safe = np.clip(a, .12, 1.0)
    recovered = (rgb - screen[None, None, :] * (1.0 - a)) / safe
    blended = np.where(a >= .999, rgb, recovered)
    out = np.clip(blended, 0, 255).astype("uint8")
    result = Image.fromarray(out, "RGB").convert("RGBA")
    result.putalpha(alpha)
    return result


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


def silhouette(alpha: Image.Image, radius: float) -> "np.ndarray":
    """Round the outline into a drawn line instead of a torn edge.

    Tracing the alpha exactly makes the border spike out along every hair
    strand, which reads as torn paper. Blurring the binary shape and cutting it
    again at half limits how sharply the contour can turn, so corners round off
    while gaps wider than the radius stay open — unlike filling holes, which
    swallows the gaps between strands and leaves a white slab.
    """
    solid = np.asarray(alpha) > 96
    if radius > 0:
        solid = ndimage.gaussian_filter(solid.astype(np.float32), radius) > .5
    labels, count = ndimage.label(solid)
    if count:
        areas = np.bincount(labels.ravel())
        areas[0] = 0
        keep = areas >= max(64, areas.max() * .002)
        solid = keep[labels]  # 잡티에까지 테를 두르지 않는다
    return solid


def compose(foreground: Image.Image, background: Image.Image,
            border: int, color: str, blur: float,
            solid: "np.ndarray | None" = None) -> Image.Image:
    backdrop = ImageOps.fit(background.convert("RGB"), foreground.size,
                             method=Image.Resampling.LANCZOS)
    backdrop = backdrop.filter(ImageFilter.GaussianBlur(blur)).convert("RGBA")
    if border:
        if solid is None:
            solid = silhouette(foreground.getchannel("A"), max(border * 1.1, 1.5))
        outside = ndimage.distance_transform_edt(~solid)
        outline = np.clip(border + 0.5 - outside, 0, 1)
        outline = np.clip(ndimage.gaussian_filter(outline, .6) * 1.4, 0, 1)
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
    parser.add_argument("--despill", type=float, default=None, help="Edge band in pixels to pull chroma-key colour from; default 1.2%% of short side, 0 disables")
    parser.add_argument("--shrink", type=float, default=2, help="Pixels to pull the cutout edge inwards before despill; 0 disables")
    parser.add_argument("--key", default="auto", choices=["auto", "chroma", "model"], help="auto: key a detected chroma screen by colour, else segment")
    parser.add_argument("--smooth", type=float, default=None, help="Alpha smoothing radius in pixels; default 0.2%% of short side, 0 disables")
    parser.add_argument("--keep-wisps", action="store_true", help="Leave strands that fall outside the smoothed silhouette instead of trimming them")
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
    keyed = None
    if args.mask:
        with Image.open(args.mask) as source:
            mask = source.convert("L")
        if mask.size != foreground.size:
            parser.error("Mask must match character dimensions")
    elif alpha_is_cutout(original_alpha):
        mask = original_alpha
    else:
        channel = screen_channel(foreground) if args.key != "model" else None
        keyed = channel
        if args.key == "chroma" and not channel:
            parser.error("No chroma screen detected; use --key auto or --key model")
        if channel:
            print(f"Keying {channel} screen by colour…", flush=True)
            mask = chroma_mask(foreground, channel)
        else:
            from rembg import new_session, remove
            print(f"Removing background locally ({args.model})…", flush=True)
            session = new_session(args.model, providers=["CPUExecutionProvider"])
            mask = remove(foreground, session=session, only_mask=True)
    mask = clean_mask(mask)
    smooth = args.smooth if args.smooth is not None else min(foreground.size) * .002
    mask = smooth_alpha(mask, smooth)
    mask = shrink_mask(mask, args.shrink)
    merged = Image.fromarray(np.minimum(np.asarray(mask), np.asarray(original_alpha)))
    foreground.putalpha(merged)
    if keyed:
        index = 1 if keyed == "green" else 2
        foreground = unmix(foreground, merged, screen_colour(foreground, index))
    else:
        spill = args.despill if args.despill is not None else min(foreground.size) * .012
        foreground = despill(foreground, merged, spill)
        foreground.putalpha(merged)
    # 실루엣 밖으로 삐져나온 가닥을 남기면 보더가 있는 구간과 없는 구간이 섞여
    # 외곽선이 어정쩡해진다. 잘라내면 한 줄이 전체를 균일하게 감싼다.
    solid = silhouette(foreground.getchannel("A"), max(border * 1.1, 1.5))
    if not args.keep_wisps:
        trimmed = np.where(solid, np.asarray(foreground.getchannel("A")), 0)
        foreground.putalpha(Image.fromarray(trimmed.astype("uint8")))
    result = compose(foreground, background, border, args.border_color, blur, solid)
    output.parent.mkdir(parents=True, exist_ok=True)
    foreground.save(cutout_path)
    if output.suffix.lower() == ".webp":
        result.save(output, lossless=True)
    else:
        result.save(output)
    print(f"Composite: {output.resolve()}\nCutout: {cutout_path.resolve()}")


if __name__ == "__main__":
    main()
