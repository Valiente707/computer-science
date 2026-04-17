from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from config.settings import get_settings
from src.models import CarouselPlan


TIKTOK_WIDTH = 1080
TIKTOK_HEIGHT = 1920
SAFE_TOP = 100
SAFE_BOTTOM = 250
INITIAL_FONT_SIZE = 140
MIN_FONT_SIZE = 48
STROKE_WIDTH = 6
TEXT_MAX_WIDTH_RATIO = 0.85


def _font_path() -> Path:
    fp = get_settings().fonts_dir / "Inter-Bold.ttf"
    if not fp.exists():
        raise FileNotFoundError(
            f"Missing font at {fp}. Run scripts/fetch_font.sh or drop Inter-Bold.ttf into fonts/."
        )
    return fp


def _wrap_lines(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        trial = " ".join([*current, word])
        bbox = draw.textbbox((0, 0), trial, font=font, stroke_width=STROKE_WIDTH)
        if (bbox[2] - bbox[0]) <= max_width or not current:
            current.append(word)
        else:
            lines.append(" ".join(current))
            current = [word]
    if current:
        lines.append(" ".join(current))
    return lines


def _fit_font(
    draw: ImageDraw.ImageDraw, text: str, max_width: int, max_height: int
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    font_path = str(_font_path())
    size = INITIAL_FONT_SIZE
    while size >= MIN_FONT_SIZE:
        font = ImageFont.truetype(font_path, size)
        lines = _wrap_lines(draw, text, font, max_width)
        total_height = sum(
            draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)[3]
            - draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)[1]
            for line in lines
        ) + (len(lines) - 1) * int(size * 0.2)
        widest = max(
            draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)[2]
            for line in lines
        )
        if widest <= max_width and total_height <= max_height:
            return font, lines
        size -= 6
    font = ImageFont.truetype(font_path, MIN_FONT_SIZE)
    return font, _wrap_lines(draw, text, font, max_width)


def _draw_hook(img: Image.Image, text: str) -> None:
    draw = ImageDraw.Draw(img)
    max_width = int(img.width * TEXT_MAX_WIDTH_RATIO)
    safe_height = img.height - SAFE_TOP - SAFE_BOTTOM
    font, lines = _fit_font(draw, text, max_width, safe_height)

    line_heights = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)
        line_heights.append(bbox[3] - bbox[1])
    gap = int(font.size * 0.2)
    total_height = sum(line_heights) + gap * (len(lines) - 1)

    # Center anchor at ~40% from top of image.
    anchor_y = int(img.height * 0.40)
    y = anchor_y - total_height // 2
    if y < SAFE_TOP:
        y = SAFE_TOP
    if y + total_height > img.height - SAFE_BOTTOM:
        y = img.height - SAFE_BOTTOM - total_height

    for line, height in zip(lines, line_heights):
        bbox = draw.textbbox((0, 0), line, font=font, stroke_width=STROKE_WIDTH)
        line_w = bbox[2] - bbox[0]
        x = (img.width - line_w) // 2
        draw.text(
            (x, y),
            line,
            font=font,
            fill=(255, 255, 255),
            stroke_width=STROKE_WIDTH,
            stroke_fill=(0, 0, 0),
        )
        y += height + gap


def apply_overlays(plan: CarouselPlan, image_paths: list[Path], out_dir: Path) -> list[Path]:
    """For each slide image: resize to 1080×1920 and draw hook text on slide 1."""
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[Path] = []
    for slide, path in zip(plan.slides, image_paths):
        img = Image.open(path).convert("RGB")
        if img.size != (TIKTOK_WIDTH, TIKTOK_HEIGHT):
            img = img.resize((TIKTOK_WIDTH, TIKTOK_HEIGHT), Image.LANCZOS)

        if slide.slide_number == 1 and slide.overlay_text:
            _draw_hook(img, slide.overlay_text)
        elif slide.overlay_text:
            # Subtle subhead on non-hook slides is a future enhancement.
            pass

        dest = out_dir / f"final_slide_{slide.slide_number}.png"
        img.save(dest, format="PNG", optimize=True)
        results.append(dest)
    return results
