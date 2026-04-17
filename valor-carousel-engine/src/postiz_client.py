from __future__ import annotations

import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import requests
from rich.console import Console
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings
from src.models import CarouselPlan, PostizPostResponse, PostizUploadResponse


console = Console()

# Postiz caps at 30 requests/hour. Warn at 25, refuse at 30.
HOURLY_LIMIT = 30
WARN_THRESHOLD = 25
WINDOW_SECONDS = 3600


class PostizRateLimitError(Exception):
    pass


class PostizError(Exception):
    pass


class PostizClient:
    def __init__(self, session: requests.Session | None = None):
        settings = get_settings()
        self._base_url = settings.postiz_base_url.rstrip("/")
        self._api_key = settings.postiz_api_key
        self._integration_id = settings.postiz_tiktok_integration_id
        self._session = session or requests.Session()
        self._call_times: deque[float] = deque()

    def upload_images(self, image_paths: list[Path]) -> list[PostizUploadResponse]:
        if len(image_paths) != 6:
            raise PostizError(f"Expected 6 images, got {len(image_paths)}")
        return [self._upload_one(p) for p in image_paths]

    def create_draft(
        self,
        plan: CarouselPlan,
        uploads: list[PostizUploadResponse],
    ) -> PostizPostResponse:
        if len(uploads) != 6:
            raise PostizError(f"Expected 6 uploads, got {len(uploads)}")
        payload = self._build_draft_payload(plan, uploads)
        self._assert_draft_shape(payload)
        return self._post_draft(payload)

    def _build_draft_payload(
        self, plan: CarouselPlan, uploads: list[PostizUploadResponse]
    ) -> dict:
        settings = get_settings()
        caption = plan.caption
        if plan.hashtags and not caption.rstrip().endswith(plan.hashtags[-1]):
            caption = f"{caption.rstrip()}\n\n{' '.join(plan.hashtags)}"

        return {
            "type": "draft",
            "date": datetime.now(timezone.utc).isoformat(),
            "shortLink": False,
            "tags": [],
            "posts": [
                {
                    "integration": {"id": self._integration_id},
                    "value": [
                        {
                            "content": caption,
                            "image": [{"id": u.id} for u in uploads],
                        }
                    ],
                    "settings": {
                        "__type": "tiktok",
                        "title": "",
                        "privacy_level": settings.tiktok_privacy_level,
                        "duet": settings.tiktok_allow_duet,
                        "stitch": settings.tiktok_allow_stitch,
                        "comment": settings.tiktok_allow_comments,
                        "autoAddMusic": "no",
                        "brand_content_toggle": False,
                        "brand_organic_toggle": False,
                        "video_made_with_ai": True,
                        "content_posting_method": "DIRECT_POST",
                    },
                }
            ],
        }

    @staticmethod
    def _assert_draft_shape(payload: dict) -> None:
        if payload.get("type") != "draft":
            raise PostizError(
                "Refusing to send: payload type must be 'draft'. "
                "Valor requires manual sound selection on the phone."
            )
        settings = payload["posts"][0]["settings"]
        if not settings.get("video_made_with_ai"):
            raise PostizError(
                "Refusing to send: video_made_with_ai must be True (TikTok AI policy)."
            )
        if settings.get("privacy_level") != "SELF_ONLY":
            raise PostizError(
                "Refusing to send: privacy_level must be SELF_ONLY for drafts."
            )

    # --- HTTP layer ------------------------------------------------------- #

    def _check_rate(self) -> None:
        now = time.time()
        while self._call_times and now - self._call_times[0] > WINDOW_SECONDS:
            self._call_times.popleft()
        if len(self._call_times) >= HOURLY_LIMIT:
            raise PostizRateLimitError(
                "Postiz hourly rate limit reached (30/hr). Wait before retrying."
            )
        if len(self._call_times) >= WARN_THRESHOLD:
            console.print(
                f"[yellow]⚠ Postiz rate: {len(self._call_times)}/{HOURLY_LIMIT} "
                "calls in the last hour.[/]"
            )
        self._call_times.append(now)

    def _headers(self, include_content_type: bool = True) -> dict:
        h = {"Authorization": self._api_key}
        if include_content_type:
            h["Content-Type"] = "application/json"
        return h

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _upload_one(self, path: Path) -> PostizUploadResponse:
        self._check_rate()
        with open(path, "rb") as f:
            files = {"file": (path.name, f, "image/png")}
            resp = self._session.post(
                f"{self._base_url}/upload",
                headers=self._headers(include_content_type=False),
                files=files,
                timeout=60,
            )
        if resp.status_code >= 400:
            raise PostizError(f"Upload failed ({resp.status_code}): {resp.text}")
        return PostizUploadResponse.model_validate(resp.json())

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(requests.RequestException),
        reraise=True,
    )
    def _post_draft(self, payload: dict) -> PostizPostResponse:
        self._check_rate()
        resp = self._session.post(
            f"{self._base_url}/posts",
            headers=self._headers(),
            json=payload,
            timeout=60,
        )
        if resp.status_code >= 400:
            raise PostizError(f"Draft create failed ({resp.status_code}): {resp.text}")
        return PostizPostResponse.model_validate(resp.json())
