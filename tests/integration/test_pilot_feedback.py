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
])
def test_homeowner_replies_are_sorted(body, verdict):
    assert classify_homeowner_reply(body) == verdict


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
