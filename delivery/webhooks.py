"""GoHighLevel → our database: replies, opt-outs, bookings, outcomes
(WORKFLOW.md section 4, steps 7-8).

`handle_event(conn, event)` is the whole logic, called by the HTTP server in
delivery/webhook_server.py with an autocommit connection. Rules:
- Routed by locationId → pilot. Events for a known location but an unknown
  contact are stored (not dropped) so nothing is silently lost.
- Each event is processed once (pilot_events.source_event_id is unique).
- Homeowner states only move forward (delivery/states.py); opted_out beats
  everything; a person with several rows is updated on all of them.
- Only the fields we need are stored (ids, status, a trimmed message body),
  never GHL's full payload with names and addresses; for contacts that
  aren't our homeowners not even the message body.
- An opt-out (STOP, complaint, wrong person, DND) reaches every quote of
  that person (person_key), not only the row GHL knows.
- Opt-outs we detect (complaints, DND) are queued as 'dnd_pending' and pushed
  to GHL by delivery.ghl_push.push_opt_outs (webhook server + `check`).
"""

import base64
import hashlib
import hmac
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
# Replays are already blocked by the unique event id; the window only stops
# very old captured requests. Wide enough that GHL retries after an outage
# (which may keep the original timestamp) still get in.
REPLAY_WINDOW = timedelta(hours=24)
BODY_KEEP = 500

# Opt-out keyword only when it is the whole message ("STOP", "stop.", "Unsubscribe").
# Bare "cancel" is NOT here: a booked homeowner may be cancelling the survey,
# so it goes to a person.
_STOP = re.compile(r"^\s*(stop|stop all|stopall|unsubscribe|end|quit|opt[ -]?out|remove me)\s*[.!]*\s*$", re.I)
_COMPLAINT = re.compile(
    r"how did you get (my|this) (number|email|details)|where did you get (my|this)|\bico\b|information commissioner|"
    r"\breport(ing)? you\b|harass|leave me alone|stop (texting|messaging|contacting|emailing) me|"
    r"don'?t (text|message|contact) me|\bscam\b|\bgdpr\b", re.I)
_WRONG_PERSON = re.compile(r"wrong (number|person)|\bnot me\b|never (asked|enquired|had a quote)|don'?t know (you|any)", re.I)
# GHL appointment statuses → our homeowner states (others are logged only).
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


def verify_secret(given: str | None, expected: str | None) -> None:
    """For GHL *workflow* webhook actions (unsigned): a long random secret we
    put in the action's header. Constant-time compare."""
    if not expected or not given or not hmac.compare_digest(given.encode(), expected.encode()):
        raise BadSignature("missing or wrong shared secret")


def check_fresh(event: dict, now: datetime | None = None) -> None:
    stamp = event.get("timestamp")
    if not stamp:
        return
    try:
        sent = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
        if sent.tzinfo is None:
            sent = sent.replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise BadSignature("unreadable timestamp") from exc
    if abs((now or datetime.now(timezone.utc)) - sent) > REPLAY_WINDOW:
        raise BadSignature("timestamp outside the replay window")


_SHORT_STOP = re.compile(r"\b(stop|unsubscribe|opt[ -]?out|remove me)\b", re.I)
_SHORT_OPT_OUT_PHRASE = re.compile(r"\b(remove my (number|details)|no more (texts|messages))\b", re.I)
# "Stop by Tuesday?", "Yes stop by", "stop round", "Don't stop": not opt-outs.
_NOT_A_STOP = re.compile(r"\bstop\s+(by|round|over|off|in|past)\b|"
                         r"\b(don'?t|do not|dont|never|not|won'?t|can'?t)\s+stop\b", re.I)


def reply_signals(body: str) -> set[str]:
    """Every signal in a homeowner's reply: any of 'opt_out', 'complaint',
    'wrong_person' (empty = an ordinary reply). Complaint and wrong-person are
    always checked, so "STOP ICO" or "Stop. Wrong number" record both.
    Opt-out = the whole message is a stop word, or a short message (3 words or
    fewer) containing stop/unsubscribe ("stop please"), or a short "remove my
    number" / "no more texts"; but not "stop by"/"don't stop". Longer
    messages go to a person, so "End of the month works" isn't lost."""
    text = (body or "").strip()
    words = len(re.findall(r"[A-Za-z']+", text))
    found = set()
    if _STOP.match(text) or (
            not _NOT_A_STOP.search(text)
            and ((words <= 3 and _SHORT_STOP.search(text)) or (words <= 5 and _SHORT_OPT_OUT_PHRASE.search(text)))):
        found.add("opt_out")
    if _COMPLAINT.search(text):
        found.add("complaint")
    if _WRONG_PERSON.search(text):
        found.add("wrong_person")
    return found


