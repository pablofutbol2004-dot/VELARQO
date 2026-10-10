"""Stop-condition check (WORKFLOW.md section 5). Run every 15 minutes while a
pilot is running. Any breach moves a sending pilot to 'paused' (no new waves;
the wave code also stops mid-way) and records why. Resuming needs a new
'resume' approval given after the pause; after a resume only events newer
than the resume count, so an old, reviewed breach doesn't re-pause forever.

Thresholds are the ones proposed in WORKFLOW.md. Pablo confirms them before
the first pilot; they must not be loosened mid-pilot.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from psycopg.types.json import Jsonb

UK = ZoneInfo("Europe/London")
MIN_CONTACTED_FOR_RATES = 20          # below this one person is too many percent
OPT_OUT_MAX = 0.08
DELIVERY_FAIL_MAX = 0.10
WRONG_PERSON_MAX = 0.05
COMPLAINTS_MAX = 1                    # 2 or more pauses
MANUAL_MINUTES_PER_100_MAX = 60
MIN_CONTACTED_FOR_MINUTES = 50
REPLY_SLA = timedelta(hours=1)        # working hours, Mon-Fri 08:00-18:00 UK
WORK_START, WORK_END = time(8), time(18)
CONTACTED_STATES = ["enrolled", "replied", "booked", "no_show", "attended", "requoted", "won", "lost", "no_response"]
EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


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


def breaches_for(counts: dict, scope: str) -> list[Breach]:
    """Pure rule check over one scope's counts (a wave, or the whole pilot)."""
    out = []
    contacted = counts.get("contacted", 0)
    if counts.get("regulator_mentions", 0) > 0:
        out.append(Breach("complaint mentions the ICO/regulator", f"{scope}: {counts['regulator_mentions']}"))
    if counts.get("complaints", 0) > COMPLAINTS_MAX:
        out.append(Breach("complaints", f"{scope}: {counts['complaints']}"))
    if counts.get("installer_missed", 0) > 0:
        out.append(Breach("installer missed a booked survey", f"{scope}: {counts['installer_missed']}"))
    if counts.get("late_replies", 0) > 0:
        out.append(Breach("replies not answered within 1 working hour", f"{scope}: {counts['late_replies']}"))
    if contacted >= MIN_CONTACTED_FOR_RATES:
        for key, limit, label in (("opted_out", OPT_OUT_MAX, "opt-out rate"),
                                  ("delivery_failed", DELIVERY_FAIL_MAX, "text delivery failures"),
                                  ("wrong_person", WRONG_PERSON_MAX, "wrong-person replies")):
            rate = counts.get(key, 0) / contacted
            if rate > limit:
                out.append(Breach(label, f"{scope}: {counts.get(key, 0)}/{contacted} = {rate:.0%} (limit {limit:.0%})"))
    if counts.get("manual_minutes") is not None and contacted >= MIN_CONTACTED_FOR_MINUTES:
        per_100 = float(counts["manual_minutes"]) / contacted * 100
        if per_100 > MANUAL_MINUTES_PER_100_MAX:
            out.append(Breach("manual time", f"{scope}: {per_100:.0f} min per 100 contacted (limit {MANUAL_MINUTES_PER_100_MAX})"))
    return out


def wave_breaches(counts: dict) -> list[Breach]:
    """One wave's counts (kept for callers/tests)."""
    return breaches_for(counts, "wave")


