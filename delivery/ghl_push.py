"""Release a wave of homeowners to GoHighLevel (WORKFLOW.md section 4, steps 4-6),
and push opt-outs back to GHL (step 8).

Adding the wave tag starts the GHL workflow, i.e. real texts to real
homeowners, so every homeowner goes through:

    treatment --(claim into wave)--> queued --(committed first)--> pushing
      --(contact upserted + wave tag added)--> enrolled
      --(400/422: our data is wrong)--> push_failed

Safety:
- Callers pass an AUTOCOMMIT connection (delivery.pilot.db()); every step
  below is its own committed transaction, so a crash loses nothing.
- One send_wave per pilot at a time (Postgres advisory lock); a second run
  exits immediately instead of pushing the same people concurrently.
- The pilot state is re-read before each homeowner; if it isn't
  canary_running/live the wave stops at once.
- Only arm = 'treatment' rows are claimed, one row per person, and never a
  person (same person_key, mobile or email) who is in the holdout, opted out,
  excluded person-wide, or already claimed in this pilot. The canary claims
  at most CANARY_MAX people across all its waves. The database also refuses
  a holdout row with a wave.
- Opt-outs are re-checked at send time: an opted_out row is never touched.
  After the GHL upsert (which can take seconds) the row and pilot state are
  re-read under lock; the wave tag is added only if the row is still
  'pushing' and the pilot still sending ('tag_skipped' event otherwise).
- A crash after GHL created the contact leaves the row in 'pushing'; the
  next run upserts again (GHL matches by phone/email: sub-account setting
  "allow duplicate contacts" OFF), the tag is a set, and the GHL workflow has
  re-entry OFF, so nobody is texted twice.
- 5xx/timeouts are retried by the client; if they persist the row stays
  'pushing' for the next run. 401/403 stops the whole run (token problem,
  rows untouched). 400/404/422 marks the row push_failed with the error.
"""

import uuid
from datetime import datetime, timezone

from psycopg.types.json import Jsonb
from requests import HTTPError

from delivery.states import PAST_ENROLLED, PERSON_WIDE_REASONS, SENDING, can_move_homeowner
from integrations.ghl.client import GHLAuthError, GHLRateLimitError, GHLTemporaryError

CANARY_MAX = 30


class WaveError(Exception):
    pass


def _event(conn, pilot_id, run_id, type_, payload, key=None):
    conn.execute("insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, %s, %s)",
                 (pilot_id, key, run_id, type_, Jsonb(payload)))


def claim_wave(conn, pilot_id: str, wave_id: str, size: int) -> int:
    """Moves up to `size` treatment people into the wave. Idempotent per
    wave: re-running with the same wave_id claims nobody new once it's full.
    At most one row per person is ever claimed (even within one statement),
    and never a person who is in the holdout, opted out, excluded for a
    person-wide reason (opt-out / do-not-contact / won) or already claimed,
    matched by person_key, phone or email. While the pilot is in its canary,
    at most CANARY_MAX people are claimed across all waves."""
    with conn.transaction():
        state = conn.execute("select state from pilots where id = %s for update", (pilot_id,)).fetchone()
        if not state or state[0] not in SENDING:
            raise WaveError(f"{pilot_id} isn't sending (state {state[0] if state else 'missing'})")
        if state[0] == "canary_running" and size > CANARY_MAX:
            raise WaveError(f"the canary wave is at most {CANARY_MAX} homeowners")
        already = conn.execute(
            "select count(*) from pilot_homeowners where pilot_id = %s and wave_id = %s", (pilot_id, wave_id)
        ).fetchone()[0]
        room = max(size - already, 0)
        if state[0] == "canary_running":   # the whole canary, not each wave
            canary_people = conn.execute(
                "select count(distinct coalesce(person_key, homeowner_key)) from pilot_homeowners "
                "where pilot_id = %s and wave_id is not null", (pilot_id,)).fetchone()[0]
            room = min(room, max(CANARY_MAX - canary_people, 0))
        if not room:
            return 0
        # The pilot row lock above serialises claims; `state = 'treatment'` is
        # repeated on the outer UPDATE so a row opted out meanwhile is skipped.
        claimed = conn.execute(
            """update pilot_homeowners set wave_id = %(w)s, state = 'queued', claimed_at = now(), updated_at = now()
               where pilot_id = %(p)s and state = 'treatment' and arm = 'treatment' and homeowner_key in (
                 select homeowner_key from (
                   select distinct on (coalesce(t.person_key, t.homeowner_key)) t.homeowner_key,
                          md5(%(w)s || coalesce(t.person_key, t.homeowner_key)) as draw
                   from pilot_homeowners t
                   where t.pilot_id = %(p)s and t.arm = 'treatment' and t.state = 'treatment'
                     and not exists (
                       select 1 from pilot_homeowners o
                       where o.pilot_id = t.pilot_id and o.homeowner_key <> t.homeowner_key
                         and ((t.person_key is not null and o.person_key = t.person_key)
                              or (t.phone is not null and o.phone = t.phone) or (t.email is not null and o.email = t.email))
                         and (o.arm = 'holdout' or o.state = 'opted_out' or o.wave_id is not null
                              or o.exclusion_reason = any(%(reasons)s)))
                   order by coalesce(t.person_key, t.homeowner_key), t.quote_date desc nulls last, t.homeowner_key) one_per_person
                 order by draw limit %(n)s)
               returning homeowner_key""",
            {"w": wave_id, "p": pilot_id, "reasons": list(PERSON_WIDE_REASONS), "n": room},
        ).fetchall()
        _event(conn, pilot_id, uuid.uuid4(), "wave_claimed", {"wave_id": wave_id, "claimed": len(claimed)})
        return len(claimed)


