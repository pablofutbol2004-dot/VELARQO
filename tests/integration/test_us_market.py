"""US market (CAN-SPAM): guards, state time zones, windows, footer. No database
for the unit tests; the last test (opt-in, VELARQO_DB_TESTS=1) runs a US
prospect through cohort -> window gate -> legal re-check -> send."""

import copy
import os
from datetime import date, datetime, timezone

import psycopg
import pytest

from outreach.send_engine import compose, experiments, guards

ADDRESS = "123 Main Street, Suite 4, Austin, TX 78701"
ROW = {"id": "x", "display_name": "Lone Star Kitchens LLC", "email": "bob@lonestarkitchens.com"}


@pytest.fixture
def us_env(monkeypatch):
    monkeypatch.setenv("VELARQO_POSTAL_ADDRESS", ADDRESS)
    for name in ("VELARQO_SENDER_NAME", "VELARQO_BUSINESS_NAME", "VELARQO_SEND_WINDOW_US", "VELARQO_PREFERRED_WINDOW_US"):
        monkeypatch.delenv(name, raising=False)


def us_experiment():
    exp = copy.deepcopy(experiments.load("cold_offer_v1"))
    exp.pop("segment", None)
    exp.pop("exclude_segments", None)
    exp["market"] = "US"
    return exp


# --- market on experiments ---------------------------------------------------

def test_experiments_default_to_uk_and_validate_market():
    assert experiments.market(experiments.load("cold_offer_v1")) == "UK"
    assert experiments.market(None) == "UK"
    exp = us_experiment()
    experiments.validate(exp)
    assert experiments.market(exp) == "US"
    exp["market"] = "us"
    assert experiments.market(exp) == "US"
    exp["market"] = "FR"
    with pytest.raises(ValueError):
        experiments.validate(exp)


# --- guard rules --------------------------------------------------------------

@pytest.mark.parametrize("email, ok", [
    ("bob@lonestarkitchens.com", True),
    ("bobsbaths@gmail.com", True),          # free-mail is fine under CAN-SPAM
    ("bob@yahoo.com", True),
    ("blog@wordpress.com", False),          # platform junk is still junk
    ("info@yelp.example.com", True),
    ("someone@example.com", False),
    ("no-at-sign", False),
    ("", False),
    (None, False),
])
def test_us_mailboxes_allow_free_mail_but_not_platform_junk(email, ok):
    assert guards.is_us_mailbox(email) is ok


def test_uk_mailbox_rules_are_unchanged():
    assert not guards.is_company_mailbox("bobsbaths@gmail.com")
    assert guards.is_company_mailbox("bob@acme-windows.co.uk")
    assert not guards.is_corporate("Sole Trader")


@pytest.mark.parametrize("subject, bad", [
    ("Quick question about quotes", False),
    ("Re: Quick question", True),
    ("  RE: hello", True),
    ("Fwd: hello", True),
    ("FW: hello", True),
    ("Recommended: hello", False),
    ("Re-roofing quotes", False),
    ("", True),
])
def test_deceptive_subjects(subject, bad):
    assert guards.deceptive_subject(subject) is bad


def test_postal_address_comes_from_env_and_must_look_real(monkeypatch):
    monkeypatch.delenv("VELARQO_POSTAL_ADDRESS", raising=False)
    assert guards.postal_address() is None
    for junk in ("", "   ", "Austin", "somewhere in Texas", "123 Main St, Austin, TX"):   # last: no ZIP
        monkeypatch.setenv("VELARQO_POSTAL_ADDRESS", junk)
        assert guards.postal_address() is None, junk
    monkeypatch.setenv("VELARQO_POSTAL_ADDRESS", "123 Main Street\nSuite 4\nAustin, TX 78701\n")
    assert guards.postal_address() == "123 Main Street, Suite 4, Austin, TX 78701"


# --- time zones and windows -------------------------------------------------------

@pytest.mark.parametrize("state, zone", [
    ("NY", "America/New_York"), ("fl", "America/New_York"), ("Texas", "America/Chicago"),
    ("IL", "America/Chicago"), ("CO", "America/Denver"), ("AZ", "America/Denver"),
    ("CA", "America/Los_Angeles"), ("WA", "America/Los_Angeles"), ("AK", "America/Anchorage"),
    ("HI", "Pacific/Honolulu"), ("District of Columbia", "America/New_York"),
    (None, "America/New_York"), ("", "America/New_York"), ("ZZ", "America/New_York"), ("Narnia", "America/New_York"),
])
def test_us_state_maps_to_local_time_zone(state, zone):
    assert str(guards.us_timezone(state)) == zone


