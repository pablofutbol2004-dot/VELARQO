"""Send-engine rules that need no database: guards, reply categories, copy."""

from datetime import datetime, timezone

import pytest

from outreach.reply_classifier.classify import categorize_reply, strip_quoted
from outreach.send_engine import compose, experiments, guards
OUR_EMAIL_QUOTED = (
    "\n\nOn Tue, 6 Oct 2026 at 09:12, Pablo <pablo@getvelarqo.com> wrote:\n"
    "> Hi there,\n> We run follow-up campaigns...\n> Reply \"no\" and I won't email again.\n"
)


@pytest.mark.parametrize("category, ok", [
    ("Private Limited Company", True),
    ("Limited Liability Partnership", True),
    ("Limited Partnership", False),
    (None, False),
    ("Charitable Incorporated Organisation", False),
])
def test_only_corporate_subscribers_are_emailable(category, ok):
    assert guards.is_corporate(category) is ok


def test_send_window_is_uk_weekday_working_hours():
    assert guards.in_send_window(datetime(2026, 10, 6, 9, 0, tzinfo=timezone.utc))       # Tue 10:00 BST
    assert not guards.in_send_window(datetime(2026, 10, 6, 6, 0, tzinfo=timezone.utc))   # Tue 07:00 BST
    assert not guards.in_send_window(datetime(2026, 10, 10, 10, 0, tzinfo=timezone.utc)) # Saturday
    assert guards.in_send_window(datetime(2026, 12, 1, 16, 30, tzinfo=timezone.utc))     # Tue 16:30 GMT


def test_follow_ups_wait_business_days_not_calendar_days():
    friday = datetime(2026, 10, 9, 10, 0, tzinfo=timezone.utc)
    assert not guards.follow_up_due(friday, 2, datetime(2026, 10, 13, 10, tzinfo=timezone.utc))  # Tue = 2 bdays
    assert guards.follow_up_due(friday, 2, datetime(2026, 10, 14, 10, tzinfo=timezone.utc))      # Wed = 3 bdays
    assert not guards.follow_up_due(friday, 4, datetime(2027, 1, 1, tzinfo=timezone.utc))         # no step 4


def test_bounce_stop_needs_enough_volume():
    assert not guards.bounce_stop(10, 3)
    assert not guards.bounce_stop(40, 2)
    assert guards.bounce_stop(40, 3)


def test_free_mail_domains_are_never_domain_suppressed():
    assert not guards.domain_suppressible("gmail.com")
    assert guards.domain_suppressible("acmewindows.co.uk")
    assert guards.email_domain("Info@AcmeWindows.co.uk") == "acmewindows.co.uk"


@pytest.mark.parametrize("sender, subject, body, category", [
    ("mailer-daemon@googlemail.com", "Delivery Status Notification (Failure)", "Address not found", "bounce"),
    ("postmaster@outlook.com", "Undeliverable: old quotes", "", "bounce"),
    ("info@acme.co.uk", "Automatic reply: old quotes", "I'm on annual leave until Monday", "out_of_office"),
    ("info@acme.co.uk", "Re: old quotes", "No", "unsubscribe"),
    ("info@acme.co.uk", "Re: old quotes", "please remove us from your list", "unsubscribe"),
    ("info@acme.co.uk", "Re: old quotes", "Not interested thanks", "not_interested"),
    ("info@acme.co.uk", "Re: old quotes", "Where did you get my email? This is spam", "complaint"),
    ("info@acme.co.uk", "Re: old quotes", "Sounds good, give me a call tomorrow", "positive"),
    ("info@acme.co.uk", "Re: old quotes", "What does it cost?", "unknown"),
])
def test_reply_categories(sender, subject, body, category):
    assert categorize_reply(sender, subject, body + OUR_EMAIL_QUOTED)["category"] == category


def test_our_quoted_opt_out_line_never_reads_as_an_opt_out():
    verdict = categorize_reply("info@acme.co.uk", "Re: old quotes", "Yes, tell me more" + OUR_EMAIL_QUOTED)
    assert verdict["category"] == "positive"
    assert not verdict["suppress"]
    assert verdict["needs_human"]


def test_reply_actions():
    unsub = categorize_reply("a@b.co.uk", "Re: x", "stop")
    assert unsub["suppress"] and unsub["stops_sequence"] and not unsub["needs_human"]
    ooo = categorize_reply("a@b.co.uk", "Out of office", "back Monday")
    assert not ooo["suppress"] and not ooo["stops_sequence"]
    complaint = categorize_reply("a@b.co.uk", "Re: x", "reported to the ICO")
    assert complaint["suppress"] and complaint["needs_human"]


def test_strip_quoted_keeps_only_new_text():
    assert strip_quoted("Call me on 0113 496 0000" + OUR_EMAIL_QUOTED) == "Call me on 0113 496 0000"


