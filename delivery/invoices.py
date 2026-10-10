"""Weekly invoice per pilot (WORKFLOW.md steps 9-10; pilot agreement sections 4-5).

Charges
- One charge per PERSON (all their quotes share a person_key) whose survey
  got booked on the pilot's survey calendar, or who booked directly with the
  installer within the attribution window (`pilot log ... direct_booking`).
  Rebooks and moved appointments don't charge again.
- Free start: bookings from the first `free_homeowners` people contacted (by
  claim order) are listed at £0.
- Caps: once `max_billable` (whole pilot) or `max_billable_per_week` is
  reached, further bookings are listed at £0 and never charged later.

Credits (once per charged person, on the next invoice)
- No-show: the survey wasn't held because the homeowner wasn't in, and they
  haven't rebooked or attended since. Not credited if the installer logged
  the miss as theirs (`pilot log ... installer_missed`).
- Cancellation: credited only if not rebooked within 14 days.

Idempotency: one invoice per (pilot, ISO week); re-running returns it.
Lines are unique per (pilot, homeowner, booking_ref, kind).
Known limit: "one charge per address" is enforced per person (mobile/email),
not per street address; two different people at one address would both be
charged unless the export's address is added to person matching.
"""

from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
ROOT = Path(__file__).parents[1]
CANCEL_REBOOK_DAYS = 14


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
    """`conn` should be autocommit; the whole invoice is one transaction."""
    terms = conn.execute(
        "select price_per_booked_gbp, max_billable, max_billable_per_week, free_homeowners from pilots where id = %s",
        (pilot_id,)).fetchone()
    if not terms or terms[0] is None:
        raise InvoiceError(f"{pilot_id} has no agreed price per booked survey; set it from the signed agreement first")
    price, cap_total, cap_week, free_n = float(terms[0]), terms[1], terms[2], terms[3] or 0
    _, end = week_bounds(iso_week)
    with conn.transaction():
        existing = conn.execute("select id, total_gbp from invoices where pilot_id = %s and iso_week = %s",
                                (pilot_id, iso_week)).fetchone()
        if existing:
            return {"invoice_id": existing[0], "total": float(existing[1]), "new_lines": 0, "existing": True}
        invoice_id = conn.execute("insert into invoices (pilot_id, iso_week) values (%s, %s) returning id",
                                  (pilot_id, iso_week)).fetchone()[0]
        free_people = {k for (k,) in conn.execute(
            """select person_key from (select person_key, min(claimed_at) as first from pilot_homeowners
                 where pilot_id = %s and claimed_at is not null and person_key is not null group by person_key) x
               order by first, person_key limit %s""", (pilot_id, free_n)).fetchall()} if free_n else set()
        charged_people = {k for (k,) in conn.execute(
            "select h.person_key from invoice_lines l join pilot_homeowners h on h.pilot_id = l.pilot_id "
            "and h.homeowner_key = l.homeowner_key where l.pilot_id = %s and l.kind = 'booked'", (pilot_id,)).fetchall()}
        billed_total = conn.execute("select count(*) from invoice_lines where pilot_id = %s and kind = 'booked' and amount_gbp > 0",
                                    (pilot_id,)).fetchone()[0]
        candidates = conn.execute(
            """select distinct on (coalesce(h.person_key, h.homeowner_key)) h.homeowner_key, h.person_key
               from pilot_events e join pilot_homeowners h on h.pilot_id = e.pilot_id and h.homeowner_key = e.homeowner_key
               where e.pilot_id = %s and e.type in ('survey_booked', 'direct_booking') and e.created_at < %s and h.arm = 'treatment'
               order by coalesce(h.person_key, h.homeowner_key), e.created_at""", (pilot_id, end)).fetchall()
        charges = free = capped = 0
        billed_week = 0
        for key, person in candidates:
            if (person or key) in charged_people:
                continue
            amount = price
            if (person or key) in free_people:
                amount, free = 0.0, free + 1
            elif (cap_total is not None and billed_total >= cap_total) or (cap_week is not None and billed_week >= cap_week):
                amount, capped = 0.0, capped + 1
            inserted = conn.execute(
                "insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp) "
                "values (%s, %s, %s, 'survey', 'booked', %s) on conflict do nothing returning id",
                (invoice_id, pilot_id, key, amount)).fetchone()
            if inserted:
                charged_people.add(person or key)
                if amount > 0:
                    charges += 1
                    billed_total += 1
                    billed_week += 1
        credits = conn.execute(
            """insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp)
               select %(inv)s, l.pilot_id, l.homeowner_key, 'survey', 'no_show_credit', -l.amount_gbp
               from invoice_lines l
               join pilot_homeowners h on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key
               join lateral (select n.created_at, n.payload->>'reason' as reason from pilot_events n
                             where n.pilot_id = l.pilot_id and n.homeowner_key = l.homeowner_key and n.type = 'survey_not_held'
                             order by n.created_at desc limit 1) miss on true
               where l.pilot_id = %(p)s and l.kind = 'booked' and l.amount_gbp > 0
                 and h.state not in ('booked', 'attended', 'requoted', 'won', 'lost')
                 and not exists (select 1 from pilot_events b where b.pilot_id = l.pilot_id and b.homeowner_key = l.homeowner_key
                                 and b.type in ('survey_booked', 'direct_booking') and b.created_at > miss.created_at)
                 and not exists (select 1 from pilot_events m where m.pilot_id = l.pilot_id and m.homeowner_key = l.homeowner_key
                                 and m.type = 'installer_missed')
                 and (miss.reason <> 'cancelled' or miss.created_at < %(cutoff)s)
               on conflict (pilot_id, homeowner_key, booking_ref, kind) do nothing
               returning id""",
            {"inv": invoice_id, "p": pilot_id, "cutoff": end - timedelta(days=CANCEL_REBOOK_DAYS)},
        ).fetchall()
        total = conn.execute("select coalesce(sum(amount_gbp), 0) from invoice_lines where invoice_id = %s",
                             (invoice_id,)).fetchone()[0]
        conn.execute("update invoices set total_gbp = %s where id = %s", (total, invoice_id))
    return {"invoice_id": invoice_id, "total": float(total), "charges": charges, "free": free, "over_cap": capped,
            "credits": len(credits), "existing": False}


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

    def label(kind, amount):
        if kind != "booked":
            return "No-show credit"
        return "Booked survey" if amount > 0 else "Booked survey (free / over cap)"

    rows = [f"| {label(kind, amount)} | {first or '-'} ({area or '-'}) | {start or '-'} | £{amount:,.2f} |"
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
