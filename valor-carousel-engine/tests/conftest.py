from __future__ import annotations

import base64
import io
import json
import os
import sys
from pathlib import Path

import pytest
from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _env(monkeypatch, tmp_path):
    """Inject fake credentials and redirect output/runs dirs to tmp."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    monkeypatch.setenv("POSTIZ_API_KEY", "pos_test")
    monkeypatch.setenv("POSTIZ_TIKTOK_INTEGRATION_ID", "tiktok_int_test")
    monkeypatch.setenv("TIKTOK_AI_LABEL", "true")
    monkeypatch.setenv("IMAGE_MODEL", "gpt-image-1")
    monkeypatch.setenv("IMAGE_SIZE", "1024x1536")
    monkeypatch.setenv("IMAGE_QUALITY", "medium")
    monkeypatch.setenv("SLACK_WEBHOOK_URL", "")

    # Clear settings cache so env changes take effect per test.
    from config import settings as settings_mod
    settings_mod.get_settings.cache_clear()

    # Redirect output/runs to temp.
    monkeypatch.setattr(settings_mod, "PROJECT_ROOT", ROOT, raising=False)
    s = settings_mod.get_settings()
    s.output_dir = tmp_path / "output"
    s.runs_dir = tmp_path / "runs"
    s.output_dir.mkdir()
    s.runs_dir.mkdir()
    yield


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_plan_dict() -> dict:
    return {
        "carousel_title": "AI tools solopreneurs steal from agencies",
        "slides": [
            {
                "slide_number": i,
                "overlay_text": (
                    "The AI stack agencies don't tell you about"
                    if i == 1
                    else ""
                ),
                "image_prompt": (
                    f"Minimalist desk scene slide {i}, warm daylight, laptop and notebook. "
                    "iPhone photo, realistic natural lighting, 9:16 vertical composition, "
                    "no text, no watermarks, no people's faces visible"
                ),
            }
            for i in range(1, 7)
        ],
        "caption": (
            "Agencies charge $5k/month for workflows you can run for $40. "
            "Here's the five-tool stack I use daily. I packed all of this into "
            "The Ultimate AI Business Starter Kit if you want the shortcut. "
            "Grab it — link in bio.\n\n"
            "#ai #solopreneur #aitools #aistack #onemanbusiness"
        ),
        "hashtags": ["#ai", "#solopreneur", "#aitools", "#aistack", "#onemanbusiness"],
    }


@pytest.fixture
def sample_brief_dict() -> dict:
    return {
        "topic": "5 AI tools every solopreneur should steal from agencies",
        "angle": "list",
        "product": "The Ultimate AI Business Starter Kit",
        "product_url": "https://valorpromotionsagents.com/starter-kit",
        "price": "$42",
        "target_audience": "Solopreneurs",
        "hook_style": "curiosity",
        "cta": "Grab the kit — link in bio",
        "visual_direction": "Minimalist desk scenes",
        "forbidden_words": ["revolutionary"],
        "schedule": "now",
    }


@pytest.fixture
def tiny_png_b64() -> str:
    buf = io.BytesIO()
    Image.new("RGB", (16, 24), (128, 128, 200)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


@pytest.fixture
def sized_png_b64() -> str:
    """Fake 'OpenAI-sized' 1024x1536 PNG (solid colour) for overlay tests."""
    buf = io.BytesIO()
    Image.new("RGB", (1024, 1536), (40, 40, 40)).save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()