def split_name(name: str | None) -> tuple[str | None, str | None]:
    """'Gary Johnson' -> ('Gary', 'Johnson'); 'Johnson, Gary' -> ('Gary', 'Johnson');
    'MR G JOHNSON' -> ('G', 'JOHNSON'). The first name goes into "Hi [first name]",
    so a wrong split would be read by the homeowner."""
    text = " ".join(str(name or "").split()).strip(" .")
    if "," in text:
        last, _, first = text.partition(",")
        first, last = first.strip(), last.strip()
    else:
        first, _, last = text.partition(" ")
    if first.lower().rstrip(".") in ("mr", "mrs", "ms", "miss", "dr", "mr&mrs", "mr/mrs") and last:
        first, _, last = last.partition(" ")
    return first.strip(" ,.") or None, last.strip(" ,.") or None


def _contact(row: dict, key_field_id: str | None) -> dict:
    first, last = split_name(row["name"])
    contact = {"firstName": first, "lastName": last, "phone": row["phone"], "email": row["email"],
               "postalCode": row["postcode"], "source": "velarqo pilot"}
    if key_field_id:  # our stable ID on their contact, so outcomes map back exactly
        contact["customFields"] = [{"id": key_field_id, "value": row["homeowner_key"]}]
    return {k: v for k, v in contact.items() if v is not None}


def _set_state(conn, pilot_id, key, new, run_id, **extra) -> str:
    """Moves one homeowner; returns the state they're in afterwards. Inside a transaction."""
    current = conn.execute(
        "select state from pilot_homeowners where pilot_id = %s and homeowner_key = %s for update", (pilot_id, key)
    ).fetchone()[0]
    if current == new or not can_move_homeowner(current, new):
        return current
    sets = "".join(f", {column} = %({column})s" for column in extra)
    conn.execute(f"update pilot_homeowners set state = %(new)s{sets}, updated_at = now() "
                 "where pilot_id = %(pilot_id)s and homeowner_key = %(key)s",
                 {"new": new, "pilot_id": pilot_id, "key": key, **extra})
    _event(conn, pilot_id, run_id, "homeowner_state", {"from": current, "to": new}, key)
    return new


def send_wave(conn, client, pilot_id: str, wave_id: str, key_field_id: str | None = None) -> dict:
    """Pushes and enrols every queued/pushing homeowner in the wave. `conn`
    must be autocommit (each step commits on its own)."""
    if not conn.autocommit:
        raise WaveError("send_wave needs an autocommit connection (delivery.pilot.db())")
    if not conn.execute("select pg_try_advisory_lock(hashtext(%s))", (f"send:{pilot_id}",)).fetchone()[0]:
        return {"enrolled": 0, "push_failed": 0, "left_for_retry": 0, "skipped": 0, "stopped": True,
                "reason": "another run is sending"}
    try:
        return _send_wave_locked(conn, client, pilot_id, wave_id, key_field_id)
    finally:
        conn.execute("select pg_advisory_unlock(hashtext(%s))", (f"send:{pilot_id}",))


