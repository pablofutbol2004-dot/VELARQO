"""Run a client pilot, step by step (docs/delivery/WORKFLOW.md).

    python -m delivery.pilot create acme-windows --vertical windows --areas LS,BD
    python -m delivery.pilot approve acme-windows-202611-1 agreement --actor pablo --note "signed v1"
    python -m delivery.pilot advance acme-windows-202611-1 sample_received
    python -m delivery.pilot import  acme-windows-202611-1 clients/acme-windows/full_export.xlsx --dnc clients/acme-windows/dnc.csv
    python -m delivery.pilot freeze  acme-windows-202611-1
    python -m delivery.pilot set     acme-windows-202611-1 --ghl-location L --ghl-calendar C --price 80 --max-billable 20
    python -m delivery.pilot send-wave acme-windows-202611-1 w1 --size 25
    python -m delivery.pilot optout  acme-windows-202611-1 --phone 07700900123
    python -m delivery.pilot check            # every 15 minutes
    python -m delivery.pilot status  acme-windows-202611-1

Every command commits its own work (autocommit connection; each step is an
explicit transaction) and logs pilot_events with its run_id. Commands check
the pilot's state themselves, so running one at the wrong time does nothing.
"""

import csv
import hashlib
import json
import os
import re
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import click
from psycopg.types.json import Jsonb

from client_onboarding.field_mapping.mapper import apply_mapping
from client_onboarding.sample_audit import age_bucket, classify, load, map_columns, parse_date
from data.supabase_store import connect
from delivery.contacts import email as norm_email
from delivery.contacts import person_key, uk_mobile
from delivery.split import split
from delivery.states import GATES, allowed_pilot_moves
from lib.normalization.normalize import normalize_postcode

RULES_VERSION = "eligibility-v2"
CANARY_MAX = 30
DATA_RETENTION_DAYS = 30
# A person excluded for one of these on ANY of their quotes is excluded on all.
PERSON_WIDE_REASONS = ("opted out", "on client's do-not-contact list", "already won/booked")
DUPLICATE_REASON = "another quote for the same person"


class PilotError(click.ClickException):
    pass


def db():
    """Autocommit connection: every `with conn.transaction()` is a real commit.
    (A plain connection silently opens a transaction on the first query and
    turns later blocks into savepoints that are rolled back on exit.)"""
    conn = connect()
    conn.autocommit = True
    return conn


def log(conn, pilot_id: str, run_id, type_: str, payload: dict, homeowner_key: str | None = None) -> None:
    conn.execute(
        "insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, %s, %s)",
        (pilot_id, homeowner_key, run_id, type_, Jsonb(payload)),
    )


PILOT_COLUMNS = ["id", "client_slug", "state", "holdout_fraction", "service_postcode_areas", "frozen_at",
                 "ghl_location_id", "ghl_calendar_id"]


def pilot_row(conn, pilot_id: str, lock: bool = False) -> dict:
    row = conn.execute(
        f"select {', '.join(PILOT_COLUMNS)} from pilots where id = %s{' for update' if lock else ''}", (pilot_id,)
    ).fetchone()
    if not row:
        raise PilotError(f"no pilot {pilot_id}")
    pilot = dict(zip(PILOT_COLUMNS, row))
    pilot["areas"] = pilot.pop("service_postcode_areas")
    return pilot


def homeowner_key(client_slug: str, record: dict) -> str:
    """Stable per quote row: the export's own record ID if it has one, else
    mobile/email, else name + postcode + quote date."""
    basis = (
        str(record.get("record_id") or "").strip()
        or uk_mobile(record.get("phone")) or norm_email(record.get("email"))
        or "|".join(str(record.get(k) or "").strip().lower() for k in ("name", "postcode", "quote_date"))
    )
    return hashlib.sha256(f"{client_slug}:{basis}".encode()).hexdigest()[:32]


def postcode_area(postcode: str | None) -> str | None:
    match = re.match(r"^([A-Z]{1,2})\d", (postcode or "").upper().strip())
    return match[1] if match else None


