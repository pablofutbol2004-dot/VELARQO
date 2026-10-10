"""Run a client pilot, step by step (docs/delivery/WORKFLOW.md).

    python -m delivery.pilot create acme-windows --vertical windows --areas LS,BD
    python -m delivery.pilot approve acme-windows-202611-1 agreement --actor pablo --note "signed v1"
    python -m delivery.pilot advance acme-windows-202611-1 sample_received
    python -m delivery.pilot import  acme-windows-202611-1 clients/acme-windows/full_export.xlsx --dnc clients/acme-windows/dnc.csv
    python -m delivery.pilot freeze  acme-windows-202611-1
    python -m delivery.pilot status  acme-windows-202611-1

Every command logs a pilot_events row with its run_id. Commands check the
pilot's state themselves, so running one at the wrong time does nothing.
"""

import csv
import hashlib
import json
import re
import uuid
from datetime import date
from pathlib import Path

import click
from psycopg.types.json import Jsonb

from client_onboarding.field_mapping.mapper import apply_mapping
from client_onboarding.sample_audit import age_bucket, classify, load, map_columns
from data.supabase_store import connect
from delivery.split import split
from delivery.states import GATES, allowed_pilot_moves
from lib.normalization.normalize import normalize_email, normalize_phone, normalize_postcode

RULES_VERSION = "eligibility-v1"


class PilotError(click.ClickException):
    pass


def log(conn, pilot_id: str, run_id, type_: str, payload: dict, homeowner_key: str | None = None) -> None:
    conn.execute(
        "insert into pilot_events (pilot_id, homeowner_key, run_id, type, payload) values (%s, %s, %s, %s, %s)",
        (pilot_id, homeowner_key, run_id, type_, Jsonb(payload)),
    )


def pilot_row(conn, pilot_id: str, lock: bool = False) -> dict:
    row = conn.execute(
        f"select id, state, holdout_fraction, service_postcode_areas, frozen_at from pilots where id = %s{' for update' if lock else ''}",
        (pilot_id,),
    ).fetchone()
    if not row:
        raise PilotError(f"no pilot {pilot_id}")
    return dict(zip(["id", "state", "holdout_fraction", "areas", "frozen_at"], row))


def homeowner_key(client_slug: str, record: dict) -> str:
    """Stable per person: their own record ID if the export has one, else
    phone/email, else name + postcode + quote date."""
    basis = (
        str(record.get("record_id") or "").strip()
        or normalize_phone(str(record.get("phone") or "")) or normalize_email(str(record.get("email") or ""))
        or "|".join(str(record.get(k) or "").strip().lower() for k in ("name", "postcode", "quote_date"))
    )
    return hashlib.sha256(f"{client_slug}:{basis}".encode()).hexdigest()[:32]


def postcode_area(postcode: str | None) -> str | None:
    match = re.match(r"^([A-Z]{1,2})\d", (postcode or "").upper().strip())
    return match[1] if match else None


def load_dnc(path: Path | None) -> set[str]:
    """Client's do-not-contact list: any file with phone and/or email columns."""
    if not path:
        return set()
    blocked = set()
    with path.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            for value in row.values():
                value = str(value or "")
                blocked |= {v for v in (normalize_email(value), normalize_phone(value)) if v}
    return blocked


def eligibility(record: dict, areas: list[str], dnc: set[str], today: date) -> tuple[str | None, int | None]:
    """(exclusion reason or None, quote age in months)."""
    verdict, age = classify(record, today)
    if verdict != "worth chasing":
        return verdict, age
    phone, email = normalize_phone(str(record.get("phone") or "")), normalize_email(str(record.get("email") or ""))
    if not phone and not email:
        return "no phone or email", age
    if phone in dnc or email in dnc:
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
    conn = connect()
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
    conn = connect()
    with conn.transaction():
        pilot_row(conn, pilot_id)
        conn.execute(
            "insert into pilot_approvals (pilot_id, gate, decision, actor, details) values (%s, %s, %s, %s, %s)",
            (pilot_id, gate, "rejected" if reject else "approved", actor, Jsonb(details)),
        )
        log(conn, pilot_id, uuid.uuid4(), "approval", {"gate": gate, "decision": "rejected" if reject else "approved", "actor": actor})
    click.echo(f"{gate}: {'rejected' if reject else 'approved'} by {actor}")


def advance_pilot(conn, pilot_id: str, to_state: str, run_id) -> None:
    pilot = pilot_row(conn, pilot_id, lock=True)
    if to_state not in allowed_pilot_moves(pilot["state"]):
        raise PilotError(f"{pilot_id} is '{pilot['state']}'; can't move to '{to_state}'")
    gate = GATES.get((pilot["state"], to_state))
    if gate:
        latest = conn.execute(
            "select decision, decided_at from pilot_approvals where pilot_id = %s and gate = %s order by decided_at desc limit 1",
            (pilot_id, gate),
        ).fetchone()
        if not latest or latest[0] != "approved":
            raise PilotError(f"moving to '{to_state}' needs an approved '{gate}' gate (python -m delivery.pilot approve ...)")
        if gate == "resume":
            paused_at = conn.execute(
                "select max(created_at) from pilot_events where pilot_id = %s and type = 'state' and payload->>'to' = 'paused'",
                (pilot_id,),
            ).fetchone()[0]
            if paused_at and latest[1] < paused_at:
                raise PilotError("the 'resume' approval is older than the pause; approve again after reviewing why it paused")
    conn.execute("update pilots set state = %s, updated_at = now() where id = %s", (to_state, pilot_id))
    log(conn, pilot_id, run_id, "state", {"from": pilot["state"], "to": to_state})


