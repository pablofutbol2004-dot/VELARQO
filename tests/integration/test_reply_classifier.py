"""The reply classifier against a labelled set of realistic UK installer
replies (tests/fixtures/installer_replies.json): positive, "how much",
"send info", "we already follow up", GDPR questions, not interested,
opt-outs, legal threats, out-of-office, bounces, wrong person, one-word
answers, typos and trades slang.

Two invariants matter more than any single label:
- a complaint, legal threat or GDPR question is always read by a human and
  is never auto-suppressed as "not interested";
- anything a person wrote that is not a plain no goes to a human.
"""

import json
from pathlib import Path

import pytest

from outreach.reply_classifier.classify import CATEGORIES, INTENTS, URGENT_CATEGORIES, categorize_reply, label

FIXTURE = Path(__file__).parents[1] / "fixtures" / "installer_replies.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))


def _verdict(case: dict) -> dict:
    return categorize_reply(case["from"], case["subject"], case["body"], auto_submitted=case.get("auto_submitted", False))


def test_set_is_big_and_varied():
    assert len(CASES) >= 80
    assert len({c["id"] for c in CASES}) == len(CASES), "duplicate ids"
    groups = {c["group"] for c in CASES}
    for needed in ("positive", "how_much", "send_info", "already_follow_up", "gdpr", "not_interested", "unsubscribe",
                   "complaint", "out_of_office", "bounce", "wrong_person", "later", "mixed", "unknown", "signature"):
        assert needed in groups, needed


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_category(case):
    verdict = _verdict(case)
    assert verdict["category"] in CATEGORIES
    assert verdict["category"] == case["category"], f"{case['id']}: {case['body'][:80]!r} -> {verdict}"


@pytest.mark.parametrize("case", [c for c in CASES if c.get("intent")], ids=[c["id"] for c in CASES if c.get("intent")])
def test_intent(case):
    verdict = _verdict(case)
    assert verdict["intent"] in INTENTS
    assert verdict["intent"] == case["intent"], f"{case['id']}: {case['body'][:80]!r} -> {verdict}"


@pytest.mark.parametrize("case", [c for c in CASES if c["group"] in ("gdpr", "complaint")],
                         ids=[c["id"] for c in CASES if c["group"] in ("gdpr", "complaint")])
def test_legal_and_gdpr_always_reach_a_human_and_are_never_not_interested(case):
    verdict = _verdict(case)
    assert verdict["needs_human"] is True
    assert verdict["stops_sequence"] is True
    assert verdict["category"] != "not_interested"
    assert verdict["category"] in URGENT_CATEGORIES
    if case["group"] == "gdpr":
        # a question is answered by hand; only the human suppresses, if asked
        assert verdict["suppress"] is False
        assert verdict["intent"] == "gdpr_question"
    else:
        # a threat suppresses the sender; the engine also pauses all sending on "complaint"
        assert verdict["category"] == "complaint" and verdict["suppress"] is True


@pytest.mark.parametrize("case", [c for c in CASES if c["category"] not in ("bounce", "out_of_office")],
                         ids=[c["id"] for c in CASES if c["category"] not in ("bounce", "out_of_office")])
def test_every_human_reply_needs_a_human(case):
    verdict = _verdict(case)
    assert verdict["needs_human"] is True
    assert verdict["stops_sequence"] is True


@pytest.mark.parametrize("case", [c for c in CASES if c["category"] in ("bounce", "out_of_office")],
                         ids=[c["id"] for c in CASES if c["category"] in ("bounce", "out_of_office")])
def test_automatic_notices_need_nobody(case):
    verdict = _verdict(case)
    assert verdict["needs_human"] is False
    assert verdict["sentiment"] is None
    assert verdict["suppress"] is (case["category"] == "bounce")
    assert verdict["stops_sequence"] is (case["category"] == "bounce")


def test_suppression_only_on_a_clear_no():
    for case in CASES:
        verdict = _verdict(case)
        if verdict["suppress"]:
            assert verdict["category"] in ("bounce", "unsubscribe", "complaint", "not_interested"), case["id"]
        if case["group"] in ("mixed", "later", "wrong_person", "already_follow_up") and case["category"] == "unknown":
            assert verdict["suppress"] is False, case["id"]


def test_positive_intents_cover_the_playbook():
    intents = {c["intent"] for c in CASES if c["category"] == "positive" and c.get("intent")}
    assert {"call_me", "how_much", "send_info", "yes"} <= intents


def test_labels_read_well():
    assert label("positive", "how_much") == "POSITIVE: asks how much"
    assert label("unknown", "gdpr_question") == "READ IT: GDPR / where-did-you-get-my-email question"
    assert label("complaint", "legal") == "COMPLAINT (sending paused)"
    assert label("positive", "interested") == "POSITIVE"
    assert label("not_interested", None) == "not interested"
