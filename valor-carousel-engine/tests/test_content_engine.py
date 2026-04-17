import json
from types import SimpleNamespace

import pytest

from src.content_engine import ContentEngine, ContentGenerationError
from src.models import ContentBrief


def _mk_response(text: str):
    return SimpleNamespace(content=[SimpleNamespace(type="text", text=text)])


class _FakeClient:
    def __init__(self, responses):
        self._responses = list(responses)
        self.messages = self
        self.calls = 0

    def create(self, **kwargs):
        self.calls += 1
        return self._responses.pop(0)


def test_generate_happy_path(sample_brief_dict, sample_plan_dict):
    fake = _FakeClient([_mk_response(json.dumps(sample_plan_dict))])
    engine = ContentEngine(client=fake)  # type: ignore[arg-type]
    plan = engine.generate(ContentBrief.model_validate(sample_brief_dict))
    assert plan.hashtags[0] == "#ai"
    assert fake.calls == 1


def test_generate_retries_bad_json(sample_brief_dict, sample_plan_dict):
    fake = _FakeClient(
        [
            _mk_response("not json at all"),
            _mk_response(json.dumps(sample_plan_dict)),
        ]
    )
    engine = ContentEngine(client=fake)  # type: ignore[arg-type]
    plan = engine.generate(ContentBrief.model_validate(sample_brief_dict))
    assert plan.carousel_title
    assert fake.calls == 2


def test_generate_fails_after_three(sample_brief_dict):
    fake = _FakeClient(
        [
            _mk_response("garbage"),
            _mk_response("still garbage"),
            _mk_response("nope"),
        ]
    )
    engine = ContentEngine(client=fake)  # type: ignore[arg-type]
    with pytest.raises(ContentGenerationError):
        engine.generate(ContentBrief.model_validate(sample_brief_dict))
    assert fake.calls == 3


def test_forbidden_word_rejection(sample_brief_dict, sample_plan_dict):
    # Inject forbidden word into the caption.
    sample_plan_dict["caption"] = (
        "This revolutionary stack changes everything. "
        "I packed it into The Ultimate AI Business Starter Kit. Link in bio.\n\n"
        "#ai #solopreneur #aitools #aistack #onemanbusiness"
    )
    fake = _FakeClient(
        [_mk_response(json.dumps(sample_plan_dict))] * 3
    )
    engine = ContentEngine(client=fake)  # type: ignore[arg-type]
    with pytest.raises(ContentGenerationError):
        engine.generate(ContentBrief.model_validate(sample_brief_dict))
    assert fake.calls == 3
