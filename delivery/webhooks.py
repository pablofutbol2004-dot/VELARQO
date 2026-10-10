"""GoHighLevel → our database: replies, opt-outs, bookings, outcomes
(WORKFLOW.md section 4, steps 7-8).

`handle_event(conn, event)` is the whole logic and is called by the small
HTTP server in delivery/webhook_server.py. Rules:
- Routed by locationId → pilot; contacts we didn't send are ignored.
- Each event is processed once: its id goes into pilot_events.source_event_id
  (unique). A retry from GHL finds it and does nothing.
- Homeowner states only move forward (delivery/states.py), so events arriving
  out of order can't undo progress. opted_out beats everything.
- Signals the pause check needs (complaints, wrong person, failed delivery)
  are stored as events, not guessed later.
"""

import base64
import hashlib
import json
import re
import uuid
from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb

from delivery.states import can_move_homeowner

# GHL's published webhook key (docs/ghl/api/official-docs/docs/oauth/WebhookAuthentication.md).
# It can rotate: GHL announces it by email; update here when it does.
GHL_PUBLIC_KEY = b"""-----BEGIN PUBLIC KEY-----
MIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAokvo/r9tVgcfZ5DysOSC
Frm602qYV0MaAiNnX9O8KxMbiyRKWeL9JpCpVpt4XHIcBOK4u3cLSqJGOLaPuXw6
dO0t6Q/ZVdAV5Phz+ZtzPL16iCGeK9po6D6JHBpbi989mmzMryUnQJezlYJ3DVfB
csedpinheNnyYeFXolrJvcsjDtfAeRx5ByHQmTnSdFUzuAnC9/GepgLT9SM4nCpv
uxmZMxrJt5Rw+VUaQ9B8JSvbMPpez4peKaJPZHBbU3OdeCVx5klVXXZQGNHOs8gF
3kvoV5rTnXV0IknLBXlcKKAQLZcY/Q9rG6Ifi9c+5vqlvHPCUJFT5XUGG5RKgOKU
J062fRtN+rLYZUV+BjafxQauvC8wSWeYja63VSUruvmNj8xkx2zE/Juc+yjLjTXp
IocmaiFeAO6fUtNjDeFVkhf5LNb59vECyrHD2SQIrhgXpO4Q3dVNA5rw576PwTzN
h/AMfHKIjE4xQA1SZuYJmNnmVZLIZBlQAF9Ntd03rfadZ+yDiOXCCs9FkHibELhC
HULgCsnuDJHcrGNd5/Ddm5hxGQ0ASitgHeMZ0kcIOwKDOzOU53lDza6/Y09T7sYJ
PQe7z0cvj7aE4B+Ax1ZoZGPzpJlZtGXCsu9aTEGEnKzmsFqwcSsnw3JB31IGKAyk
T1hhTiaCeIY/OwwwNUY2yvcCAwEAAQ==
-----END PUBLIC KEY-----"""
REPLAY_WINDOW = timedelta(minutes=5)

_STOP = re.compile(r"^\s*(stop|stopall|unsubscribe|end|quit|cancel|opt ?out)\b", re.I)
_COMPLAINT = re.compile(
    r"how did you get (my|this) (number|email)|where did you get|\bico\b|information commissioner|"
    r"\breport(ing)? you\b|harass|leave me alone|stop (texting|messaging|contacting) me|\bscam\b|gdpr", re.I)
_WRONG_PERSON = re.compile(r"wrong (number|person)|not me\b|don'?t know (you|who)|never (asked|enquired|had a quote)|who is this\b", re.I)
# GHL appointment statuses → our homeowner states (unknown statuses are logged only).
_APPOINTMENT_STATE = {"new": "booked", "confirmed": "booked", "booked": "booked",
                      "showed": "attended", "noshow": "no_show", "cancelled": "no_show"}


class BadSignature(Exception):
    pass


def verify_signature(raw_body: bytes, signature_b64: str | None, public_key_pem: bytes = GHL_PUBLIC_KEY) -> None:
    """RSA-SHA256 over the raw body, per GHL's guide. Raises BadSignature."""
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding

    if not signature_b64:
        raise BadSignature("missing x-wh-signature")
    key = serialization.load_pem_public_key(public_key_pem)
    try:
        key.verify(base64.b64decode(signature_b64), raw_body, padding.PKCS1v15(), hashes.SHA256())
    except (InvalidSignature, ValueError) as exc:
        raise BadSignature("signature does not match") from exc


def check_fresh(event: dict, now: datetime | None = None) -> None:
    stamp = event.get("timestamp")
    if not stamp:
        return
    sent = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    if abs((now or datetime.now(timezone.utc)) - sent) > REPLAY_WINDOW:
        raise BadSignature("timestamp outside the 5-minute window (possible replay)")


def classify_homeowner_reply(body: str) -> str:
    """'opt_out' | 'complaint' | 'wrong_person' | 'reply'. Opt-out wins over
    everything (an angry STOP is still a STOP); a complaint is flagged too."""
    text = (body or "").strip()
    if _STOP.match(text):
        return "opt_out"
    if _COMPLAINT.search(text):
        return "complaint"
    if _WRONG_PERSON.search(text):
        return "wrong_person"
    return "reply"