def test_every_state_and_dc_has_a_zone():
    assert len(guards.US_STATE_TZ) == 51
    assert all(guards.us_state_code(code) == code for code in guards.US_STATE_TZ)


def utc(y, m, d, h, mi=0):
    return datetime(y, m, d, h, mi, tzinfo=timezone.utc)


def test_us_default_windows(monkeypatch):
    monkeypatch.delenv("VELARQO_SEND_WINDOW_US", raising=False)
    monkeypatch.delenv("VELARQO_PREFERRED_WINDOW_US", raising=False)
    assert guards.send_window_us() == guards.parse_window("Mon-Fri 08:30-16:30")
    assert guards.preferred_window_us() == guards.parse_window("Tue-Thu 08:30-11:30")


def test_us_windows_are_overridable_from_the_environment(monkeypatch):
    monkeypatch.setenv("VELARQO_SEND_WINDOW_US", "Mon-Thu 09:00-15:00")
    monkeypatch.setenv("VELARQO_PREFERRED_WINDOW_US", "off")
    assert guards.send_window_us() == guards.parse_window("Mon-Thu 09:00-15:00")
    assert guards.preferred_window_us() is None


def test_send_window_is_the_prospects_local_time(monkeypatch):
    monkeypatch.delenv("VELARQO_SEND_WINDOW_US", raising=False)
    # Tue 13 Oct 2026, 13:00 UTC = 09:00 EDT = 08:00 CDT = 07:00 MDT = 06:00 PDT = 05:00 AKDT = 03:00 HST.
    now = utc(2026, 10, 13, 13)
    assert guards.us_state_open(now, "NY")
    assert not guards.us_state_open(now, "TX")      # 08:00 Central: too early
    assert not guards.us_state_open(now, "CA")
    assert not guards.us_state_open(now, "HI")
    assert guards.us_state_open(now, None)          # unknown -> New York
    # 15:00 UTC = 11:00 EDT, 10:00 CDT, 09:00 MDT, 08:00 PDT (too early).
    later = utc(2026, 10, 13, 15)
    assert guards.us_state_open(later, "TX") and guards.us_state_open(later, "CO")
    assert not guards.us_state_open(later, "CA")
    # 20:30 UTC = 16:30 EDT (window end is exclusive) / 13:30 PDT.
    end = utc(2026, 10, 13, 20, 30)
    assert not guards.us_state_open(end, "NY") and guards.us_state_open(end, "CA")
    # UK clock is untouched: 13:00 UTC is 14:00 BST, inside the UK window.
    assert guards.in_send_window(now)


def test_us_weekends_and_dst_are_handled(monkeypatch):
    monkeypatch.delenv("VELARQO_SEND_WINDOW_US", raising=False)
    assert not guards.us_state_open(utc(2026, 10, 17, 15), "NY")        # Saturday
    # After US clocks go back (1 Nov 2026) 14:00 UTC is 09:00 EST.
    assert guards.us_state_open(utc(2026, 11, 3, 14), "NY")
    assert not guards.us_state_open(utc(2026, 10, 13, 12), "NY")        # 08:00 EDT
    assert guards.us_state_open(utc(2026, 11, 3, 14), "NY") and not guards.us_state_open(utc(2026, 11, 3, 13), "NY")


def test_us_first_emails_wait_for_the_local_preferred_window(monkeypatch):
    monkeypatch.delenv("VELARQO_PREFERRED_WINDOW_US", raising=False)
    preferred = guards.preferred_window_us()
    ny, la = guards.us_timezone("NY"), guards.us_timezone("CA")
    tue_10_ny = utc(2026, 10, 13, 14)                         # 10:00 EDT, 07:00 PDT
    assert not guards.hold_first_emails(tue_10_ny, 10, 25, preferred, ny)
    assert guards.hold_first_emails(tue_10_ny, 10, 25, preferred, la)      # LA hasn't reached 08:30
    mon_ny = utc(2026, 10, 12, 14)                            # Monday: preferred days are Tue-Thu
    assert guards.hold_first_emails(mon_ny, 10, 25, preferred, ny)
    assert not guards.hold_first_emails(mon_ny, 500, 25, preferred, ny), "huge queue: use the normal window too"
    tue_12_ny = utc(2026, 10, 13, 16)                         # 12:00 EDT, past 11:30
    assert guards.hold_first_emails(tue_12_ny, 10, 25, preferred, ny)


# --- footer -----------------------------------------------------------------