ROW = {"id": "c1", "display_name": "Urg Windows & Doors", "email": "hello@urg.co.uk", "city": "Leicester"}

# Every arm of every cold-email test config is checked, so a bad edit to a
# JSON file fails here before it can reach an installer.
COLD_ARMS = [
    (path.stem, i)
    for path in sorted(experiments.EXPERIMENTS_DIR.glob("*.json"))
    if experiments.load(path.stem)["stage"] == "cold_email" and experiments.load(path.stem).get("status") != "waiting"
    for i in range(len(experiments.load(path.stem)["arms"]))
]
BANNED = ["campaign", "performance-based", "came across", "just bumping", "top of your inbox", "solution",
          "leverage", "AI", "we've helped", "%", "£", "per survey", "only pay for", "guarantee", "results"]


@pytest.mark.parametrize("name, arm", COLD_ARMS)
def test_every_cold_email_arm_is_clean_short_and_identifies_us(name, arm):
    email = compose.first_touch(ROW, experiments.load(name), arm)
    body = email["body"]
    assert compose.problems(email) == []
    assert body.rstrip().endswith(compose.OPT_OUT_LINE)
    assert "Pablo" in body and "velarqo.com" in body
    assert compose.word_count(body) <= compose.MAX_WORDS
    assert not [w for w in BANNED if w in body], "agency talk, unbacked claim, or a price (pricing is undecided)"
    assert body.count("Urg Windows & Doors") <= 1


def test_offer_test_changes_only_the_offer():
    a, b = experiments.load("cold_offer_v1")["arms"]
    assert a["subject"] == b["subject"]
    assert a["body"].split("\n\n")[:2] == b["body"].split("\n\n")[:2], "same greeting and opener in both arms"


def test_price_arm_is_stable_per_company_and_spreads_across_arms():
    exp = experiments.load("pricing_p1")
    assert experiments.assigned_arm(exp, "company-1") == experiments.assigned_arm(exp, "company-1")
    keys = {experiments.assigned_arm(exp, f"company-{i}")["key"] for i in range(60)}
    assert keys == {"low", "high"}


def test_stats_are_honest_about_small_numbers():
    low, high = experiments.wilson_interval(2, 100)
    assert low < 0.02 < high and high > 0.06
    assert 0.4 < experiments.probability_best([(3, 100), (4, 100)])[1] < 0.8
    assert experiments.probability_best([(2, 300), (15, 300)])[1] > 0.99


def test_verdict_refuses_to_call_a_winner_too_early():
    exp = experiments.load("cold_offer_v1")
    early = [{"arm": "A", "sent": 50, "positive": 0}, {"arm": "B", "sent": 50, "positive": 4}]
    assert experiments.verdict(exp, early).startswith("Too early")
    clear = [{"arm": "A", "sent": 300, "positive": 3}, {"arm": "B", "sent": 300, "positive": 15}]
    assert experiments.verdict(exp, clear).startswith("Decision: keep B")


def test_invalid_experiment_is_rejected():
    with pytest.raises(ValueError):
        experiments.validate({"name": "x", "stage": "cold_email", "hypothesis": "h", "primary_metric": "m",
                              "decision_rule": "d", "arms": [{"key": "a", "subject": "s", "body": "{first_name}"},
                                                             {"key": "b", "subject": "s", "body": "b"}]})


@pytest.mark.parametrize("step", [2, 3])
def test_follow_ups_thread_and_identify_us(step):
    email = compose.follow_up(step, ROW, "old quotes at Urg Windows & Doors")
    assert email["subject"] == "Re: old quotes at Urg Windows & Doors"
    assert compose.problems(email) == []
    assert compose.word_count(email["body"]) <= 80


def test_placeholder_signature_is_caught():
    assert "unfilled placeholder" in compose.problems({"subject": "x", "body": "Hi [Your name] velarqo.com"})


@pytest.mark.parametrize("name", ["cold_offer_v1"])
def test_every_live_email_passes_checks(name):
    exp = experiments.load(name)
    for i, arm in enumerate(exp["arms"]):
        first = compose.first_touch(ROW, exp, i)
        assert compose.problems(first) == [], arm["key"]
        for step in (2, 3):
            assert compose.problems(compose.follow_up(step, ROW, first["subject"], arm)) == [], (arm["key"], step)


def test_arm_follow_up_overrides_default():
    arm = {"follow_ups": {"2": "Hi,\n\nArm specific."}}
    assert "Arm specific." in compose.follow_up(2, ROW, "s", arm)["body"]
    assert "Arm specific." not in compose.follow_up(3, ROW, "s", arm)["body"]


def test_waiting_angle_test_cannot_be_sent_as_is():
    exp = experiments.load("cold_angle_v1")
    assert exp["status"] == "waiting"
    assert "unfilled placeholder" in compose.problems(compose.first_touch(ROW, exp, 0))
