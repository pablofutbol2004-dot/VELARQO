"""Weekly report for the installer (docs/delivery/10_weekly_report_template.md),
filled from the database. Counts of PEOPLE only; no names, no percentages
in the headline. Rows the code can't know (e.g. "interested") are left out
rather than guessed; outcome rows depend on the installer recording them in
GoHighLevel (appointment status, opportunity won).

    python -m delivery.pilot report <pilot_id> [--week 2026-W44]

Writes clients/<slug>/reports/<week>.md. Run `pilot invoice` for the same
week first, so the invoice section has numbers.
"""

from datetime import date, datetime
from pathlib import Path

from delivery.invoices import week_bounds

ROOT = Path(__file__).parents[1]
PERSON = "coalesce(h.person_key, h.homeowner_key)"


def _count_people(conn, pilot_id: str, where: str, params: dict, start: datetime | None, end: datetime) -> int:
    """Distinct people with a matching event before `end` (and after `start` when given)."""
    window = "and e.created_at >= %(start)s " if start else ""
    return conn.execute(
        f"""select count(distinct {PERSON}) from pilot_events e
            join pilot_homeowners h on h.pilot_id = e.pilot_id and h.homeowner_key = e.homeowner_key
            where e.pilot_id = %(p)s and h.arm = 'treatment' and e.created_at < %(end)s {window}and ({where})""",
        {"p": pilot_id, "start": start, "end": end, **params}).fetchone()[0]


ROWS = [
    ("Homeowners contacted", "e.type = 'homeowner_state' and e.payload->>'to' = 'enrolled'"),
    ("Texts that didn't deliver", "e.type = 'delivery_failed'"),
    ("Replied", "e.type = 'homeowner_state' and e.payload->>'to' = 'replied'"),
    ("Surveys booked", "e.type in ('survey_booked', 'direct_booking')"),
    ("Surveys attended", "e.type = 'homeowner_state' and e.payload->>'to' = 'attended'"),
    ("No-shows (homeowner not in)", "e.type = 'survey_not_held' and e.payload->>'reason' = 'noshow'"),
    ("Survey cancelled", "e.type = 'survey_not_held' and e.payload->>'reason' = 'cancelled'"),
    ("Requoted", "e.type = 'homeowner_state' and e.payload->>'to' = 'requoted'"),
    ("Jobs won", "e.type = 'outcome' and e.payload->>'status' = 'won'"),
    ("Opted out (STOP / \"don't contact\")", "e.type = 'homeowner_state' and e.payload->>'to' = 'opted_out'"),
    ("Complaints", "e.type = 'complaint'"),
    ("Wrong person / moved", "e.type = 'wrong_person'"),
]


def report_data(conn, pilot_id: str, iso_week: str, today: date | None = None) -> dict:
    today = today or date.today()
    start, end = week_bounds(iso_week)
    slug, state, holdout_fraction = conn.execute(
        "select client_slug, state, holdout_fraction from pilots where id = %s", (pilot_id,)).fetchone()
    table = []
    for label, where in ROWS:
        table.append((label, _count_people(conn, pilot_id, where, {}, start, end), _count_people(conn, pilot_id, where, {}, None, end)))
    won_value = conn.execute(
        """select coalesce(sum((e.payload->>'value')::numeric) filter (where e.created_at >= %s), 0),
                  coalesce(sum((e.payload->>'value')::numeric), 0)
           from pilot_events e where e.pilot_id = %s and e.type = 'outcome' and e.payload->>'status' = 'won'
             and e.payload->>'value' ~ '^[0-9.]+$' and e.created_at < %s""", (start, pilot_id, end)).fetchone()
    waiting = conn.execute(
        f"""select count(distinct {PERSON}) from pilot_homeowners h
            join pilot_events e on e.pilot_id = h.pilot_id and e.homeowner_key = h.homeowner_key and e.type = 'survey_booked'
            where h.pilot_id = %s and h.state = 'booked' and (e.payload->>'start')::timestamptz < %s""",
        (pilot_id, end)).fetchone()[0]
    arms = dict(conn.execute(
        f"select arm, count(distinct {PERSON}) from pilot_homeowners h where pilot_id = %s and arm is not null group by 1",
        (pilot_id,)).fetchall())
    contacted_total = _count_people(conn, pilot_id, ROWS[0][1], {}, None, end)
    booked_total = _count_people(conn, pilot_id, ROWS[3][1], {}, None, end)
    won_total = _count_people(conn, pilot_id, ROWS[8][1], {}, None, end)
    invoice = conn.execute(
        """select i.id, i.total_gbp,
                  count(*) filter (where l.kind = 'booked' and l.amount_gbp > 0),
                  count(*) filter (where l.kind = 'booked' and l.amount_gbp = 0),
                  count(*) filter (where l.kind = 'no_show_credit'),
                  coalesce(sum(l.amount_gbp) filter (where l.kind = 'no_show_credit'), 0)
           from invoices i left join invoice_lines l on l.invoice_id = i.id
           where i.pilot_id = %s and i.iso_week = %s group by i.id, i.total_gbp""", (pilot_id, iso_week)).fetchone()
    paused = conn.execute(
        "select payload from pilot_events where pilot_id = %s and type = 'stop_condition' and created_at >= %s and created_at < %s "
        "order by created_at desc limit 1", (pilot_id, start, end)).fetchone()
    return {
        "slug": slug, "state": state, "week": iso_week, "start": start.date(), "end": end.date(), "today": today,
        "table": table, "won_value": (float(won_value[0]), float(won_value[1])), "waiting": waiting,
        "treatment": arms.get("treatment", 0), "holdout": arms.get("holdout", 0), "holdout_fraction": float(holdout_fraction),
        "contacted_total": contacted_total, "booked_total": booked_total, "won_total": won_total,
        "invoice": invoice, "paused": paused[0] if paused else None,
    }


