"""Send-engine rules that need no database: guards, reply categories, copy."""

import re
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


def test_send_window_is_uk_weekday_working_hours(monkeypatch):
    monkeypatch.delenv("VELARQO_SEND_WINDOW", raising=False)
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
    assert unsub["suppress"] and unsub["stops_sequence"] and unsub["needs_human"]   # a person sees every opt-out
    ooo = categorize_reply("a@b.co.uk", "Out of office", "back Monday")
    assert not ooo["suppress"] and not ooo["stops_sequence"]
    complaint = categorize_reply("a@b.co.uk", "Re: x", "reported to the ICO")
    assert complaint["suppress"] and complaint["needs_human"]


import pytest


@pytest.mark.parametrize("body,category", [
    ("Yes please, give me a call\n\nKind regards\nDave\nICO registration Z123. Scanned for spam and viruses", "positive"),
    ("Sounds good, ring me Monday\nRegards\nAll data processed in line with GDPR", "positive"),
    ("Interested.\n\nData Protection: see our privacy notice", "positive"),
    ("I'm currently away until Monday but please remove us from your list", "unsubscribe"),
    ("No\n\nDave\nAcme Ltd", "unsubscribe"),
    ("This is spam, how did you get my email?", "complaint"),
    ("I will report you to the ICO", "complaint"),
    ("Back in the office Monday", "out_of_office"),
])
def test_footers_dont_make_complaints_and_opt_outs_beat_out_of_office(body, category):
    assert categorize_reply("dave@acme.co.uk", "Re: last year's quotes", body)["category"] == category


def test_delay_notices_and_auto_acks_are_not_bounces_or_replies():
    assert categorize_reply("mailer-daemon@googlemail.com", "Delivery Status Notification (Delay)", "x")["category"] == "out_of_office"
    assert categorize_reply("mailer-daemon@googlemail.com", "Delivery Status Notification (Failure)", "x")["category"] == "bounce"
    ack = categorize_reply("help@acme.co.uk", "Re: x", "Thanks for your email, we'll be in touch", auto_submitted=True)
    assert ack["category"] == "out_of_office" and not ack["stops_sequence"]


def test_platform_and_shared_isp_domains():
    from outreach.send_engine import guards
    assert not guards.is_company_mailbox("blog@wordpress.com")
    assert guards.is_company_mailbox("info@acme.co.uk")
    assert not guards.domain_suppressible("btconnect.com")      # one firm's "no" mustn't block 16 others
    assert guards.domain_suppressible("acme.co.uk")


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
          "leverage", "AI", "we've helped", "%", "£", "per survey", "guarantee", "results"]


@pytest.mark.parametrize("name, arm", COLD_ARMS)
def test_every_cold_email_arm_is_clean_short_and_identifies_us(name, arm):
    email = compose.first_touch(ROW, experiments.load(name), arm)
    body = email["body"]
    assert compose.problems(email) == []
    assert body.rstrip().endswith(compose.OPT_OUT_LINE)
    assert "Pablo" in body and "velarqo.com" in body
    assert compose.word_count(body, email["company"]) <= compose.MAX_WORDS
    assert not [w for w in BANNED if w in body], "agency talk, unbacked claim, or a price (pricing is undecided)"
    # The name once in our words; the quoted homeowner text may carry it again (v2).
    ours = re.sub(r'"[^"]*"', "", body.split("\n\nPablo")[0])
    assert ours.count("Urg Windows & Doors") <= 1


@pytest.mark.parametrize("name", ["cold_offer_v1", "cold_roofing_v1"])
def test_offer_test_changes_only_the_offer(name):
    a, b = experiments.load(name)["arms"]
    assert a["subject"] == b["subject"] == "last year's quotes"
    pa, pb = a["body"].split("\n\n"), b["body"].split("\n\n")
    differ = [i for i, (x, y) in enumerate(zip(pa, pb)) if x != y]
    assert len(pa) == len(pb) and len(differ) == 1, "only the offer line differs between arms"
    assert "You only pay for surveys that get booked." in pa[differ[0]]
    assert pb[differ[0]] == "I'll chase your first 50 free. Anyone still keen goes in your diary."


