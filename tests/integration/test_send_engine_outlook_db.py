"""Dry run of the whole cold-email flow through a *mocked Microsoft 365
mailbox*: the real OutlookProvider talking to a fake Graph API, against the
real database schema, inside one transaction that is always rolled back.

send -> follow-up (threaded reply) -> replies/bounce/complaint read back from
the mailbox -> suppression and kill switch. Nothing persists, nothing is sent.

Opt-in like test_send_engine_db.py: VELARQO_DB_TESTS=1 and DATABASE_URL.
"""

import os
from datetime import datetime, timedelta, timezone

import psycopg
import pytest

from integrations.email.outlook import OutlookProvider
from lib.rate_limiter import RateLimiter
from pipelines.cold_outreach.pipeline import DEFAULT_ICP_PATH, load_icp
from tests.integration.fake_graph import FakeGraph

pytestmark = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")

MAILBOX = "pablo@velarqomail.example"


@pytest.fixture
def conn():
    from data.supabase_store import connect
    c = connect()
    c.autocommit = True
    with c.transaction():
        yield c
        raise psycopg.Rollback()
    c.close()


def _outlook(graph):
    return OutlookProvider(access_token=graph.token, sender_email=MAILBOX, session=graph,
                           rate_limiter=RateLimiter(clock=lambda: 0.0, sleep=lambda _: None), sleep=lambda _: None)


def test_outlook_mailbox_end_to_end(conn):
    from outreach.send_engine import engine, experiments

    graph = FakeGraph(mailbox=MAILBOX)
    provider = _outlook(graph)
    assert provider.profile_email() == MAILBOX        # the token-belongs-to-this-mailbox check the CLI runs
    icp = load_icp(DEFAULT_ICP_PATH)
    send = lambda **kw: engine.send_due(  # noqa: E731
        conn, provider, MAILBOX, daily_cap=50, max_this_run=50, respect_window=False, pause_seconds=(0, 0), **kw)

    cohort = engine.create_cohort(conn, "pytest outlook", 3, experiments.load("cold_offer_v1"), icp, "test")
    assert cohort["messages"] == 3
    engine.set_campaign_status(conn, cohort["campaign_id"], "active")
    engine.set_sending(conn, True)

    # First emails go out as new Graph messages; the engine stores Graph's id,
    # conversationId and Message-ID so the follow-up can thread.
    assert send()["sent"] == 3
    with conn.cursor() as cur:
        rows = cur.execute(
            "select to_email, provider, provider_message_id, provider_thread_id, rfc_message_id from messages "
            "where campaign_id = %s and status = 'sent'", (cohort["campaign_id"],)).fetchall()
    assert len(rows) == 3 and all(r[1] == "OutlookProvider" and r[2] and r[3] and r[4] for r in rows)
    first = {r[0]: {"id": r[2], "conv": r[3], "rfc": r[4]} for r in rows}
    assert {m["id"] for m in graph.sent()} == {v["id"] for v in first.values()}
    replier, bouncer, quiet = list(first)

    # Follow-ups queued after 3 business days.
    later = lambda: datetime.now(timezone.utc) + timedelta(days=6)  # noqa: E731
    assert engine.schedule_followups(conn, now=later) == 3

    # The mailbox now holds a "no" (threaded, same conversation), an Exchange
    # NDR for another company, and an unrelated newsletter.
    graph.receive(replier, "Re: old quotes", "No thanks\n\nOn Tue, Pablo wrote:\n> Reply \"no\"",
                  conversation_id=first[replier]["conv"])
    graph.receive(f"postmaster@{MAILBOX.split('@')[1]}", "Undeliverable: old quotes",
                  f"Your message to {bouncer} couldn't be delivered. 550 5.1.1 Recipient not found")
    graph.receive("news@supplier-example.co.uk", "October offers", "Big sale on uPVC profiles")

    counts = engine.sync_inbox(conn, provider, MAILBOX)
    assert counts == {"unsubscribe": 1, "bounce": 1, "unknown": 1}, counts
    assert engine.sync_inbox(conn, provider, MAILBOX) == {}, "already-seen messages are not re-processed"

    # Only the quiet company's follow-up goes out, as a reply to its first email.
    result = send(now=later)
    assert (result["sent"], result["skipped"]) == (1, 0), result
    follow_up = [m for m in graph.sent() if m["id"] not in {v["id"] for v in first.values()}]
    assert len(follow_up) == 1
    follow_up = follow_up[0]
    assert follow_up["toRecipients"] == [{"emailAddress": {"address": quiet}}]
    assert follow_up["subject"].startswith("Re: ") and follow_up["conversationId"] == first[quiet]["conv"]
    headers = {h["name"]: h["value"] for h in follow_up["internetMessageHeaders"]}
    assert headers["In-Reply-To"] == first[quiet]["rfc"]
    assert any(c["url"].endswith(f"/me/messages/{first[quiet]['id']}/createReply") for c in graph.calls)

    with conn.cursor() as cur:
        suppressed = {r[0] for r in cur.execute("select lower(email) from suppressions where email is not null")}
        cancelled = cur.execute("select count(*) from messages where campaign_id = %s and status = 'cancelled'",
                                (cohort["campaign_id"],)).fetchone()[0]
        bounced = cur.execute("select count(bounced_at) from messages where campaign_id = %s",
                              (cohort["campaign_id"],)).fetchone()[0]
    assert {replier.lower(), bouncer.lower()} <= suppressed
    assert cancelled == 2 and bounced == 1         # replier's and bouncer's follow-ups dropped
    assert any(r["category"] == "unknown" and r["from_email"] == "news@supplier-example.co.uk"
               for r in engine.open_replies(conn)), "unmatched mail is left for a human"

    # A complaint read from the Outlook mailbox pulls the global kill switch.
    graph.receive(quiet, "Re: old quotes", "This is spam, how did you get my email?", conversation_id=first[quiet]["conv"])
    engine.sync_inbox(conn, provider, MAILBOX)
    assert not engine.controls(conn)["sending_enabled"]
    assert "complaint" in engine.controls(conn)["paused_reason"]
    assert send(now=later)["stopped"] == "sending disabled"


def test_outlook_login_failure_puts_the_email_back_and_stops_the_mailbox(conn):
    from outreach.send_engine import engine, experiments

    graph = FakeGraph(mailbox=MAILBOX)
    provider = _outlook(graph)
    provider.access_token = "revoked"
    icp = load_icp(DEFAULT_ICP_PATH)
    cohort = engine.create_cohort(conn, "pytest outlook auth", 2, experiments.load("cold_offer_v1"), icp, "test")
    engine.set_campaign_status(conn, cohort["campaign_id"], "active")
    engine.set_sending(conn, True)

    result = engine.send_due(conn, provider, MAILBOX, daily_cap=50, respect_window=False, pause_seconds=(0, 0))

    assert result["sent"] == 0 and "login refused" in result["stopped"]
    with conn.cursor() as cur:
        statuses = [r[0] for r in cur.execute("select status from messages where campaign_id = %s", (cohort["campaign_id"],))]
    assert statuses == ["queued", "queued"], "nothing marked failed or sent"
