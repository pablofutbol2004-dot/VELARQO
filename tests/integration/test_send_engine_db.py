"""End-to-end send engine against the real Supabase schema, inside one
transaction that is always rolled back - nothing persists.

Opt-in: VELARQO_DB_TESTS=1 (needs DATABASE_URL and the send_engine migration).
"""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from pipelines.cold_outreach.pipeline import DEFAULT_ICP_PATH, load_icp

pytestmark = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")

MAILBOX = "test@example.invalid"


class FakeMailbox:
    def __init__(self):
        self.sent = []

    def send_email(self, to, subject, body, thread_id=None, in_reply_to_message_id=None):
        self.sent.append({"to": to, "subject": subject, "thread_id": thread_id, "in_reply_to": in_reply_to_message_id})
        n = len(self.sent)
        return {"message_id": f"m{n}", "thread_id": thread_id or f"t{n}"}

    def rfc_message_id(self, message_id):
        return f"<{message_id}@test>"


@pytest.fixture
def conn():
    from data.supabase_store import connect
    c = connect()
    c.autocommit = True
    with c.transaction():
        yield c
        raise psycopg.Rollback()
    c.close()


def test_full_cycle(conn):
    from outreach.send_engine import engine, experiments

    icp = load_icp(DEFAULT_ICP_PATH)
    send = lambda provider, **kw: engine.send_due(  # noqa: E731
        conn, provider, MAILBOX, daily_cap=50, max_this_run=50, respect_window=False, pause_seconds=(0, 0), **kw)

    cohort = engine.create_cohort(conn, "pytest cohort", 4, experiments.load("cold_offer_v1"), icp, "test")
    assert cohort["messages"] == 4
    rows = engine.review_rows(conn, cohort["campaign_id"])
    assert all("Reply \"no\"" in r["body"] for r in rows)

    # Nothing sends while the campaign is a draft or the kill switch is off.
    provider = FakeMailbox()
    engine.set_sending(conn, False, "test")
    assert send(provider)["sent"] == 0
    engine.set_campaign_status(conn, cohort["campaign_id"], "active")
    assert send(provider)["stopped"] == "sending disabled"
    engine.set_sending(conn, True)

    # Suppressed addresses are skipped at send time, not just at cohort time.
    with conn.cursor() as cur:
        engine.suppress(cur, rows[0]["to_email"], "manual", "pytest")
    result = send(provider)
    assert (result["sent"], result["skipped"]) == (3, 1)
    assert send(provider)["sent"] == 0, "a second run must never resend"

    # A second cohort never re-picks companies already contacted.
    again = engine.create_cohort(conn, "pytest cohort 2", 4, experiments.load("cold_offer_v1"), icp, "test")
    contacted = {r["to_email"] for r in rows}
    assert not contacted & {r["to_email"] for r in engine.review_rows(conn, again["campaign_id"])}
    engine.set_campaign_status(conn, again["campaign_id"], "done")

    # Follow-ups wait 3 business days, then thread onto the first email.
    assert engine.schedule_followups(conn) == 0
    later = lambda: datetime.now(timezone.utc) + timedelta(days=6)  # noqa: E731
    assert engine.schedule_followups(conn, now=later) == 3
    assert engine.schedule_followups(conn, now=later) == 0, "idempotent"

    sent_first = {s["to"]: s for s in provider.sent}
    replier, bouncer, quiet = list(sent_first)

    # "no" from one company: suppressed, its queued follow-up cancelled.
    engine.record_inbound(conn, MAILBOX, {
        "provider_message_id": "in1", "thread_id": sent_first[replier]["thread_id"] or "t1",
        "from_email": replier, "subject": "Re: old quotes", "body": "No\n\nOn Tue someone wrote:\n> Reply \"no\"",
        "internal_date_ms": None,
    })
    # Bounce for another: matched through the notice text, address suppressed.
    engine.record_inbound(conn, MAILBOX, {
        "provider_message_id": "in2", "thread_id": None, "from_email": "mailer-daemon@googlemail.com",
        "subject": "Delivery Status Notification (Failure)", "body": f"Your message to {bouncer} was not delivered",
        "internal_date_ms": None,
    })

    result = send(provider, now=later)
    assert result["sent"] == 1, result
    follow_up = provider.sent[-1]
    assert follow_up["to"] == quiet
    assert follow_up["subject"].startswith("Re: ")
    assert follow_up["thread_id"] and follow_up["in_reply_to"].endswith("@test>")

    with conn.cursor() as cur:
        suppressed = {r[0] for r in cur.execute("select lower(email) from suppressions where email is not null")}
    assert {replier.lower(), bouncer.lower()} <= suppressed

    # A complaint pulls the global kill switch.
    engine.record_inbound(conn, MAILBOX, {
        "provider_message_id": "in3", "thread_id": None, "from_email": quiet,
        "subject": "Re: old quotes", "body": "This is spam. How did you get my email?", "internal_date_ms": None,
    })
    assert not engine.controls(conn)["sending_enabled"]
    assert any(r["category"] == "complaint" for r in engine.open_replies(conn))

    # Funnel outcomes feed the experiment readout.
    company = engine.find_company(conn, quiet)
    engine.log_outcome(conn, company["id"], "call_held", {"pricing_experiment": "pricing_p1", "price_arm": "mid"})
    engine.log_outcome(conn, company["id"], "sample_received", {})
    rows = engine.cold_email_results(conn, "cold_offer_v1")
    assert sum(r["sent"] for r in rows) == 3
    assert sum(r["calls"] for r in rows) == 1 and sum(r["samples"] for r in rows) == 1
    assert sum(r["complaints"] for r in rows) == 1
    assert engine.pricing_results(conn, "pricing_p1")[0]["samples"] == 1