def test_v2_copy_matches_the_approved_doc():
    """Email 1 shows the homeowner text (docs/COLD_EMAIL_V2.md, approved 2026-10-11)."""
    windows = compose.first_touch(ROW, experiments.load("cold_offer_v1"), 0)["body"]
    roofing = compose.first_touch(ROW, experiments.load("cold_roofing_v1"), 1)["body"]
    assert windows.startswith(
        "Hi,\n\nEver had a homeowner ring back months after a quote, ready to go?\n\n"
        "Most don't. So I'd text the ones Urg Windows & Doors quoted last year, from your name:\n\n"
        "\"Hi, it's Urg Windows & Doors. We quoted for your windows a while back. Did you ever get that sorted?\"\n\n"
        "Anyone still keen goes in your diary. You only pay for surveys that get booked.\n\nWorth a go?\n\n")
    assert "We quoted for your roof a while back." in roofing and "your windows" not in roofing
    follow_up = compose.follow_up(2, ROW, "last year's quotes", experiments.load("cold_roofing_v1")["arms"][0])["body"]
    assert follow_up.startswith("Hi,\n\nWhat you'd get back: a short list of homeowners")
    assert "Read me five old quotes on a ten-minute call" in follow_up
    assert "Roughly how many have you got: tens, hundreds?" in follow_up


def test_segment_tests_follow_the_v2_structure_or_wait():
    tailored, control = experiments.load("cold_nopressure_v1")["arms"]
    assert control["body"] == experiments.load("cold_offer_v1")["arms"][0]["body"], "control = cold_offer_v1 arm A"
    assert tailored["body"].split("\n\n")[3:] == control["body"].split("\n\n")[3:], "only the opener differs"
    assert experiments.load("cold_survey_line_v1")["status"] == "waiting", "its cost-sentence variable is gone in v2"


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


@pytest.mark.parametrize("name", ["cold_offer_v1", "cold_roofing_v1", "cold_nopressure_v1"])
def test_every_live_email_passes_checks(name):
    exp = experiments.load(name)
    for i, arm in enumerate(exp["arms"]):
        first = compose.first_touch(ROW, exp, i)
        assert compose.problems(first) == [], arm["key"]
        for step in range(2, experiments.steps(exp) + 1):
            assert compose.problems(compose.follow_up(step, ROW, first["subject"], arm)) == [], (arm["key"], step)


def test_arm_follow_up_overrides_default():
    arm = {"follow_ups": {"2": "Hi,\n\nArm specific."}}
    assert "Arm specific." in compose.follow_up(2, ROW, "s", arm)["body"]
    assert "Arm specific." not in compose.follow_up(3, ROW, "s", arm)["body"]


def test_waiting_angle_test_cannot_be_sent_as_is():
    exp = experiments.load("cold_angle_v1")
    assert exp["status"] == "waiting"
    assert "unfilled placeholder" in compose.problems(compose.first_touch(ROW, exp, 0))


def test_segment_filters_are_whitelisted_and_reserved():
    from outreach.send_engine.engine import _segment_filter
    assert _segment_filter({"segment": ["no_pressure_sales"]}) == "and q.no_pressure_sales"
    assert "not coalesce(q.no_pressure_sales" in _segment_filter(experiments.load("cold_offer_v1"))
    with pytest.raises(ValueError):
        _segment_filter({"segment": ["1=1; drop table companies"]})


@pytest.mark.parametrize("name", sorted(p.stem for p in experiments.EXPERIMENTS_DIR.glob("*.json")
                                        if experiments.load(p.stem)["stage"] == "cold_email"
                                        and experiments.load(p.stem).get("status") != "waiting"))
def test_long_company_names_never_break_the_word_cap(name):
    exp = experiments.load(name)
    row = {"display_name": "Premier Double Glazing Windows Doors And Conservatories Of Greater Manchester"}
    for arm in range(len(exp["arms"])):
        assert compose.problems(compose.first_touch(row, exp, arm)) == []


def test_free_mail_addresses_are_never_company_mailboxes():
    assert not guards.is_company_mailbox("philipadamsglazing@gmail.com")
    assert not guards.is_company_mailbox("a1glassmedway@yahoo.co.uk")
    assert guards.is_company_mailbox("info@acornupvc.co.uk")


def test_possessive_for_names_ending_in_s():
    exp = {"arms": [{"key": "a", "subject": "s", "body": "Hi,\n\nStill in {company}'s inbox?"}]}
    email = compose.first_touch({"display_name": "Leeds Windows And Doors"}, exp, 0)
    assert "Leeds Windows And Doors' inbox" in email["body"] and "Doors's" not in email["body"]


# --- Sequence length per experiment ---------------------------------------

@pytest.mark.parametrize("name", ["cold_offer_v1", "cold_roofing_v1"])
def test_two_email_experiments_never_send_follow_up_three(name):
    steps = experiments.steps(experiments.load(name))
    assert steps == 2
    sent = datetime(2026, 10, 6, 9, tzinfo=timezone.utc)                                      # Tue
    assert guards.follow_up_due(sent, 2, datetime(2026, 10, 9, 9, tzinfo=timezone.utc), steps)  # Fri = +3 bdays
    assert not guards.follow_up_due(sent, 3, datetime(2026, 11, 30, 9, tzinfo=timezone.utc), steps)