def _pct(n: int, of: int) -> str:
    return f"{n} ({n / of:.0%})" if of else f"{n}"


def report_markdown(data: dict) -> str:
    rows = {label: (week, total) for label, week, total in data["table"]}
    contacted, replied, booked = rows["Homeowners contacted"][0], rows["Replied"][0], rows["Surveys booked"][0]
    first = f"**This week:** {contacted} homeowners contacted → {replied} replied → {booked} surveys booked."
    if data["paused"]:
        rules = ", ".join(dict.fromkeys(b["rule"] for b in data["paused"].get("breaches", [])))
        first += f"\nSending was paused this week ({rules}). No new homeowners are messaged until we've agreed what changes."
    elif data["waiting"]:
        first += f"\n{data['waiting']} survey{'s' if data['waiting'] != 1 else ''} need an outcome from you, see below."
    lines = [f"Subject: [Installer] old quotes: week {data['week']} report", "", "Hi [name],", "", first, "",
             "## Where things stand", "", "| | This week | Pilot so far |", "|---|---:|---:|"]
    lines += [f"| {label} | {week} | {total} |" for label, week, total in data["table"]]
    lines.insert(lines.index(f"| Jobs won | {rows['Jobs won'][0]} | {rows['Jobs won'][1]} |") + 1,
                 f"| Value of jobs won | £{data['won_value'][0]:,.0f} | £{data['won_value'][1]:,.0f} |")
    lines += [""]
    if data["waiting"]:
        lines += [f"Waiting for your outcome: {data['waiting']} survey{'s' if data['waiting'] != 1 else ''} already past their date. "
                  "Please mark attended / no-show / requoted / won and the job value in the booking calendar.", ""]
    lines += ["## Compared with the quotes we left alone", "",
              "| | Contacted group | Left-alone group |", "|---|---:|---:|",
              f"| Number of homeowners | {data['contacted_total']} | {data['holdout']} |",
              f"| Booked a survey | {_pct(data['booked_total'], data['contacted_total'])} | not recorded yet |",
              f"| Won a job | {_pct(data['won_total'], data['contacted_total'])} | not recorded yet |", "",
              f"The left-alone group is a random {data['holdout_fraction']:.0%} of the eligible quotes we never contacted "
              f"({data['holdout']} people). For them, \"booked\" or \"won\" means they came back to you on their own; "
              "please tell us when that happens, we have no other way of knowing.", "",
              "**Small numbers warning:** with this few homeowners, a difference of one or two bookings can be luck. "
              "Treat this as an early sign, not proof, until the pilot ends.", "", "## Invoice", ""]
    if data["invoice"]:
        _, total, charged, free, credits, credit_total = data["invoice"]
        lines += ["| | Number | Amount |", "|---|---:|---:|",
                  f"| Surveys booked, charged | {charged} | £{float(total) - float(credit_total):,.2f} |",
                  f"| Surveys booked, free / over cap | {free} | £0.00 |",
                  f"| No-show credits | {credits} | £{float(credit_total):,.2f} |",
                  f"| **Total due** [VAT wording to confirm] | | **£{float(total):,.2f}** |", "",
                  "Payment due by [date]. Each line is listed with booking date and time on the invoice, so you can check it against your diary."]
    else:
        lines += ["No invoice for this week yet (run `pilot invoice` first)."]
    lines += ["", "## Next week", "", "- [Send batch n: [n] homeowners / nothing new while paused.]",
              "- [Change: none / what changed and why.]",
              f"- [Need from you: outcomes for {data['waiting']} surveys; new survey slots.]", "", "Pablo", "Velarqo, velarqo.com", "",
              f"_Generated from the database on {data['today']:%d %b %Y} for week {data['week']} ({data['start']:%d %b} to {data['end'] - date.resolution:%d %b}). "
              "Counts are people, not quote rows. Pilot state: " + data["state"] + "._", ""]
    return "\n".join(lines)


def write_report(conn, pilot_id: str, iso_week: str, today: date | None = None) -> Path:
    data = report_data(conn, pilot_id, iso_week, today)
    out = ROOT / "clients" / data["slug"] / "reports"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"{iso_week}.md"
    path.write_text(report_markdown(data), encoding="utf-8")
    return path
