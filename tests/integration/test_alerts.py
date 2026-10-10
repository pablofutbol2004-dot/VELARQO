"""Reply alerts and the scoreboard.

Without a database: the channels (ntfy, Telegram, email) with a fake HTTP
session and a fake mailbox, the playbook suggestions, the sample alert,
and the scoreboard text/CSV from a synthetic board.

With VELARQO_DB_TESTS=1 (rolled back, nothing persists): a positive reply
recorded by the engine produces exactly one alert with the reply text,
the company, the call sheet and the suggested reply; a second tick sends
nothing; the 20:00 summary goes once; the scoreboard counts it per arm.
"""

import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from outreach.alerts import playbook
from outreach.alerts import replies as alerts
from outreach.alerts.channels import Alert, Notifier
from reporting import scoreboard


class FakeResponse:
    def __init__(self, status=200):
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, fail: set[str] = ()):
        self.posts, self.fail = [], set(fail)

    def post(self, url, **kwargs):
        self.posts.append({"url": url, **kwargs})
        return FakeResponse(500 if any(f in url for f in self.fail) else 200)


class FakeMailbox:
    def __init__(self):
        self.sent = []

    def send_email(self, to, subject, body, **kwargs):
        self.sent.append({"to": to, "subject": subject, "body": body})
        return {"message_id": f"m{len(self.sent)}"}


CONFIG = {"email_to": "pablo@example.com", "mailbox": None, "ntfy_topic": "velarqo-secret-topic",
          "ntfy_server": "https://ntfy.sh", "telegram_token": "123:abc", "telegram_chat": "42"}


def _notifier(session=None, mailbox=None, config=CONFIG):
    mailbox = mailbox or FakeMailbox()
    return Notifier(config=config, send_email=mailbox.send_email, session=session or FakeSession()), mailbox


def test_every_configured_channel_gets_the_alert():
    session = FakeSession()
    notifier, mailbox = _notifier(session)
    assert notifier.channels == ["ntfy", "telegram", "email"]
    result = notifier.send(Alert(title="[Velarqo] POSITIVE: Acme", body="Yeah go on then ✓", priority="urgent", tags=["tada"]))
    assert [(d.channel, d.ok) for d in result] == [("ntfy", True), ("telegram", True), ("email", True)]
    ntfy, telegram = session.posts
    assert ntfy["url"] == "https://ntfy.sh/velarqo-secret-topic"
    assert ntfy["headers"]["Priority"] == "5" and ntfy["headers"]["Tags"] == "tada"
    assert ntfy["headers"]["Title"].isascii() and ntfy["data"] == "Yeah go on then ✓".encode("utf-8")
    assert telegram["url"].startswith("https://api.telegram.org/bot123:abc/sendMessage")
    assert telegram["json"]["chat_id"] == "42" and "Yeah go on then" in telegram["json"]["text"]
    assert mailbox.sent[0]["to"] == "pablo@example.com" and mailbox.sent[0]["subject"] == "[Velarqo] POSITIVE: Acme"


def test_a_dead_channel_does_not_lose_the_others():
    notifier, mailbox = _notifier(FakeSession(fail={"ntfy.sh"}))
    result = notifier.send(Alert(title="t", body="b"))
    assert [(d.channel, d.ok) for d in result] == [("ntfy", False), ("telegram", True), ("email", True)]
    assert "HTTP 500" in result[0].detail
    assert len(mailbox.sent) == 1


def test_unconfigured_channels_are_skipped():
    notifier = Notifier(config={"email_to": None, "ntfy_topic": None, "ntfy_server": "https://ntfy.sh",
                                "telegram_token": None, "telegram_chat": None}, session=FakeSession())
    assert notifier.channels == []
    assert notifier.send(Alert(title="t", body="b")) == []
    only_push = Notifier(config={**CONFIG, "email_to": None}, session=FakeSession())
    assert only_push.channels == ["ntfy", "telegram"]


def test_sample_positive_alert_has_everything_a_human_needs():
    session = FakeSession()
    notifier, mailbox = _notifier(session)
    deliveries = alerts.test_alert(notifier)
    assert all(d.ok for d in deliveries) and len(deliveries) == 3
    body = mailbox.sent[0]["body"]
    assert mailbox.sent[0]["subject"].startswith("[Velarqo] TEST alert: POSITIVE: wants a call")
    assert "give me a bell on 07700 900123" in body            # the reply text
    assert "Example Windows Ltd (TEST)" in body                 # the company
    assert "call-sheet" in body and "Ring them" in body         # the playbook step for "call me"
    assert "handled test-0000" in body


