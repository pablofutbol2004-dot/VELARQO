"""Velarqo's own cold outreach, run from the command line.

    python -m pipelines.outbound status
    python -m pipelines.outbound create-cohort --size 25 --name "Batch 1"
    python -m pipelines.outbound review <campaign_id>        # CSV to read before activating
    python -m pipelines.outbound cancel <message_id>         # drop one email from a batch
    python -m pipelines.outbound activate <campaign_id>
    python -m pipelines.outbound sending on                  # global kill switch (starts off)
    python -m pipelines.outbound run                         # one tick: inbox, follow-ups, send
    python -m pipelines.outbound run --dry-run               # same, fake mailbox, rolled back
    python -m pipelines.outbound replies                     # replies a human must answer
    python -m pipelines.outbound call-sheet info@acme.co.uk  # before a call: history + price to quote
    python -m pipelines.outbound outcome info@acme.co.uk call_held --reaction ok
    python -m pipelines.outbound results cold_offer_v1       # how a test is going, in plain English

Mailboxes live in config/mailboxes.json (see mailboxes.example.json);
their OAuth tokens live in .env (authorize-mailbox writes them).
"""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import click

from data.supabase_store import connect, icp_version
from integrations.email.gmail import GmailProvider
from integrations.email.google_auth import access_token_for, authorize_mailbox
from outreach.reply_classifier.classify import strip_quoted
from outreach.send_engine import compose, engine, experiments

ROOT = Path(__file__).parents[2]
ICP_PATH = ROOT / "config" / "templates" / "icp-template.json"
MAILBOXES_PATH = ROOT / "config" / "mailboxes.json"
DEFAULT_EXPERIMENT = "cold_offer_v1"
DEFAULT_PRICING = "pricing_p1"


def _conn():
    conn = connect()
    conn.autocommit = True
    return conn


def _icp() -> dict:
    return json.loads(ICP_PATH.read_text())


def _mailboxes() -> list[dict]:
    if not MAILBOXES_PATH.exists():
        raise click.ClickException(
            f"{MAILBOXES_PATH} not found. Copy config/mailboxes.example.json and list your sending mailboxes."
        )
    return [m for m in json.loads(MAILBOXES_PATH.read_text()) if m.get("enabled", True)]


def _provider(mailbox: dict):
    if mailbox.get("provider", "gmail") != "gmail":
        raise click.ClickException(f"{mailbox['email']}: only gmail mailboxes are supported for now")
    provider = GmailProvider(access_token=access_token_for(mailbox["email"]), sender_email=mailbox["email"])
    actual = provider.profile_email()
    if actual != mailbox["email"].lower():
        raise click.ClickException(f"token for {mailbox['email']} belongs to {actual}; re-run authorize-mailbox")
    return provider


class FakeMailbox:
    """Stands in for Gmail on --dry-run: records sends, has an empty inbox."""

    def __init__(self, email: str):
        self.email, self.sent = email, []

    def send_email(self, to, subject, body, thread_id=None, in_reply_to_message_id=None):
        self.sent.append({"to": to, "subject": subject, "body": body})
        n = len(self.sent)
        return {"message_id": f"dry-{n}", "thread_id": thread_id or f"dry-thread-{n}"}

    def list_inbox(self, query):
        return []


@click.group()
def cli():
    """Velarqo outbound: cohorts, sending, follow-ups, replies."""


@cli.command()
def status():
    """Kill switch, campaigns, today's sends, replies waiting."""
    s = engine.status(_conn())
    c = s["controls"]
    click.echo(f"Sending: {'ON' if c['sending_enabled'] else 'OFF'}"
               + (f"  (paused: {c['paused_reason']})" if c["paused_reason"] else ""))
    for cp in s["campaigns"]:
        click.echo(f"  {cp['id']}  {cp['name'][:28]:28} {cp['status']:7} queued {cp['queued']:4} sent {cp['sent']:4} "
                   f"replied {cp['replied']:3} bounced {cp['bounced']:3} skipped {cp['skipped']:3} failed {cp['failed']:3}"
                   + (f"  STUCK SENDING {cp['stuck_sending']}" if cp["stuck_sending"] else ""))
    for row in s["sent_today"]:
        click.echo(f"  sent today from {row['mailbox']}: {row['n']}")
    click.echo(f"Replies needing you: {s['replies']['needs_human']} (of {s['replies']['total']} total)")
    problems = engine.recent_problems(_conn())
    if problems:
        click.echo("PROBLEMS in the last 24h (a mailbox with a problem doesn't send):")
        for p in problems:
            click.echo(f"  {p['created_at']:%a %H:%M} {p['mailbox']}: {p['problem'][:160]}")