def classify_homeowner_reply(body: str) -> str:
    """The main verdict: 'complaint' > 'wrong_person' > 'opt_out' > 'reply'
    (all three of the first opt the person out; see reply_signals)."""
    found = reply_signals(body)
    for verdict in ("complaint", "wrong_person", "opt_out"):
        if verdict in found:
            return verdict
    return "reply"


def event_id(event: dict) -> str:
    """GHL's webhookId when present; otherwise a hash of the meaningful parts,
    so GHL retries of the same event still collapse to one."""
    if event.get("webhookId"):
        return f"ghl:{event['webhookId']}"
    entity = event.get("appointment") or event
    basis = json.dumps([event.get("type"), entity.get("id") or event.get("messageId"),
                        entity.get("appointmentStatus") or event.get("status"),
                        entity.get("dateUpdated") or event.get("dateAdded"), (event.get("body") or "")[:200]],
                       sort_keys=True, default=str)
    return "ghl:" + hashlib.sha256(basis.encode()).hexdigest()[:40]


def minimal(event: dict) -> dict:
    """What we keep of a GHL event: no names, addresses or full payloads."""
    appointment = event.get("appointment") or {}
    keep = {
        "type": event.get("type"), "contactId": event.get("contactId") or appointment.get("contactId"),
        "messageId": event.get("messageId"), "messageType": event.get("messageType"), "direction": event.get("direction"),
        "status": event.get("status"), "userId": event.get("userId"), "source": event.get("source"),
        "body": (event.get("body") or "")[:BODY_KEEP] or None,
        "appointmentId": appointment.get("id"), "appointmentStatus": appointment.get("appointmentStatus"),
        "calendarId": appointment.get("calendarId"), "startTime": appointment.get("startTime"),
        "dnd": event.get("dnd"), "monetaryValue": event.get("monetaryValue"),
    }
    return {k: v for k, v in keep.items() if v not in (None, "")}


def _is_dnd(event: dict) -> bool:
    if event.get("dnd"):
        return True
    settings = event.get("dndSettings") or {}
    return any(str((settings.get(ch) or {}).get("status", "")).lower() == "active" for ch in ("SMS", "Email", "Call"))