def test_us_footer_has_name_business_address_and_opt_out(us_env):
    email = compose.first_touch(ROW, us_experiment(), 0)
    body = email["body"]
    assert email["market"] == "US"
    assert body.endswith(f"Pablo\nVelarqo, velarqo.com\n{ADDRESS}\n\n{compose.US_OPT_OUT_LINE}\n")
    assert "unsubscribe" in compose.US_OPT_OUT_LINE and '"no"' in compose.US_OPT_OUT_LINE
    assert compose.OPT_OUT_LINE not in body
    assert compose.problems(email) == []
    assert compose.legal_problems(email) == []
    follow = compose.follow_up(2, ROW, email["subject"], us_experiment()["arms"][0], "US")
    assert ADDRESS in follow["body"] and compose.US_OPT_OUT_LINE in follow["body"]


def test_us_footer_sender_and_business_come_from_env(us_env, monkeypatch):
    monkeypatch.setenv("VELARQO_SENDER_NAME", "Pablo Example")
    monkeypatch.setenv("VELARQO_BUSINESS_NAME", "Velarqo LLC")
    body = compose.first_touch(ROW, us_experiment(), 0)["body"]
    assert "Pablo Example\nVelarqo LLC, velarqo.com\n" + ADDRESS in body


def test_us_email_fails_closed_without_a_postal_address(monkeypatch):
    monkeypatch.delenv("VELARQO_POSTAL_ADDRESS", raising=False)
    with pytest.raises(compose.PostalAddressMissing):
        compose.first_touch(ROW, us_experiment(), 0)
    with pytest.raises(compose.PostalAddressMissing):
        compose.follow_up(2, ROW, "Quick question", None, "US")
    with pytest.raises(compose.PostalAddressMissing):
        compose.us_signature()
    # An already-written US email is also refused at send time.
    monkeypatch.setenv("VELARQO_POSTAL_ADDRESS", ADDRESS)
    written = compose.first_touch(ROW, us_experiment(), 0)
    monkeypatch.delenv("VELARQO_POSTAL_ADDRESS")
    assert any("POSTAL_ADDRESS" in issue for issue in compose.legal_problems(written))
    assert compose.problems(written)


def test_us_email_missing_footer_pieces_is_caught(us_env):
    email = compose.first_touch(ROW, us_experiment(), 0)
    no_address = {**email, "body": email["body"].replace(ADDRESS, "")}
    assert "missing postal address" in compose.legal_problems(no_address)
    no_opt_out = {**email, "body": email["body"].replace(compose.US_OPT_OUT_LINE, compose.OPT_OUT_LINE)}
    assert "missing opt-out line" in compose.legal_problems(no_opt_out)
    assert "deceptive or empty subject" in compose.legal_problems({**email, "subject": "Re: your quote"})
    assert "missing sender name or business name" in compose.legal_problems(
        {**email, "body": email["body"].replace("Velarqo, velarqo.com", "velarqo.com")})


def test_us_follow_up_subject_is_never_a_fake_reply(us_env):
    follow = compose.follow_up(2, ROW, "Quick question", None, "US")
    assert follow["subject"] == "Quick question"
    assert compose.follow_up(2, ROW, "Re: Quick question", None, "US")["subject"] == "Quick question"
    assert compose.follow_up(2, ROW, "Quick question")["subject"] == "Re: Quick question"   # UK unchanged
    assert not guards.deceptive_subject(follow["subject"])


def test_us_first_emails_can_not_carry_a_fake_reply_subject(us_env):
    exp = us_experiment()
    exp["arms"][0]["subject"] = "Re: {company}"
    email = compose.first_touch(ROW, exp, 0)
    assert "deceptive or empty subject" in compose.problems(email)


@pytest.mark.parametrize("name", ["cold_offer_v1", "cold_roofing_v1", "cold_nopressure_v1", "cold_survey_line_v1"])
def test_every_live_arm_passes_the_us_checks(us_env, name):
    exp = copy.deepcopy(experiments.load(name))
    exp["market"] = "US"
    for index in range(len(exp["arms"])):
        email = compose.first_touch(ROW, exp, index)
        assert compose.problems(email) == [], (name, exp["arms"][index]["key"])
        for step in (2, 3):
            follow = compose.follow_up(step, ROW, email["subject"], exp["arms"][index], "US")
            assert compose.legal_problems(follow) == []


def test_uk_footer_is_unchanged(us_env):
    email = compose.first_touch(ROW, experiments.load("cold_offer_v1"), 0)
    assert email["market"] == "UK"
    assert email["body"].endswith(f"\n\n{compose.SIGNATURE}\n\n{compose.OPT_OUT_LINE}\n")
    assert ADDRESS not in email["body"]