@cli.command("create-cohort")
@click.option("--size", default=25, show_default=True, help="How many companies to put in this batch")
@click.option("--name", default=None, help="Campaign name (defaults to today's date)")
@click.option("--experiment", default=DEFAULT_EXPERIMENT, show_default=True, help="config/experiments/<name>.json")
def create_cohort(size, name, experiment):
    """Pick the best unsent installers and draft their first emails (nothing is sent)."""
    icp = _icp()
    exp = experiments.load(experiment)
    if exp.get("status") == "waiting":
        raise click.ClickException(f"{exp['name']} is waiting: {exp['decision_rule']}")
    name = name or f"Windows {datetime.now():%Y-%m-%d} {exp['name']}"
    result = engine.create_cohort(_conn(), name, size, exp, icp, icp_version(icp))
    if not result["campaign_id"]:
        raise click.ClickException("No eligible companies left in outreach_queue")
    click.echo(f"Drafted campaign {result['campaign_id']} with {result['messages']} emails.")
    click.echo(f"Next: python -m pipelines.outbound review {result['campaign_id']}")


@cli.command()
@click.argument("campaign_id")
@click.option("--out", type=click.Path(path_type=Path), default=None)
def review(campaign_id, out):
    """Write every email in a campaign to a CSV for reading before activation."""
    rows = engine.review_rows(_conn(), campaign_id)
    out = out or ROOT / "data" / f"review_{campaign_id[:8]}.csv"
    with out.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=[*rows[0].keys(), "words"] if rows else ["message_id"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "words": compose.word_count(row["body"], row["display_name"])})
    click.echo(f"{len(rows)} emails written to {out}")
    for row in rows[:2]:
        click.echo(f"\n--- {row['display_name']} <{row['to_email']}> ---\nSubject: {row['subject']}\n\n{row['body']}")


@cli.command()
@click.argument("message_id")
@click.option("--reason", default="removed at review")
def cancel(message_id, reason):
    """Remove one queued email (e.g. wrong company) from its campaign."""
    ok = engine.cancel_message(_conn(), message_id, reason)
    click.echo("Cancelled." if ok else "Not cancelled (not found or no longer queued).")


@cli.command()
@click.argument("campaign_id")
def activate(campaign_id):
    """Allow a reviewed campaign to send (still needs `sending on`)."""
    engine.set_campaign_status(_conn(), campaign_id, "active")
    click.echo("Campaign active.")


@cli.command()
@click.argument("campaign_id")
def pause(campaign_id):
    """Stop one campaign sending; follow-ups wait until re-activated."""
    engine.set_campaign_status(_conn(), campaign_id, "paused")
    click.echo("Campaign paused.")


@cli.command()
@click.argument("campaign_id")
def finish(campaign_id):
    """Close a campaign and cancel anything still queued in it."""
    engine.set_campaign_status(_conn(), campaign_id, "done")
    click.echo("Campaign done.")


@cli.command()
@click.argument("state", type=click.Choice(["on", "off"]))
@click.option("--reason", default="paused manually")
def sending(state, reason):
    """Global kill switch for all sending."""
    engine.set_sending(_conn(), state == "on", reason)
    click.echo(f"Sending {state.upper()}.")


