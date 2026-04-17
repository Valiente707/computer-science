from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


HookStyle = Literal["curiosity", "contrarian", "stat", "question"]
Angle = Literal["list", "story", "transformation", "myth-bust", "framework"]


class ContentBrief(BaseModel):
    model_config = ConfigDict(extra="forbid")

    topic: str
    angle: Angle = "list"
    product: str
    product_url: str
    price: str
    target_audience: str = ""
    hook_style: HookStyle = "curiosity"
    cta: str = "Link in bio"
    visual_direction: str = ""
    forbidden_words: list[str] = Field(default_factory=list)
    schedule: str = "now"


class SlideConcept(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_number: int = Field(ge=1, le=6)
    overlay_text: str = ""
    image_prompt: str


class CarouselPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    carousel_title: str
    slides: list[SlideConcept]
    caption: str
    hashtags: list[str]

    @field_validator("slides")
    @classmethod
    def _exactly_six(cls, v: list[SlideConcept]) -> list[SlideConcept]:
        if len(v) != 6:
            raise ValueError(f"Expected exactly 6 slides, got {len(v)}")
        numbers = sorted(s.slide_number for s in v)
        if numbers != [1, 2, 3, 4, 5, 6]:
            raise ValueError(f"Slide numbers must be 1-6 exactly, got {numbers}")
        return sorted(v, key=lambda s: s.slide_number)

    @field_validator("hashtags")
    @classmethod
    def _exactly_five(cls, v: list[str]) -> list[str]:
        if len(v) != 5:
            raise ValueError(f"Expected exactly 5 hashtags, got {len(v)}")
        for tag in v:
            if not tag.startswith("#"):
                raise ValueError(f"Hashtag must start with '#': {tag!r}")
        return v

    @field_validator("caption")
    @classmethod
    def _caption_length(cls, v: str) -> str:
        if not (100 <= len(v) <= 500):
            raise ValueError(
                f"Caption must be 100–500 chars (got {len(v)}). "
                "Target is 150–400 including hashtags."
            )
        return v


class PostizUploadResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    path: str | None = None


class PostizPostResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str | None = None
    postId: str | None = None

    @property
    def identifier(self) -> str:
        return self.id or self.postId or "unknown"


class RunRecord(BaseModel):
    model_config = ConfigDict(extra="allow")

    run_id: str
    created_at: datetime
    brief: ContentBrief
    plan: CarouselPlan | None = None
    slide_image_paths: list[Path] = Field(default_factory=list)
    final_image_paths: list[Path] = Field(default_factory=list)
    postiz_upload_ids: list[str] = Field(default_factory=list)
    postiz_post_id: str | None = None
    dry_run: bool = False
    errors: list[str] = Field(default_factory=list)


class TikTokDirectPayload(BaseModel):
    """Appendix A fallback shape. Only built if Postiz rejects the carousel."""

    model_config = ConfigDict(extra="forbid")

    title: str
    privacy_level: Literal["SELF_ONLY"] = "SELF_ONLY"
    disable_comment: bool = False
    auto_add_music: bool = True
    photo_image_urls: list[str]
    photo_cover_index: int = 0

    def to_api_body(self) -> dict:
        return {
            "post_info": {
                "title": self.title,
                "privacy_level": self.privacy_level,
                "disable_comment": self.disable_comment,
                "auto_add_music": self.auto_add_music,
            },
            "source_info": {
                "source": "PULL_FROM_URL",
                "photo_cover_index": self.photo_cover_index,
                "photo_images": self.photo_image_urls,
            },
            "post_mode": "DIRECT_POST",
            "media_type": "PHOTO",
        }
