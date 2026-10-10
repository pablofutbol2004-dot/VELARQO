"""Webhooks in, stop conditions, invoices. Pure tests always run; database
tests need VELARQO_DB_TESTS=1 and roll back."""

import base64
import json
import os
import uuid
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import psycopg
import pytest

from delivery.monitor import reply_deadline, wave_breaches
from delivery.webhooks import BadSignature, check_fresh, classify_homeowner_reply, event_id, verify_signature

UK = ZoneInfo("Europe/London")
db = pytest.mark.skipif(os.environ.get("VELARQO_DB_TESTS") != "1", reason="set VELARQO_DB_TESTS=1")


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


def test_old_timestamps_are_rejected_as_replays():
    now = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc)
    check_fresh({"timestamp": "2026-11-02T11:58:00Z"}, now)
    with pytest.raises(BadSignature):
        check_fresh({"timestamp": "2026-11-02T11:00:00Z"}, now)


@pytest.mark.parametrize("body,verdict", [
    ("STOP", "opt_out"), ("stop please", "opt_out"), ("Unsubscribe", "opt_out"),
    ("How did you get my number??", "complaint"), ("I'll report you to the ICO", "complaint"),
    ("wrong number mate", "wrong_person"), ("Yes still interested, when can you come?", "reply"),
    ("Can't stop thinking about the new windows, ring me", "reply"),
])
def test_homeowner_replies_are_sorted(body, verdict):
    assert classify_homeowner_reply(body) == verdict


def test_retried_events_get_the_same_id():
    event = {"type": "AppointmentUpdate", "appointment": {"id": "a1", "appointmentStatus": "showed", "dateUpdated": "x"}}
    assert event_id(event) == event_id(json.loads(json.dumps(event)))
    assert event_id({**event, "webhookId": "w9"}) == "ghl:w9"


def test_reply_deadline_respects_working_hours():
    weekday_noon = datetime(2026, 11, 3, 12, 0, tzinfo=UK)          # Tuesday
    assert reply_deadline(weekday_noon) == weekday_noon + timedelta(hours=1)
    friday_night = datetime(2026, 11, 6, 21, 0, tzinfo=UK)
    assert reply_deadline(friday_night) == datetime(2026, 11, 9, 9, 0, tzinfo=UK)   # Monday 09:00
    early = datetime(2026, 11, 3, 6, 30, tzinfo=UK)
    assert reply_deadline(early) == datetime(2026, 11, 3, 9, 0, tzinfo=UK)


def test_stop_rules():
    assert wave_breaches({"contacted": 25}) == []
    assert [b.rule for b in wave_breaches({"contacted": 25, "opted_out": 3})] == ["opt-out rate"]       # 12% > 8%
    assert wave_breaches({"contacted": 10, "opted_out": 3}) == []                                     # too few to judge a rate
    assert [b.rule for b in wave_breaches({"contacted": 5, "complaints": 2})] == ["complaints"]
    assert wave_breaches({"contacted": 5, "complaints": 1}) == []
    assert "ICO" in wave_breaches({"contacted": 5, "regulator_mentions": 1, "complaints": 1})[0].rule
    assert wave_breaches({"contacted": 60, "manual_minutes": 35}) == []                               # 58 min per 100: fine
    assert [b.rule for b in wave_breaches({"contacted": 60, "manual_minutes": 40})] == ["manual time"]  # 67 per 100


# ---------- database ----------

@pytest.fixture()
def live_pilot():
    from data.supabase_store import connect
    from delivery.ghl_push import claim_wave
    from delivery.pilot import freeze_pilot, import_records

    conn = connect()
    pilot_id = f"test-{uuid.uuid4().hex[:8]}"
    location = f"loc-{pilot_id}"
    tx = conn.transaction()
    tx.__enter__()
    conn.execute("insert into pilots (id, client_slug, vertical, holdout_fraction, state, ghl_location_id, price_per_booked_gbp) "
                 "values (%s, 'test', 'windows', 0.2, 'data_received', %s, 80)", (pilot_id, location))
    records = [{"Ref": f"Q{i}", "Quote Date": "01/05/2026", "Status": "Lost", "Phone": f"07700900{i:03d}", "Name": f"Ann{i} Smith",
                "Postcode": "LS1 1AA"} for i in range(30)]
    run = uuid.uuid4()
    import_records(conn, pilot_id, records, set(), run, date(2026, 10, 10))
    freeze_pilot(conn, pilot_id, run)
    conn.execute("update pilots set state = 'canary_running' where id = %s", (pilot_id,))
    claim_wave(conn, pilot_id, "w1", 24)
    conn.execute("update pilot_homeowners set state = 'enrolled', ghl_contact_id = 'c-' || phone "
                 "where pilot_id = %s and wave_id = 'w1'", (pilot_id,))
    contacts = [c for (c,) in conn.execute("select ghl_contact_id from pilot_homeowners where pilot_id = %s and wave_id = 'w1' "
                                           "order by ghl_contact_id", (pilot_id,))]
    yield conn, pilot_id, location, contacts
    try:
        tx.__exit__(psycopg.Rollback, psycopg.Rollback(), None)
    finally:
        conn.close()


def state_of(conn, pilot_id, contact):
    return conn.execute("select state from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s",
                        (pilot_id, contact)).fetchone()[0]


