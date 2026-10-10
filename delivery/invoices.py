"""Weekly invoice per pilot (WORKFLOW.md steps 9-10; pilot agreement sections 4-5).

Charges
- One charge per PERSON (all their quotes share a person_key) whose survey
  got booked on the pilot's survey calendar, or who booked directly with the
  installer within the attribution window (`pilot log ... direct_booking`).
  Rebooks and moved appointments don't charge again.
  A second row of the same GHL contact is never charged either (safety net).
- Free start: bookings from the first `free_homeowners` people actually
  contacted (enrolled or beyond, by claim order) are listed at £0.
- Caps: billable = charges minus credited no-shows (plus charge-backs).
  Once `max_billable` (whole pilot) or `max_billable_per_week` (counted in
  the ISO week the survey was BOOKED, not the invoice run) is reached,
  further bookings are listed at £0 and never charged later. Who is free or
  over the cap is decided in booking order.

Credits (on the next invoice)
- No-show: the survey wasn't held because the homeowner wasn't in, and they
  haven't rebooked or attended since. Not credited if the installer logged
  the miss as theirs (`pilot log ... installer_missed`).
- Cancellation: credited only if not rebooked within 14 days.
- Charge-back ('credit_reversal'): a credited homeowner who later rebooks or
  attends is charged again (a rebook is still one booked survey); a later
  no-show is credited again. booking_ref numbers each credit/charge-back pair.

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


def iso_week_of(moment: datetime) -> str:
    year, week, _ = moment.astimezone(UK).isocalendar()
    return f"{year}-W{week:02d}"


BOOKING_EVENTS = ("survey_booked", "direct_booking")
CHARGE_KINDS = ("booked", "credit_reversal")


class Ledger:
    """Every invoice line of one pilot, to count billable surveys for the caps:
    a charge (booked / credit_reversal > £0) counts +1 in the ISO week of its
    booking, a no-show credit (< £0) counts -1 in the week of the booking it
    credits. So a credited no-show doesn't use up the cap."""

    def __init__(self, conn, pilot_id: str):
        self.lines = [dict(zip(("key", "kind", "ref", "amount", "booked_at"), r)) for r in conn.execute(
            "select homeowner_key, kind, booking_ref, amount_gbp, booked_at from invoice_lines where pilot_id = %s order by id",
            (pilot_id,)).fetchall()]

    def add(self, key, kind, ref, amount, booked_at):
        self.lines.append({"key": key, "kind": kind, "ref": ref, "amount": amount, "booked_at": booked_at})

    def billable(self, week: str | None = None) -> int:
        n = 0
        for line in self.lines:
            if week is not None and (line["booked_at"] is None or iso_week_of(line["booked_at"]) != week):
                continue
            if line["kind"] in CHARGE_KINDS and line["amount"] > 0:
                n += 1
            elif line["kind"] == "no_show_credit" and line["amount"] < 0:
                n -= 1
        return n

    def of(self, key) -> list[dict]:
        return [line for line in self.lines if line["key"] == key]


class Caps:
    def __init__(self, ledger: Ledger, cap_total, cap_week):
        self.ledger, self.cap_total, self.cap_week = ledger, cap_total, cap_week

    def reached(self, booked_at: datetime) -> bool:
        return ((self.cap_total is not None and self.ledger.billable() >= self.cap_total)
                or (self.cap_week is not None and self.ledger.billable(iso_week_of(booked_at)) >= self.cap_week))


def _credit_ref(n: int) -> str:
    """booking_ref of the n-th credit/reversal pair of one homeowner (n from 0)."""
    return "survey" if n == 0 else f"survey-{n + 1}"


