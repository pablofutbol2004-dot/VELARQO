"""Reply alerts and the 20:00 summary.

What pings (push + email, within the 15-minute tick):
- positive replies (interested, "how much", "send info", "call me", a bare yes)
- anything a human must read: GDPR questions, wrong person, "we already
  follow up", maybe later, mixed signals, unmatched replies
- complaints (sending is already paused by the engine; the alert says so)

What doesn't ping: "not interested" and opt-outs (already suppressed, no
rush; they are in the `replies` list and the 20:00 summary) and automatic
notices (bounces, out-of-office).

Every alert is recorded in alert_log first, so the next tick never sends
it again; a failed send is retried on the next two ticks, then left for
the `replies` list.
"""

import json
from datetime import datetime, timezone

from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from outreach.alerts import playbook
from outreach.alerts.channels import Alert, Delivery, Notifier
from outreach.reply_classifier.classify import URGENT_CATEGORIES, label, strip_quoted
from outreach.send_engine import experiments, guards

MAX_ATTEMPTS = 3
SUMMARY_HOUR_UK = 20
PRICING_EXPERIMENT = "pricing_p1"
REPLY_EXCERPT = 700


def _now() -> datetime:
    return datetime.now(timezone.utc)


# --- Which replies ------------------------------------------------------

def pending(conn, limit: int = 20) -> list[dict]:
    """Urgent replies not yet alerted (or alerted and failed fewer than MAX_ATTEMPTS times)."""
    with conn.cursor(row_factory=dict_row) as cur:
        return cur.execute(
            """
            select r.id, r.received_at, r.from_email, r.subject, r.body, r.category, r.human_category, r.classification,
                   r.needs_human, r.message_id, r.company_id, r.mailbox,
                   c.display_name, c.legal_name, c.city, c.postcode, c.phone, c.website, c.company_category
            from replies r
            left join companies c on c.id = r.company_id
            left join alert_log a on a.kind = 'reply' and a.ref = r.id::text
            where r.needs_human and r.handled_at is null
              and r.received_at > now() - interval '7 days'
              and (coalesce(r.human_category, r.category) = any(%s) or r.company_id is null)
              and (a.id is null or (a.sent_at is null and a.attempts < %s))
            order by r.received_at
            limit %s
            """,
            (list(URGENT_CATEGORIES), MAX_ATTEMPTS, limit),
        ).fetchall()


# --- What the alert says ------------------------------------------------

def _history(conn, company_id) -> dict:
    with conn.cursor(row_factory=dict_row) as cur:
        return {
            "messages": cur.execute(
                """
                select m.sequence_step, m.status, m.sent_at, m.subject, m.mailbox,
                       cp.settings->'experiment'->>'name' experiment,
                       cp.settings->'experiment'->'arms'->m.variant_index->>'key' arm
                from messages m join campaigns cp on cp.id = m.campaign_id
                where m.company_id = %s order by m.sequence_step
                """, (company_id,)).fetchall(),
            "replies": cur.execute(
                "select received_at, coalesce(human_category, category) category, body from replies "
                "where company_id = %s order by received_at", (company_id,)).fetchall(),
            "events": cur.execute(
                "select occurred_at, type, payload from events where company_id = %s "
                "and type in ('call_booked', 'call_held', 'sample_received', 'pilot_signed', 'lost') order by occurred_at",
                (company_id,)).fetchall(),
        }


def _price_arm(company_id) -> dict | None:
    try:
        exp = experiments.load(PRICING_EXPERIMENT)
        arm = experiments.assigned_arm(exp, str(company_id))
        return {"experiment": exp["name"], "key": arm["key"], "price_gbp": arm.get("price_gbp")}
    except Exception:  # noqa: BLE001 - a missing pricing file must not stop the alert
        return None


def _first_name(reply_body: str, from_email: str) -> str:
    """Best guess at who signed: the last short word-only line, else the mailbox's local part."""
    lines = [ln.strip() for ln in strip_quoted(reply_body).splitlines() if ln.strip()]
    for ln in reversed(lines[-3:]):
        words = ln.replace(",", "").split()
        if 1 <= len(words) <= 2 and all(w.isalpha() for w in words) and words[0].lower() not in ("thanks", "cheers", "regards", "ta", "yes", "no", "ok"):
            return words[0].capitalize()
    local = (from_email or "").split("@")[0]
    return "" if local.lower() in ("info", "sales", "enquiries", "office", "admin", "hello", "contact", "accounts", "mail") else local.split(".")[0].capitalize()


