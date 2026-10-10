"""The pilot dry run (docs/delivery/DRY_RUN_2026-10.md): fake export, fake
GoHighLevel, weekly report, and the whole path end to end. Pure tests always
run; database tests need VELARQO_DB_TESTS=1 and clean up after themselves."""

import json
import os
from datetime import date, datetime, timedelta, timezone

import pytest

from client_onboarding.sample_audit import audit, classify, map_columns, parse_date
from delivery.fake_export import dnc_rows, rows, write
from delivery.ghl_push import split_name
from integrations.ghl.dry_run import DryRunGHL, DryRunRefused
from tests.integration.pilot_fixtures import DB, TODAY, autocommit, cleanup, pilot

pytestmark = []


# ---------- pure ----------

def test_fake_export_is_deterministic_messy_and_has_the_traps():
    a, b = rows(seed=7, n=100, today=TODAY), rows(seed=7, n=100, today=TODAY)
    assert a == b and len(a) == 100 + 12 + 3
    assert a[-1]["Customer"] == "TOTAL" and all(v == "" for v in a[-2].values())
    phones = [r["Tel"] for r in a if r["Tel"]]
    assert any(isinstance(p, int) for p in phones)                      # Excel-mangled number
    assert any("0113" in str(p) for p in phones)                        # a landline
    assert any(r["Source"] in ("Checkatrade", "Bark", "Bought leads") for r in a)
    assert any(r["Opt out"] in ("Y", "yes", "DO NOT CONTACT") for r in a)
    assert any(r["Customer"].count(",") == 1 for r in a[:100])          # "Last, First"
    assert len({r["Quote No"] for r in a[:112]}) == 112 and a[112] in a[:100]   # exact duplicate row
    dnc = dnc_rows(a, seed=7)
    assert len(dnc) >= 3 and any(d["Email"] == "nobody.here@example.com" for d in dnc)


def test_fake_export_writes_xlsx_csv_and_dnc(tmp_path):
    result = write(tmp_path / "clients" / "x", seed=1, n=20, today=TODAY)
    assert result["rows"] == 35
    for name in ("old_quotes.xlsx", "old_quotes.csv", "dnc.csv"):
        assert (tmp_path / "clients" / "x" / name).exists()
    from client_onboarding.sample_audit import load

    assert len(load(result["xlsx"])) == 35 and len(load(result["csv"])) == 35


def test_audit_maps_installer_style_headers_and_ages_every_row():
    mapping = map_columns(["Quote No", "Date Quoted", "Customer", "Tel", "Job", "Quote £", "Status", "Source", "Opt out"])
    assert mapping["Customer"] == "name" and mapping["Quote £"] == "quote_value" and mapping["Job"] == "product"
    assert mapping["Quote No"] == "record_id" and mapping["Date Quoted"] == "quote_date"
    # a won quote still has an age (the audit's age table was showing them as "unknown date")
    assert classify({"quote_status": "Sold", "quote_date": "01/05/2026"}, TODAY) == ("already won/booked", 5)
    assert classify({"quote_status": "Lost", "quote_date": "TBC"}, TODAY) == ("no usable date", None)
    result = audit([{"Customer": "Jo Bloggs", "Quote £": "£3,450", "Date Quoted": "01/05/2026", "Status": "Lost"}], TODAY)
    assert result["chase_values"] == [3450.0] and result["unmapped"] == []


def test_dates_in_the_shapes_installers_use():
    assert parse_date("12/03/2026") == date(2026, 3, 12)
    assert parse_date("2026-03-12") == date(2026, 3, 12)
    assert parse_date("12 Mar 26") == date(2026, 3, 12)
    assert parse_date("12.03.26") == date(2026, 3, 12)
    assert parse_date(46093) == date(2026, 3, 12)                       # Excel serial in a CSV
    assert parse_date(46093.0) == date(2026, 3, 12)
    assert parse_date("TBC") is None and parse_date("?") is None and parse_date(12.5) is None


