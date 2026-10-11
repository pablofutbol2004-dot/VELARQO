"""Select the 50 best-fit UK window/door installers for the letter test.

Rule (docs/LETTERS.md, "Who gets a letter"):
  outreach_queue  (already excludes parked sites, suppliers, commercial-only,
                   non-UK, Limited Partnerships, inactive/insolvent at Companies
                   House and suppressed emails/domains)
  + vertical = windows, tier = A, residential signal, years_trading >= 5
  + company_category is a private limited company (PECR corporate subscriber)
  + a registered office address on the Companies House profile, not flagged
    undeliverable or in dispute
  - anyone already in a campaign/messages row (active email cohort)
  then rank: address looks like the firm's own premises first (its postcode
  district appears on their website), accountant/agent addresses last,
  and by priority score within each group. Top 50.

Writes data/letters_batch1.csv (gitignored) and prints a summary.

Usage:  python -m outreach.letters.select_batch [--limit 50] [--out data/letters_batch1.csv]
"""
from __future__ import annotations

import argparse
import csv
import os
import re
from datetime import date
from pathlib import Path

import psycopg
from dotenv import load_dotenv

AGENT_ADDRESS_RE = re.compile(
    r"\b(accountants?|accounting|accountancy|chartered|chambers|c/o|care of|formations?|"
    r"secretarial|solicitors?|registered agent|business services|tax|bookkeep\w*|llp)\b",
    re.I,
)
# Well-known UK virtual-office / formation-agent registered addresses.
VIRTUAL_OFFICE_RE = re.compile(
    r"(27 old gloucester|20-22 wenlock|71-75 shelton|128 city road|kemp house|"
    r"85 great portland|167-169 great portland|63/66 hatton|2 woodberry grove|"
    r"207 regent street|483 green lanes|124 city road|86-90 paul street|"
    r"suite \d+|international house)",
    re.I,
)
POSTCODE_RE = re.compile(r"\b([A-Z]{1,2}\d[A-Z\d]?) ?(\d[A-Z]{2})\b", re.I)

SELECT_SQL = """
with queue as (
  select q.*
  from outreach_queue q
  where q.vertical = 'windows'
    and q.tier = 'A'
    and q.residential
    and q.years_trading >= %(min_years)s
    and q.company_category ilike 'private limited%%'
    and not exists (select 1 from messages m where m.company_id = q.id)
),
profile as (
  select company_id, payload from company_facts
  where source = 'ch_profile' and company_id in (select id from queue)
),
officers as (
  select company_id, payload from company_facts
  where source = 'ch_officers' and company_id in (select id from queue)
),
page as (
  select distinct on (company_id) company_id, coalesce(text, '') as text
  from website_snapshots where company_id in (select id from queue)
  order by company_id, fetched_at desc
)
select q.id, q.display_name, q.legal_name, q.company_number, q.email, q.phone, q.website,
       q.city, q.postcode, q.years_trading, q.accredited, q.priority, q.priority_breakdown,
       q.no_pressure_sales, q.home_survey, q.runs_ads, q.lead_sites,
       c.incorporation_date, c.sic_codes,
       ws.established_year, ws.years_claimed, ws.family_run, ws.has_showroom,
       p.payload -> 'registered_office_address' as reg_office,
       o.payload -> 'items' as officers,
       pg.text as page_text
from queue q
join companies c on c.id = q.id
left join website_signals ws on ws.company_id = q.id
left join profile p on p.company_id = q.id
left join officers o on o.company_id = q.id
left join page pg on pg.company_id = q.id
where p.payload -> 'registered_office_address' ->> 'postal_code' is not null
  and coalesce((p.payload ->> 'undeliverable_registered_office_address')::bool, false) = false
  and coalesce((p.payload ->> 'registered_office_is_in_dispute')::bool, false) = false
order by q.priority desc, q.years_trading desc
"""


def _cap(w: str) -> str:
    w = w.lower()
    if w.startswith("mc") and len(w) > 2:
        return "Mc" + w[2:].capitalize()
    if "'" in w:
        a, b = w.split("'", 1)
        return a.capitalize() + "'" + b.capitalize()
    return "-".join(p.capitalize() for p in w.split("-"))


def tidy_name(raw: str) -> tuple[str, str]:
    """'HARGREAVES, Peter John' -> ('Peter Hargreaves', 'Peter')."""
    if "," not in raw:
        return "", ""
    raw = re.sub(r"\s*\([^)]*\)", "", raw)  # drop '(jnr)', '(snr)'
    surname, forenames = [s.strip() for s in raw.split(",", 1)]
    first = forenames.split()[0] if forenames else ""
    first_c = _cap(first) if first else ""
    surname_c = " ".join(_cap(w) for w in surname.split())
    return (f"{first_c} {surname_c}".strip(), first_c)


def pick_director(items: list | None) -> tuple[str, str, str]:
    """Longest-serving active human director. Returns (full_name, first_name, appointed_on)."""
    if not items:
        return "", "", ""
    active = [
        i for i in items
        if not i.get("resigned_on")
        and "director" in (i.get("officer_role") or "")
        and "corporate" not in (i.get("officer_role") or "")
        and "," in (i.get("name") or "")
    ]
    if not active:
        return "", "", ""
    active.sort(key=lambda i: i.get("appointed_on") or "9999")
    d = active[0]
    full, first = tidy_name(d["name"])
    return full, first, d.get("appointed_on") or ""