def test_steps_default_to_three_and_are_validated():
    assert experiments.steps({}) == 3 == experiments.steps(None)
    assert guards.follow_up_due(datetime(2026, 10, 6, tzinfo=timezone.utc), 3, datetime(2026, 11, 30, tzinfo=timezone.utc))
    base = {"name": "x", "stage": "cold_email", "hypothesis": "h", "primary_metric": "m", "decision_rule": "d",
            "arms": [{"key": "a", "subject": "s", "body": "b"}, {"key": "b", "subject": "s", "body": "b"}]}
    for bad in (0, 4, "2", 2.5):
        with pytest.raises(ValueError):
            experiments.validate({**base, "steps": bad})
    experiments.validate({**base, "steps": 1})


# --- Send windows -------------------------------------------------------------

def test_send_windows_parse_and_come_from_the_environment(monkeypatch):
    window = guards.parse_window("Tue-Thu 08:30-12:00")
    assert window.days == {1, 2, 3}
    assert guards.parse_window("Mon,Wed-Thu 09:00-11:00").days == {0, 2, 3}
    assert guards.parse_window("off") is None
    for bad in ("Tue-Thu", "Funday 09:00-10:00", "Mon 12:00-09:00"):
        with pytest.raises(ValueError):
            guards.parse_window(bad)

    monkeypatch.delenv("VELARQO_SEND_WINDOW", raising=False)
    monkeypatch.delenv("VELARQO_PREFERRED_WINDOW", raising=False)
    assert guards.send_window() == guards.parse_window("Mon-Fri 08:30-17:00")
    assert guards.preferred_window() == window
    monkeypatch.setenv("VELARQO_SEND_WINDOW", "Mon-Sat 09:00-18:00")
    monkeypatch.setenv("VELARQO_PREFERRED_WINDOW", "off")
    assert guards.in_send_window(datetime(2026, 10, 10, 16, 30, tzinfo=timezone.utc))  # Sat 17:30 BST
    assert guards.preferred_window() is None


def test_first_emails_wait_for_the_preferred_window_unless_the_queue_is_too_big():
    preferred = guards.parse_window("Tue-Thu 08:30-12:00")
    monday = datetime(2026, 10, 12, 9, tzinfo=timezone.utc)            # Mon 10:00 BST
    tuesday_morning = datetime(2026, 10, 13, 9, tzinfo=timezone.utc)   # Tue 10:00 BST
    tuesday_afternoon = datetime(2026, 10, 13, 13, tzinfo=timezone.utc)
    # The 7 days from Monday hold Tue, Wed, Thu: 3 x 25 first emails per mailbox.
    assert guards.preferred_capacity(monday, 25, preferred) == 75
    assert guards.hold_first_emails(monday, 60, 25, preferred)
    assert not guards.hold_first_emails(monday, 200, 25, preferred), "big queue: use the normal window too"
    assert not guards.hold_first_emails(tuesday_morning, 10, 25, preferred)
    # Tuesday afternoon: only Wed and Thu are ahead within the week.
    assert guards.preferred_capacity(tuesday_afternoon, 25, preferred) == 50
    assert guards.hold_first_emails(tuesday_afternoon, 10, 25, preferred)
    assert not guards.hold_first_emails(monday, 10, 25, None), "preferred window off"


# --- Best-fit cohorts ---------------------------------------------------------

def test_cohort_preferences_are_whitelisted_and_ordered():
    from outreach.send_engine.engine import PREFERENCES, _preference_order
    assert list(PREFERENCES) == ["named_director", "years_trading_5", "accredited", "runs_ads", "tier_a"]
    order = _preference_order(list(PREFERENCES))
    assert order.index("has_director") < order.index("years_trading") < order.index("accredited") \
        < order.index("runs_ads") < order.index("tier")
    assert _preference_order([]) == ""
    with pytest.raises(ValueError):
        _preference_order(["1; drop table companies"])


def test_slice_composition_counts_each_trait():
    from outreach.send_engine.engine import slice_composition
    rows = [{"has_director": True, "years_trading": 12, "accredited": True, "runs_ads": False, "tier": "A"},
            {"has_director": False, "years_trading": None, "accredited": None, "runs_ads": True, "tier": "B"}]
    assert slice_composition(rows, ["named_director"]) == {
        "companies": 2, "prefer": ["named_director"], "named_director": 1, "years_trading_5": 1,
        "accredited": 1, "runs_ads": 1, "tier_a": 1}