@cli.command()
@click.argument("pilot_id")
@click.argument("to_state")
def advance(pilot_id, to_state):
    conn = connect()
    with conn.transaction():
        advance_pilot(conn, pilot_id, to_state, uuid.uuid4())
    click.echo(f"{pilot_id} -> {to_state}")


def import_records(conn, pilot_id: str, records: list[dict], dnc: set[str], run_id, today: date | None = None) -> dict:
    """Insert every row once (re-imports are no-ops) and decide eligibility."""
    today = today or date.today()
    pilot = pilot_row(conn, pilot_id, lock=True)
    if pilot["state"] != "data_received":
        raise PilotError(f"import needs the pilot in 'data_received' (it's '{pilot['state']}')")
    client_slug = conn.execute("select client_slug from pilots where id = %s", (pilot_id,)).fetchone()[0]
    headers = list(dict.fromkeys(k for r in records for k in r))
    mapped = apply_mapping(records, map_columns(headers))
    stats = {"rows": len(mapped), "new": 0, "already_imported": 0, "eligible": 0, "excluded": {}}
    for raw, record in zip(records, mapped):
        key = homeowner_key(client_slug, record)
        reason, age = eligibility(record, pilot["areas"], dnc, today)
        quote_date = record.get("quote_date")
        inserted = conn.execute(
            """insert into pilot_homeowners (pilot_id, homeowner_key, source_record_id, name, phone, email, postcode,
                 quote_date, product, quote_value, quote_status, lead_source, state, exclusion_reason, stratum, raw)
               values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               on conflict (pilot_id, homeowner_key) do nothing returning homeowner_key""",
            (pilot_id, key, str(record.get("record_id") or "") or None, record.get("name"),
             normalize_phone(str(record.get("phone") or "")), normalize_email(str(record.get("email") or "")),
             normalize_postcode(str(record.get("postcode") or "")),
             _iso(quote_date), record.get("product"), _number(record.get("quote_value")), record.get("quote_status"),
             record.get("lead_source"), "excluded" if reason else "eligible", reason, age_bucket(age),
             Jsonb(json.loads(json.dumps(raw, default=str)))),
        ).fetchone()
        if not inserted:
            stats["already_imported"] += 1
            continue
        stats["new"] += 1
        if reason:
            stats["excluded"][reason] = stats["excluded"].get(reason, 0) + 1
        else:
            stats["eligible"] += 1
    log(conn, pilot_id, run_id, "import", {**stats, "rules_version": RULES_VERSION})
    return stats


def _iso(value):
    from client_onboarding.sample_audit import parse_date
    parsed = parse_date(value)
    return parsed.isoformat() if parsed else None


def _number(value):
    try:
        return float(str(value).replace("£", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


@cli.command("import")
@click.argument("pilot_id")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--dnc", type=click.Path(exists=True, path_type=Path), help="Client's do-not-contact list (CSV)")
def import_cmd(pilot_id, path, dnc):
    if "clients" not in path.resolve().parts:
        raise PilotError("client files must live under clients/<slug>/ (git ignores that folder)")
    conn = connect()
    with conn.transaction():
        stats = import_records(conn, pilot_id, load(path), load_dnc(dnc), uuid.uuid4())
    click.echo(json.dumps(stats, indent=2))


def freeze_pilot(conn, pilot_id: str, run_id) -> dict:
    """Split eligible homeowners into treatment and holdout, once, forever."""
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
    conn = connect()
    with conn.transaction():
        counts = freeze_pilot(conn, pilot_id, uuid.uuid4())
    click.echo(f"frozen: {counts['treatment']} to contact, {counts['holdout']} held back for comparison")


@cli.command("send-wave")
@click.argument("pilot_id")
@click.argument("wave")
@click.option("--size", type=int, required=True, help="Homeowners in this wave (canary: 20-30)")
def send_wave_cmd(pilot_id, wave, size):
    """Claims up to SIZE treatment homeowners into WAVE and enrols them in
    GoHighLevel. Safe to re-run: finishes a half-sent wave without resending."""
    import os

    from delivery.ghl_push import claim_wave, send_wave
    from integrations.ghl.client import GHLClient

    conn = connect()
    slug = conn.execute("select client_slug from pilots where id = %s", (pilot_id,)).fetchone()[0]
    env = slug.upper().replace("-", "_")
    token, location = os.environ.get(f"GHL_TOKEN_{env}"), os.environ.get(f"GHL_LOCATION_{env}")
    if not token or not location:
        raise PilotError(f"set GHL_TOKEN_{env} and GHL_LOCATION_{env} in .env (that client's sub-account)")
    wave_id = f"{pilot_id}-{wave}"
    claimed = claim_wave(conn, pilot_id, wave_id, size)
    stats = send_wave(conn, GHLClient(token, location), pilot_id, wave_id, os.environ.get(f"GHL_KEYFIELD_{env}"))
    click.echo(f"{wave_id}: {claimed} newly claimed; {json.dumps(stats)}")


@cli.command()
@click.argument("pilot_id")
def status(pilot_id):
    conn = connect()
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
