"""Webhooks in, stop conditions, invoices. Pure tests always run; database
tests commit for real (VELARQO_DB_TESTS=1) and delete their pilot after."""

import base64
import json
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from delivery.monitor import breaches_for, reply_deadline
from delivery.webhooks import BadSignature, check_fresh, classify_homeowner_reply, event_id, minimal, verify_secret, verify_signature
from tests.integration.pilot_fixtures import DB, pilot

UK = ZoneInfo("Europe/London")


# ---------- pure ----------

def test_signature_check_accepts_only_bodies_signed_by_the_key():
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding, rsa

    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
    body = b'{"type":"InboundMessage"}'
    signature = base64.b64encode(private.sign(body, padding.PKCS1v15(), hashes.SHA256())).decode()
    verify_signature(body, signature, public_pem)
    with pytest.raises(BadSignature):
        verify_signature(body + b" ", signature, public_pem)
    with pytest.raises(BadSignature):
        verify_signature(body, None, public_pem)


def test_shared_secret_for_workflow_webhooks():
    verify_secret("s3cret-long", "s3cret-long")
    for given, expected in (("wrong", "s3cret-long"), (None, "s3cret-long"), ("x", None)):
        with pytest.raises(BadSignature):
            verify_secret(given, expected)


def test_replay_window_and_malformed_timestamps():
    now = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
    check_fresh({"timestamp": "2026-11-02T03:00:00Z"}, now)                 # GHL retry hours later: fine
    with pytest.raises(BadSignature):
        check_fresh({"timestamp": "2026-10-30T11:00:00Z"}, now)
    with pytest.raises(BadSignature):
        check_fresh({"timestamp": "yesterday"}, now)


@pytest.mark.parametrize("body,verdict", [
    ("STOP", "opt_out"), ("stop.", "opt_out"), ("Unsubscribe", "opt_out"), ("remove me", "opt_out"),
    ("stop please", "opt_out"), ("please stop", "opt_out"),
    ("End of the month works for me", "reply"), ("Cancel that, Tuesday is better", "reply"),
    ("Can't stop thinking about the windows, ring me", "reply"), ("Please stop texting me", "complaint"),
    ("How did you get my number??", "complaint"), ("I'll report you to the ICO", "complaint"),
    ("wrong number mate", "wrong_person"), ("Who is this?", "reply"), ("Yes still interested", "reply"),
    # second review: no false opt-outs, bare "cancel" goes to a person, signals combine
    ("Stop by Tuesday?", "reply"), ("Yes stop by", "reply"), ("Don't stop", "reply"), ("stop round", "reply"),
    ("Cancel", "reply"), ("Cancel please", "reply"), ("opt-out", "opt_out"), ("STOP \U0001F6D1", "opt_out"),
    ("No more texts", "opt_out"), ("Please remove my number", "opt_out"),
    ("STOP ICO", "complaint"), ("Stop. Wrong number", "wrong_person"),
])
def test_homeowner_replies_are_sorted(body, verdict):
    assert classify_homeowner_reply(body) == verdict


def test_finding7_complaint_and_wrong_person_are_kept_alongside_an_opt_out():
    from delivery.webhooks import reply_signals
    assert reply_signals("STOP ICO") == {"opt_out", "complaint"}
    assert reply_signals("Stop. Wrong number") == {"opt_out", "wrong_person"}
    assert reply_signals("STOP") == {"opt_out"}
    assert reply_signals("Stop by Tuesday?") == set()


def test_retried_events_get_the_same_id_and_we_keep_only_what_we_need():
    event = {"type": "AppointmentUpdate", "appointment": {"id": "a1", "appointmentStatus": "showed", "dateUpdated": "x",
                                                          "address": "1 High St", "title": "Survey for Jane"}}
    assert event_id(event) == event_id(json.loads(json.dumps(event)))
    assert event_id({**event, "webhookId": "w9"}) == "ghl:w9"
    kept = minimal({**event, "contactId": "c1", "firstName": "Jane", "address1": "1 High St", "body": "x" * 900})
    assert "address1" not in kept and "firstName" not in kept and len(kept["body"]) == 500