@pytest.mark.parametrize("category, intent, must_contain", [
    ("positive", "interested", "15-minute call"),
    ("positive", "how_much", "No setup fee"),
    ("positive", "send_info", "Short version of how it works"),     # docs/delivery/01_send_info_email.md
    ("positive", "call_me", "call-sheet"),
    ("positive", "yes", "15-minute call"),
    ("unknown", "already_follow_up", "second or third chase"),
    ("unknown", "gdpr_question", "Answer it yourself"),
    ("unknown", "wrong_person", "person they named"),
    ("unknown", "later", "come back to you"),
    ("unknown", "mixed", "both a no and a yes"),
    ("unknown", "question", "Answer the question"),
    ("unknown", None, "Read it and decide"),
    ("complaint", "legal", "PAUSED"),
    ("not_interested", None, "Already suppressed"),
    ("unsubscribe", None, "Already suppressed"),
])
def test_playbook_suggestion_matches_the_sales_playbook(category, intent, must_contain):
    text = playbook.suggestion(category, intent, name="Dave", company="Acme Windows Ltd", email="dave@acme.co.uk", reply_id="r1")
    assert must_contain in text
    assert "{" not in text.replace("{company}", ""), "unfilled placeholder"


def test_send_info_text_names_the_company_and_arm_b_variant():
    text = playbook.suggestion("positive", "send_info", company="Acme Windows Ltd", arm="B_first_50_free")
    assert "Acme Windows Ltd's name" in text
    assert "first 50 for free" in text
    assert "price" not in text.split("Roughly how many")[0].lower().replace("you only pay", ""), "no price in writing"


def test_unmatched_reply_tells_you_to_find_the_thread():
    assert "couldn't be tied" in playbook.suggestion("positive", "interested", matched=False)
    assert "Already suppressed" in playbook.suggestion("unsubscribe", None, matched=False)


def test_summary_is_due_from_20_00_uk():
    assert not alerts.summary_due(datetime(2026, 10, 26, 18, 59, tzinfo=timezone.utc))     # 18:59 GMT
    assert alerts.summary_due(datetime(2026, 10, 26, 20, 0, tzinfo=timezone.utc))
    assert alerts.summary_due(datetime(2026, 7, 6, 19, 5, tzinfo=timezone.utc))            # 20:05 BST


def _board():
    zero = dict.fromkeys(scoreboard.METRICS, 0)
    return {
        "day": date(2026, 10, 26),
        "today": {**zero, "sent": 40, "bounces": 1, "replies": 3, "positive": 1, "opt_outs": 1},
        "total": {**zero, "sent": 120, "bounces": 2, "replies": 7, "positive": 2, "calls": 1, "opt_outs": 2},
        "by_arm": [
            {"experiment": "cold_offer_v1", "arm": "A_pay_per_booked_survey", "today": {**zero, "sent": 20, "replies": 2, "positive": 1},
             "total": {**zero, "sent": 60, "replies": 4, "positive": 2, "calls": 1}},
            {"experiment": "cold_offer_v1", "arm": "B_first_50_free", "today": {**zero, "sent": 20, "replies": 1, "opt_outs": 1},
             "total": {**zero, "sent": 60, "replies": 3, "opt_outs": 2}},
        ],
        "by_step": [{"step": 1, "today": {**zero, "sent": 40}, "total": {**zero, "sent": 100}},
                    {"step": 2, "today": zero, "total": {**zero, "sent": 20, "replies": 2}}],
        "waiting": 2, "oldest_waiting_minutes": 95, "handled_today": 1, "minutes_to_handle": 23.0,
        "sending_enabled": True, "paused_reason": None,
    }


def test_scoreboard_text_and_csv(tmp_path):
    text = scoreboard.format_text(_board())
    assert text.splitlines()[0] == "Velarqo scoreboard Mon 26 Oct  (today|total)"
    assert "sent 40|120  bounces 1|2  replies 3|7  positive 1|2  calls 0|1  samples 0|0  pilots 0|0  opt-outs 1|2" in text
    assert "cold_offer_v1 / A_pay_per_booked_survey: sent 20|60" in text
    assert "step 2: sent 0|20" in text
    assert "waiting for you: 2 (oldest 1h35m); handled today 1, avg 23 min to handle" in text
    assert text.endswith("sending: ON")
    assert "step" not in scoreboard.format_text(_board(), short=True)

    path = scoreboard.write_csv(_board(), tmp_path)
    assert path.name == "scoreboard_2026-10-26.csv"
    rows = path.read_text(encoding="utf-8-sig").splitlines()
    assert rows[0] == "day,scope,experiment,arm,step,period,sent,bounces,replies,positive,calls,samples,pilots,opt_outs"
    assert "2026-10-26,all,,,,today,40,1,3,1,0,0,0,1" in rows
    assert "2026-10-26,arm,cold_offer_v1,B_first_50_free,,total,60,0,3,0,0,0,0,2" in rows
    assert len(rows) == 1 + 2 * (1 + 2 + 2)


def test_merge_fills_zeros_for_sides_with_no_rows():
    merged = scoreboard._merge([{"k": 1, "sent_today": 3, "sent_total": 9}], [{"k": 1, "calls_total": 1}], ("k",))
    assert merged == [{"k": 1, "today": {**dict.fromkeys(scoreboard.METRICS, 0), "sent": 3},
                       "total": {**dict.fromkeys(scoreboard.METRICS, 0), "sent": 9, "calls": 1}}]


# --- With the database ----------------------------------------------------

db = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")


@pytest.fixture
def conn():
    import psycopg
    from data.supabase_store import connect
    c = connect()
    c.autocommit = True
    with c.transaction():
        yield c
        raise psycopg.Rollback()
    c.close()


class RecordingNotifier(Notifier):
    def __init__(self):
        super().__init__(config={**CONFIG, "email_to": None}, session=FakeSession())
        self.alerts = []

    def send(self, alert, **kw):
        self.alerts.append(alert)
        return super().send(alert, **kw)


@db
def test_positive_reply_pings_once_and_counts_on_the_scoreboard(conn):
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    from outreach.send_engine import engine, experiments

    exp = experiments.load("cold_offer_v1")
    mailbox = "test@example.invalid"
    with conn.cursor(row_factory=dict_row) as cur:
        company = cur.execute("select id, display_name from companies where email is not null and display_name is not null limit 1").fetchone()
        assert company, "the local database has no companies"
        campaign = cur.execute(
            "insert into campaigns (name, vertical, settings, status) values ('pytest alerts', 'windows', %s, 'active') returning id",
            (Jsonb({"experiment": exp}),)).fetchone()["id"]
        message = cur.execute(
            """insert into messages (campaign_id, company_id, to_email, variant_index, subject, body, sequence_step, status,
                                     sent_at, mailbox, provider_thread_id, idempotency_key)
               values (%s, %s, 'dave@pytest-alerts.invalid', 0, 'old quotes', 'hi', 1, 'sent', now(), %s, 'thread-1', %s) returning id""",
            (campaign, company["id"], mailbox, f"{campaign}:{company['id']}:1")).fetchone()["id"]

    inbound = {"provider_message_id": "pytest-reply-1", "thread_id": "thread-1", "from_email": "dave@pytest-alerts.invalid",
               "subject": "Re: old quotes", "body": "Yeah go on then, how much is it? Give me a bell on 07700 900123\n\nDave",
               "internal_date_ms": int(datetime.now(timezone.utc).timestamp() * 1000)}
    assert engine.record_inbound(conn, mailbox, inbound)["category"] == "positive"

    notifier = RecordingNotifier()
    assert alerts.send_pending(conn, notifier) == {"alerted": 1, "failed": 0, "no_channel": False}
    alert = notifier.alerts[0]
    assert alert.title == f"[Velarqo] POSITIVE: wants a call: {company['display_name']}"
    assert alert.priority == "urgent"
    assert "how much is it? Give me a bell" in alert.body               # the reply text
    assert company["display_name"] in alert.body                         # the company
    assert "step 1 sent" in alert.body and "cold_offer_v1 / A_pay_per_booked_survey" in alert.body   # call sheet
    assert "PRICE TO QUOTE (pricing_p1" in alert.body
    assert "Ring them" in alert.body and "call-sheet dave@pytest-alerts.invalid" in alert.body     # playbook
    # the same reply is never alerted twice
    assert alerts.send_pending(conn, notifier)["alerted"] == 0
    assert len(notifier.alerts) == 1

    # not-interested replies are not pinged (suppressed already, no rush)
    inbound2 = {**inbound, "provider_message_id": "pytest-reply-2", "from_email": "no@pytest-alerts.invalid", "thread_id": None,
                "body": "Not interested thanks"}
    with conn.cursor() as cur:
        cur.execute("insert into messages (campaign_id, company_id, to_email, variant_index, subject, body, sequence_step, status, sent_at, mailbox, idempotency_key) "
                    "values (%s, %s, 'no@pytest-alerts.invalid', 1, 'old quotes', 'hi', 1, 'sent', now(), %s, %s)",
                    (campaign, company["id"], mailbox, f"{campaign}:{company['id']}:1b"))
    assert engine.record_inbound(conn, mailbox, inbound2)["category"] == "not_interested"
    assert alerts.send_pending(conn, notifier)["alerted"] == 0

    # the 20:00 summary goes once a day
    evening = datetime.now(timezone.utc).replace(hour=20, minute=30)
    first = alerts.send_daily_summary(conn, notifier, now=evening)
    assert first.startswith("sent via ntfy, telegram"), first
    assert alerts.send_daily_summary(conn, notifier, now=evening).startswith("already sent today")
    assert "Velarqo scoreboard" in notifier.alerts[-1].body
    assert alerts.send_daily_summary(conn, notifier, now=evening.replace(hour=9)) == "not yet (before 20:00 UK)"

    board = scoreboard.compute(conn)
    assert board["today"]["sent"] >= 2 and board["today"]["replies"] >= 2 and board["today"]["positive"] >= 1
    arms = {(r["experiment"], r["arm"]): r for r in board["by_arm"]}
    assert arms[("cold_offer_v1", "A_pay_per_booked_survey")]["today"]["positive"] >= 1
    assert arms[("cold_offer_v1", "B_first_50_free")]["today"]["replies"] >= 1
    assert any(r["step"] == 1 for r in board["by_step"])
    assert board["waiting"] >= 2
    assert "sent " in scoreboard.format_text(board)
