from __future__ import annotations

import json
import re
from pathlib import Path

from anthropic import Anthropic
from pydantic import ValidationError
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings
from src.models import CarouselPlan, ContentBrief


class ContentGenerationError(Exception):
    def __init__(self, message: str, raw_response: str | None = None):
        super().__init__(message)
        self.raw_response = raw_response


def _load_prompt(name: str) -> str:
    return (get_settings().prompts_dir / name).read_text(encoding="utf-8")


def _extract_json(text: str) -> str:
    """Pull the first top-level JSON object out of a response."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ContentGenerationError(
            "No JSON object found in model response.", raw_response=text
        )
    return text[start : end + 1]


def _scrub_forbidden(plan: CarouselPlan, forbidden: list[str]) -> list[str]:
    if not forbidden:
        return []
    lower_forbidden = [w.lower() for w in forbidden]
    hits: list[str] = []
    blobs = [plan.caption, *[s.overlay_text for s in plan.slides]]
    for word in lower_forbidden:
        for blob in blobs:
            if word in blob.lower():
                hits.append(word)
                break
    return hits


class ContentEngine:
    def __init__(self, client: Anthropic | None = None):
        settings = get_settings()
        self._client = client or Anthropic(api_key=settings.anthropic_api_key)
        self._model = settings.anthropic_model
        self._system_prompt = _load_prompt("slide_planner.md")
        self._caption_guidance = _load_prompt("caption_writer.md")

    def generate(self, brief: ContentBrief) -> CarouselPlan:
        user_message = self._build_user_message(brief)
        try:
            return self._call_with_retry(user_message)
        except RetryError as e:
            inner = e.last_attempt.exception()
            raw = getattr(inner, "raw_response", None)
            raise ContentGenerationError(
                f"Content generation failed after 3 attempts: {inner}",
                raw_response=raw,
            ) from e

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(ContentGenerationError),
        reraise=True,
    )
    def _call_with_retry(self, user_message: str) -> CarouselPlan:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=2000,
            system=self._system_prompt + "\n\n" + self._caption_guidance,
            messages=[{"role": "user", "content": user_message}],
        )
        text = "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )
        if not text:
            raise ContentGenerationError("Empty response from model.", raw_response=str(response))

        try:
            payload = json.loads(_extract_json(text))
        except json.JSONDecodeError as e:
            raise ContentGenerationError(f"Invalid JSON: {e}", raw_response=text) from e

        try:
            plan = CarouselPlan.model_validate(payload)
        except ValidationError as e:
            raise ContentGenerationError(
                f"Plan failed schema validation: {e}", raw_response=text
            ) from e

        hits = _scrub_forbidden(plan, self._current_forbidden)
        if hits:
            raise ContentGenerationError(
                f"Plan contains forbidden words: {hits}", raw_response=text
            )
        return plan

    _current_forbidden: list[str] = []

    def _build_user_message(self, brief: ContentBrief) -> str:
        self._current_forbidden = list(brief.forbidden_words)
        parts = [
            f"Topic: {brief.topic}",
            f"Angle: {brief.angle}",
            f"Product: {brief.product}",
            f"Product URL: {brief.product_url}",
            f"Price: {brief.price}",
            f"Target audience: {brief.target_audience}",
            f"Hook style: {brief.hook_style}",
            f"CTA: {brief.cta}",
            f"Visual direction: {brief.visual_direction}",
        ]
        if brief.forbidden_words:
            parts.append(
                f"Forbidden words (must not appear anywhere): {', '.join(brief.forbidden_words)}"
            )
        parts.append(
            "\nReturn the JSON plan as specified. No prose, no markdown fences."
        )
        return "\n".join(parts)