def test_reply_deadline_respects_working_hours():
    weekday_noon = datetime(2026, 11, 3, 12, 0, tzinfo=UK)
    assert reply_deadline(weekday_noon) == weekday_noon + timedelta(hours=1)
    assert reply_deadline(datetime(2026, 11, 6, 21, 0, tzinfo=UK)) == datetime(2026, 11, 9, 9, 0, tzinfo=UK)
    assert reply_deadline(datetime(2026, 11, 3, 6, 30, tzinfo=UK)) == datetime(2026, 11, 3, 9, 0, tzinfo=UK)


def test_stop_rules():
    def rules(c):
        return [b.rule for b in breaches_for(c, "w")]
    assert rules({"contacted": 25}) == []
    assert rules({"contacted": 25, "opted_out": 3}) == ["opt-out rate"]
    assert rules({"contacted": 10, "opted_out": 3}) == []
    assert rules({"contacted": 5, "complaints": 2}) == ["complaints"]
    assert rules({"contacted": 5, "complaints": 1}) == []
    assert "ICO" in rules({"contacted": 5, "regulator_mentions": 1, "complaints": 1})[0]
    assert rules({"contacted": 60, "manual_minutes": 35}) == []                    # 58 per 100
    assert rules({"contacted": 60, "manual_minutes": 40}) == ["manual time"]       # 67 per 100


def test_http_endpoint_rejects_untrusted_and_malformed_requests():
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    from delivery.webhook_server import make_handler

    def no_db():
        raise AssertionError("must not touch the database for rejected requests")

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(no_db, secret="topsecret"))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        for path, headers, body, expected in (
            ("/ghl/webhook", {}, b'{"type":"x"}', 401),
            ("/ghl/webhook", {"x-wh-signature": "bm90LWEtc2ln"}, b'{"type":"x"}', 401),
            ("/ghl/webhook", {"x-velarqo-secret": "nope"}, b'{"type":"x"}', 401),
            ("/ghl/webhook", {"x-velarqo-secret": "topsecret"}, b"not json", 400),
            ("/ghl/webhook", {"x-velarqo-secret": "topsecret"}, b'{"timestamp": "garbage"}', 401),
            ("/other", {}, b"{}", 404),
        ):
            request = urllib.request.Request(base + path, data=body, headers=headers, method="POST")
            with pytest.raises(urllib.error.HTTPError) as err:
                urllib.request.urlopen(request, timeout=5)
            assert err.value.code == expected, (headers, body)
    finally:
        server.shutdown()


def test_webhook_replies_200_before_the_slow_ghl_follow_up(monkeypatch):
    import threading
    import time
    import urllib.request
    from http.server import ThreadingHTTPServer

    from delivery import webhook_server

    class Conn:
        def close(self):
            pass

    monkeypatch.setattr(webhook_server, "handle_event", lambda conn, event: "stored")
    release, finished = threading.Event(), threading.Event()

    def slow_after(conn, event):          # e.g. GHL hanging on the do-not-disturb push
        release.wait(5)
        finished.set()

    server = ThreadingHTTPServer(("127.0.0.1", 0), webhook_server.make_handler(Conn, "topsecret", slow_after))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        request = urllib.request.Request(f"http://127.0.0.1:{server.server_address[1]}/ghl/webhook",
                                         data=b'{"type": "InboundMessage"}', headers={"x-velarqo-secret": "topsecret"}, method="POST")
        started = time.monotonic()
        with urllib.request.urlopen(request, timeout=5) as response:
            assert response.status == 200 and response.read() == b"stored"
        assert time.monotonic() - started < 2 and not finished.is_set()      # answered while the follow-up still runs
        release.set()
        assert finished.wait(5)
    finally:
        release.set()
        server.shutdown()


# ---------- database ----------

def state_of(conn, pilot_id, contact):
    return conn.execute("select state from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s",
                        (pilot_id, contact)).fetchone()[0]


def inbound(loc, contact, body, mid):
    return {"type": "InboundMessage", "locationId": loc, "contactId": contact, "body": body, "messageId": mid, "direction": "inbound"}


def appointment(loc, contact, status, n, appt_id=None, calendar="cal-1"):
    return {"type": "AppointmentCreate" if n == 0 else "AppointmentUpdate", "locationId": loc,
            "appointment": {"id": appt_id or f"a-{contact}", "contactId": contact, "appointmentStatus": status,
                            "calendarId": calendar, "startTime": "2026-11-10T10:00:00Z", "dateUpdated": str(n)}}


