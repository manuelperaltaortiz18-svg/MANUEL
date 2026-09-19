import json
from pathlib import Path

import pytest

from amazon_idq import Listing, score_listing, render
from amazon_idq.profiles import get_profile
from amazon_idq.rules import (
    backend_rules, compliance_rules, image_rules,
    keyword_coverage_rules, title_rules, attribute_rules,
)

SAMPLES = Path(__file__).resolve().parents[1] / "samples"


def load(name: str) -> Listing:
    return Listing.from_dict(json.loads((SAMPLES / name).read_text(encoding="utf-8")))


def finding(findings, code):
    return next(f for f in findings if f.code == code)


# ------------------------------------------------------------- end to end
def test_bad_listing_scores_far_below_good_one():
    bad = score_listing(load("bad_listing.json"))
    good = score_listing(load("good_listing.json"))
    assert bad.score < 40
    assert good.score > 90
    assert good.score > bad.score


def test_bad_listing_surfaces_policy_blockers():
    result = score_listing(load("bad_listing.json"))
    codes = {f.code for f in result.blockers}
    assert {"policy.phrases", "policy.links", "policy.contact", "policy.claims"} <= codes


def test_good_listing_has_no_blockers():
    assert score_listing(load("good_listing.json")).blockers == []


def test_score_is_bounded():
    for name in ("bad_listing.json", "good_listing.json"):
        s = score_listing(load(name)).score
        assert 0.0 <= s <= 100.0


def test_top_fixes_are_sorted_by_recoverable_points():
    result = score_listing(load("bad_listing.json"))
    gains = [result._weighted_loss(f) for f in result.top_fixes()]
    assert gains == sorted(gains, reverse=True)
    assert all(f.fix for f in result.top_fixes())


def test_report_renders_without_error():
    text = render(score_listing(load("bad_listing.json")), verbose=True)
    assert "LISTING QUALITY AUDIT" in text
    assert "not Amazon's IDQ" in text


def test_to_dict_is_json_serialisable():
    payload = score_listing(load("good_listing.json")).to_dict()
    json.dumps(payload)
    assert payload["grade"] == "A"
    assert set(payload["pillars"]) >= {"content", "media", "keywords", "attributes"}


# ------------------------------------------------------------- unit rules
def test_title_over_category_limit_is_critical():
    p = get_profile("apparel")
    l = Listing(asin="A", category="apparel", brand="X", title="X " + "a" * 200)
    assert finding(title_rules(l, p), "title.length").severity == "critical"


def test_title_missing_brand_penalised():
    p = get_profile("default")
    l = Listing(asin="A", category="default", brand="Luminar", title="Crema hidratante facial " * 4)
    assert finding(title_rules(l, p), "title.brand").earned == 0


def test_title_keyword_stuffing_detected():
    p = get_profile("default")
    l = Listing(asin="A", category="default", brand="X",
                title="X crema crema crema crema hidratante facial para piel seca y sensible de uso diario")
    assert finding(title_rules(l, p), "title.stuffing").earned == 0


def test_backend_over_249_bytes_scores_zero():
    p = get_profile("default")
    l = Listing(asin="A", category="default", backend_search_terms="palabra " * 40)
    f = finding(backend_rules(l, p), "backend.present")
    assert f.earned == 0 and f.severity == "high"


def test_backend_byte_limit_counts_utf8_not_chars():
    p = get_profile("default")
    l = Listing(asin="A", category="default", backend_search_terms="ñ" * 130)  # 260 bytes, 130 chars
    assert finding(backend_rules(l, p), "backend.present").earned == 0


def test_backend_commas_penalised():
    p = get_profile("default")
    l = Listing(asin="A", category="default", backend_search_terms="uno, dos, tres")
    assert finding(backend_rules(l, p), "backend.separators").earned == 0


def test_keyword_coverage_rewards_front_placement():
    p = get_profile("default")
    front = Listing(asin="A", category="default", title="crema hidratante facial",
                    target_keywords=["crema hidratante facial"])
    back = Listing(asin="A", category="default", backend_search_terms="crema hidratante facial",
                   target_keywords=["crema hidratante facial"])
    assert keyword_coverage_rules(front, p)[0].earned > keyword_coverage_rules(back, p)[0].earned


def test_missing_keywords_are_named_in_the_message():
    p = get_profile("default")
    l = Listing(asin="A", category="default", title="otra cosa", target_keywords=["serum retinol"])
    assert "serum retinol" in keyword_coverage_rules(l, p)[0].message


def test_compliance_flags_prohibited_phrase():
    p = get_profile("default")
    l = Listing(asin="A", category="default", title="Crema BEST SELLER")
    assert finding(compliance_rules(l, p), "policy.phrases").earned == 0


def test_clean_copy_passes_compliance():
    p = get_profile("default")
    l = Listing(asin="A", category="default", title="Crema hidratante facial 50 ml",
                bullets=["Hidrata durante 24 horas"], description="Textura ligera.")
    assert all(f.passed for f in compliance_rules(l, p))


def test_low_resolution_images_flagged():
    from amazon_idq.models import Image
    p = get_profile("default")
    l = Listing(asin="A", category="default",
                images=[Image(url="u", width=500, height=500, is_main=True, has_white_background=True)])
    assert finding(image_rules(l, p), "images.resolution").severity == "high"


def test_required_attributes_are_category_specific():
    grocery = get_profile("grocery")
    l = Listing(asin="A", category="grocery", attributes={"brand": "X", "ingredients": "agua"})
    msg = finding(attribute_rules(l, grocery), "attrs.required").message
    assert "allergen_information" in msg


def test_unknown_field_rejected():
    with pytest.raises(ValueError):
        Listing.from_dict({"asin": "A", "category": "beauty", "bogus": 1})