def _credits_and_reversals(conn, pilot_id: str, invoice_id: int, end: datetime, ledger: Ledger, caps: Caps) -> tuple[int, int]:
    """No-show credits, and charge-backs when a credited homeowner rebooks
    (agreement section 4: a rebook is still one booked survey). Each charged
    homeowner alternates: charged -> credited (missed, not rebooked) ->
    reversed (rebooked or attended after the miss) -> credited again..."""
    credits = reversals = 0
    charged = conn.execute(
        """select l.homeowner_key, h.state from invoice_lines l
           join pilot_homeowners h on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key
           where l.pilot_id = %s and l.kind = 'booked' and l.amount_gbp > 0 order by l.id""", (pilot_id,)).fetchall()
    for key, state in charged:
        lines = ledger.of(key)
        n_credits = sum(1 for line in lines if line["kind"] == "no_show_credit")
        n_reversals = sum(1 for line in lines if line["kind"] == "credit_reversal")
        miss = conn.execute(
            "select created_at, payload->>'reason' from pilot_events where pilot_id = %s and homeowner_key = %s "
            "and type = 'survey_not_held' order by created_at desc, id desc limit 1", (pilot_id, key)).fetchone()
        if not miss:
            continue
        miss_at, reason = miss
        if n_credits > n_reversals:
            # Credited: charge back if they rebooked or attended after the miss.
            rebook = conn.execute(
                """select min(created_at) from pilot_events where pilot_id = %s and homeowner_key = %s and created_at > %s
                     and created_at < %s and (type = any(%s)
                       or (type = 'homeowner_state' and payload->>'to' in ('booked', 'attended')))""",
                (pilot_id, key, miss_at, end, list(BOOKING_EVENTS))).fetchone()[0]
            if not rebook:
                continue
            credited = [line for line in lines if line["kind"] == "no_show_credit"][-1]
            amount = 0.0 if caps.reached(rebook) else -float(credited["amount"])
            ref = _credit_ref(n_reversals)
            if conn.execute(
                    "insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp, booked_at) "
                    "values (%s, %s, %s, %s, 'credit_reversal', %s, %s) on conflict do nothing returning id",
                    (invoice_id, pilot_id, key, ref, amount, rebook)).fetchone():
                ledger.add(key, "credit_reversal", ref, amount, rebook)
                reversals += 1
            continue
        last_charge = [line for line in lines if line["kind"] in CHARGE_KINDS][-1]
        if last_charge["amount"] <= 0:
            continue                                  # nothing was charged for the current booking
        if state in ("booked", "attended", "requoted", "won", "lost"):
            continue
        rebooked = conn.execute(
            "select 1 from pilot_events where pilot_id = %s and homeowner_key = %s and type = any(%s) and created_at > %s",
            (pilot_id, key, list(BOOKING_EVENTS), miss_at)).fetchone()
        installer = conn.execute("select 1 from pilot_events where pilot_id = %s and homeowner_key = %s "
                                 "and type = 'installer_missed'", (pilot_id, key)).fetchone()
        if rebooked or installer:
            continue
        if reason == "cancelled" and miss_at >= end - timedelta(days=CANCEL_REBOOK_DAYS):
            continue                                  # cancellations: wait to see if they rebook
        ref = _credit_ref(n_credits)
        amount = -float(last_charge["amount"])
        if conn.execute(
                "insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp, booked_at) "
                "values (%s, %s, %s, %s, 'no_show_credit', %s, %s) on conflict do nothing returning id",
                (invoice_id, pilot_id, key, ref, amount, last_charge["booked_at"])).fetchone():
            ledger.add(key, "no_show_credit", ref, amount, last_charge["booked_at"])
            credits += 1
    return credits, reversals