def this_week():
    week = datetime.now(UK).date().isocalendar()
    return f"{week[0]}-W{week[1]:02d}"


@DB
def test_reply_booking_attendance_flow_duplicates_and_unknowns():
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pilot_id, loc, contacts):
        c = contacts[0]
        assert handle_event(conn, inbound(loc, c, "Yes please", "m1")) == "replied"
        assert handle_event(conn, inbound(loc, c, "Yes please", "m1")) == "duplicate"
        assert handle_event(conn, appointment(loc, c, "confirmed", 0)) == "booked"
        handle_event(conn, inbound(loc, c, "see you then", "m2"))
        assert state_of(conn, pilot_id, c) == "booked"                                   # can't move backwards
        assert handle_event(conn, appointment(loc, c, "showed", 1)) == "attended"
        other_cal = appointment(loc, contacts[1], "confirmed", 0, calendar="installers-own")
        assert handle_event(conn, other_cal).startswith("appointment on another calendar")
        assert handle_event(conn, inbound(loc, "c-unknown", "hello", "m3")) == "stored: contact not in this pilot"
        assert handle_event(conn, inbound("other-location", c, "hi", "m4")) == "ignored: unknown location"


@DB
def test_complaints_and_stop_opt_out_queue_dnd_and_pause():
    from delivery.ghl_push import WaveError, claim_wave
    from delivery.monitor import check_pilot
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pilot_id, loc, contacts):
        assert handle_event(conn, inbound(loc, contacts[0], "STOP", "s1")) == "opted out"
        assert state_of(conn, pilot_id, contacts[0]) == "opted_out"
        assert check_pilot(conn, pilot_id) == []                                          # 1/24: fine
        for i, contact in enumerate(contacts[1:3]):
            assert handle_event(conn, inbound(loc, contact, "How did you get my number", f"x{i}")) == "complaint"
        pending = conn.execute("select count(*) from pilot_events where pilot_id = %s and type = 'dnd_pending'", (pilot_id,)).fetchone()[0]
        assert pending == 3                                                               # STOP + 2 complaints go to GHL
        assert any(b.rule == "complaints" for b in check_pilot(conn, pilot_id))
        assert conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0] == "paused"
        with pytest.raises(WaveError):
            claim_wave(conn, pilot_id, "w2", 5)


@DB
def test_resume_counts_only_new_events_and_goes_back_to_the_paused_state():
    from delivery.monitor import check_pilot
    from delivery.pilot import PilotError, advance_pilot
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pilot_id, loc, contacts):
        for i, contact in enumerate(contacts[:2]):
            handle_event(conn, inbound(loc, contact, "how did you get my number", f"k{i}"))
        assert check_pilot(conn, pilot_id)                                                # paused from canary_running
        with conn.transaction():
            conn.execute("insert into pilot_approvals (pilot_id, gate, decision, actor) values (%s, 'resume', 'approved', 'test')", (pilot_id,))
        with pytest.raises(PilotError):
            with conn.transaction():
                advance_pilot(conn, pilot_id, "live", uuid.uuid4())                       # can't skip the go-live gate
        with conn.transaction():
            advance_pilot(conn, pilot_id, "canary_running", uuid.uuid4())
        assert check_pilot(conn, pilot_id) == []                                          # old, reviewed breach doesn't re-pause


@DB
def test_unanswered_and_late_replies_breach():
    from delivery.monitor import check_pilot
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pilot_id, loc, contacts):
        handle_event(conn, inbound(loc, contacts[0], "interested", "r1"))
        created = conn.execute("select created_at from pilot_events where pilot_id = %s and type = 'needs_answer'", (pilot_id,)).fetchone()[0]
        assert check_pilot(conn, pilot_id, now=created + timedelta(minutes=10)) == []
        # an automated workflow message is not an answer
        handle_event(conn, {"type": "OutboundMessage", "locationId": loc, "contactId": contacts[0], "messageId": "auto1", "status": "delivered"})
        late = reply_deadline(created) + timedelta(minutes=1)
        assert [b.rule for b in check_pilot(conn, pilot_id, now=late)] == ["replies not answered within 1 working hour"]