def build(conn, reply: dict, history: dict | None = None) -> Alert:
    """The alert for one reply: what they said, who they are, what was sent,
    the price arm to quote, and the playbook reply to send. `history` is
    looked up unless given (the sample alert passes a made-up one)."""
    category = reply.get("human_category") or reply.get("category") or "unknown"
    classification = reply.get("classification") or {}
    if isinstance(classification, str):
        classification = json.loads(classification)
    intent = classification.get("intent")
    matched = reply.get("company_id") is not None
    text = strip_quoted(reply.get("body") or "").strip() or "(empty reply)"
    company = reply.get("display_name") or "(unmatched: not tied to an email we sent)"
    received = reply["received_at"].astimezone(guards.UK) if reply.get("received_at") else None

    head = label(category, intent)
    title = f"[Velarqo] {head}: {company}"
    lines = [
        f"{head}",
        f"From: {reply.get('from_email')}  {received:%a %d %b %H:%M} UK" if received else f"From: {reply.get('from_email')}",
        f"Subject: {reply.get('subject') or ''}",
        "",
        text[:REPLY_EXCERPT] + ("..." if len(text) > REPLY_EXCERPT else ""),
        "",
    ]

    if history is None:
        history = _history(conn, reply["company_id"]) if matched else {"messages": [], "replies": [], "events": []}
    cold_arm = next((m["arm"] for m in history["messages"] if m.get("arm")), None)
    if matched:
        lines.append(f"COMPANY: {company} ({reply.get('legal_name') or ''}; {reply.get('company_category') or '?'})")
        lines.append(f"  {reply.get('city') or ''} {reply.get('postcode') or ''}  phone {reply.get('phone') or '-'}  web {reply.get('website') or '-'}")
        lines.append("CALL SHEET:")
        for m in history["messages"]:
            when = m["sent_at"].astimezone(guards.UK).strftime("%d %b") if m.get("sent_at") else ""
            lines.append(f"  step {m['sequence_step']} {m['status']} {when}: {m['subject']}  [{m.get('experiment') or '?'} / {m.get('arm') or '?'}]")
        for r in history["replies"]:
            if r["body"] != reply.get("body"):
                lines.append(f"  earlier reply [{r['category']}] {r['received_at'].astimezone(guards.UK):%d %b}: {strip_quoted(r['body'])[:160]}")
        for e in history["events"]:
            lines.append(f"  {e['occurred_at'].astimezone(guards.UK):%d %b} {e['type']} {e.get('payload') or ''}")
        price = _price_arm(reply["company_id"])
        if price:
            lines.append(f"  PRICE TO QUOTE ({price['experiment']} arm {price['key']}): GBP {price['price_gbp']} per qualified booked survey. "
                         "Ask the docs/PRICING.md questions first.")
        lines.append(f"  Full sheet: python -m pipelines.outbound call-sheet {reply.get('from_email')}")
    lines.append("")
    lines.append("SUGGESTED REPLY (playbook, edit before sending):")
    lines.append(playbook.suggestion(
        category, intent, name=_first_name(reply.get("body") or "", reply.get("from_email") or ""),
        company=reply.get("display_name") or "", email=reply.get("from_email") or "", reply_id=str(reply["id"]),
        matched=matched, arm=cold_arm,
    ))
    lines.append("")
    lines.append(f"When done: python -m pipelines.outbound handled {reply['id']}")

    priority = "urgent" if category in ("positive", "complaint") else "high"
    tags = {"positive": ["tada"], "complaint": ["rotating_light"], "unknown": ["eyes"]}.get(category, ["email"])
    return Alert(title=title, body="\n".join(lines), priority=priority, tags=tags)


# --- Sending and recording ----------------------------------------------

def _claim(conn, kind: str, ref: str) -> int:
    """Record the attempt before sending; returns the attempt number."""
    with conn.transaction(), conn.cursor() as cur:
        return cur.execute(
            "insert into alert_log (kind, ref, attempts) values (%s, %s, 1) "
            "on conflict (kind, ref) do update set attempts = alert_log.attempts + 1 returning attempts",
            (kind, ref),
        ).fetchone()[0]


def _record(conn, kind: str, ref: str, deliveries: list[Delivery]) -> bool:
    ok = any(d.ok for d in deliveries)
    with conn.transaction(), conn.cursor() as cur:
        cur.execute(
            "update alert_log set sent_at = case when %s then now() else sent_at end, channels = %s, error = %s "
            "where kind = %s and ref = %s",
            (ok, Jsonb([d.channel for d in deliveries if d.ok]),
             "; ".join(f"{d.channel}: {d.detail}" for d in deliveries if not d.ok) or None, kind, ref),
        )
    return ok