@pytest.mark.parametrize("name,expected", [
    ("Gary Johnson", ("Gary", "Johnson")), ("Johnson, Gary", ("Gary", "Johnson")), ("  Sarah   Smith ", ("Sarah", "Smith")),
    ("Mr G Johnson", ("G", "Johnson")), ("Mrs. Patel", ("Patel", None)), ("Jo", ("Jo", None)), ("", (None, None)), (None, (None, None)),
    ("Smith, Ann Marie", ("Ann Marie", "Smith")),
])
def test_first_name_is_what_the_homeowner_will_read(name, expected):
    assert split_name(name) == expected


def test_dry_run_ghl_logs_calls_and_refuses_real_looking_locations(tmp_path):
    with pytest.raises(DryRunRefused):
        DryRunGHL(tmp_path / "log.jsonl", "abc123realLocation")
    ghl = DryRunGHL(tmp_path / "log.jsonl", "dry-test")
    contact_id = ghl.upsert_contact({"phone": "+447700900123", "firstName": "Ann"})["contact"]["id"]
    assert contact_id.startswith("dry-")
    assert ghl.upsert_contact({"phone": "+447700900123"})["contact"]["id"] == contact_id      # same person, same id
    ghl.add_tags(contact_id, ["vq-w1"])
    ghl.set_dnd(contact_id)
    ghl.remove_tags(contact_id, ["vq-w1"])
    calls = [json.loads(line)["call"] for line in (tmp_path / "log.jsonl").read_text().splitlines()]
    assert calls == ["upsert_contact", "upsert_contact", "add_tags", "set_dnd", "remove_tags"]


# ---------- database ----------

@DB
def test_ghl_client_for_uses_the_fake_only_in_dry_run_mode_and_only_for_dry_locations(monkeypatch):
    from delivery.pilot import PilotError, ghl_client_for

    monkeypatch.setenv("GHL_DRY_RUN", "1")
    with pilot(5, ghl_location_id="dry-loc-test") as (conn, pilot_id, _, _):
        client, key_field = ghl_client_for(conn, pilot_id)
        assert isinstance(client, DryRunGHL) and key_field is None
    with pilot(5) as (conn, pilot_id, _, _):                             # location 'loc-test-...': looks real
        with pytest.raises(PilotError, match="dry-"):
            ghl_client_for(conn, pilot_id)
    monkeypatch.delenv("GHL_DRY_RUN")
    monkeypatch.delenv("GHL_TOKEN_TEST", raising=False)
    with pilot(5, ghl_location_id="dry-loc-test") as (conn, pilot_id, _, _):
        with pytest.raises(PilotError, match="GHL_TOKEN_TEST"):          # without the flag: the real client, needs a token
            ghl_client_for(conn, pilot_id)