def handle_event(conn, event: dict) -> str:
    """Processes one GHL webhook with an autocommit connection. Returns a short
    outcome for logs/tests."""
    kind = event.get("type")
    appointment = event.get("appointment") or {}
    contact_id = event.get("contactId") or appointment.get("contactId") or (event.get("id") if kind == "ContactDndUpdate" else None)
    if not kind or not event.get("locationId"):
        return "ignored: no type or location"
    run_id = uuid.uuid4()
    with conn.transaction():
        pilot = conn.execute("select id, ghl_calendar_id from pilots where ghl_location_id = %s", (event["locationId"],)).fetchone()
        if not pilot:
            return "ignored: unknown location"
        pilot_id, calendar_id = pilot
        rows = conn.execute(
            "select homeowner_key, state from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s "
            "order by homeowner_key for update",
            (pilot_id, contact_id)).fetchall() if contact_id else []
        kept = minimal(event)
        if not rows:
            kept.pop("body", None)          # not one of our homeowners: don't keep what they wrote
        stored = conn.execute(
            "insert into pilot_events (pilot_id, homeowner_key, run_id, type, source_event_id, payload) "
            "values (%s, %s, %s, %s, %s, %s) on conflict (source_event_id) do nothing returning id",
            (pilot_id, rows[0][0] if rows else None, run_id, f"ghl:{kind}" if rows else f"ghl:unmatched:{kind}",
             event_id(event), Jsonb(kept)),
        ).fetchone()
        if not stored:
            return "duplicate"
        if not rows:
            return "stored: contact not in this pilot"

        def signal(name, extra=None):
            for key, _ in rows:
                conn.execute("insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, %s, %s)",
                             (pilot_id, key, run_id, name, Jsonb(extra or {})))

        def move(new, why):
            targets = list(rows)
            if new == "opted_out":      # every quote of the same person, not only the row GHL knows
                targets += conn.execute(
                    """select homeowner_key, state from pilot_homeowners
                       where pilot_id = %s and homeowner_key <> all(%s) and person_key in (
                         select person_key from pilot_homeowners where pilot_id = %s and ghl_contact_id = %s
                           and person_key is not null)
                       order by homeowner_key for update""",
                    (pilot_id, [k for k, _ in rows], pilot_id, contact_id)).fetchall()
            moved = False
            for key, current in targets:
                if can_move_homeowner(current, new):
                    conn.execute("update pilot_homeowners set state = %s, updated_at = now() where pilot_id = %s and homeowner_key = %s",
                                 (new, pilot_id, key))
                    conn.execute("insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, 'homeowner_state', %s)",
                                 (pilot_id, key, run_id, Jsonb({"from": current, "to": new, "why": why})))
                    if new == "opted_out":
                        conn.execute("insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, 'dnd_pending', %s)",
                                     (pilot_id, key, run_id, Jsonb({"contact_id": contact_id})))
                    moved = True
            return moved

        body = event.get("body") or ""
        if kind == "InboundMessage" and (event.get("direction") or "inbound") == "inbound":
            found = reply_signals(body)
            booked = any(state == "booked" for _, state in rows)
            if found != {"opt_out"} or booked:
                # A person reads every reply except a plain STOP; a STOP from
                # someone with a booked survey may also be cancelling it.
                signal("needs_answer", {"message_id": event.get("messageId")})
            if "complaint" in found:
                signal("complaint", {"body": body[:BODY_KEEP]})
            if "wrong_person" in found:
                signal("wrong_person", {"body": body[:BODY_KEEP]})
            if found:                                                         # never message them again
                verdict = classify_homeowner_reply(body)
                move("opted_out", {"complaint": "complaint", "wrong_person": "wrong person"}.get(verdict, "replied with a stop word"))
                return {"complaint": "complaint", "wrong_person": "wrong_person"}.get(verdict, "opted out")
            move("replied", "inbound message")
            return "replied"

        if kind == "OutboundMessage":
            status = (event.get("status") or "").lower()
            if status in ("failed", "undelivered"):
                signal("delivery_failed", {"message_id": event.get("messageId"), "status": status})
                return "delivery failed"
            if event.get("userId"):                                              # typed by a person, not the workflow
                signal("answered", {"message_id": event.get("messageId")})
                return "answered"
            return "logged"

        if kind == "ContactDndUpdate" and _is_dnd(event):
            move("opted_out", "DND switched on in GHL")
            return "opted out"

        if kind in ("AppointmentCreate", "AppointmentUpdate"):
            if calendar_id and appointment.get("calendarId") and appointment["calendarId"] != calendar_id:
                return "appointment on another calendar: logged only"
            status = (appointment.get("appointmentStatus") or "").lower()
            new = _APPOINTMENT_STATE.get(status)
            if not new:
                return f"appointment status '{status}' logged only"
            seen = conn.execute(
                "select 1 from pilot_events where pilot_id = %s and type = 'survey_booked' and payload->>'appointment_id' = %s",
                (pilot_id, appointment.get("id"))).fetchone()
            if new == "booked" and not seen:
                signal("survey_booked", {"appointment_id": appointment.get("id"), "start": appointment.get("startTime")})
            if new == "no_show":
                signal("survey_not_held", {"appointment_id": appointment.get("id"), "reason": status})
            moved = move(new, f"appointment {status}")
            return new if moved else f"{new} (state unchanged)"

        if kind in ("OpportunityStatusUpdate", "OpportunityStageUpdate"):
            status = (event.get("status") or "").lower()
            new = {"won": "won", "lost": "lost", "abandoned": "lost"}.get(status)
            if new:
                signal("outcome", {"status": status, "value": event.get("monetaryValue")})
                move(new, f"opportunity {status}")
                return new
            return "opportunity update logged"

        return "logged"