def test_unsubscribe_and_no_replies_are_opt_outs_the_engine_honours():
    from outreach.reply_classifier.classify import categorize_reply

    for text in ("no", "Unsubscribe", "unsubscribe please"):
        verdict = categorize_reply("bob@gmail.com", "Re: Quick question", text)
        assert verdict["category"] == "unsubscribe" and verdict["suppress"], text


# --- end to end against the database (opt-in) ----------------------------------------

@pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")
def test_us_prospect_end_to_end(us_env, monkeypatch):
    from data.supabase_store import connect
    from outreach.send_engine import engine
    from pipelines.cold_outreach.pipeline import DEFAULT_ICP_PATH, load_icp

    mailbox, opened = "test@example.invalid", date(2026, 1, 1)

    class Fake:
        def __init__(self):
            self.sent = []

        def send_email(self, to, subject, body, thread_id=None, in_reply_to_message_id=None):
            self.sent.append({"to": to, "subject": subject, "body": body})
            return {"message_id": f"m{len(self.sent)}", "thread_id": "t"}

        def rfc_message_id(self, message_id):
            return f"<{message_id}@test>"

    conn = connect()
    conn.autocommit = True
    try:
        with conn.transaction():
            for state, email in (("TX", "bob@gmail.com"), ("CA", "sue@westcoastbaths.com"), ("NY", "blog@wordpress.com")):
                conn.execute(
                    "insert into companies (vertical, source_key, display_name, email, tier, country, extra, icp_score) "
                    "values ('windows', %s, %s, %s, 'A', 'US', %s::jsonb, 50)",
                    (f"pytest-us-{state}", f"Pytest {state} Windows LLC", email, f'{{"state": "{state}"}}'))
            exp = us_experiment()
            cohort = engine.create_cohort(conn, "pytest us", 50, exp, load_icp(DEFAULT_ICP_PATH), "test")
            rows = engine.review_rows(conn, cohort["campaign_id"])
            mine = [r for r in rows if r["display_name"].startswith("Pytest ")]
            assert {r["to_email"] for r in mine} == {"bob@gmail.com", "sue@westcoastbaths.com"}, "platform address is never picked"
            assert all(ADDRESS in r["body"] and compose.US_OPT_OUT_LINE in r["body"] for r in mine)
            engine.set_campaign_status(conn, cohort["campaign_id"], "active")
            engine.set_sending(conn, True)
            # Park every other queued message so only this test's campaign can send.
            conn.execute("update messages set status = 'cancelled', skip_reason = 'pytest' "
                         "where status = 'queued' and campaign_id <> %s", (cohort["campaign_id"],))

            def send(now):
                provider = Fake()
                result = engine.send_due(conn, provider, mailbox, daily_cap=50, max_this_run=50, pause_seconds=(0, 0),
                                         cold_from=opened, now=lambda: now)
                return result, provider

            # Tue 13 Oct 2026 18:30 UTC = 13:30 CDT, 11:30 PDT: both past the 11:30 preferred window and
            # the queue is small, so first emails are held for everyone.
            result, provider = send(utc(2026, 10, 13, 18, 30))
            assert provider.sent == [] and result.get("held"), result
            # 15:00 UTC = 10:00 CDT (preferred) but only 08:00 PDT (window not open yet): only Texas sends.
            result, provider = send(utc(2026, 10, 13, 15))
            assert [m["to"] for m in provider.sent] == ["bob@gmail.com"], result
            # Wed 14 Oct 16:30 UTC = 09:30 PDT: inside the California preferred window.
            result, provider = send(utc(2026, 10, 14, 16, 30))
            assert [m["to"] for m in provider.sent] == ["sue@westcoastbaths.com"], result
            # Saturday: nothing, and the stop reason names both markets.
            result, provider = send(utc(2026, 10, 17, 16))
            assert provider.sent == [] and result["stopped"]
            # Without the postal address the send-time re-check refuses US mail.
            conn.execute("update messages set status = 'queued', sent_at = null where campaign_id = %s "
                         "and to_email = 'bob@gmail.com'", (cohort["campaign_id"],))
            monkeypatch.delenv("VELARQO_POSTAL_ADDRESS")
            result, provider = send(utc(2026, 10, 13, 15))
            assert provider.sent == [] and result["skipped"] == 1
            reason = conn.execute("select skip_reason from messages where campaign_id = %s and to_email = 'bob@gmail.com'",
                                  (cohort["campaign_id"],)).fetchone()[0]
            assert "POSTAL_ADDRESS" in reason
            raise psycopg.Rollback()
    finally:
        conn.close()