def _free_people(conn, pilot_id: str, free_n: int) -> set[str]:
    """The first `free_n` people actually contacted (enrolled or beyond), by claim time."""
    if not free_n:
        return set()
    from delivery.monitor import CONTACTED_STATES

    return {p for (p,) in conn.execute(
        """select person from (
             select coalesce(h.person_key, h.homeowner_key) as person, min(h.claimed_at) as first
             from pilot_homeowners h
             where h.pilot_id = %(p)s and h.claimed_at is not null
               and (h.state = any(%(states)s) or exists (
                     select 1 from pilot_events e where e.pilot_id = h.pilot_id and e.homeowner_key = h.homeowner_key
                       and e.type = 'homeowner_state' and e.payload->>'to' = 'enrolled'))
             group by 1) x
           order by first, person limit %(n)s""",
        {"p": pilot_id, "states": CONTACTED_STATES, "n": free_n}).fetchall()}


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
        ledger = Ledger(conn, pilot_id)
        caps = Caps(ledger, cap_total, cap_week)
        # Credits first, so cap room freed by a credited no-show is usable now.
        credits, reversals = _credits_and_reversals(conn, pilot_id, invoice_id, end, ledger, caps)
        free_people = _free_people(conn, pilot_id, free_n)
        charged_people, charged_contacts = set(), set()
        for person, contact in conn.execute(
                "select coalesce(h.person_key, h.homeowner_key), h.ghl_contact_id from invoice_lines l "
                "join pilot_homeowners h on h.pilot_id = l.pilot_id and h.homeowner_key = l.homeowner_key "
                "where l.pilot_id = %s and l.kind = 'booked'", (pilot_id,)).fetchall():
            charged_people.add(person)
            if contact:
                charged_contacts.add(contact)
        # One candidate per person: their first booking; free/cap decided in booking order.
        candidates = conn.execute(
            """select * from (
                 select distinct on (coalesce(h.person_key, h.homeowner_key))
                        h.homeowner_key, coalesce(h.person_key, h.homeowner_key) as person, h.ghl_contact_id, e.created_at
                 from pilot_events e join pilot_homeowners h on h.pilot_id = e.pilot_id and h.homeowner_key = e.homeowner_key
                 where e.pilot_id = %s and e.type = any(%s) and e.created_at < %s and h.arm = 'treatment'
                 order by coalesce(h.person_key, h.homeowner_key), e.created_at, e.id) first_bookings
               order by created_at, person""", (pilot_id, list(BOOKING_EVENTS), end)).fetchall()
        charges = free = capped = 0
        for key, person, contact, booked_at in candidates:
            if person in charged_people or (contact and contact in charged_contacts):
                continue                                  # same person, or same GHL contact: never twice
            amount = price
            if person in free_people:
                amount, free = 0.0, free + 1
            elif caps.reached(booked_at):
                amount, capped = 0.0, capped + 1
            inserted = conn.execute(
                "insert into invoice_lines (invoice_id, pilot_id, homeowner_key, booking_ref, kind, amount_gbp, booked_at) "
                "values (%s, %s, %s, 'survey', 'booked', %s, %s) on conflict do nothing returning id",
                (invoice_id, pilot_id, key, amount, booked_at)).fetchone()
            if inserted:
                ledger.add(key, "booked", "survey", amount, booked_at)
                charged_people.add(person)
                if contact:
                    charged_contacts.add(contact)
                if amount > 0:
                    charges += 1
        # Then no-shows of bookings charged just now.
        more_credits, more_reversals = _credits_and_reversals(conn, pilot_id, invoice_id, end, ledger, caps)
        credits, reversals = credits + more_credits, reversals + more_reversals
        total = conn.execute("select coalesce(sum(amount_gbp), 0) from invoice_lines where invoice_id = %s",
                             (invoice_id,)).fetchone()[0]
        conn.execute("update invoices set total_gbp = %s where id = %s", (total, invoice_id))
    return {"invoice_id": invoice_id, "total": float(total), "charges": charges, "free": free, "over_cap": capped,
            "credits": credits, "reversals": reversals, "existing": False}


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
        if kind == "no_show_credit":
            return "No-show credit"
        if kind == "credit_reversal":
            return "Rebooked after a credited no-show" + ("" if amount > 0 else " (over cap)")
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
