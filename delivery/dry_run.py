"""End-to-end pilot dry run with made-up data: the real CLI, the real
database, the real webhook server, and a fake GoHighLevel that only writes
a log. Nothing is texted or emailed; no real GHL is called.

    python -m delivery.dry_run                # slug dryrun-windows
    python -m delivery.dry_run --slug dryrun-roofing --vertical roofing

Walks docs/delivery/README.md pieces 3-12 in order, times every step and
says who does it (Pablo by hand, or the code), then writes
clients/<slug>/dry_run_timings.md. The pilot it creates stays in the
database (state: live) so `pilot status` / `report` can be tried on it;
re-running deletes and rebuilds it. Only slugs starting with "dryrun-" are
accepted, so this can never touch a real pilot.
"""

import json
import os
import shutil
import threading
import time
import urllib.request
from datetime import date, datetime, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

import click
from click.testing import CliRunner

ROOT = Path(__file__).parents[1]
SECRET = "dry-run-webhook-secret-not-for-real-use"


class Step:
    def __init__(self, n, who, what):
        self.n, self.who, self.what = n, who, what
        self.seconds = None
        self.note = ""


class DryRun:
    def __init__(self, slug: str, vertical: str, echo=click.echo):
        if not slug.startswith("dryrun-"):
            raise click.UsageError("slug must start with 'dryrun-' (this deletes and rebuilds the pilot)")
        self.slug, self.vertical, self.echo = slug, vertical, echo
        self.folder = ROOT / "clients" / slug
        self.steps: list[Step] = []
        self.pilot_id = None
        self.location = f"dry-{slug}"
        self.server = None
        self.port = None
        self.booked: list[str] = []

    # ---- plumbing ----
    def step(self, who, what, fn, *args):
        step = Step(len(self.steps) + 1, who, what)
        started = time.perf_counter()
        result = fn(*args)
        step.seconds = time.perf_counter() - started
        if isinstance(result, str):
            step.note = result
        self.steps.append(step)
        self.echo(f"[{step.n:2}] {step.seconds:6.2f}s  {who:6} {what}" + (f"  -> {step.note}" if step.note else ""))
        return result

    def cli(self, *args) -> str:
        from delivery.pilot import cli

        result = CliRunner().invoke(cli, [str(a) for a in args], catch_exceptions=False)
        if result.exit_code != 0:
            raise RuntimeError(f"pilot {' '.join(map(str, args))} failed ({result.exit_code}):\n{result.output}")
        return result.output.strip()

    def conn(self):
        from delivery.pilot import db

        return db()

    def sql(self, query, params=()):
        conn = self.conn()
        try:
            return conn.execute(query, params).fetchall()
        finally:
            conn.close()

    # ---- steps ----
    def clean(self):
        ids = [p for (p,) in self.sql("select id from pilots where client_slug = %s", (self.slug,))]
        conn = self.conn()
        try:
            for pid in ids:
                with conn.transaction():
                    for table in ("invoice_lines", "invoices", "pilot_events", "pilot_approvals", "pilot_homeowners"):
                        conn.execute(f"delete from {table} where pilot_id = %s", (pid,))
                    conn.execute("delete from pilots where id = %s", (pid,))
        finally:
            conn.close()
        if self.folder.exists():
            shutil.rmtree(self.folder)
        return f"removed {len(ids)} old dry-run pilot(s)"

    def fake_export(self):
        from delivery.fake_export import write

        result = write(self.folder)
        return f"{result['rows']} rows in old_quotes.xlsx / .csv + dnc.csv"

    def audit(self):
        from client_onboarding.sample_audit import main

        result = CliRunner().invoke(main, [str(self.folder / "old_quotes.xlsx"), "--company", "Dry Run Windows Ltd"], catch_exceptions=False)
        if result.exit_code != 0:
            raise RuntimeError(result.output)
        return result.output.splitlines()[0]

    def create(self):
        self.pilot_id = self.cli("create", self.slug, "--vertical", self.vertical, "--areas", "LS,BD,HG,WF")
        return self.pilot_id

    def advance(self, to):
        return self.cli("advance", self.pilot_id, to)

    def approve(self, gate, *extra):
        return self.cli("approve", self.pilot_id, gate, "--actor", "Dry Run Windows Ltd (signed sheet)", *extra)

    def import_(self):
        out = self.cli("import", self.pilot_id, self.folder / "old_quotes.xlsx", "--dnc", self.folder / "dnc.csv")
        stats = json.loads(out)
        return f"{stats['rows']} rows, {stats['eligible']} eligible, excluded: {stats['excluded']}"

    def freeze(self):
        return self.cli("freeze", self.pilot_id)

    def settings(self):
        return self.cli("set", self.pilot_id, "--ghl-location", self.location, "--ghl-calendar", "dry-cal-surveys",
                        "--price", "80", "--max-billable", "20", "--max-per-week", "10")

    def approved_messages(self):
        sheet = (ROOT / "docs/delivery/09_message_approval_sheet.md").read_text(encoding="utf-8")
        body = sheet.split("## Sequence")[1].split("## Sign-off")[0]
        path = self.folder / "approved_messages_v1.txt"
        path.write_text("## Sequence" + body, encoding="utf-8")
        return self.approve("messages", "--messages-file", path, "--note", "signed sheet v1 (dry run)")

    def send_wave(self, wave, size):
        return self.cli("send-wave", self.pilot_id, wave, "--size", size)

    def start_webhooks(self):
        from delivery.webhook_server import make_handler, push_opt_outs_after

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.conn, SECRET, push_opt_outs_after))
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        return f"listening on 127.0.0.1:{self.port}/ghl/webhook (shared-secret auth)"

    def post(self, event: dict) -> str:
        event = {"locationId": self.location, "timestamp": datetime.now(timezone.utc).isoformat(), **event}
        request = urllib.request.Request(f"http://127.0.0.1:{self.port}/ghl/webhook", data=json.dumps(event).encode(),
                                         headers={"x-velarqo-secret": SECRET, "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=10) as response:
            return response.read().decode()

    def contacts(self, wave):
        return [c for (c,) in self.sql(
            "select ghl_contact_id from pilot_homeowners where pilot_id = %s and wave_id = %s and state = 'enrolled' order by homeowner_key",
            (self.pilot_id, f"{self.pilot_id}-{wave}"))]

    def inbound(self, contact, body, mid):
        return self.post({"type": "InboundMessage", "contactId": contact, "body": body, "messageId": mid, "direction": "inbound",
                          "webhookId": f"wh-{self.pilot_id}-{mid}"})

    def outbound(self, contact, mid, status="delivered", user=None):
        event = {"type": "OutboundMessage", "contactId": contact, "messageId": mid, "status": status, "webhookId": f"wh-{self.pilot_id}-{mid}"}
        if user:
            event["userId"] = user
        return self.post(event)

    def appointment(self, contact, status, appt_id, n=0, calendar="dry-cal-surveys", start="2026-10-14T10:00:00Z"):
        return self.post({"type": "AppointmentCreate" if n == 0 else "AppointmentUpdate", "webhookId": f"wh-{self.pilot_id}-{appt_id}-{n}",
                          "appointment": {"id": f"{self.pilot_id}-{appt_id}", "contactId": contact, "appointmentStatus": status,
                                          "calendarId": calendar, "startTime": start, "dateUpdated": str(n)}})

    def wave1_events(self):
        c = self.contacts("w1")
        outcomes = []
        for i, contact in enumerate(c):                       # GHL workflow sent text 1 to everyone
            outcomes.append(self.outbound(contact, f"w1-t1-{i}"))
        outcomes.append(self.outbound(c[0], "w1-fail", status="failed"))
        for i, body in enumerate(["Yes still interested, when can you come?", "Yes please", "Maybe, how much is it now?",
                                  "Hi, is this the windows quote? yes still thinking about it", "Who is this?"]):
            outcomes.append(self.inbound(c[1 + i], body, f"w1-r{i}"))
            outcomes.append(self.outbound(c[1 + i], f"w1-a{i}", user="pablo"))        # Pablo answers in GHL
        outcomes.append(self.inbound(c[7], "STOP", "w1-stop"))
        outcomes.append(self.inbound(c[7], "STOP", "w1-stop"))                        # GHL delivered it twice
        outcomes.append(self.inbound(c[8], "Already done it thanks", "w1-done"))
        outcomes.append(self.outbound(c[8], "w1-done-a", user="pablo"))
        self.booked = c[1:4]
        for i, contact in enumerate(self.booked):                                    # 3 surveys booked
            outcomes.append(self.appointment(contact, "confirmed", f"w1-appt-{i}"))
        outcomes.append(self.appointment(c[9], "confirmed", "w1-other-cal", calendar="installers-own-diary"))
        time.sleep(0.5)                                                              # background opt-out push
        from collections import Counter
        return ", ".join(f"{k} x{v}" for k, v in Counter(outcomes).items())

    def check(self):
        from delivery.pilot import cli

        result = CliRunner().invoke(cli, ["check", "--pilot", self.pilot_id], catch_exceptions=False)
        return f"exit {result.exit_code}: " + " | ".join(result.output.strip().splitlines())

    def wave2_events(self):
        c = self.contacts("w2")
        outcomes = []
        for i, contact in enumerate(c):
            outcomes.append(self.outbound(contact, f"w2-t1-{i}"))
        outcomes.append(self.inbound(c[0], "How did you get my number?? I'll report you to the ICO", "w2-c0"))
        outcomes.append(self.inbound(c[1], "wrong number, never asked for a quote", "w2-c1"))
        outcomes.append(self.inbound(c[2], "Please stop texting me", "w2-c2"))
        time.sleep(0.5)
        from collections import Counter
        return ", ".join(f"{k} x{v}" for k, v in Counter(outcomes).items())

    def survey_outcomes(self):
        booked = self.booked
        out = [self.appointment(booked[0], "noshow", "w1-appt-0", n=1),            # homeowner wasn't in
               self.appointment(booked[1], "showed", "w1-appt-1", n=1),
               self.appointment(booked[2], "showed", "w1-appt-2", n=1),
               self.post({"type": "OpportunityStatusUpdate", "contactId": booked[1], "status": "won", "monetaryValue": 4200,
                          "webhookId": f"wh-{self.pilot_id}-won-1"})]
        return ", ".join(out)

    def this_week(self):
        week = date.today().isocalendar()
        return f"{week[0]}-W{week[1]:02d}"

    def invoice(self):
        return self.cli("invoice", self.pilot_id, "--week", self.this_week()).splitlines()[-1]

    def report(self):
        return self.cli("report", self.pilot_id, "--week", self.this_week())

    def status(self):
        return " | ".join(self.cli("status", self.pilot_id).splitlines())

    def ghl_log(self):
        path = self.folder / "ghl_dry_run.jsonl"
        from collections import Counter
        calls = Counter(json.loads(line)["call"] for line in path.read_text(encoding="utf-8").splitlines())
        return "GHL calls that would have happened: " + ", ".join(f"{k} x{v}" for k, v in sorted(calls.items()))

    # ---- the run ----
    def run(self):
        os.environ["GHL_DRY_RUN"] = "1"
        os.environ.setdefault("VELARQO_WEBHOOK_SECRET", SECRET)
        s = self.step
        s("code", "delete any earlier dry run for this slug", self.clean)
        s("client", "installer exports old quotes (here: generated)", self.fake_export)
        s("code", "sample audit -> audit.md (counts only)", self.audit)
        s("Pablo", "send 03 audit result email; 15-min call", lambda: "manual: copy counts from audit.md into the 03 template")
        s("code", "pilot create", self.create)
        s("code", "advance sample_received", self.advance, "sample_received")
        s("code", "advance audited", self.advance, "audited")
        s("Pablo", "installer signs 04 pilot terms + 05 DPA (PDFs); approve agreement", self.approve, "agreement", "--note", "signed 04 v1 + 05 v1 (dry run PDFs)")
        s("code", "advance agreement_signed", self.advance, "agreement_signed")
        s("Pablo", "installer fills 07 intake form; full export + DNC list arrive", lambda: "manual: areas, products, slots, source, DNC list")
        s("code", "advance data_received", self.advance, "data_received")
        s("code", "import full export + do-not-contact list", self.import_)
        s("code", "freeze eligibility + holdout split", self.freeze)
        s("Pablo", "pilot set: GHL location/calendar ids, price, caps (from the signed agreement)", self.settings)
        s("Pablo", "installer ticks + signs 09 message sheet; approve messages --messages-file", self.approved_messages)
        s("code", "advance messages_approved", self.advance, "messages_approved")
        s("Pablo", "build GHL sub-account: snapshot, UK number, workflow (tags vq-<wave>), calendar, webhook", lambda: "manual: 3-5 days (number + domain checks); not covered by this dry run")
        s("code", "advance canary_ready", self.advance, "canary_ready")
        s("Pablo", "test send to own phone + dead number; approve canary_go", self.approve, "canary_go", "--note", "test send to own phone done (dry run)")
        s("code", "advance canary_running", self.advance, "canary_running")
        s("code", "send-wave w1 --size 25 (canary; GHL mocked)", self.send_wave, "w1", 25)
        s("code", "start webhook server (real HTTP, shared secret)", self.start_webhooks)
        s("GHL", "wave 1 webhooks: texts delivered, 1 failed, 5 replies answered, STOP x2 (dup), 3 bookings, 1 on another calendar", self.wave1_events)
        s("code", "pilot check (stop conditions)", self.check)
        s("Pablo", "review canary vs stop conditions; advance canary_reviewed", self.advance, "canary_reviewed")
        s("Pablo", "approve go_live", self.approve, "go_live", "--note", "canary ok: 3 booked, 1 STOP (dry run)")
        s("code", "advance live", self.advance, "live")
        s("code", "send-wave w2 --size 60", self.send_wave, "w2", 60)
        s("GHL", "wave 2 webhooks: texts delivered, ICO complaint, wrong number, 'stop texting me'", self.wave2_events)
        s("code", "pilot check -> expected PAUSED (2+ complaints, ICO)", self.check)
        s("Pablo", "pilot log manual_minutes 45", self.cli, "log", self.pilot_id, "manual_minutes", "--minutes", "45", "--note", "replies + bookings, week 1")
        s("Pablo", "installer reports an opt-out by phone: pilot optout", lambda: self.cli("optout", self.pilot_id, "--phone", self.sql(
            "select phone from pilot_homeowners where pilot_id = %s and state in ('treatment', 'enrolled') and phone is not null "
            "order by state limit 1", (self.pilot_id,))[0][0]))
        s("Pablo", "review the pause; approve resume", self.approve, "resume", "--note", "ICO mention reviewed, wording unchanged, reply answered (dry run)")
        s("code", "advance live (resume)", self.advance, "live")
        s("code", "pilot check after resume -> ok", self.check)
        s("GHL", "survey outcomes: 1 no-show, 2 attended, 1 won GBP 4,200", self.survey_outcomes)
        s("code", "pilot invoice (this week)", self.invoice)
        s("code", "pilot report (this week)", self.report)
        s("code", "pilot status", self.status)
        s("code", "what the fake GHL received", self.ghl_log)
        if self.server:
            self.server.shutdown()
        self.write_timings()

    def write_timings(self):
        total = sum(s.seconds for s in self.steps)
        lines = [f"# Dry run timings: {self.pilot_id} ({datetime.now():%Y-%m-%d %H:%M})", "",
                 "| # | Who | Step | Seconds | Result |", "|---|---|---|---:|---|"]
        lines += [f"| {s.n} | {s.who} | {s.what} | {s.seconds:.2f} | {s.note.replace('|', '/')} |" for s in self.steps]
        lines += ["", f"Code time in total: {total:.1f}s. 'Pablo' rows are manual steps; the seconds there are only the command."]
        (self.folder / "dry_run_timings.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
        self.echo(f"-> {self.folder / 'dry_run_timings.md'}")


@click.command()
@click.option("--slug", default="dryrun-windows", show_default=True)
@click.option("--vertical", default="windows", type=click.Choice(["windows", "roofing", "solar"]), show_default=True)
def main(slug, vertical):
    DryRun(slug, vertical).run()


if __name__ == "__main__":
    main()