def _send_wave_locked(conn, client, pilot_id, wave_id, key_field_id) -> dict:
    run_id = uuid.uuid4()
    stats = {"enrolled": 0, "push_failed": 0, "left_for_retry": 0, "skipped": 0, "stopped": False}
    columns = ["homeowner_key", "name", "phone", "email", "postcode", "state", "ghl_contact_id"]
    rows = [dict(zip(columns, r)) for r in conn.execute(
        f"select {', '.join(columns)} from pilot_homeowners where pilot_id = %s and wave_id = %s "
        "and arm = 'treatment' and state in ('queued', 'pushing') order by homeowner_key",
        (pilot_id, wave_id),
    ).fetchall()]
    for row in rows:
        with conn.transaction():
            pilot_state = conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0]
            if pilot_state not in SENDING:
                stats["stopped"] = True
                break
            if _set_state(conn, pilot_id, row["homeowner_key"], "pushing", run_id) != "pushing":
                continue                                # opted out (or moved on) since we read the list
        try:
            contact_id = row["ghl_contact_id"] or client.upsert_contact(_contact(row, key_field_id))["contact"]["id"]
            with conn.transaction():                              # saved first: an opt-out can now reach GHL
                conn.execute("update pilot_homeowners set ghl_contact_id = %s where pilot_id = %s and homeowner_key = %s",
                             (contact_id, pilot_id, row["homeowner_key"]))
            with conn.transaction():
                # Re-check under lock: an opt-out (or pause) may have landed
                # while GHL was upserting. The row stays locked until the tag
                # is added, so an opt-out arriving now waits and then queues
                # the tag removal + do-not-disturb.
                now_state = conn.execute("select state from pilot_homeowners where pilot_id = %s and homeowner_key = %s "
                                         "for update", (pilot_id, row["homeowner_key"])).fetchone()[0]
                pilot_state = conn.execute("select state from pilots where id = %s for share", (pilot_id,)).fetchone()[0]
                if now_state != "pushing" or pilot_state not in SENDING:
                    why = f"homeowner is now '{now_state}'" if now_state != "pushing" else f"pilot is now '{pilot_state}'"
                    _event(conn, pilot_id, run_id, "tag_skipped", {"wave_id": wave_id, "contact_id": contact_id, "why": why},
                           row["homeowner_key"])
                    skipped_for_pilot = pilot_state not in SENDING
                else:
                    client.add_tags(contact_id, [f"vq-{wave_id}"])   # this starts the texts
                    skipped_for_pilot = None
            if skipped_for_pilot is not None:
                stats["skipped"] += 1
                if skipped_for_pilot:
                    stats["stopped"] = True
                    break
                continue
        except GHLAuthError as exc:
            stats["stopped"] = True
            stats["reason"] = f"GoHighLevel refused the token ({exc}); fix .env and re-run"
            break
        except (GHLTemporaryError, GHLRateLimitError):
            stats["left_for_retry"] += 1                          # stays 'pushing'; next run reconciles
            continue
        except HTTPError as exc:
            code = exc.response.status_code if exc.response is not None else ""
            with conn.transaction():
                _set_state(conn, pilot_id, row["homeowner_key"], "push_failed", run_id, push_error=f"{code} {exc}"[:500])
            stats["push_failed"] += 1
            continue
        with conn.transaction():
            after = _set_state(conn, pilot_id, row["homeowner_key"], "enrolled", run_id)
        if after == "enrolled" or after in PAST_ENROLLED:          # a fast reply/opt-out webhook may have got there first
            stats["enrolled"] += 1
    with conn.transaction():
        _event(conn, pilot_id, run_id, "wave_sent", {"wave_id": wave_id, **stats})
    return stats


def push_opt_outs(conn, client, pilot_id: str) -> dict:
    """Sets do-not-disturb in GHL and removes the wave tag for every opted-out
    homeowner with a GHL contact and no 'dnd_confirmed' event yet, whatever
    the pilot's state. Re-run by every `check` until GHL accepts it."""
    pending = conn.execute(
        """select distinct on (h.homeowner_key) h.homeowner_key, h.ghl_contact_id, h.wave_id
           from pilot_homeowners h
           where h.pilot_id = %s and h.state = 'opted_out' and h.ghl_contact_id is not null
             and not exists (select 1 from pilot_events c where c.pilot_id = h.pilot_id
                             and c.homeowner_key = h.homeowner_key and c.type = 'dnd_confirmed')""",
        (pilot_id,)).fetchall()
    done, failed = 0, 0
    run_id = uuid.uuid4()
    for key, contact_id, wave_id in pending:
        try:
            client.set_dnd(contact_id)
            if wave_id:
                client.remove_tags(contact_id, [f"vq-{wave_id}"])
        except (GHLAuthError, GHLTemporaryError, GHLRateLimitError, HTTPError) as exc:
            failed += 1
            with conn.transaction():
                _event(conn, pilot_id, run_id, "dnd_failed", {"contact_id": contact_id, "error": str(exc)[:300]}, key)
            continue
        with conn.transaction():
            _event(conn, pilot_id, run_id, "dnd_confirmed",
                   {"contact_id": contact_id, "at": datetime.now(timezone.utc).isoformat()}, key)
        done += 1
    return {"confirmed": done, "failed": failed}