def address_lines(reg: dict) -> list[str]:
    parts = [reg.get("care_of"), reg.get("po_box"), reg.get("premises"),
             reg.get("address_line_1"), reg.get("address_line_2"),
             reg.get("locality"), reg.get("region")]
    lines: list[str] = []
    for p in parts:
        if p and p.strip() and p.strip().lower() not in [l.lower() for l in lines]:
            lines.append(p.strip())
    return lines


def address_quality(reg: dict, page_text: str) -> tuple[str, str]:
    """('own' | 'unknown' | 'agent', reason)."""
    flat = " ".join(address_lines(reg))
    if reg.get("care_of") or AGENT_ADDRESS_RE.search(flat) or VIRTUAL_OFFICE_RE.search(flat):
        return "agent", "address looks like an accountant/agent/virtual office"
    reg_pc = (reg.get("postal_code") or "").upper().replace(" ", "")
    site_pcs = {(a + b).upper() for a, b in POSTCODE_RE.findall(page_text or "")}
    if not site_pcs:
        return "unknown", "website shows no postcode"
    if reg_pc in site_pcs:
        return "own", "registered postcode appears on their website"
    m = POSTCODE_RE.match(reg.get("postal_code") or "")
    if m and any(pc.startswith(m.group(1).upper()) for pc in site_pcs):
        return "own", "registered postcode district appears on their website"
    return "agent", "website postcodes differ from registered office"


FIELDS = ["letter_code", "company_id", "company_number", "display_name", "legal_name",
          "addressee", "salutation_first_name", "director_since",
          "address_1", "address_2", "address_3", "address_4", "address_5", "postcode",
          "addr_quality", "addr_reason", "incorporation_year", "years_trading",
          "website_established_year", "accredited", "family_run", "has_showroom",
          "city", "website", "email", "phone", "priority", "qr_url", "reply_email"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=50)
    ap.add_argument("--min-years", type=int, default=5)
    ap.add_argument("--out", default="data/letters_batch1.csv")
    args = ap.parse_args()

    load_dotenv(".env")
    load_dotenv("D:/velarqo/.env")  # worktrees share the main checkout's secrets
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        cur = conn.execute(SELECT_SQL, {"min_years": args.min_years})
        cols = [d.name for d in cur.description]
        rows = cur.fetchall()

    candidates = []
    for r in rows:
        d = dict(zip(cols, r))
        reg = d["reg_office"] or {}
        quality, reason = address_quality(reg, d["page_text"] or "")
        full, first, since = pick_director(d["officers"])
        candidates.append({**d, "addr_quality": quality, "addr_reason": reason,
                           "director": full, "director_first": first, "director_since": since,
                           "lines": address_lines(reg), "reg_postcode": reg.get("postal_code", "")})

    rank = {"own": 0, "unknown": 1, "agent": 2}
    candidates.sort(key=lambda c: (rank[c["addr_quality"]], -c["priority"], -(c["years_trading"] or 0)))
    chosen = candidates[: args.limit]

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for i, c in enumerate(chosen, 1):
            code = f"L{i:02d}"
            lines = (c["lines"] + [""] * 5)[:5]
            w.writerow({
                "letter_code": code, "company_id": c["id"], "company_number": c["company_number"],
                "display_name": c["display_name"], "legal_name": c["legal_name"],
                "addressee": c["director"] or "The Owner", "salutation_first_name": c["director_first"],
                "director_since": c["director_since"],
                **{f"address_{k + 1}": lines[k] for k in range(5)}, "postcode": c["reg_postcode"],
                "addr_quality": c["addr_quality"], "addr_reason": c["addr_reason"],
                "incorporation_year": c["incorporation_date"].year if c["incorporation_date"] else "",
                "years_trading": c["years_trading"], "website_established_year": c["established_year"] or "",
                "accredited": c["accredited"], "family_run": c["family_run"], "has_showroom": c["has_showroom"],
                "city": c["city"], "website": c["website"], "email": c["email"], "phone": c["phone"],
                "priority": c["priority"],
                "qr_url": f"https://velarqo.com/windows?l={code}",
                "reply_email": "post@velarqo.com",
            })

    # Summary without company names, safe to paste into docs.
    n = len(candidates)
    q = {k: sum(1 for c in candidates if c["addr_quality"] == k) for k in rank}
    qc = {k: sum(1 for c in chosen if c["addr_quality"] == k) for k in rank}
    named = sum(1 for c in chosen if c["director"])
    print(f"date: {date.today()}")
    print(f"candidates after filters: {n}  (address own/unknown/agent: {q['own']}/{q['unknown']}/{q['agent']})")
    print(f"chosen: {len(chosen)}  (own/unknown/agent: {qc['own']}/{qc['unknown']}/{qc['agent']}); named director: {named}/{len(chosen)}")
    if chosen:
        ys = sorted(c["years_trading"] for c in chosen)
        ps = sorted(c["priority"] for c in chosen)
        print(f"years trading: min {ys[0]}, median {ys[len(ys) // 2]}, max {ys[-1]}")
        print(f"priority: min {ps[0]}, max {ps[-1]}")
        print(f"accredited: {sum(1 for c in chosen if c['accredited'])}; "
              f"website claims an earlier start: {sum(1 for c in chosen if c['established_year'])}")
        regions: dict[str, int] = {}
        for c in chosen:
            reg = c["reg_office"] or {}
            key = reg.get("region") or reg.get("locality") or "?"
            regions[key] = regions.get(key, 0) + 1
        top = sorted(regions.items(), key=lambda kv: -kv[1])[:12]
        print("regions:", ", ".join(f"{k} {v}" for k, v in top))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