def event_id(event: dict) -> str:
    """GHL's webhookId when present; otherwise a hash of the meaningful parts,
    so GHL retries of the same event still collapse to one."""
    if event.get("webhookId"):
        return f"ghl:{event['webhookId']}"
    entity = event.get("appointment") or event
    basis = json.dumps([event.get("type"), entity.get("id") or event.get("messageId"),
                        entity.get("appointmentStatus") or event.get("status"),
                        entity.get("dateUpdated") or event.get("dateAdded")], sort_keys=True)
    return "ghl:" + hashlib.sha256(basis.encode()).hexdigest()[:40]


def _homeowner(conn, location_id: str, contact_id: str):
    return conn.execute(
        """select h.pilot_id, h.homeowner_key, h.state from pilot_homeowners h
           join pilots p on p.id = h.pilot_id
           where p.ghl_location_id = %s and h.ghl_contact_id = %s for update of h""",
        (location_id, contact_id),
    ).fetchone()


def _move(conn, pilot_id, key, current, new, run_id, why) -> bool:
    if not can_move_homeowner(current, new):
        return False
    conn.execute("update pilot_homeowners set state = %s, updated_at = now() where pilot_id = %s and homeowner_key = %s",
                 (new, pilot_id, key))
    conn.execute(
        "insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, 'homeowner_state', %s)",
        (pilot_id, key, run_id, Jsonb({"from": current, "to": new, "why": why})),
    )
    return True


def handle_event(conn, event: dict) -> str:
    """Processes one GHL webhook. Returns a short outcome for logs/tests."""
    kind = event.get("type")
    contact_id = event.get("contactId") or (event.get("appointment") or {}).get("contactId") or (
        event.get("id") if kind == "ContactDndUpdate" else None)
    if not kind or not contact_id or not event.get("locationId"):
        return "ignored: not a contact event"
    run_id = uuid.uuid4()
    with conn.transaction():
        found = _homeowner(conn, event["locationId"], contact_id)
        if not found:
            return "ignored: not one of our homeowners"
        pilot_id, key, state = found
        source_id = event_id(event)
        inserted = conn.execute(
            "insert into pilot_events (pilot_id, homeowner_key, run_id, type, source_event_id, payload) "
            "values (%s, %s, %s, %s, %s, %s) on conflict (source_event_id) do nothing returning id",
            (pilot_id, key, run_id, f"ghl:{kind}", source_id, Jsonb(event)),
        ).fetchone()
        if not inserted:
            return "duplicate"

        def signal(name, extra=None):
            conn.execute(
                "insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, %s, %s)",
                (pilot_id, key, run_id, name, Jsonb(extra or {})),
            )

        if kind == "InboundMessage" and (event.get("direction") or "inbound") == "inbound":
            verdict = classify_homeowner_reply(event.get("body") or "")
            if verdict == "opt_out":
                _move(conn, pilot_id, key, state, "opted_out", run_id, "replied STOP")
                if _COMPLAINT.search(event.get("body") or ""):
                    signal("complaint", {"body": (event.get("body") or "")[:500]})
                return "opted out"
            if verdict in ("complaint", "wrong_person"):
                signal(verdict, {"body": (event.get("body") or "")[:500]})
                if verdict == "complaint":
                    _move(conn, pilot_id, key, state, "opted_out", run_id, "complaint")  # never message them again
                return verdict
            _move(conn, pilot_id, key, state, "replied", run_id, "inbound message")
            signal("needs_answer", {"message_id": event.get("messageId")})
            return "replied"

        if kind == "OutboundMessage" and (event.get("status") or "").lower() in ("failed", "undelivered"):
            signal("delivery_failed", {"message_id": event.get("messageId"), "status": event.get("status")})
            return "delivery failed"

        if kind == "ContactDndUpdate" and event.get("dnd"):
            _move(conn, pilot_id, key, state, "opted_out", run_id, "DND switched on in GHL")
            return "opted out"

        if kind in ("AppointmentCreate", "AppointmentUpdate"):
            appointment = event.get("appointment") or {}
            status = (appointment.get("appointmentStatus") or "").lower()
            new = _APPOINTMENT_STATE.get(status)
            if not new:
                return f"appointment status '{status}' logged only"
            if new == "booked":
                # A booked survey counts once per appointment id (billing key).
                signal("survey_booked", {"appointment_id": appointment.get("id"), "start": appointment.get("startTime")})
            if new == "no_show":
                signal("survey_not_held", {"appointment_id": appointment.get("id"), "reason": status})
            moved = _move(conn, pilot_id, key, state, new, run_id, f"appointment {status}")
            return f"{new}" if moved else f"{new} (state unchanged: {state})"

        if kind in ("OpportunityStatusUpdate", "OpportunityStageUpdate"):
            status = (event.get("status") or "").lower()
            new = {"won": "won", "lost": "lost", "abandoned": "lost"}.get(status)
            if new:
                signal("outcome", {"status": status, "value": event.get("monetaryValue")})
                _move(conn, pilot_id, key, state, new, run_id, f"opportunity {status}")
                return new
            return "opportunity update logged"

        return "logged"