@DB
def test_invoice_rules_one_per_person_credits_caps_and_idempotent():
    from delivery.invoices import build_invoice, invoice_markdown
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24, price_per_booked_gbp=80, max_billable=3) as (conn, pilot_id, loc, contacts):
        for c in contacts[:5]:
            handle_event(conn, appointment(loc, c, "confirmed", 0))
        handle_event(conn, appointment(loc, contacts[0], "confirmed", 0, appt_id="rebook-0"))         # rebook: no second charge
        handle_event(conn, appointment(loc, contacts[1], "noshow", 1))                                # credited
        handle_event(conn, appointment(loc, contacts[2], "cancelled", 1))                             # cancel: wait 14 days
        first = build_invoice(conn, pilot_id, this_week())
        assert first["charges"] == 3 and first["over_cap"] == 2                                     # cap 3, 5 people booked
        assert first["credits"] == 1 and first["total"] == 3 * 80 - 80
        again = build_invoice(conn, pilot_id, this_week())
        assert again["existing"] and again["invoice_id"] == first["invoice_id"]
        text = invoice_markdown(conn, first["invoice_id"])
        assert "No-show credit" in text and "07700" not in text


@DB
def test_rebook_after_no_show_is_not_credited_and_installer_miss_is_charged():
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24, price_per_booked_gbp=80) as (conn, pilot_id, loc, contacts):
        a, b = contacts[0], contacts[1]
        handle_event(conn, appointment(loc, a, "confirmed", 0))
        handle_event(conn, appointment(loc, a, "noshow", 1))
        assert handle_event(conn, appointment(loc, a, "confirmed", 2, appt_id="rebooked")) == "booked"   # rebook allowed
        handle_event(conn, appointment(loc, b, "confirmed", 0))
        handle_event(conn, appointment(loc, b, "noshow", 1))
        key = conn.execute("select homeowner_key from pilot_homeowners where ghl_contact_id = %s", (b,)).fetchone()[0]
        conn.execute("insert into pilot_events (pilot_id, homeowner_key, type) values (%s, %s, 'installer_missed')", (pilot_id, key))
        result = build_invoice(conn, pilot_id, this_week())
        assert result["charges"] == 2 and result["credits"] == 0 and result["total"] == 160


@DB
def test_free_first_homeowners_are_listed_at_zero():
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24, price_per_booked_gbp=80, free_homeowners=50) as (conn, pilot_id, loc, contacts):
        for c in contacts[:3]:
            handle_event(conn, appointment(loc, c, "confirmed", 0))
        result = build_invoice(conn, pilot_id, this_week())
        assert result["free"] == 3 and result["total"] == 0


# ---------- second review (2026-10-11) ----------

def week_after(n: int) -> str:
    week = (datetime.now(UK) + timedelta(weeks=n)).date().isocalendar()
    return f"{week[0]}-W{week[1]:02d}"


def key_of(conn, pilot_id, contact):
    return conn.execute("select homeowner_key from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s",
                        (pilot_id, contact)).fetchone()[0]


def events_of(conn, pilot_id, contact, type_):
    return conn.execute("select payload from pilot_events where pilot_id = %s and homeowner_key = %s and type = %s",
                        (pilot_id, key_of(conn, pilot_id, contact), type_)).fetchall()


@DB
def test_finding7_stop_with_complaint_or_wrong_person_records_both_and_booked_stop_goes_to_a_person():
    from delivery.monitor import check_pilot
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pilot_id, loc, contacts):
        assert handle_event(conn, inbound(loc, contacts[0], "STOP ICO", "s1")) == "complaint"
        assert state_of(conn, pilot_id, contacts[0]) == "opted_out" and events_of(conn, pilot_id, contacts[0], "complaint")
        assert handle_event(conn, inbound(loc, contacts[1], "Stop. Wrong number", "s2")) == "wrong_person"
        assert events_of(conn, pilot_id, contacts[1], "wrong_person")
        handle_event(conn, appointment(loc, contacts[2], "confirmed", 0))
        assert handle_event(conn, inbound(loc, contacts[2], "STOP", "s3")) == "opted out"
        assert events_of(conn, pilot_id, contacts[2], "needs_answer")                 # may be cancelling the survey
        assert handle_event(conn, inbound(loc, contacts[3], "STOP", "s4")) == "opted out"
        assert not events_of(conn, pilot_id, contacts[3], "needs_answer")
        assert handle_event(conn, inbound(loc, contacts[4], "Cancel", "s5")) == "replied"
        assert events_of(conn, pilot_id, contacts[4], "needs_answer")
        assert any("ICO" in b.rule for b in check_pilot(conn, pilot_id))