def test_one_sequence_per_inbox_and_unmatched_opt_outs(conn):
    """Review fixes: rows sharing an email get one sequence; an address already
    emailed is never picked again (any trade); a colleague at the same firm
    who replies from another address is matched by domain; an opt-out from an
    address we can't match is still honoured."""
    from outreach.send_engine import engine, experiments

    icp = load_icp(DEFAULT_ICP_PATH)
    shared = conn.execute(
        "select lower(q.email) from outreach_queue q join companies c on c.id = q.id where q.vertical = 'windows' "
        "and c.company_category = 'Private Limited Company' group by 1 having count(*) > 1 limit 1").fetchone()
    if not shared:
        pytest.skip("no shared email addresses in the current data")
    exp = experiments.load("cold_offer_v1")
    exp.pop("exclude_segments", None)
    cohort = engine.create_cohort(conn, "pytest shared", 2000, exp, icp, "test")
    rows = engine.review_rows(conn, cohort["campaign_id"])
    addresses = [r["to_email"].lower() for r in rows]
    assert len(addresses) == len(set(addresses)), "every inbox appears once"
    again = engine.create_cohort(conn, "pytest shared 2", 2000, exp, icp, "test")
    assert again["messages"] == 0 or not set(addresses) & {r["to_email"].lower() for r in engine.review_rows(conn, again["campaign_id"])}

    # Send one, then a colleague at the same domain says "take us off your list".
    engine.set_campaign_status(conn, cohort["campaign_id"], "active")
    engine.set_sending(conn, True)
    provider = FakeMailbox()
    engine.send_due(conn, provider, MAILBOX, daily_cap=1, max_this_run=1, respect_window=False, pause_seconds=(0, 0))
    sent_to = provider.sent[0]["to"]
    domain = sent_to.split("@")[1]
    result = engine.record_inbound(conn, MAILBOX, {
        "provider_message_id": "colleague1", "thread_id": None, "from_email": f"dave.colleague@{domain}",
        "subject": "your email", "body": "Please take us off your list", "internal_date_ms": None})
    assert result["matched"] and result["category"] == "unsubscribe"
    assert engine._is_suppressed(conn.cursor(), sent_to)

    # Unknown sender, unknown domain: still suppressed.
    result = engine.record_inbound(conn, MAILBOX, {
        "provider_message_id": "stranger1", "thread_id": None, "from_email": "someone@neverheardof-example.co.uk",
        "subject": "stop", "body": "unsubscribe", "internal_date_ms": None})
    assert not result["matched"] and engine._is_suppressed(conn.cursor(), "someone@neverheardof-example.co.uk")