@DB
def test_weekly_report_counts_people_and_fills_the_invoice_section():
    from delivery.invoices import build_invoice
    from delivery.report import report_data, report_markdown, write_report
    from delivery.webhooks import handle_event

    now = datetime.now(timezone.utc)
    year, week, _ = now.date().isocalendar()
    this_week = f"{year}-W{week:02d}"
    with pilot(30, wave_size=24, price_per_booked_gbp=80) as (conn, pilot_id, loc, contacts):
        inbound = lambda c, body, mid: {"type": "InboundMessage", "locationId": loc, "contactId": c, "body": body, "messageId": mid}
        appt = lambda c, status, n: {"type": "AppointmentCreate" if n == 0 else "AppointmentUpdate", "locationId": loc,
                                     "appointment": {"id": f"a-{c}", "contactId": c, "appointmentStatus": status, "calendarId": "cal-1",
                                                     "startTime": (now - timedelta(days=1)).isoformat(), "dateUpdated": str(n)}}
        handle_event(conn, inbound(contacts[0], "yes please", "m0"))
        handle_event(conn, inbound(contacts[1], "STOP", "m1"))
        handle_event(conn, inbound(contacts[2], "how did you get my number", "m2"))
        handle_event(conn, appt(contacts[0], "confirmed", 0))
        handle_event(conn, appt(contacts[3], "confirmed", 0))
        handle_event(conn, appt(contacts[3], "noshow", 1))
        handle_event(conn, appt(contacts[4], "confirmed", 0))                 # survey yesterday, no outcome yet
        handle_event(conn, {"type": "OpportunityStatusUpdate", "locationId": loc, "contactId": contacts[0], "status": "won", "monetaryValue": 5000})
        build_invoice(conn, pilot_id, this_week)
        data = report_data(conn, pilot_id, this_week)
        table = {label: (week_n, total) for label, week_n, total in data["table"]}
        assert table["Replied"] == (1, 1) and table["Surveys booked"] == (3, 3) and table["Jobs won"] == (1, 1)
        assert table["Opted out (STOP / \"don't contact\")"] == (2, 2) and table["Complaints"] == (1, 1)
        assert table["No-shows (homeowner not in)"] == (1, 1) and data["won_value"] == (5000.0, 5000.0)
        assert data["waiting"] == 1                                       # contacts[4]; the won and no-show ones aren't waiting
        assert data["holdout"] == 6 and data["contacted_total"] == 0      # fixture sets 'enrolled' directly, without events
        assert data["invoice"][1] == 160                                  # 3 charged, 1 credited
        text = report_markdown(data)
        assert "| Jobs won | 1 | 1 |" in text and "£5,000" in text and "**£160.00**" in text and "1 survey need" in text
        assert "07700" not in text and "Ann" not in text
        path = write_report(conn, pilot_id, this_week)
        assert path.name == f"{this_week}.md" and "clients" in path.parts


@DB
def test_the_whole_pilot_path_runs_end_to_end_on_fake_data(monkeypatch):
    """The dry run itself: fake export -> audit -> pilot -> import -> freeze ->
    approvals -> waves to the fake GHL -> real webhook server -> pause ->
    resume -> invoice -> report. About 30 seconds."""
    from delivery.dry_run import DryRun

    monkeypatch.delenv("GHL_TOKEN_DRYRUN_TEST", raising=False)
    run = DryRun("dryrun-test", "windows", echo=lambda *_: None)
    try:
        run.run()
        assert len(run.steps) == 40 and all(s.seconds is not None for s in run.steps)
        notes = {s.what: s.note for s in run.steps}
        assert "PAUSED" in notes["pilot check -> expected PAUSED (2+ complaints, ICO)"]
        assert notes["pilot check after resume -> ok"].startswith("exit 0")
        assert (run.folder / "audit.md").exists() and (run.folder / "dry_run_timings.md").exists()
        assert list((run.folder / "invoices").glob("VQ-*.md")) and list((run.folder / "reports").glob("*-W*.md"))
        conn = autocommit()
        try:
            state = conn.execute("select state from pilots where id = %s", (run.pilot_id,)).fetchone()[0]
            assert state == "live"
            counts = dict(conn.execute("select state, count(*) from pilot_homeowners where pilot_id = %s group by 1", (run.pilot_id,)).fetchall())
            assert counts["holdout"] > 0 and counts["opted_out"] >= 4 and counts.get("won") == 1
            # every opted-out person GHL knows about got a do-not-disturb (a second quote row of the same person has no contact)
            with_contact = conn.execute("select count(*) from pilot_homeowners where pilot_id = %s and state = 'opted_out' "
                                        "and ghl_contact_id is not null", (run.pilot_id,)).fetchone()[0]
            assert conn.execute("select count(*) from pilot_homeowners where pilot_id = %s and arm = 'holdout' and wave_id is not null",
                                (run.pilot_id,)).fetchone()[0] == 0
        finally:
            conn.close()
        calls = [json.loads(line)["call"] for line in (run.folder / "ghl_dry_run.jsonl").read_text().splitlines()]
        assert calls.count("set_dnd") == with_contact >= 4 and "add_tags" in calls
    finally:
        if run.pilot_id:
            cleanup(run.pilot_id)
        import shutil

        shutil.rmtree(run.folder, ignore_errors=True)
        os.environ.pop("GHL_DRY_RUN", None)