def load_dnc(path: Path | None) -> set[str]:
    """Client's do-not-contact list: any CSV with phone and/or email columns."""
    if not path:
        return set()
    blocked = set()
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for value in row.values():
                blocked |= {v for v in (norm_email(value), uk_mobile(value)) if v}
    return blocked


# Leads bought from lead sites: the homeowner gave their details to the
# site, not to the installer, so the installer's soft opt-in doesn't cover
# them (docs/delivery/06_compliance_notes.md). Same for bought/rented lists.
_LEAD_SITE = re.compile(r"checkatrade|\bbark\b|bark\.com|mybuilder|my builder|rated ?people|trustatrader|trust a trader|"
                        r"which\??\s*trusted|houzz|\byell\b|yell\.com|\bbought\b|purchased|rented list|lead ?gen|third.?party", re.I)


def eligibility(record: dict, areas: list[str], dnc: set[str], today: date) -> tuple[str | None, int | None]:
    """(exclusion reason or None, quote age in months) for one quote row."""
    verdict, age = classify(record, today)
    if verdict != "worth chasing":
        return verdict, age
    if _LEAD_SITE.search(str(record.get("lead_source") or "")):
        return "came from a lead site or bought list", age
    phone, mail = uk_mobile(record.get("phone")), norm_email(record.get("email"))
    if not phone and not mail:
        return "no UK mobile or email", age
    if phone in dnc or mail in dnc:
        return "on client's do-not-contact list", age
    if areas and postcode_area(record.get("postcode")) not in areas:
        return "outside service area", age
    return None, age


@click.group()
def cli():
    pass


@cli.command()
@click.argument("client_slug")
@click.option("--vertical", required=True, type=click.Choice(["windows", "roofing", "solar"]))
@click.option("--areas", default="", help="Comma-separated postcode areas they cover, e.g. LS,BD,HG")
@click.option("--holdout", default=0.15, show_default=True)
def create(client_slug, vertical, areas, holdout):
    conn = db()
    with conn.transaction():
        n = conn.execute("select count(*) from pilots where client_slug = %s", (client_slug,)).fetchone()[0] + 1
        pilot_id = f"{client_slug}-{date.today():%Y%m}-{n}"
        conn.execute(
            "insert into pilots (id, client_slug, vertical, holdout_fraction, service_postcode_areas, rules_version) "
            "values (%s, %s, %s, %s, %s, %s)",
            (pilot_id, client_slug, vertical, holdout, [a.strip().upper() for a in areas.split(",") if a.strip()], RULES_VERSION),
        )
        log(conn, pilot_id, uuid.uuid4(), "pilot_created", {"vertical": vertical, "areas": areas, "holdout": holdout})
    click.echo(pilot_id)


@cli.command()
@click.argument("pilot_id")
@click.argument("gate", type=click.Choice(sorted(set(GATES.values()))))
@click.option("--actor", required=True)
@click.option("--reject", is_flag=True)
@click.option("--note", default="")
@click.option("--messages-file", type=click.Path(exists=True, path_type=Path), help="For the messages gate: the exact approved texts")
def approve(pilot_id, gate, actor, reject, note, messages_file):
    details = {"note": note}
    if gate == "messages":
        if not messages_file:
            raise PilotError("the messages gate needs --messages-file with the exact approved texts")
        text = messages_file.read_text(encoding="utf-8")
        details |= {"messages": text, "sha256": hashlib.sha256(text.encode()).hexdigest(), "file": str(messages_file)}
    conn = db()
    with conn.transaction():
        pilot_row(conn, pilot_id)
        conn.execute(
            "insert into pilot_approvals (pilot_id, gate, decision, actor, details) values (%s, %s, %s, %s, %s)",
            (pilot_id, gate, "rejected" if reject else "approved", actor, Jsonb(details)),
        )
        log(conn, pilot_id, uuid.uuid4(), "approval", {"gate": gate, "decision": "rejected" if reject else "approved", "actor": actor})
    click.echo(f"{gate}: {'rejected' if reject else 'approved'} by {actor}")