@db
def test_reply_booking_attendance_flow_and_duplicates(live_pilot):
    from delivery.webhooks import handle_event
    conn, pilot_id, loc, contacts = live_pilot
    c = contacts[0]
    reply = {"type": "InboundMessage", "locationId": loc, "contactId": c, "body": "Yes please", "messageId": "m1", "direction": "inbound"}
    assert handle_event(conn, reply) == "replied"
    assert handle_event(conn, reply) == "duplicate"                                   # GHL retry
    booked = {"type": "AppointmentCreate", "locationId": loc, "appointment": {"id": "a1", "contactId": c, "appointmentStatus": "confirmed",
              "startTime": "2026-11-10T10:00:00Z", "dateUpdated": "1"}}
    assert handle_event(conn, booked) == "booked"
    late_reply = {**reply, "messageId": "m2", "body": "see you then"}
    handle_event(conn, late_reply)
    assert state_of(conn, pilot_id, c) == "booked"                                    # can't move backwards
    showed = {"type": "AppointmentUpdate", "locationId": loc, "appointment": {**booked["appointment"], "appointmentStatus": "showed", "dateUpdated": "2"}}
    assert handle_event(conn, showed) == "attended"
    assert handle_event(conn, {"type": "InboundMessage", "locationId": "someone-else", "contactId": c, "body": "hi"}).startswith("ignored")


@db
def test_stop_and_complaints_opt_out_and_pause_the_pilot(live_pilot):
    from delivery.monitor import check_pilot
    from delivery.webhooks import handle_event
    conn, pilot_id, loc, contacts = live_pilot
    assert handle_event(conn, {"type": "InboundMessage", "locationId": loc, "contactId": contacts[0], "body": "STOP", "messageId": "s1"}) == "opted out"
    assert state_of(conn, pilot_id, contacts[0]) == "opted_out"
    assert check_pilot(conn, pilot_id) == []                                          # 1/24 opted out: fine
    for i, contact in enumerate(contacts[1:3]):
        handle_event(conn, {"type": "InboundMessage", "locationId": loc, "contactId": contact,
                            "body": "How did you get my number", "messageId": f"x{i}"})
    breaches = check_pilot(conn, pilot_id)
    assert any(b.rule == "complaints" for b in breaches)
    assert conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0] == "paused"
    from delivery.ghl_push import WaveError, claim_wave
    with pytest.raises(WaveError):
        claim_wave(conn, pilot_id, "w2", 5)                                           # paused: no new waves


@db
def test_unanswered_reply_pauses_after_one_working_hour(live_pilot):
    from delivery.monitor import check_pilot
    from delivery.webhooks import handle_event
    conn, pilot_id, loc, contacts = live_pilot
    handle_event(conn, {"type": "InboundMessage", "locationId": loc, "contactId": contacts[0], "body": "interested", "messageId": "r1"})
    created = conn.execute("select created_at from pilot_events where pilot_id = %s and type = 'needs_answer'", (pilot_id,)).fetchone()[0]
    assert check_pilot(conn, pilot_id, now=created + timedelta(minutes=10)) == []
    late = reply_deadline(created) + timedelta(minutes=1)
    assert [b.rule for b in check_pilot(conn, pilot_id, now=late)] == ["replies not answered within 1 working hour"]


@db
def test_invoice_charges_once_per_homeowner_credits_no_shows_and_is_idempotent(live_pilot):
    from delivery.invoices import build_invoice, invoice_markdown
    from delivery.webhooks import handle_event
    conn, pilot_id, loc, contacts = live_pilot

    def appointment(contact, status, n):
        return {"type": "AppointmentUpdate" if n else "AppointmentCreate", "locationId": loc,
                "appointment": {"id": f"a-{contact}", "contactId": contact, "appointmentStatus": status,
                                "startTime": "2026-11-10T10:00:00Z", "dateUpdated": str(n)}}

    for c in contacts[:3]:
        handle_event(conn, appointment(c, "confirmed", 0))
    handle_event(conn, {**appointment(contacts[0], "confirmed", 0), "appointment": {**appointment(contacts[0], "confirmed", 0)["appointment"], "id": "rebook", "dateUpdated": "9"}})
    handle_event(conn, appointment(contacts[1], "noshow", 1))
    week = datetime.now(UK).date().isocalendar()
    this_week = f"{week[0]}-W{week[1]:02d}"
    first = build_invoice(conn, pilot_id, this_week)
    assert first["charges"] == 3 and first["credits"] == 1 and first["total"] == 3 * 80 - 80
    again = build_invoice(conn, pilot_id, this_week)
    assert again["existing"] and again["invoice_id"] == first["invoice_id"]
    text = invoice_markdown(conn, first["invoice_id"])
    assert "No-show credit" in text and "£160.00" in text and "07700" not in text     # no phone numbers on invoices


def test_http_endpoint_rejects_unsigned_requests_and_unknown_paths():
    import threading
    import urllib.error
    import urllib.request
    from http.server import ThreadingHTTPServer

    from delivery.webhook_server import make_handler

    def no_db():
        raise AssertionError("must not touch the database for rejected requests")

    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(no_db))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        for path, headers, expected in (("/ghl/webhook", {}, 401),
                                        ("/ghl/webhook", {"x-wh-signature": "bm90LWEtc2ln"}, 401),
                                        ("/other", {}, 404)):
            request = urllib.request.Request(base + path, data=b'{"type":"InboundMessage"}', headers=headers, method="POST")
            with pytest.raises(urllib.error.HTTPError) as err:
                urllib.request.urlopen(request, timeout=5)
            assert err.value.code == expected
    finally:
        server.shutdown()