def send_pending(conn, notifier: Notifier) -> dict:
    """Alert every urgent reply not yet alerted. -> {"alerted": n, "failed": n, "no_channel": bool}"""
    summary = {"alerted": 0, "failed": 0, "no_channel": not notifier.channels}
    if summary["no_channel"]:
        return summary
    for reply in pending(conn):
        ref = str(reply["id"])
        attempt = _claim(conn, "reply", ref)
        if attempt > MAX_ATTEMPTS:
            continue
        alert = build(conn, reply)
        deliveries = notifier.send(alert)
        if _record(conn, "reply", ref, deliveries):
            summary["alerted"] += 1
        else:
            summary["failed"] += 1
    return summary


def summary_due(now: datetime | None = None) -> bool:
    return (now or _now()).astimezone(guards.UK).hour >= SUMMARY_HOUR_UK


def send_daily_summary(conn, notifier: Notifier, board: dict | None = None, force: bool = False,
                       now: datetime | None = None) -> str:
    """The scoreboard to the alert channels, once per UK day (after 20:00
    unless forced). Returns a one-line result for the tick report."""
    from reporting import scoreboard

    now = now or _now()
    if not force and not summary_due(now):
        return "not yet (before 20:00 UK)"
    if not notifier.channels:
        return "no alert channel configured"
    ref = guards.uk_day_start(now).date().isoformat()
    with conn.cursor() as cur:
        already = cur.execute("select sent_at from alert_log where kind = 'daily' and ref = %s", (ref,)).fetchone()
    if already and already[0] and not force:
        return f"already sent today at {already[0].astimezone(guards.UK):%H:%M}"
    if not force and _claim(conn, "daily", ref) > MAX_ATTEMPTS:
        return "gave up after repeated failures"
    if force:
        _claim(conn, "daily", ref)
    board = board or scoreboard.compute(conn, now)
    text = scoreboard.format_text(board, short=True)
    alert = Alert(title=f"[Velarqo] scoreboard {board['day']:%a %d %b}", body=text, priority="normal", tags=["bar_chart"])
    deliveries = notifier.send(alert)
    ok = _record(conn, "daily", ref, deliveries)
    return ("sent via " + ", ".join(d.channel for d in deliveries if d.ok)) if ok else \
        "FAILED: " + "; ".join(f"{d.channel}: {d.detail}" for d in deliveries)


def test_alert(notifier: Notifier) -> list[Delivery]:
    """A sample positive alert through every configured channel (no database)."""
    sample = {
        "id": "test-0000", "received_at": _now(), "from_email": "dave@examplewindows.co.uk",
        "subject": "Re: old quotes", "body": "Yeah go on then, give me a bell on 07700 900123\n\nDave",
        "category": "positive", "human_category": None, "classification": {"intent": "call_me"},
        "company_id": "00000000-0000-0000-0000-000000000000", "display_name": "Example Windows Ltd (TEST)",
        "legal_name": "EXAMPLE WINDOWS LIMITED", "company_category": "Private Limited Company",
        "city": "Leeds", "postcode": "LS1 1AA", "phone": "0113 496 0000", "website": "https://examplewindows.co.uk",
    }
    history = {
        "messages": [{"sequence_step": 1, "status": "sent", "sent_at": _now(), "subject": "old quotes",
                      "mailbox": "pablo@getvelarqo.com", "experiment": "cold_offer_v1", "arm": "A_pay_per_booked_survey"}],
        "replies": [], "events": [],
    }
    alert = build(None, sample, history=history)
    alert.title = alert.title.replace("[Velarqo] ", "[Velarqo] TEST alert: ", 1)
    alert.body = "This is a test of the Velarqo alert channel.\n\n" + alert.body
    return notifier.send(alert)


# --- Email channel wiring -----------------------------------------------

def email_sender(provider_for=None, mailboxes: list[dict] | None = None):
    """send_email(to, subject, body) through the alert mailbox
    (VELARQO_ALERT_MAILBOX, else the first enabled mailbox), built lazily so
    a token is only refreshed when there is something to send. Returns None
    when no mailbox is configured (then only push channels are used)."""
    from outreach.alerts.channels import settings

    if provider_for is None or mailboxes is None:
        try:
            from pipelines.outbound.__main__ import _mailboxes, _provider
        except Exception:  # noqa: BLE001
            return None
        try:
            mailboxes = mailboxes if mailboxes is not None else _mailboxes()
        except Exception:  # noqa: BLE001 - no mailboxes.json yet
            return None
        provider_for = provider_for or _provider
    wanted = (settings().get("mailbox") or "").lower()
    mailbox = next((m for m in mailboxes if m["email"].lower() == wanted), None) or (mailboxes[0] if mailboxes else None)
    if mailbox is None:
        return None

    def send_email(to: str, subject: str, body: str) -> dict:
        return provider_for(mailbox).send_email(to=to, subject=subject, body=body)

    return send_email