def last_pause(conn, pilot_id: str):
    """(paused_at, state it was paused from) or (None, None)."""
    row = conn.execute(
        "select created_at, payload->>'from' from pilot_events where pilot_id = %s and type = 'state' "
        "and payload->>'to' = 'paused' order by created_at desc, id desc limit 1", (pilot_id,)).fetchone()
    return row if row else (None, None)


def advance_pilot(conn, pilot_id: str, to_state: str, run_id) -> None:
    """Call inside a transaction."""
    pilot = pilot_row(conn, pilot_id, lock=True)
    paused_at, paused_from = last_pause(conn, pilot_id) if pilot["state"] == "paused" else (None, None)
    if to_state not in allowed_pilot_moves(pilot["state"], paused_from):
        raise PilotError(f"{pilot_id} is '{pilot['state']}'; can't move to '{to_state}'")
    gate = GATES.get((pilot["state"], to_state))
    if gate:
        latest = conn.execute(
            "select decision, decided_at from pilot_approvals where pilot_id = %s and gate = %s order by decided_at desc, id desc limit 1",
            (pilot_id, gate),
        ).fetchone()
        if not latest or latest[0] != "approved":
            raise PilotError(f"moving to '{to_state}' needs an approved '{gate}' gate (python -m delivery.pilot approve ...)")
        if gate == "resume" and paused_at and latest[1] < paused_at:
            raise PilotError("the 'resume' approval is older than the pause; approve again after reviewing why it paused")
    if to_state == "canary_running" and pilot["state"] == "canary_ready" and not (pilot["ghl_location_id"] and pilot["ghl_calendar_id"]):
        raise PilotError("set the client's GoHighLevel location and survey calendar first (pilot set --ghl-location --ghl-calendar)")
    conn.execute("update pilots set state = %s, updated_at = now() where id = %s", (to_state, pilot_id))
    log(conn, pilot_id, run_id, "state", {"from": pilot["state"], "to": to_state})


@cli.command()
@click.argument("pilot_id")
@click.argument("to_state")
def advance(pilot_id, to_state):
    conn = db()
    with conn.transaction():
        advance_pilot(conn, pilot_id, to_state, uuid.uuid4())
    click.echo(f"{pilot_id} -> {to_state}")


def _iso(value):
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else None


