from __future__ import annotations

import asyncio
import base64
from pathlib import Path
from typing import Awaitable, Callable

from openai import AsyncOpenAI
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings
from src.models import CarouselPlan


class ImageGenerationError(Exception):
    pass


def _style_suffix() -> str:
    return (get_settings().prompts_dir / "image_style.md").read_text(
        encoding="utf-8"
    ).strip()


class ImageGenerator:
    """Generates 6 slide images in parallel with a concurrency cap of 3."""

    def __init__(
        self,
        client: AsyncOpenAI | None = None,
        concurrency: int = 3,
    ):
        settings = get_settings()
        self._client = client or AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.image_model
        self._size = settings.image_size
        self._quality = settings.image_quality
        self._sem = asyncio.Semaphore(concurrency)

    async def generate_all(self, plan: CarouselPlan, out_dir: Path) -> list[Path]:
        out_dir.mkdir(parents=True, exist_ok=True)
        suffix = _style_suffix()
        tasks = [
            self._generate_one(
                prompt=self._compose_prompt(slide.image_prompt, suffix),
                dest=out_dir / f"slide_{slide.slide_number}.png",
            )
            for slide in plan.slides
        ]
        return list(await asyncio.gather(*tasks))

    @staticmethod
    def _compose_prompt(base: str, suffix: str) -> str:
        if suffix.lower() in base.lower():
            return base
        base = base.rstrip(" .")
        return f"{base}. {suffix}"

    async def _generate_one(self, prompt: str, dest: Path) -> Path:
        async with self._sem:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(3),
                wait=wait_exponential(multiplier=1, min=2, max=10),
                retry=retry_if_exception_type(Exception),
                reraise=True,
            ):
                with attempt:
                    response = await self._client.images.generate(
                        model=self._model,
                        prompt=prompt,
                        size=self._size,
                        quality=self._quality,
                        n=1,
                    )
            data = response.data[0]
            png_bytes = self._extract_png(data)
            dest.write_bytes(png_bytes)
            return dest

    @staticmethod
    def _extract_png(data) -> bytes:
        b64 = getattr(data, "b64_json", None)
        if b64:
            return base64.b64decode(b64)
        url = getattr(data, "url", None)
        if url:
            import requests

            resp = requests.get(url, timeout=60)
            resp.raise_for_status()
            return resp.content
        raise ImageGenerationError(
            "OpenAI image response contained neither b64_json nor url."
        )


def generate_images_sync(plan: CarouselPlan, out_dir: Path) -> list[Path]:
    """Sync convenience wrapper for CLI callers."""
    return asyncio.run(ImageGenerator().generate_all(plan, out_dir))
