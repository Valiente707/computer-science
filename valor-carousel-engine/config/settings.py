from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, HttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    anthropic_api_key: str = Field(..., alias="ANTHROPIC_API_KEY")
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")

    image_model: str = Field("gpt-image-1.5", alias="IMAGE_MODEL")
    image_size: str = Field("1024x1536", alias="IMAGE_SIZE")
    image_quality: Literal["low", "medium", "high"] = Field(
        "medium", alias="IMAGE_QUALITY"
    )

    postiz_api_key: str = Field(..., alias="POSTIZ_API_KEY")
    postiz_base_url: str = Field(
        "https://api.postiz.com/public/v1", alias="POSTIZ_BASE_URL"
    )
    postiz_tiktok_integration_id: str = Field(
        ..., alias="POSTIZ_TIKTOK_INTEGRATION_ID"
    )

    tiktok_privacy_level: Literal[
        "SELF_ONLY", "PUBLIC_TO_EVERYONE", "MUTUAL_FOLLOW_FRIENDS", "FOLLOWER_OF_CREATOR"
    ] = Field("SELF_ONLY", alias="TIKTOK_PRIVACY_LEVEL")
    tiktok_allow_comments: bool = Field(True, alias="TIKTOK_ALLOW_COMMENTS")
    tiktok_allow_duet: bool = Field(False, alias="TIKTOK_ALLOW_DUET")
    tiktok_allow_stitch: bool = Field(False, alias="TIKTOK_ALLOW_STITCH")
    tiktok_ai_label: bool = Field(True, alias="TIKTOK_AI_LABEL")

    product_name: str = Field(
        "The Ultimate AI Business Starter Kit", alias="PRODUCT_NAME"
    )
    product_url: str = Field(
        "https://valorpromotionsagents.com/starter-kit", alias="PRODUCT_URL"
    )
    product_price: str = Field("$42", alias="PRODUCT_PRICE")

    slack_webhook_url: str | None = Field(None, alias="SLACK_WEBHOOK_URL")

    anthropic_model: str = Field(
        "claude-sonnet-4-5-20250929", alias="ANTHROPIC_MODEL"
    )

    project_root: Path = PROJECT_ROOT
    output_dir: Path = PROJECT_ROOT / "output"
    runs_dir: Path = PROJECT_ROOT / "runs"
    prompts_dir: Path = PROJECT_ROOT / "config" / "prompts"
    fonts_dir: Path = PROJECT_ROOT / "fonts"

    @field_validator("image_model")
    @classmethod
    def _must_be_gpt_image(cls, v: str) -> str:
        if not v.startswith("gpt-image-"):
            raise ValueError(
                f"IMAGE_MODEL must be a gpt-image-* model (got {v!r}). "
                "DALL-E is deprecated and not supported."
            )
        return v

    @field_validator("image_size")
    @classmethod
    def _must_be_portrait(cls, v: str) -> str:
        if v != "1024x1536":
            raise ValueError(
                "IMAGE_SIZE must be 1024x1536 (9:16 portrait). "
                "TikTok requires portrait photos."
            )
        return v

    @field_validator("tiktok_ai_label")
    @classmethod
    def _ai_label_locked_on(cls, v: bool) -> bool:
        if not v:
            raise ValueError(
                "TIKTOK_AI_LABEL must be true. "
                "TikTok policy requires AI-generated content disclosure."
            )
        return v


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    return settings