@DB
def test_finding8_unmatched_events_keep_no_message_body():
    from delivery.webhooks import handle_event
    with pilot(10, wave_size=5) as (conn, pilot_id, loc, _):
        assert handle_event(conn, inbound(loc, "c-stranger", "my address is 1 High St", "u1")) == "stored: contact not in this pilot"
        payload = conn.execute("select payload from pilot_events where pilot_id = %s and type like 'ghl:unmatched:%%'",
                               (pilot_id,)).fetchone()[0]
        assert "body" not in payload and payload["contactId"] == "c-stranger"


@DB
def test_finding2_same_person_or_same_ghl_contact_is_charged_once():
    from delivery.ghl_push import claim_wave
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    rows = [
        {"Ref": "A", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": "07700900001", "Email": "fam@x.com", "Postcode": "LS1 1AA"},
        {"Ref": "B", "Quote Date": "01/06/2026", "Status": "Lost", "Phone": None, "Email": "fam@x.com", "Postcode": "LS1 1AA"},
        {"Ref": "C", "Quote Date": "01/06/2026", "Status": "Lost", "Phone": "07700900003", "Postcode": "LS1 1AA"},
        {"Ref": "D", "Quote Date": "01/06/2026", "Status": "Lost", "Phone": "07700900004", "Postcode": "LS1 1AA"},
    ]
    with pilot(rows=rows, holdout=0.0, state="live", price_per_booked_gbp=80) as (conn, pid, loc, _):
        assert claim_wave(conn, pid, "w1", 30) == 3                                    # A/B are one person
        with conn.transaction():
            conn.execute("update pilot_homeowners set state = 'enrolled', ghl_contact_id = 'c-fam' "
                         "where pilot_id = %s and wave_id = 'w1' and source_record_id in ('A', 'B')", (pid,))
            # safety net: two different people that GHL merged into one contact
            conn.execute("update pilot_homeowners set state = 'enrolled', ghl_contact_id = 'c-merged' "
                         "where pilot_id = %s and source_record_id in ('C', 'D')", (pid,))
        handle_event(conn, appointment(loc, "c-fam", "confirmed", 0))
        handle_event(conn, appointment(loc, "c-merged", "confirmed", 0))
        result = build_invoice(conn, pid, this_week())
        assert result["charges"] == 2 and result["total"] == 160


@DB
def test_finding3_rebook_after_a_credited_no_show_is_charged_again():
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(10, holdout=0.0, wave_size=5, price_per_booked_gbp=80) as (conn, pid, loc, contacts):
        a, b = contacts[0], contacts[1]
        for c in (a, b):
            handle_event(conn, appointment(loc, c, "confirmed", 0, appt_id=f"ap1-{c}"))
        first = build_invoice(conn, pid, week_after(1))
        for c in (a, b):
            handle_event(conn, appointment(loc, c, "noshow", 1, appt_id=f"ap1-{c}"))
        second = build_invoice(conn, pid, week_after(2))
        assert second["credits"] == 2
        handle_event(conn, appointment(loc, a, "confirmed", 2, appt_id=f"ap2-{a}"))      # a rebooks and attends
        handle_event(conn, appointment(loc, a, "showed", 3, appt_id=f"ap2-{a}"))
        handle_event(conn, appointment(loc, b, "confirmed", 2, appt_id=f"ap2-{b}"))      # b rebooks...
        third = build_invoice(conn, pid, week_after(3))
        assert third["reversals"] == 2 and third["total"] == 160
        handle_event(conn, appointment(loc, b, "noshow", 3, appt_id=f"ap2-{b}"))         # ...and misses again
        fourth = build_invoice(conn, pid, week_after(4))
        assert fourth["credits"] == 1 and fourth["total"] == -80
        net = {k: float(t) for k, t in conn.execute(
            "select h.ghl_contact_id, sum(l.amount_gbp) from invoice_lines l join pilot_homeowners h "
            "on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key where l.pilot_id = %s group by 1", (pid,)).fetchall()}
        assert net == {a: 80.0, b: 0.0}                                                  # one booked survey; one credited
        assert first["total"] + second["total"] + third["total"] + fourth["total"] == 80
        assert build_invoice(conn, pid, week_after(5))["total"] == 0                     # nothing repeats


@DB
def test_finding4_credited_no_show_frees_the_cap():
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24, price_per_booked_gbp=80, max_billable=2) as (conn, pid, loc, contacts):
        handle_event(conn, appointment(loc, contacts[0], "confirmed", 0))
        handle_event(conn, appointment(loc, contacts[1], "confirmed", 0))
        handle_event(conn, appointment(loc, contacts[0], "noshow", 1))
        first = build_invoice(conn, pid, this_week())
        assert first["charges"] == 2 and first["credits"] == 1
        handle_event(conn, appointment(loc, contacts[2], "confirmed", 0))
        second = build_invoice(conn, pid, week_after(1))
        assert second["charges"] == 1 and second["over_cap"] == 0                         # 2 charged - 1 credited = room for 1
        handle_event(conn, appointment(loc, contacts[3], "confirmed", 0))
        assert build_invoice(conn, pid, week_after(2))["over_cap"] == 1                   # now full