def _number(value):
    try:
        return float(str(value).replace("£", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def apply_person_rules(conn, pilot_id: str) -> dict:
    """One person = one contactable row. If any of a person's quotes is
    opted out / on the do-not-contact list / already won, all of them are
    excluded; otherwise only their most recent eligible quote stays."""
    spread = conn.execute(
        """update pilot_homeowners h set state = 'excluded', exclusion_reason = x.reason, updated_at = now()
           from (select person_key, min(case when state = 'opted_out' then 'opted out' else exclusion_reason end) as reason
                 from pilot_homeowners
                 where pilot_id = %s and person_key is not null and (exclusion_reason = any(%s) or state = 'opted_out')
                 group by person_key) x
           where h.pilot_id = %s and h.person_key = x.person_key and h.state = 'eligible'
           returning h.homeowner_key""",
        (pilot_id, list(PERSON_WIDE_REASONS), pilot_id)).fetchall()
    dupes = conn.execute(
        """update pilot_homeowners h set state = 'excluded', exclusion_reason = %s, updated_at = now()
           from (select homeowner_key, row_number() over (
                   partition by person_key order by quote_date desc nulls last, homeowner_key) as n
                 from pilot_homeowners where pilot_id = %s and state = 'eligible' and person_key is not null) r
           where h.pilot_id = %s and h.homeowner_key = r.homeowner_key and r.n > 1
           returning h.homeowner_key""",
        (DUPLICATE_REASON, pilot_id, pilot_id)).fetchall()
    return {"excluded_person_wide": len(spread), "duplicate_quotes": len(dupes)}


def import_records(conn, pilot_id: str, records: list[dict], dnc: set[str], run_id, today: date | None = None) -> dict:
    """Upserts every row and (re)decides eligibility. Allowed only before the
    freeze, so re-importing (e.g. with a do-not-contact list added) re-applies
    the rules to every row. Call inside a transaction."""
    today = today or date.today()
    pilot = pilot_row(conn, pilot_id, lock=True)
    if pilot["state"] != "data_received" or pilot["frozen_at"]:
        raise PilotError(f"import needs an unfrozen pilot in 'data_received' (it's '{pilot['state']}')")
    headers = list(dict.fromkeys(k for r in records for k in r))
    mapped = apply_mapping(records, map_columns(headers))
    stats = {"rows": len(mapped), "new": 0, "updated": 0}
    for record in mapped:
        key = homeowner_key(pilot["client_slug"], record)
        reason, age = eligibility(record, pilot["areas"], dnc, today)
        phone, mail = uk_mobile(record.get("phone")), norm_email(record.get("email"))
        inserted = conn.execute(
            """insert into pilot_homeowners (pilot_id, homeowner_key, source_record_id, name, phone, email, postcode,
                 quote_date, product, quote_value, quote_status, lead_source, state, exclusion_reason, stratum, person_key)
               values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               on conflict (pilot_id, homeowner_key) do update set
                 name = excluded.name, phone = excluded.phone, email = excluded.email, postcode = excluded.postcode,
                 quote_date = excluded.quote_date, product = excluded.product, quote_value = excluded.quote_value,
                 quote_status = excluded.quote_status, lead_source = excluded.lead_source, state = excluded.state,
                 exclusion_reason = excluded.exclusion_reason, stratum = excluded.stratum, person_key = excluded.person_key,
                 updated_at = now()
               where pilot_homeowners.state in ('eligible', 'excluded')
               returning (xmax = 0)""",
            (pilot_id, key, str(record.get("record_id") or "") or None, record.get("name"), phone, mail,
             normalize_postcode(str(record.get("postcode") or "")), _iso(record.get("quote_date")), record.get("product"),
             _number(record.get("quote_value")), record.get("quote_status"), record.get("lead_source"),
             "excluded" if reason else "eligible", reason, age_bucket(age), person_key(phone, mail)),
        ).fetchone()
        if inserted:
            stats["new" if inserted[0] else "updated"] += 1
    stats |= apply_person_rules(conn, pilot_id)
    stats["eligible"] = conn.execute("select count(*) from pilot_homeowners where pilot_id = %s and state = 'eligible'",
                                     (pilot_id,)).fetchone()[0]
    stats["excluded"] = dict(conn.execute(
        "select exclusion_reason, count(*) from pilot_homeowners where pilot_id = %s and state = 'excluded' group by 1",
        (pilot_id,)).fetchall())
    log(conn, pilot_id, run_id, "import", {**stats, "rules_version": RULES_VERSION})
    return stats


@cli.command("import")
@click.argument("pilot_id")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--dnc", type=click.Path(exists=True, path_type=Path), help="Client's do-not-contact list (CSV)")
def import_cmd(pilot_id, path, dnc):
    if "clients" not in path.resolve().parts:
        raise PilotError("client files must live under clients/<slug>/ (git ignores that folder)")
    conn = db()
    with conn.transaction():
        stats = import_records(conn, pilot_id, load(path), load_dnc(dnc), uuid.uuid4())
    click.echo(json.dumps(stats, indent=2))


def freeze_pilot(conn, pilot_id: str, run_id) -> dict:
    """Split eligible people into treatment and holdout, once, forever.
    Call inside a transaction."""
    pilot = pilot_row(conn, pilot_id, lock=True)
    if pilot["state"] != "data_received" or pilot["frozen_at"]:
        raise PilotError(f"freeze needs an unfrozen pilot in 'data_received' (it's '{pilot['state']}')")
    rows = conn.execute(
        "select homeowner_key, stratum from pilot_homeowners where pilot_id = %s and state = 'eligible'", (pilot_id,)
    ).fetchall()
    if not rows:
        raise PilotError("nobody is eligible; check the import first")
    arms = split(pilot_id, rows, float(pilot["holdout_fraction"]))
    for key, arm in arms.items():
        conn.execute(
            "update pilot_homeowners set arm = %s, state = %s, updated_at = now() where pilot_id = %s and homeowner_key = %s",
            (arm, arm, pilot_id, key),
        )
    conn.execute("update pilots set frozen_at = now() where id = %s", (pilot_id,))
    advance_pilot(conn, pilot_id, "eligibility_frozen", run_id)
    counts = {"treatment": sum(a == "treatment" for a in arms.values()), "holdout": sum(a == "holdout" for a in arms.values())}
    log(conn, pilot_id, run_id, "freeze", counts)
    return counts


@cli.command()
@click.argument("pilot_id")
def freeze(pilot_id):
    conn = db()
    with conn.transaction():
        counts = freeze_pilot(conn, pilot_id, uuid.uuid4())
    click.echo(f"frozen: {counts['treatment']} to contact, {counts['holdout']} held back for comparison")


def ghl_client_for(conn, pilot_id: str):
    """The client's GoHighLevel API client, after checking the .env location
    matches the pilot's (else webhooks would be routed nowhere)."""
    from integrations.ghl.client import GHLClient

    pilot = pilot_row(conn, pilot_id)
    env = pilot["client_slug"].upper().replace("-", "_")
    token, location = os.environ.get(f"GHL_TOKEN_{env}"), os.environ.get(f"GHL_LOCATION_{env}")
    if not token or not location:
        raise PilotError(f"set GHL_TOKEN_{env} and GHL_LOCATION_{env} in .env (that client's sub-account)")
    if pilot["ghl_location_id"] != location:
        raise PilotError(f"pilot's GHL location ({pilot['ghl_location_id']}) doesn't match GHL_LOCATION_{env}; "
                         "replies would be lost. Fix with: pilot set --ghl-location")
    return GHLClient(token, location), os.environ.get(f"GHL_KEYFIELD_{env}")


@cli.command("send-wave")
@click.argument("pilot_id")
@click.argument("wave")
@click.option("--size", type=int, required=True, help=f"Homeowners in this wave (canary: at most {CANARY_MAX})")
def send_wave_cmd(pilot_id, wave, size):
    """Claims up to SIZE treatment homeowners into WAVE and enrols them in
    GoHighLevel. Safe to re-run: finishes a half-sent wave without resending."""
    from delivery.ghl_push import claim_wave, send_wave

    conn = db()
    client, key_field = ghl_client_for(conn, pilot_id)
    wave_id = f"{pilot_id}-{wave}"
    claimed = claim_wave(conn, pilot_id, wave_id, size)
    stats = send_wave(conn, client, pilot_id, wave_id, key_field)
    click.echo(f"{wave_id}: {claimed} newly claimed; {json.dumps(stats)}")


def opt_out_people(conn, pilot_id: str, identifiers: set[str], run_id, why: str) -> int:
    """Marks every row of these people opted out (any pilot state) and queues
    the do-not-disturb push to GoHighLevel. Call inside a transaction."""
    from delivery.states import can_move_homeowner

    rows = conn.execute(
        "select homeowner_key, state, ghl_contact_id from pilot_homeowners where pilot_id = %s "
        "and (person_key = any(%s) or phone = any(%s) or email = any(%s)) for update",
        (pilot_id, list(identifiers), list(identifiers), list(identifiers))).fetchall()
    moved = 0
    for key, state, contact in rows:
        if not can_move_homeowner(state, "opted_out"):
            continue
        conn.execute("update pilot_homeowners set state = 'opted_out', updated_at = now() where pilot_id = %s and homeowner_key = %s",
                     (pilot_id, key))
        log(conn, pilot_id, run_id, "homeowner_state", {"from": state, "to": "opted_out", "why": why}, key)
        if contact:
            log(conn, pilot_id, run_id, "dnd_pending", {"contact_id": contact}, key)
        moved += 1
    return moved


@cli.command()
@click.argument("pilot_id")
@click.option("--phone")
@click.option("--email", "mail")
@click.option("--file", "path", type=click.Path(exists=True, path_type=Path), help="CSV of opt-outs (phones/emails)")
def optout(pilot_id, phone, mail, path):
    """Record opt-outs that reached the installer some other way. Works at any
    stage; the person is also set to do-not-disturb in GoHighLevel on the next
    `check` (or right away if the client's GHL is configured)."""
    ids = {v for v in (uk_mobile(phone), norm_email(mail)) if v} | load_dnc(path)
    if not ids:
        raise PilotError("give --phone, --email or --file")
    conn = db()
    with conn.transaction():
        moved = opt_out_people(conn, pilot_id, ids, uuid.uuid4(), "reported by installer")
    pushed = _push_opt_outs_quietly(conn, pilot_id)
    click.echo(f"{moved} opted out; {pushed}")


def _push_opt_outs_quietly(conn, pilot_id: str) -> str:
    from delivery.ghl_push import push_opt_outs

    try:
        client, _ = ghl_client_for(conn, pilot_id)
    except PilotError as exc:
        return f"GHL not updated yet ({exc.message})"
    result = push_opt_outs(conn, client, pilot_id)
    return f"GHL do-not-disturb: {result}"


@cli.command("set")
@click.argument("pilot_id")
@click.option("--price", type=float, help="Price per booked survey, from the SIGNED agreement")
@click.option("--ghl-location", help="The client's GoHighLevel sub-account (location) id")
@click.option("--ghl-calendar", help="The GHL calendar id for surveys booked by this pilot")
@click.option("--max-billable", type=int, help="Cap on billable booked surveys for the whole pilot")
@click.option("--max-per-week", type=int, help="Cap on billable booked surveys per week")
@click.option("--free", "free_homeowners", type=int, help="First N contacted homeowners are free (offer B)")
def set_cmd(pilot_id, price, ghl_location, ghl_calendar, max_billable, max_per_week, free_homeowners):
    changes = {"price_per_booked_gbp": price, "ghl_location_id": ghl_location, "ghl_calendar_id": ghl_calendar,
               "max_billable": max_billable, "max_billable_per_week": max_per_week, "free_homeowners": free_homeowners}
    changes = {k: v for k, v in changes.items() if v is not None}
    if not changes:
        raise PilotError("nothing to set")
    conn = db()
    with conn.transaction():
        pilot_row(conn, pilot_id, lock=True)
        for column, value in changes.items():  # column names come from the fixed dict above
            conn.execute(f"update pilots set {column} = %s, updated_at = now() where id = %s", (value, pilot_id))
        log(conn, pilot_id, uuid.uuid4(), "settings", changes)
    click.echo("saved")


@cli.command("log")
@click.argument("pilot_id")
@click.argument("what", type=click.Choice(["manual_minutes", "installer_missed", "answered", "direct_booking"]))
@click.option("--minutes", type=float, help="For manual_minutes")
@click.option("--phone", help="Homeowner's phone, for installer_missed / answered")
@click.option("--note", default="")
def log_cmd(pilot_id, what, minutes, phone, note):
    """Things only a person knows: time spent, a survey the installer missed,
    a reply answered outside GoHighLevel, or a homeowner we messaged who
    booked directly with the installer within the attribution window."""
    conn = db()
    with conn.transaction():
        key = None
        if what != "manual_minutes":
            row = conn.execute("select homeowner_key from pilot_homeowners where pilot_id = %s and phone = %s "
                               "order by state = 'excluded' limit 1", (pilot_id, uk_mobile(phone))).fetchone()
            if not row:
                raise PilotError("no homeowner with that phone in this pilot")
            key = row[0]
        elif minutes is None:
            raise PilotError("--minutes is required")
        log(conn, pilot_id, uuid.uuid4(), what, {"minutes": minutes, "note": note}, key)
    click.echo("logged")


@cli.command()
@click.option("--pilot", "pilot_id", help="One pilot; default: every sending or paused pilot")
def check(pilot_id):
    """Stop conditions + pending GoHighLevel do-not-disturb pushes. Schedule
    every 15 minutes while any pilot is running. Exit code 2 if anything paused."""
    from delivery.monitor import check_pilot

    conn = db()
    ids = [pilot_id] if pilot_id else [p for (p,) in conn.execute(
        "select id from pilots where state in ('canary_running', 'live', 'paused')").fetchall()]
    paused_any = False
    for pid in ids:
        click.echo(f"{pid}: {_push_opt_outs_quietly(conn, pid)}")
        breaches = check_pilot(conn, pid)
        if breaches:
            paused_any = True
            click.echo(f"PAUSED {pid}:")
            for b in breaches:
                click.echo(f"  - {b.rule}: {b.detail}")
        else:
            click.echo(f"ok {pid}")
    if paused_any:
        raise SystemExit(2)


@cli.command()
@click.argument("pilot_id")
@click.option("--week", help="ISO week like 2026-W44; default: last week")
def invoice(pilot_id, week):
    from delivery.invoices import build_invoice, last_week, write_invoice_file

    conn = db()
    result = build_invoice(conn, pilot_id, week or last_week())
    path = write_invoice_file(conn, result["invoice_id"])
    click.echo(json.dumps(result))
    click.echo(f"-> {path}")


def purge_pilot(conn, pilot_id: str, run_id) -> dict:
    """Deletes homeowner personal data (names, contact details, message
    bodies) for a pilot that ended more than DATA_RETENTION_DAYS ago; keeps
    anonymous counts. Call inside a transaction."""
    pilot = pilot_row(conn, pilot_id, lock=True)
    ended = conn.execute("select max(created_at) from pilot_events where pilot_id = %s and type = 'state' "
                         "and payload->>'to' in ('completed', 'cancelled')", (pilot_id,)).fetchone()[0]
    if pilot["state"] not in ("completed", "cancelled") or not ended:
        raise PilotError("only completed or cancelled pilots can be purged")
    if datetime.now(timezone.utc) - ended < timedelta(days=DATA_RETENTION_DAYS):
        raise PilotError(f"pilot ended {ended:%Y-%m-%d}; purge after {DATA_RETENTION_DAYS} days unless the installer asks sooner")
    people = conn.execute(
        "update pilot_homeowners set name = null, phone = null, email = null, postcode = left(postcode, 2), "
        "person_key = null, source_record_id = null, raw = '{}'::jsonb, updated_at = now() where pilot_id = %s",
        (pilot_id,)).rowcount
    events = conn.execute(
        "update pilot_events set payload = payload - 'body' - 'note' where pilot_id = %s and (payload ? 'body' or payload ? 'note')",
        (pilot_id,)).rowcount
    log(conn, pilot_id, run_id, "purged", {"homeowners": people, "events": events})
    return {"homeowners": people, "events": events}


@cli.command()
@click.argument("pilot_id")
def purge(pilot_id):
    conn = db()
    with conn.transaction():
        result = purge_pilot(conn, pilot_id, uuid.uuid4())
    click.echo(f"personal data removed: {result}")


@cli.command()
@click.argument("pilot_id")
def status(pilot_id):
    conn = db()
    pilot = pilot_row(conn, pilot_id)
    click.echo(f"{pilot_id}: {pilot['state']}" + (f" (frozen {pilot['frozen_at']:%Y-%m-%d})" if pilot["frozen_at"] else ""))
    for state, n in conn.execute(
        "select state, count(*) from pilot_homeowners where pilot_id = %s group by 1 order by 2 desc", (pilot_id,)
    ).fetchall():
        click.echo(f"  {state:14} {n}")
    for reason, n in conn.execute(
        "select exclusion_reason, count(*) from pilot_homeowners where pilot_id = %s and state = 'excluded' group by 1 order by 2 desc",
        (pilot_id,),
    ).fetchall():
        click.echo(f"    excluded: {reason}: {n}")


if __name__ == "__main__":
    cli()
