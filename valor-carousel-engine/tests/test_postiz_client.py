from __future__ import annotations

import json
from pathlib import Path

import pytest
import requests

from src.models import CarouselPlan
from src.postiz_client import PostizClient, PostizError


class _FakeResponse:
    def __init__(self, status: int, body: dict):
        self.status_code = status
        self._body = body
        self.text = json.dumps(body)

    def json(self):
        return self._body


class _FakeSession:
    def __init__(self):
        self.posts: list[tuple[str, dict]] = []
        self._upload_counter = 0
        self._next_post = {"id": "post-abc-123"}

    def post(self, url, headers=None, files=None, json=None, timeout=None):
        if url.endswith("/upload"):
            self._upload_counter += 1
            body = {
                "id": f"upload-{self._upload_counter}",
                "path": f"https://cdn.test/upload-{self._upload_counter}.png",
            }
            self.posts.append((url, {"files": bool(files)}))
            return _FakeResponse(200, body)
        if url.endswith("/posts"):
            self.posts.append((url, json))
            return _FakeResponse(200, self._next_post)
        raise AssertionError(f"Unexpected URL: {url}")


def _image_files(tmp_path: Path) -> list[Path]:
    paths = []
    for i in range(6):
        p = tmp_path / f"final_{i}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
        paths.append(p)
    return paths


def test_upload_images_produces_six_ids(tmp_path):
    session = _FakeSession()
    client = PostizClient(session=session)  # type: ignore[arg-type]
    uploads = client.upload_images(_image_files(tmp_path))
    assert [u.id for u in uploads] == [f"upload-{i}" for i in range(1, 7)]


def test_draft_payload_has_required_fields(tmp_path, sample_plan_dict):
    session = _FakeSession()
    client = PostizClient(session=session)  # type: ignore[arg-type]
    plan = CarouselPlan.model_validate(sample_plan_dict)
    uploads = client.upload_images(_image_files(tmp_path))

    post = client.create_draft(plan, uploads)
    assert post.identifier == "post-abc-123"

    # Last call was the /posts request. Inspect the JSON body.
    url, payload = session.posts[-1]
    assert url.endswith("/posts")
    assert payload["type"] == "draft"
    settings = payload["posts"][0]["settings"]
    assert settings["video_made_with_ai"] is True
    assert settings["privacy_level"] == "SELF_ONLY"
    assert settings["__type"] == "tiktok"
    assert len(payload["posts"][0]["value"][0]["image"]) == 6
    assert payload["posts"][0]["integration"]["id"] == "tiktok_int_test"


def test_draft_shape_refuses_wrong_type(tmp_path, sample_plan_dict):
    session = _FakeSession()
    client = PostizClient(session=session)  # type: ignore[arg-type]
    plan = CarouselPlan.model_validate(sample_plan_dict)
    uploads = client.upload_images(_image_files(tmp_path))

    # Tamper with the payload builder to simulate a regression.
    original = client._build_draft_payload(plan, uploads)
    original["type"] = "now"
    with pytest.raises(PostizError):
        client._assert_draft_shape(original)


def test_caption_appends_hashtags_once(tmp_path, sample_plan_dict):
    session = _FakeSession()
    client = PostizClient(session=session)  # type: ignore[arg-type]
    plan = CarouselPlan.model_validate(sample_plan_dict)
    uploads = client.upload_images(_image_files(tmp_path))
    client.create_draft(plan, uploads)
    _, payload = session.posts[-1]
    content = payload["posts"][0]["value"][0]["content"]
    # Hashtags already present in caption — should not be doubled.
    assert content.count("#onemanbusiness") == 1