@DB
def test_finding4_weekly_cap_counts_the_booking_week_and_first_booked_wins():
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24, price_per_booked_gbp=80, max_billable_per_week=1) as (conn, pid, loc, contacts):
        early, late1, late2 = contacts[9], contacts[5], contacts[0]
        for c in (early, late1, late2):                    # booked in this order (not alphabetical)
            handle_event(conn, appointment(loc, c, "confirmed", 0))
        with conn.transaction():
            conn.execute("update pilot_events set created_at = now() - interval '14 days' where pilot_id = %s "
                         "and homeowner_key = %s and type = 'survey_booked'", (pid, key_of(conn, pid, early)))
        result = build_invoice(conn, pid, this_week())
        assert result["charges"] == 2 and result["over_cap"] == 1                         # one per booking week
        charged = {c for (c,) in conn.execute(
            "select h.ghl_contact_id from invoice_lines l join pilot_homeowners h on h.pilot_id = l.pilot_id "
            "and h.homeowner_key = l.homeowner_key where l.pilot_id = %s and l.amount_gbp > 0", (pid,)).fetchall()}
        assert charged == {early, late1}                                                  # by booking time, not name


@DB
def test_finding4_free_start_counts_people_actually_contacted():
    from delivery.ghl_push import claim_wave
    from delivery.invoices import build_invoice
    from delivery.webhooks import handle_event
    with pilot(30, holdout=0.0, state="live", wave_size=10, price_per_booked_gbp=80, free_homeowners=3) as (conn, pid, loc, contacts):
        claim_wave(conn, pid, "w2", 5)                                                    # queued, never texted...
        with conn.transaction():
            conn.execute("update pilot_homeowners set claimed_at = now() - interval '2 days' where pilot_id = %s "
                         "and wave_id = 'w2'", (pid,))                                    # ...but claimed earliest
            conn.execute("update pilot_homeowners set claimed_at = now() - interval '1 day' where pilot_id = %s "
                         "and ghl_contact_id = any(%s)", (pid, contacts[:3]))
        for c in contacts[:4]:
            handle_event(conn, appointment(loc, c, "confirmed", 0))
        result = build_invoice(conn, pid, this_week())
        assert result["free"] == 3 and result["charges"] == 1 and result["total"] == 80


