"""Appendix A fallback — direct TikTok Content Posting API.

Only built for when Postiz rejects the photo-carousel payload. NOT wired into
the main pipeline. Requires:

- A TikTok Developer App with Content Posting API scope approved.
- OAuth access token per creator account (refresh logic out of scope for v1).
- Publicly accessible image URLs (S3, CloudFront, etc.).
"""
from __future__ import annotations

import requests

from src.models import TikTokDirectPayload


TIKTOK_INIT_URL = "https://open.tiktokapis.com/v2/post/publish/content/init/"


class TikTokDirectError(Exception):
    pass


def publish_photo_carousel(
    payload: TikTokDirectPayload,
    access_token: str,
    session: requests.Session | None = None,
) -> dict:
    session = session or requests.Session()
    resp = session.post(
        TIKTOK_INIT_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        },
        json=payload.to_api_body(),
        timeout=60,
    )
    if resp.status_code >= 400:
        raise TikTokDirectError(
            f"TikTok direct publish failed ({resp.status_code}): {resp.text}"
        )
    return resp.json()
