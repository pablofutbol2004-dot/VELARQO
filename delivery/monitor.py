"""Stop-condition check (WORKFLOW.md section 5). Run every 15 minutes while a
pilot is sending. Any breach moves the pilot to 'paused' (no new waves; the
wave code also stops mid-way) and records why. Resuming needs a new 'resume'
approval, given after the pause.

Thresholds are the ones proposed in WORKFLOW.md. Pablo confirms them before
the first pilot; they must not be loosened mid-pilot.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

UK = ZoneInfo("Europe/London")
MIN_CONTACTED_FOR_RATES = 20          # a canary wave; below this one person is too many percent
OPT_OUT_MAX = 0.08
DELIVERY_FAIL_MAX = 0.10
WRONG_PERSON_MAX = 0.05
COMPLAINTS_MAX = 1                    # 2 or more pauses
MANUAL_MINUTES_PER_100_MAX = 60
MIN_CONTACTED_FOR_MINUTES = 50
REPLY_SLA = timedelta(hours=1)        # working hours, Mon-Fri 08:00-18:00 UK
WORK_START, WORK_END = time(8), time(18)
CONTACTED_STATES = ("enrolled", "replied", "booked", "no_show", "attended", "requoted", "won", "lost", "no_response")


@dataclass
class Breach:
    rule: str
    detail: str


def reply_deadline(received: datetime) -> datetime:
    """1 working hour after the reply; replies outside hours are due by
    09:00 the next working day."""
    local = received.astimezone(UK)
    day = local.date()
    if local.weekday() < 5 and WORK_START <= local.time() < WORK_END:
        return local + REPLY_SLA
    if local.weekday() < 5 and local.time() < WORK_START:
        return datetime.combine(day, time(9), tzinfo=UK)
    day += timedelta(days=1)
    while day.weekday() >= 5:
        day += timedelta(days=1)
    return datetime.combine(day, time(9), tzinfo=UK)


def wave_breaches(counts: dict) -> list[Breach]:
    """Pure rule check over one wave's counts (easy to test)."""
    breaches = []
    contacted = counts.get("contacted", 0)
    if counts.get("regulator_mentions", 0) > 0:
        breaches.append(Breach("complaint mentions the ICO/regulator", f"{counts['regulator_mentions']}"))
    if counts.get("complaints", 0) > COMPLAINTS_MAX:
        breaches.append(Breach("complaints", f"{counts['complaints']} in this wave"))
    if counts.get("installer_missed", 0) > 0:
        breaches.append(Breach("installer missed a booked survey", f"{counts['installer_missed']}"))
    if counts.get("unanswered_replies", 0) > 0:
        breaches.append(Breach("replies not answered within 1 working hour", f"{counts['unanswered_replies']}"))
    if contacted >= MIN_CONTACTED_FOR_RATES:
        for key, limit, label in (("opted_out", OPT_OUT_MAX, "opt-out rate"),
                                  ("delivery_failed", DELIVERY_FAIL_MAX, "text delivery failures"),
                                  ("wrong_person", WRONG_PERSON_MAX, "wrong-person replies")):
            rate = counts.get(key, 0) / contacted
            if rate > limit:
                breaches.append(Breach(label, f"{counts.get(key, 0)}/{contacted} = {rate:.0%} (limit {limit:.0%})"))
    if contacted >= MIN_CONTACTED_FOR_MINUTES:
        per_100 = counts.get("manual_minutes", 0) / contacted * 100
        if per_100 > MANUAL_MINUTES_PER_100_MAX:
            breaches.append(Breach("manual time", f"{per_100:.0f} min per 100 contacted (limit {MANUAL_MINUTES_PER_100_MAX})"))
    return breaches


def wave_counts(conn, pilot_id: str, wave_id: str, now: datetime) -> dict:
    keys_sql = "select homeowner_key from pilot_homeowners where pilot_id = %(p)s and wave_id = %(w)s"
    one = lambda sql: conn.execute(sql, {"p": pilot_id, "w": wave_id, "states": list(CONTACTED_STATES)}).fetchone()[0]  # noqa: E731
    counts = {
        "contacted": one("select count(*) from pilot_homeowners where pilot_id = %(p)s and wave_id = %(w)s "
                         "and (state = any(%(states)s) or (state = 'opted_out' and ghl_contact_id is not null))"),
        "opted_out": one("select count(*) from pilot_homeowners where pilot_id = %(p)s and wave_id = %(w)s "
                         "and state = 'opted_out' and ghl_contact_id is not null"),
    }
    for name in ("complaint", "delivery_failed", "wrong_person", "installer_missed"):
        counts[{"complaint": "complaints"}.get(name, name)] = one(
            f"select count(distinct homeowner_key) from pilot_events where pilot_id = %(p)s and type = '{name}' "
            f"and homeowner_key in ({keys_sql})")
    counts["regulator_mentions"] = one(
        f"select count(*) from pilot_events where pilot_id = %(p)s and type = 'complaint' "
        f"and payload->>'body' ~* '(\\mico\\M|information commissioner|regulator)' and homeowner_key in ({keys_sql})")
    counts["manual_minutes"] = conn.execute(
        "select coalesce(sum((payload->>'minutes')::numeric), 0) from pilot_events where pilot_id = %s and type = 'manual_minutes'",
        (pilot_id,)).fetchone()[0]
    pending = conn.execute(
        f"""select e.created_at from pilot_events e
            where e.pilot_id = %(p)s and e.type = 'needs_answer' and e.homeowner_key in ({keys_sql})
              and not exists (select 1 from pilot_events o where o.pilot_id = e.pilot_id and o.homeowner_key = e.homeowner_key
                              and o.type in ('ghl:OutboundMessage', 'answered') and o.created_at > e.created_at)""",
        {"p": pilot_id, "w": wave_id}).fetchall()
    counts["unanswered_replies"] = sum(1 for (received,) in pending if now > reply_deadline(received))
    return counts


def check_pilot(conn, pilot_id: str, now: datetime | None = None) -> list[Breach]:
    """Checks every wave of a sending pilot; pauses it on any breach."""
    from delivery.pilot import advance_pilot

    now = now or datetime.now(UK)
    state = conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0]
    if state not in ("canary_running", "live"):
        return []
    breaches = []
    for (wave_id,) in conn.execute(
        "select distinct wave_id from pilot_homeowners where pilot_id = %s and wave_id is not null", (pilot_id,)
    ).fetchall():
        breaches += [Breach(b.rule, f"{wave_id}: {b.detail}") for b in wave_breaches(wave_counts(conn, pilot_id, wave_id, now))]
    if breaches:
        run_id = uuid.uuid4()
        with conn.transaction():
            conn.execute(
                "insert into pilot_events (pilot_id, run_id, type, payload) values (%s, %s, 'stop_condition', %s)",
                (pilot_id, run_id, Jsonb({"breaches": [b.__dict__ for b in breaches]})),
            )
            advance_pilot(conn, pilot_id, "paused", run_id)
    return breaches