@DB
def test_rates_after_resume_use_people_contacted_since_the_resume():
    from delivery.ghl_push import claim_wave
    from delivery.monitor import check_pilot
    from delivery.pilot import advance_pilot
    from delivery.webhooks import handle_event
    with pilot(60, holdout=0.0, state="live", wave_size=24) as (conn, pid, loc, contacts):
        with conn.transaction():
            conn.execute("update pilot_homeowners set claimed_at = now() - interval '3 days' where pilot_id = %s", (pid,))
        for i in range(3):
            handle_event(conn, inbound(loc, contacts[i], "STOP", f"a{i}"))
        assert [b.rule for b in check_pilot(conn, pid)][0] == "opt-out rate"              # 3/24: paused
        with conn.transaction():
            conn.execute("insert into pilot_approvals (pilot_id, gate, decision, actor) values (%s, 'resume', 'approved', 'test')", (pid,))
            advance_pilot(conn, pid, "live", uuid.uuid4())
        for i in range(3, 5):
            handle_event(conn, inbound(loc, contacts[i], "STOP", f"b{i}"))
        assert check_pilot(conn, pid) == []          # old cohort: not "2 new / 24 ever" (8.3%) against nobody new
        claim_wave(conn, pid, "w2", 20)
        with conn.transaction():
            conn.execute("update pilot_homeowners set state = 'enrolled', ghl_contact_id = 'c-' || phone "
                         "where pilot_id = %s and wave_id = 'w2'", (pid,))
        new = [c for (c,) in conn.execute("select ghl_contact_id from pilot_homeowners where pilot_id = %s and wave_id = 'w2' "
                                          "order by 1", (pid,))]
        for i, c in enumerate(new[:2]):
            handle_event(conn, inbound(loc, c, "STOP", f"c{i}"))
        breaches = check_pilot(conn, pid)                                                 # 2/20 contacted since resume
        assert any(b.rule == "opt-out rate" and b.detail.startswith("w2") for b in breaches)


@DB
def test_reply_received_during_a_pause_still_counts_after_resume():
    from delivery.monitor import check_pilot
    from delivery.pilot import advance_pilot
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=24) as (conn, pid, loc, contacts):
        for i, c in enumerate(contacts[:2]):
            handle_event(conn, inbound(loc, c, "how did you get my number", f"k{i}"))
            handle_event(conn, {"type": "OutboundMessage", "locationId": loc, "contactId": c, "messageId": f"ans{i}",
                                "userId": "pablo", "status": "delivered"})                # answered in time
        assert check_pilot(conn, pid)                                                     # paused (complaints)
        handle_event(conn, inbound(loc, contacts[5], "interested, call me", "p1"))        # arrives while paused
        received = conn.execute("select created_at from pilot_events where pilot_id = %s and type = 'needs_answer' "
                                "and homeowner_key = %s", (pid, key_of(conn, pid, contacts[5]))).fetchone()[0]
        with conn.transaction():
            conn.execute("insert into pilot_approvals (pilot_id, gate, decision, actor) values (%s, 'resume', 'approved', 'test')", (pid,))
            advance_pilot(conn, pid, "canary_running", uuid.uuid4())
        breaches = check_pilot(conn, pid, now=reply_deadline(received) + timedelta(minutes=1))
        assert [b.detail for b in breaches if b.rule == "replies not answered within 1 working hour"] == ["w1: 1"]


@DB
def test_direct_booking_needs_a_message_from_us_within_14_days():
    from delivery.pilot import PilotError, log_manual
    from delivery.webhooks import handle_event
    with pilot(30, wave_size=10) as (conn, pid, loc, contacts):
        def outbound(c, mid):
            handle_event(conn, {"type": "OutboundMessage", "locationId": loc, "contactId": c, "messageId": mid, "status": "delivered"})

        outbound(contacts[0], "o1")
        with conn.transaction():
            assert log_manual(conn, pid, "direct_booking", phone=contacts[0][2:]) == key_of(conn, pid, contacts[0])
        outbound(contacts[1], "o2")
        with conn.transaction():
            conn.execute("update pilot_events set created_at = now() - interval '15 days' where pilot_id = %s "
                         "and homeowner_key = %s", (pid, key_of(conn, pid, contacts[1])))
        not_messaged = conn.execute("select phone from pilot_homeowners where pilot_id = %s and state = 'treatment' limit 1",
                                    (pid,)).fetchone()[0]
        holdout = conn.execute("select phone from pilot_homeowners where pilot_id = %s and arm = 'holdout' limit 1",
                               (pid,)).fetchone()[0]
        for phone, error in ((contacts[1][2:], "more than 14 days"), (contacts[2][2:], "no record of a message"),
                             (not_messaged, "never messaged"), (holdout, "never messaged")):
            with pytest.raises(PilotError, match=error):
                with conn.transaction():
                    log_manual(conn, pid, "direct_booking", phone=phone)
        assert conn.execute("select count(*) from pilot_events where pilot_id = %s and type = 'direct_booking'",
                            (pid,)).fetchone()[0] == 1
