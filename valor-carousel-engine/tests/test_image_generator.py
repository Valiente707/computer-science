import asyncio
from types import SimpleNamespace

import pytest

from src.image_generator import ImageGenerator
from src.models import CarouselPlan


class _FakeImagesAPI:
    def __init__(self, b64_png: str):
        self._b64 = b64_png
        self.calls = 0
        self.concurrent = 0
        self.peak = 0
        self._lock = asyncio.Lock()

    async def generate(self, **kwargs):
        async with self._lock:
            self.concurrent += 1
            self.peak = max(self.peak, self.concurrent)
        await asyncio.sleep(0.05)  # let other tasks stack up
        async with self._lock:
            self.concurrent -= 1
            self.calls += 1
        return SimpleNamespace(data=[SimpleNamespace(b64_json=self._b64, url=None)])


class _FakeClient:
    def __init__(self, b64_png: str):
        self.images = _FakeImagesAPI(b64_png)


def test_generates_six_images_with_semaphore(tmp_path, sample_plan_dict, tiny_png_b64):
    plan = CarouselPlan.model_validate(sample_plan_dict)
    fake = _FakeClient(tiny_png_b64)
    gen = ImageGenerator(client=fake, concurrency=3)  # type: ignore[arg-type]
    paths = asyncio.run(gen.generate_all(plan, tmp_path))
    assert len(paths) == 6
    assert all(p.exists() for p in paths)
    assert fake.images.calls == 6
    assert fake.images.peak <= 3, f"semaphore cap of 3 violated: peak={fake.images.peak}"


def test_prompt_suffix_appended(tmp_path, sample_plan_dict, tiny_png_b64):
    # Strip the suffix from a slide prompt and confirm generator re-adds it.
    sample_plan_dict["slides"][0]["image_prompt"] = "Plain desk scene."
    plan = CarouselPlan.model_validate(sample_plan_dict)

    seen_prompts: list[str] = []

    class _CapturingImages(_FakeImagesAPI):
        async def generate(self, **kwargs):
            seen_prompts.append(kwargs["prompt"])
            return await super().generate(**kwargs)

    class _CapturingClient:
        def __init__(self, b64):
            self.images = _CapturingImages(b64)

    fake = _CapturingClient(tiny_png_b64)
    gen = ImageGenerator(client=fake, concurrency=3)  # type: ignore[arg-type]
    asyncio.run(gen.generate_all(plan, tmp_path))
    assert any(
        "no people's faces visible" in p for p in seen_prompts
    ), "style suffix must be appended to every prompt"