@cli.command()
@click.option("--dry-run", is_flag=True, help="Fake mailbox, ignore kill switch/send window, include draft campaigns, roll back")
@click.option("--max-per-mailbox", default=2, show_default=True, help="Max emails per mailbox in this tick (2 x ~34 ticks a day covers a 20-30 cap and keeps ticks short)")
def run(dry_run, max_per_mailbox):
    """One tick: read replies/bounces, queue due follow-ups, check stop rules, send due emails."""
    conn = _conn()
    if dry_run and not MAILBOXES_PATH.exists():
        mailboxes = [{"email": "dry-run@example.invalid", "daily_cap": 25}]
    else:
        mailboxes = _mailboxes()

    fakes = {m["email"]: FakeMailbox(m["email"]) for m in mailboxes} if dry_run else {}

    def provider_for(m):
        # Built just before use: a fresh access token per mailbox, so a long
        # tick never sends with a token that expired mid-way.
        return fakes[m["email"]] if dry_run else _provider(m)

    def tick():
        report, synced = {}, set()
        for m in mailboxes:
            try:
                report[f"inbox {m['email']}"] = engine.sync_inbox(conn, provider_for(m), m["email"])
                synced.add(m["email"])
            except Exception as exc:  # noqa: BLE001 - one broken mailbox must not stop the others
                report[f"inbox {m['email']}"] = f"ERROR {type(exc).__name__}: {str(exc)[:200]} (not sending from it this tick)"
                engine.note_problem(conn, m["email"], f"inbox sync failed: {type(exc).__name__}: {str(exc)[:300]}")
        statuses = ("draft", "active") if dry_run else ("active",)
        report["follow-ups queued"] = engine.schedule_followups(conn, campaign_statuses=statuses)
        report["stop rule"] = engine.check_stop_rules(conn)
        for m in mailboxes:
            if m["email"] not in synced:
                continue                     # unread replies might include a "stop": don't send blind
            try:
                report[f"send {m['email']}"] = engine.send_due(
                    conn, provider_for(m), m["email"], m.get("daily_cap", 20), max_per_mailbox,
                    require_enabled=not dry_run, respect_window=not dry_run, campaign_statuses=statuses,
                    pause_seconds=(0, 0) if dry_run else (45, 120),
                )
            except Exception as exc:  # noqa: BLE001
                report[f"send {m['email']}"] = f"ERROR {type(exc).__name__}: {str(exc)[:200]}"
                engine.note_problem(conn, m["email"], f"sending failed: {type(exc).__name__}: {str(exc)[:300]}")
        if dry_run:
            for provider in fakes.values():
                for sent in provider.sent[:3]:
                    click.echo(f"\n[dry run] to {sent['to']}\nSubject: {sent['subject']}\n\n{sent['body']}")
        return report

    if dry_run:
        report = engine.dry_run(conn, tick)
    else:
        # One tick at a time: an overlapping manual run would get a second
        # daily budget per mailbox.
        if not conn.execute("select pg_try_advisory_lock(hashtext('outbound-tick'))").fetchone()[0]:
            click.echo(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} another tick is running; skipped")
            return
        try:
            report = tick()
        finally:
            conn.execute("select pg_advisory_unlock(hashtext('outbound-tick'))")
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    click.echo(f"{stamp} {'DRY RUN (rolled back) ' if dry_run else ''}{json.dumps(report, default=str)}")


@cli.command()
def replies():
    """Replies waiting for you (positive, unclear, complaints, unmatched)."""
    rows = engine.open_replies(_conn())
    if not rows:
        click.echo("Nothing waiting.")
    for r in rows:
        click.echo(f"\n[{r['category']}] {r['received_at']:%a %d %b %H:%M}  {r['display_name'] or '(unmatched)'} "
                   f"<{r['from_email']}>  {r['phone'] or ''}\n  id {r['id']}\n  Subject: {r['subject']}\n  "
                   + strip_quoted(r["body"])[:600].replace("\n", "\n  "))


@cli.command()
@click.argument("reply_id")
@click.option("--as", "category", type=click.Choice(["positive", "unknown", "not_interested", "unsubscribe",
                                                     "complaint", "out_of_office", "bounce"]),
              default=None, help="Correct the automatic category (results use your label)")
def handled(reply_id, category):
    """Mark a reply as dealt with (optionally correcting its category)."""
    engine.mark_handled(_conn(), reply_id, category)
    click.echo("Marked handled.")


def _company_or_fail(conn, ref):
    company = engine.find_company(conn, ref)
    if not company:
        raise click.ClickException(f"No company found for {ref}")
    return company


@cli.command("call-sheet")
@click.argument("ref")
@click.option("--pricing", default=DEFAULT_PRICING, show_default=True)
def call_sheet(ref, pricing):
    """Before a call: who they are, what they were sent and said, and the price to quote."""
    conn = _conn()
    c = _company_or_fail(conn, ref)
    history = engine.company_history(conn, c["id"])
    exp = experiments.load(pricing)
    arm = experiments.assigned_arm(exp, str(c["id"]))
    click.echo(f"{c['display_name']}  ({c['legal_name'] or ''}, {c['company_category'] or '?'})")
    click.echo(f"  {c['city'] or ''} {c['postcode'] or ''}  web {c['website'] or '-'}  phone {c['phone'] or '-'}")
    click.echo(f"  Companies House {c['company_number'] or '-'}, incorporated {c['incorporation_date'] or '?'}")
    for m in history["messages"]:
        click.echo(f"  sent step {m['sequence_step']} ({m['status']}) {m['sent_at'] or ''}: {m['subject']}")
    for r in history["replies"]:
        click.echo(f"  reply [{r['category']}] {r['received_at']:%d %b}: {strip_quoted(r['body'])[:300]}")
    for e in history["events"]:
        click.echo(f"  {e['occurred_at']:%d %b} {e['type']} {e['payload'] or ''}")
    click.echo(f"\nPRICE TO QUOTE ({exp['name']} arm '{arm['key']}'): GBP {arm['price_gbp']} per qualified booked survey")
    for term in exp.get("terms_for_every_arm", []):
        click.echo(f"  - {term}")
    click.echo("Ask the willingness questions in docs/PRICING.md BEFORE saying the price.")


