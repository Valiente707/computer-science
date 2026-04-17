from pathlib import Path

import pytest
from PIL import Image

from src.models import CarouselPlan
from src.overlay import SAFE_BOTTOM, SAFE_TOP, TIKTOK_HEIGHT, TIKTOK_WIDTH, apply_overlays


@pytest.fixture
def fake_raw_images(tmp_path, sample_plan_dict):
    paths = []
    for i in range(1, 7):
        p = tmp_path / f"raw_{i}.png"
        Image.new("RGB", (1024, 1536), (40 + i * 10, 40, 60)).save(p)
        paths.append(p)
    return paths


def test_overlay_resizes_to_1080x1920(tmp_path, sample_plan_dict, fake_raw_images):
    fonts_dir = Path(__file__).resolve().parent.parent / "fonts"
    if not (fonts_dir / "Inter-Bold.ttf").exists():
        pytest.skip("Inter-Bold.ttf not present — run scripts/fetch_font.sh")

    plan = CarouselPlan.model_validate(sample_plan_dict)
    finals = apply_overlays(plan, fake_raw_images, tmp_path / "final")
    assert len(finals) == 6
    for p in finals:
        img = Image.open(p)
        assert img.size == (TIKTOK_WIDTH, TIKTOK_HEIGHT)


def test_slide_one_has_text_in_safe_zone(tmp_path, sample_plan_dict, fake_raw_images):
    fonts_dir = Path(__file__).resolve().parent.parent / "fonts"
    if not (fonts_dir / "Inter-Bold.ttf").exists():
        pytest.skip("Inter-Bold.ttf not present — run scripts/fetch_font.sh")

    plan = CarouselPlan.model_validate(sample_plan_dict)
    finals = apply_overlays(plan, fake_raw_images, tmp_path / "final")
    slide1 = Image.open(finals[0]).convert("L")
    # White stroke → expect high-brightness pixels somewhere in the safe band.
    band = slide1.crop((0, SAFE_TOP, slide1.width, slide1.height - SAFE_BOTTOM))
    histogram = band.histogram()
    bright_pixels = sum(histogram[220:])
    assert bright_pixels > 0, "slide 1 must contain white hook text in the safe band"
