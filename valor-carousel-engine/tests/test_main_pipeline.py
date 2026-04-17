from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from click.testing import CliRunner

from src import main as main_mod


@pytest.fixture
def font_present() -> bool:
    return (Path(__file__).resolve().parent.parent / "fonts" / "Inter-Bold.ttf").exists()


def test_dry_run_end_to_end(monkeypatch, tmp_path, sample_plan_dict, sized_png_b64, font_present):
    if not font_present:
        pytest.skip("Inter-Bold.ttf required for overlay step")

    # Stub the content engine.
    from src.content_engine import ContentEngine
    from src.models import CarouselPlan

    plan = CarouselPlan.model_validate(sample_plan_dict)
    monkeypatch.setattr(ContentEngine, "__init__", lambda self, client=None: None)
    monkeypatch.setattr(ContentEngine, "generate", lambda self, brief: plan)

    # Stub the image engine with a fake AsyncOpenAI.
    import base64

    png_bytes = base64.b64decode(sized_png_b64)

    async def fake_generate(**kwargs):
        return SimpleNamespace(
            data=[SimpleNamespace(b64_json=sized_png_b64, url=None)]
        )

    class _FakeImages:
        generate = staticmethod(fake_generate)

    class _FakeAsyncClient:
        images = _FakeImages()

    from src import image_generator as ig_mod

    monkeypatch.setattr(ig_mod, "AsyncOpenAI", lambda api_key=None: _FakeAsyncClient())

    brief_path = tmp_path / "brief.yaml"
    brief_path.write_text(
        "topic: 'demo topic'\n"
        "angle: list\n"
        "product: 'The Ultimate AI Business Starter Kit'\n"
        "product_url: 'https://example.com'\n"
        "price: '$42'\n"
        "target_audience: ''\n"
        "hook_style: curiosity\n"
        "cta: 'Link in bio'\n"
        "visual_direction: ''\n"
        "forbidden_words: []\n"
        "schedule: now\n",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        main_mod.cli,
        ["generate", "--brief", str(brief_path), "--dry-run"],
    )
    assert result.exit_code == 0, result.output
    # A run record should now exist.
    from config.settings import get_settings

    runs = list(get_settings().runs_dir.glob("*.json"))
    assert len(runs) == 1
    record = json.loads(runs[0].read_text())
    assert record["dry_run"] is True
    assert record["postiz_post_id"] is None
    assert len(record["final_image_paths"]) == 6