@cli.command()
@click.argument("ref")
@click.argument("stage", type=click.Choice(engine.FUNNEL_STAGES))
@click.option("--reaction", type=click.Choice(["ok", "hesitant", "objected", "not_asked"]), default=None,
              help="For call_held: how they reacted to the price")
@click.option("--note", default=None)
@click.option("--pricing", default=DEFAULT_PRICING, show_default=True)
def outcome(ref, stage, reaction, note, pricing):
    """Record a funnel step for a company: call_booked, call_held, sample_received, pilot_signed, lost."""
    conn = _conn()
    c = _company_or_fail(conn, ref)
    payload = {"note": note} if note else {}
    if stage == "call_held":
        exp = experiments.load(pricing)
        arm = experiments.assigned_arm(exp, str(c["id"]))
        payload.update(pricing_experiment=exp["name"], price_arm=arm["key"], price_gbp=arm["price_gbp"],
                       price_reaction=reaction or "not_asked")
    engine.log_outcome(conn, c["id"], stage, payload)
    click.echo(f"Logged {stage} for {c['display_name']}.")


@cli.command()
@click.argument("experiment")
def results(experiment):
    """How a test is going: funnel per arm, confidence, and what to do."""
    exp = experiments.load(experiment)
    conn = _conn()
    click.echo(f"{exp['name']}: {exp['hypothesis']}\n")
    if exp["stage"] == "sales_call":
        for r in engine.pricing_results(conn, exp["name"]):
            click.echo(f"  {r['arm']:6} calls {r['calls']:3}  price objections {r['price_objections']:3}  "
                       f"samples {r['samples']:3}  pilots {r['pilots']:3}")
        click.echo(f"\nRule: {exp['decision_rule']}")
        return
    rows = engine.cold_email_results(conn, exp["name"])
    if not rows:
        click.echo("No emails sent in this experiment yet.")
        return
    for r in rows:
        r["arm"] = exp["arms"][r["variant_index"]]["key"]
        low, high = experiments.wilson_interval(r["positive"], r["sent"])
        click.echo(f"  {r['arm']:24} sent {r['sent']:4}  replied {r['replied']:3}  positive {r['positive']:3} "
                   f"({r['positive'] / max(r['sent'], 1):.1%}, likely {low:.1%}-{high:.1%})  calls {r['calls']:2}  "
                   f"samples {r['samples']:2}  pilots {r['pilots']:2}  bounced {r['bounced']:3}  opt-outs {r['opted_out']:3}")
    click.echo("\n" + experiments.verdict(exp, rows))


@cli.command("suppress")
@click.argument("address")
@click.option("--reason", type=click.Choice(["unsubscribed", "bounced", "complained", "dnd", "manual"]), default="manual")
def suppress_cmd(address, reason):
    """Never email this address (or @domain) again."""
    conn = _conn()
    with conn.transaction(), conn.cursor() as cur:
        if address.startswith("@"):
            cur.execute("insert into suppressions (domain, reason, source) values (lower(%s), %s, 'cli') "
                        "on conflict do nothing", (address[1:], reason))
        else:
            engine.suppress(cur, address, reason, "cli")
    click.echo(f"Suppressed {address}.")


@cli.command("authorize-mailbox")
@click.argument("email")
def authorize(email):
    """One-time Google sign-in for a sending mailbox; stores its token in .env."""
    authorize_mailbox(email)


@cli.command("test-send")
@click.argument("to")
@click.option("--mailbox", required=True, help="Sending mailbox from config/mailboxes.json")
def test_send(to, mailbox):
    """Send one sample first email to yourself through a real mailbox (no database writes)."""
    config = next((m for m in _mailboxes() if m["email"] == mailbox), None)
    if not config:
        raise click.ClickException(f"{mailbox} is not in config/mailboxes.json")
    sample = {"id": "test", "display_name": "Example Windows Ltd", "email": to, "city": "Leeds",
              "extra": {"website_signals": ["free quotes"], "accreditations": ["FENSA registered"]}}
    email = compose.first_touch(sample, experiments.load(DEFAULT_EXPERIMENT), 0)
    result = _provider(config).send_email(to=to, subject=f"[TEST] {email['subject']}", body=email["body"])
    click.echo(f"Sent test email, Gmail id {result['message_id']}")


if __name__ == "__main__":
    cli()
