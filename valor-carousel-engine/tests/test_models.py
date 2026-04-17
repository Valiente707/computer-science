import pytest
from pydantic import ValidationError

from src.models import CarouselPlan, ContentBrief


def test_content_brief_round_trip(sample_brief_dict):
    brief = ContentBrief.model_validate(sample_brief_dict)
    assert brief.topic.startswith("5 AI tools")
    assert brief.forbidden_words == ["revolutionary"]


def test_carousel_plan_requires_six_slides(sample_plan_dict):
    sample_plan_dict["slides"] = sample_plan_dict["slides"][:5]
    with pytest.raises(ValidationError):
        CarouselPlan.model_validate(sample_plan_dict)


def test_carousel_plan_requires_five_hashtags(sample_plan_dict):
    sample_plan_dict["hashtags"] = ["#ai", "#solo"]
    with pytest.raises(ValidationError):
        CarouselPlan.model_validate(sample_plan_dict)


def test_hashtags_must_start_with_hash(sample_plan_dict):
    sample_plan_dict["hashtags"] = ["ai", "#solo", "#tools", "#stack", "#business"]
    with pytest.raises(ValidationError):
        CarouselPlan.model_validate(sample_plan_dict)


def test_slide_numbers_must_be_1_to_6(sample_plan_dict):
    sample_plan_dict["slides"][0]["slide_number"] = 7
    with pytest.raises(ValidationError):
        CarouselPlan.model_validate(sample_plan_dict)


def test_valid_plan_accepted(sample_plan_dict):
    plan = CarouselPlan.model_validate(sample_plan_dict)
    assert [s.slide_number for s in plan.slides] == [1, 2, 3, 4, 5, 6]
    assert len(plan.hashtags) == 5
