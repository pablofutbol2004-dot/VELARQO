"""Release a wave of homeowners to GoHighLevel (WORKFLOW.md section 4, steps 4-6).

Adding the wave tag starts the GHL workflow, i.e. real texts to real
homeowners, so every homeowner goes through:

    treatment --(claim into wave)--> queued --(state written first)--> pushing
      --(contact upserted + wave tag added)--> enrolled
      --(4xx: our data is wrong)--> push_failed

Safety:
- The pilot state is re-read before each homeowner. If it's no longer
  canary_running/live (paused, cancelled) the wave stops at once.
- Only arm = 'treatment' rows are ever claimed; the database also refuses a
  holdout row with a wave (constraint holdout_never_contacted).
- Opt-outs are re-checked at send time: an opted_out row is never touched.
- A crash after GHL created the contact leaves the row in 'pushing'. The
  next run upserts it again: GHL matches the existing contact by phone/email
  (requires the sub-account setting "allow duplicate contacts" OFF), and the
  wave tag is a set, and the GHL workflow has re-entry OFF, so nobody is
  texted twice.
- 5xx/timeouts are retried by the client with backoff; if they persist the
  row stays 'pushing' for the next run. 4xx marks it push_failed with the error.
"""

import json
import uuid

from requests import HTTPError

from delivery.states import can_move_homeowner
from integrations.ghl.client import GHLRateLimitError, GHLTemporaryError

SENDING_STATES = {"canary_running", "live"}


class WaveError(Exception):
    pass


def claim_wave(conn, pilot_id: str, wave_id: str, size: int) -> int:
    """Moves up to `size` treatment homeowners into the wave. Idempotent per
    wave: re-running with the same wave_id claims nobody new once it's full."""
    with conn.transaction():
        state = conn.execute("select state from pilots where id = %s for update", (pilot_id,)).fetchone()
        if not state or state[0] not in SENDING_STATES:
            raise WaveError(f"{pilot_id} isn't sending (state {state[0] if state else 'missing'})")
        already = conn.execute(
            "select count(*) from pilot_homeowners where pilot_id = %s and wave_id = %s", (pilot_id, wave_id)
        ).fetchone()[0]
        room = max(size - already, 0)
        if not room:
            return 0
        claimed = conn.execute(
            """update pilot_homeowners set wave_id = %s, state = 'queued', updated_at = now()
               where (pilot_id, homeowner_key) in (
                 select pilot_id, homeowner_key from pilot_homeowners
                 where pilot_id = %s and arm = 'treatment' and state = 'treatment'
                 order by md5(%s || homeowner_key)
                 limit %s for update skip locked)
               returning homeowner_key""",
            (wave_id, pilot_id, wave_id, room),
        ).fetchall()
        conn.execute(
            "insert into pilot_events (pilot_id, run_id, type, payload) values (%s, %s, 'wave_claimed', %s::jsonb)",
            (pilot_id, uuid.uuid4(), json.dumps({"wave_id": wave_id, "claimed": len(claimed)})),
        )
        return len(claimed)


def _contact(row: dict, key_field_id: str | None) -> dict:
    first, _, last = (row["name"] or "").strip().partition(" ")
    contact = {"firstName": first or None, "lastName": last or None, "phone": row["phone"], "email": row["email"],
               "postalCode": row["postcode"], "source": "velarqo pilot"}
    if key_field_id:  # our stable ID on their contact, so outcomes map back exactly
        contact["customFields"] = [{"id": key_field_id, "value": row["homeowner_key"]}]
    return {k: v for k, v in contact.items() if v is not None}


def _set_state(conn, pilot_id, key, new, run_id, **extra):
    current = conn.execute(
        "select state from pilot_homeowners where pilot_id = %s and homeowner_key = %s for update", (pilot_id, key)
    ).fetchone()[0]
    if current == new:
        return
    if not can_move_homeowner(current, new):
        raise WaveError(f"{key}: can't move {current} -> {new}")
    sets = ", ".join(f"{column} = %({column})s" for column in extra)
    conn.execute(
        f"update pilot_homeowners set state = %(new)s{', ' + sets if sets else ''}, updated_at = now() "
        "where pilot_id = %(pilot_id)s and homeowner_key = %(key)s",
        {"new": new, "pilot_id": pilot_id, "key": key, **extra},
    )
    conn.execute(
        "insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) "
        "values (%s, %s, %s, 'homeowner_state', jsonb_build_object('from', %s::text, 'to', %s::text))",
        (pilot_id, key, run_id, current, new),
    )


def send_wave(conn, client, pilot_id: str, wave_id: str, key_field_id: str | None = None) -> dict:
    """Pushes and enrols every queued/pushing homeowner in the wave."""
    run_id = uuid.uuid4()
    stats = {"enrolled": 0, "push_failed": 0, "left_for_retry": 0, "stopped": False}
    columns = ["homeowner_key", "name", "phone", "email", "postcode", "state", "ghl_contact_id"]
    rows = [dict(zip(columns, r)) for r in conn.execute(
        f"select {', '.join(columns)} from pilot_homeowners where pilot_id = %s and wave_id = %s "
        "and arm = 'treatment' and state in ('queued', 'pushing') order by homeowner_key",
        (pilot_id, wave_id),
    ).fetchall()]
    for row in rows:
        with conn.transaction():
            pilot_state = conn.execute("select state from pilots where id = %s", (pilot_id,)).fetchone()[0]
            if pilot_state not in SENDING_STATES:
                stats["stopped"] = True
                break
            still = conn.execute(
                "select state from pilot_homeowners where pilot_id = %s and homeowner_key = %s for update",
                (pilot_id, row["homeowner_key"]),
            ).fetchone()[0]
            if still not in ("queued", "pushing"):     # opted out (or done) since we read the list
                continue
            _set_state(conn, pilot_id, row["homeowner_key"], "pushing", run_id)   # recorded before the remote call
        try:
            contact_id = row["ghl_contact_id"] or client.upsert_contact(_contact(row, key_field_id))["contact"]["id"]
            with conn.transaction():
                conn.execute("update pilot_homeowners set ghl_contact_id = %s where pilot_id = %s and homeowner_key = %s",
                             (contact_id, pilot_id, row["homeowner_key"]))
            client.add_tags(contact_id, [f"vq-{wave_id}"])       # this starts the texts
        except (GHLTemporaryError, GHLRateLimitError):
            stats["left_for_retry"] += 1                          # stays 'pushing'; next run reconciles
            continue
        except HTTPError as exc:
            with conn.transaction():
                _set_state(conn, pilot_id, row["homeowner_key"], "push_failed", run_id,
                           push_error=f"{exc.response.status_code if exc.response is not None else ''} {exc}"[:500])
            stats["push_failed"] += 1
            continue
        with conn.transaction():
            _set_state(conn, pilot_id, row["homeowner_key"], "enrolled", run_id)
        stats["enrolled"] += 1
    with conn.transaction():
        conn.execute(
            "insert into pilot_events (pilot_id, run_id, type, payload) values (%s, %s, 'wave_sent', %s::jsonb)",
            (pilot_id, run_id, json.dumps({"wave_id": wave_id, **stats})),
        )
    return stats