def counts_for(conn, pilot_id: str, wave_id: str | None, since: datetime, now: datetime) -> dict:
    """Counts for one wave (or the whole pilot if wave_id is None), only from
    events after `since` (the last resume). The denominator is everyone ever
    contacted in that scope."""
    scope = "h.pilot_id = %(p)s" + (" and h.wave_id = %(w)s" if wave_id else " and h.wave_id is not null")
    params = {"p": pilot_id, "w": wave_id, "since": since, "states": CONTACTED_STATES}

    def one(sql):
        return conn.execute(sql, params).fetchone()[0]

    counts = {"contacted": one(f"select count(*) from pilot_homeowners h where {scope} "
                               "and (h.state = any(%(states)s) or (h.state = 'opted_out' and h.ghl_contact_id is not null))")}
    in_scope = f"e.homeowner_key in (select h.homeowner_key from pilot_homeowners h where {scope})"
    counts["opted_out"] = one(
        f"select count(distinct e.homeowner_key) from pilot_events e where e.pilot_id = %(p)s and {in_scope} "
        "and e.type = 'homeowner_state' and e.payload->>'to' = 'opted_out' and e.created_at > %(since)s")
    for name, key in (("complaint", "complaints"), ("delivery_failed", "delivery_failed"),
                      ("wrong_person", "wrong_person"), ("installer_missed", "installer_missed")):
        counts[key] = one(f"select count(distinct e.homeowner_key) from pilot_events e where e.pilot_id = %(p)s "
                          f"and {in_scope} and e.type = '{name}' and e.created_at > %(since)s")
    counts["regulator_mentions"] = one(
        f"select count(*) from pilot_events e where e.pilot_id = %(p)s and {in_scope} and e.type = 'complaint' "
        "and e.payload->>'body' ~* '(\\mico\\M|information commissioner|regulator)' and e.created_at > %(since)s")
    # A reply is late if the first human answer after it came after the deadline, or hasn't come and the deadline passed.
    late = 0
    for received, answered in conn.execute(
        f"""select e.created_at,
                   (select min(a.created_at) from pilot_events a where a.pilot_id = e.pilot_id and a.homeowner_key = e.homeowner_key
                      and a.type = 'answered' and a.created_at > e.created_at)
            from pilot_events e where e.pilot_id = %(p)s and {in_scope} and e.type = 'needs_answer' and e.created_at > %(since)s""",
        params).fetchall():
        deadline = reply_deadline(received)
        if (answered and answered > deadline) or (not answered and now > deadline):
            late += 1
    counts["late_replies"] = late
    return counts


def check_pilot(conn, pilot_id: str, now: datetime | None = None) -> list[Breach]:
    """Checks every wave and the whole pilot. Pauses a sending pilot on any
    breach; for a paused pilot it only reports (replies still arrive)."""
    from delivery.pilot import advance_pilot

    now = now or datetime.now(UK)
    state = conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0]
    if state not in ("canary_running", "live", "paused"):
        return []
    since = conn.execute(
        "select max(created_at) from pilot_events where pilot_id = %s and type = 'state' and payload->>'from' = 'paused'",
        (pilot_id,)).fetchone()[0] or EPOCH
    breaches = []
    for (wave_id,) in conn.execute(
        "select distinct wave_id from pilot_homeowners where pilot_id = %s and wave_id is not null order by 1", (pilot_id,)
    ).fetchall():
        breaches += breaches_for(counts_for(conn, pilot_id, wave_id, since, now), wave_id)
    whole = counts_for(conn, pilot_id, None, since, now)
    whole["manual_minutes"] = conn.execute(
        "select coalesce(sum((payload->>'minutes')::numeric), 0) from pilot_events where pilot_id = %s "
        "and type = 'manual_minutes' and created_at > %s", (pilot_id, since)).fetchone()[0]
    # Pilot-wide: rates (catches many small waves) and manual time; per-wave
    # count rules (complaints etc.) are already reported per wave.
    breaches += [b for b in breaches_for(whole, "whole pilot")
                 if b.rule in ("opt-out rate", "text delivery failures", "wrong-person replies", "manual time")]
    if breaches and state != "paused":
        run_id = uuid.uuid4()
        with conn.transaction():
            conn.execute("insert into pilot_events (pilot_id, run_id, type, payload) values (%s, %s, 'stop_condition', %s)",
                         (pilot_id, run_id, Jsonb({"breaches": [b.__dict__ for b in breaches]})))
            advance_pilot(conn, pilot_id, "paused", run_id)
    return breaches
