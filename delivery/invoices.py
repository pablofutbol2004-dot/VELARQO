"""Weekly invoice per pilot (WORKFLOW.md section 4, steps 9-10; pricing P1).

- One charge per homeowner whose survey got booked (rebooking the same
  homeowner doesn't charge again).
- A booked homeowner whose survey didn't happen (no-show or cancelled) and
  who hasn't attended since is credited once, on the next invoice. Known
  limit: if they're credited and attend a rebooked survey later, they are
  not re-charged automatically (rare; fix by hand).
- One invoice per (pilot, ISO week): re-running for the same week returns
  the existing invoice; lines are unique, so nothing is billed twice.
- The price comes from the signed agreement (pilots.price_per_booked_gbp).
  No price, no invoice.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
ROOT = Path(__file__).parents[1]


class InvoiceError(Exception):
    pass


def week_bounds(iso_week: str) -> tuple[datetime, datetime]:
    year, week = iso_week.split("-W")
    start = date.fromisocalendar(int(year), int(week), 1)
    return (datetime.combine(start, datetime.min.time(), tzinfo=UK),
            datetime.combine(start + timedelta(days=7), datetime.min.time(), tzinfo=UK))


def last_week(today: date | None = None) -> str:
    year, week, _ = ((today or date.today()) - timedelta(days=7)).isocalendar()
    return f"{year}-W{week:02d}"


def build_invoice(conn, pilot_id: str, iso_week: str) -> dict:
    price = conn.execute("select price_per_booked_gbp from pilots where id = %s", (pilot_id,)).fetchone()
    if not price or price[0] is None:
        raise InvoiceError(f"{pilot_id} has no agreed price per booked survey; set it from the signed agreement first")
    price = float(price[0])
    _, end = week_bounds(iso_week)
    with conn.transaction():
        existing = conn.execute("select id, total_gbp from invoices where pilot_id = %s and iso_week = %s",
                                (pilot_id, iso_week)).fetchone()
        if existing:
            return {"invoice_id": existing[0], "total": float(existing[1]), "new_lines": 0, "existing": True}
        invoice_id = conn.execute("insert into invoices (pilot_id, iso_week) values (%s, %s) returning id",
                                  (pilot_id, iso_week)).fetchone()[0]
        # Charges: first booking per treatment homeowner, booked before the week ended, not yet charged.
        charged = conn.execute(
            """insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp)
               select %s, e.pilot_id, e.homeowner_key, 'survey', 'booked', %s
               from (select distinct on (homeowner_key) pilot_id, homeowner_key from pilot_events
                     where pilot_id = %s and type = 'survey_booked' and created_at < %s
                     order by homeowner_key, created_at) e
               join pilot_homeowners h on h.pilot_id = e.pilot_id and h.homeowner_key = e.homeowner_key and h.arm = 'treatment'
               on conflict (pilot_id, homeowner_key, booking_ref, kind) do nothing
               returning id""",
            (invoice_id, price, pilot_id, end),
        ).fetchall()
        # Credits: charged earlier or now, and the homeowner still didn't attend.
        credited = conn.execute(
            """insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp)
               select %s, l.pilot_id, l.homeowner_key, 'survey', 'no_show_credit', -l.amount_gbp
               from invoice_lines l
               join pilot_homeowners h on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key
               where l.pilot_id = %s and l.kind = 'booked'
                 and h.state not in ('booked', 'attended', 'requoted', 'won', 'lost')
                 and exists (select 1 from pilot_events n where n.pilot_id = l.pilot_id
                             and n.homeowner_key = l.homeowner_key and n.type = 'survey_not_held')
               on conflict (pilot_id, homeowner_key, booking_ref, kind) do nothing
               returning id""",
            (invoice_id, pilot_id),
        ).fetchall()
        total = conn.execute("select coalesce(sum(amount_gbp), 0) from invoice_lines where invoice_id = %s",
                             (invoice_id,)).fetchone()[0]
        conn.execute("update invoices set total_gbp = %s where id = %s", (total, invoice_id))
    return {"invoice_id": invoice_id, "total": float(total), "new_lines": len(charged) + len(credited),
            "charges": len(charged), "credits": len(credited), "existing": False}


def invoice_markdown(conn, invoice_id: int) -> str:
    """Invoice body for the installer (their own customers' first names are
    fine to show them: they're the data controller). Supplier details and VAT
    wording are placeholders until the autónomo registration and gestor advice."""
    pilot_id, iso_week, total = conn.execute(
        "select pilot_id, iso_week, total_gbp from invoices where id = %s", (invoice_id,)).fetchone()
    lines = conn.execute(
        """select l.kind, l.amount_gbp, split_part(coalesce(h.name, ''), ' ', 1), split_part(coalesce(h.postcode, ''), ' ', 1),
                  (select payload->>'start' from pilot_events e where e.pilot_id = l.pilot_id and e.homeowner_key = l.homeowner_key
                     and e.type = 'survey_booked' order by created_at limit 1)
           from invoice_lines l join pilot_homeowners h on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key
           where l.invoice_id = %s order by l.kind, 5""", (invoice_id,)).fetchall()
    rows = [f"| {'Booked survey' if kind == 'booked' else 'No-show credit'} | {first or '-'} ({area or '-'}) | {start or '-'} | £{amount:,.2f} |"
            for kind, amount, first, area, start in lines]
    return "\n".join([
        f"# Invoice {pilot_id} / {iso_week}", "",
        "From: [Pablo García Sierra, autónomo, NIF to add] · [address] · velarqo.com",
        "To: [installer legal name, address]", "",
        f"Invoice number: VQ-{invoice_id:05d} · Date: {date.today():%d %b %Y} · Due: [payment terms from the agreement]", "",
        "| Item | Homeowner | Survey date | Amount |", "|---|---|---|---|", *rows, "",
        f"**Total: £{float(total):,.2f}**", "",
        "[VAT wording to confirm with the gestor, e.g. reverse charge for B2B services to a UK business]",
        "[Bank details: GBP account]", "",
    ]) + "\n"


def write_invoice_file(conn, invoice_id: int) -> Path:
    slug = conn.execute("select p.client_slug from invoices i join pilots p on p.id = i.pilot_id where i.id = %s",
                        (invoice_id,)).fetchone()[0]
    out = ROOT / "clients" / slug / "invoices"
    out.mkdir(parents=True, exist_ok=True)
    path = out / f"VQ-{invoice_id:05d}.md"
    path.write_text(invoice_markdown(conn, invoice_id), encoding="utf-8")
    return path
