"""Irish Companies Registration Office (CRO) open data -> Irish Ltd companies
in our trades. Second-market groundwork (docs/IRELAND.md); nothing here sends.

Source: https://opendata.cro.ie/dataset/companies ("Company Records",
companies.csv.zip, ~48 MB zip / ~190 MB CSV, every company ever registered,
refreshed daily, CC BY 4.0, no key). Attribution the licence asks for:
"Contains Irish Public Sector Data (CRO) licensed under a Creative Commons
Attribution 4.0 International (CC BY 4.0) licence".
Research + sources: docs/knowledge/web_research/2026-10-11_ireland.md.

Same shape as companies_house_bulk.py so pipelines/uk_universe and the
store take the rows unchanged, with these differences:
- Activity code is NACE Rev 2 (4 digits, e.g. 4332) and is missing for
  ~36% of live companies (older incorporations). Stored as the UK SIC 2007
  equivalent (NACE + "0", 4334 -> 43342 glazing) so the ICP scoring's
  sic_code_weights apply; the raw NACE code is kept in `nace_code`.
- No accounts category: CRO publishes last-accounts dates, not size bands.
- Address is the registered office (often an accountant's), with an
  Eircode for ~63% of live companies. Town/county parsed from address_4.
- Company type text is the CRO's ("LTD - Private Company Limited by
  Shares"), which the send engine's corporate-category guard does not
  recognise - on purpose, until the Irish wording and sender exist.

Sole traders are never in this file: they are not companies and the CRO
keeps them (if at all) on the separate Register of Business Names.

    python -m prospecting.sourcing.cro_bulk download
    python -m prospecting.sourcing.cro_bulk extract data/cro_companies.csv.zip --trade windows --output data/cro_ie_windows.csv
    python -m prospecting.sourcing.cro_bulk push data/cro_ie_windows.csv --trade windows
    python -m prospecting.sourcing.cro_bulk find-websites --sample 200
"""

import csv
import io
import json
import random
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import click
import requests

COUNTRY = "IE"
DATASET_URL = ("https://opendata.cro.ie/dataset/bf6f837d-0946-4c14-9a99-82cd6980c121"
               "/resource/3fef41bc-b8f4-4b10-8434-ce51c29b1bba/download/companies.csv.zip")
DEFAULT_ZIP = Path("data/cro_companies.csv.zip")
ATTRIBUTION = "Contains Irish Public Sector Data (CRO) licensed under a Creative Commons Attribution 4.0 International (CC BY 4.0) licence"
USER_AGENT = "velarqo-lead-sourcing/0.1 (+https://velarqo.com; hello@velarqo.com)"

# CRO company types that are bodies corporate with members we can email
# under S.I. 336/2011 reg. 13(4) (not natural persons). Companies limited
# by guarantee are mostly clubs, charities and management companies;
# external companies are foreign branches; funds/SEs are not installers.
INCLUDED_TYPES = (
    "LTD - Private Company Limited by Shares",
    "DAC - Designated Activity Company (limited by shares)",
    "ULC - Private Unlimited Company",
    "PLC - Public Limited Company",
    "Private limited by shares",
    "Single member private company limited by shares",
    "Private unlimited with share capital",
)
ACTIVE_STATUS = "Normal"

# NACE Rev 2 -> UK SIC 2007 used by the ICP scoring. UK SIC is NACE plus a
# fifth digit, "0" unless the UK subdivided the class.
NACE_TO_SIC = {"4334": "43342"}
NACE_LABELS = {
    "4332": "Joinery installation",
    "4334": "Painting and glazing",
    "4391": "Roofing activities",
    "2512": "Manufacture of doors and windows of metal",
    "2223": "Manufacture of builders' ware of plastic",
    "1623": "Manufacture of other builders' carpentry and joinery",
    "4752": "Retail sale of hardware, paints and glass",
    "3102": "Manufacture of kitchen furniture",
}

_TRADE_NACE_PREFIXES = ("41", "42", "43", "16", "22", "25", "31", "46", "47")
_CORE_WINDOW = re.compile(r"(^|[^a-z])(windows?|glazing|glaziers?|double glaz\w*)([^a-z]|$)", re.IGNORECASE)
_DOOR = re.compile(r"(^|[^a-z])doors?([^a-z]|$)", re.IGNORECASE)

# trade -> (NACE codes that count alone, NACE codes that need the name too, name pattern)
TRADES = {
    "windows": ({"4332", "2512", "2223", "1623", "4752"}, {"4334"}, _CORE_WINDOW),
    "roofing": ({"4391"}, set(),
                re.compile(r"(^|[^a-z])(roof\w*|fascias?|soffits?|guttering)([^a-z]|$)", re.IGNORECASE)),
    "kitchens": ({"3102"}, set(),
                 re.compile(r"(^|[^a-z])(kitchens?|worktops?|cabinet(ry|s)?|bedrooms? and kitchens?)([^a-z]|$)", re.IGNORECASE)),
}

CSV_COLUMNS = [
    "company_name", "company_number", "postcode", "address", "city", "county", "sic_codes", "nace_code", "industry",
    "incorporation_date", "accounts_category", "company_category", "lead_source", "country", "cro_raw",
]


def nace_code(row: dict) -> str:
    """'4332.0' -> '4332'; '' when the CRO never recorded one."""
    code = (row.get("nace_v2_code") or "").strip().split(".")[0]
    return code if code.isdigit() else ""


def is_active_company(row: dict) -> bool:
    return (row.get("company_status") or "").strip() == ACTIVE_STATUS and \
        (row.get("company_type") or "").strip() in INCLUDED_TYPES


def match_reason(row: dict, trade: str) -> str | None:
    """Why this company is a candidate for `trade`, or None. Name matches
    count when the NACE code is missing (a third of live companies) or in
    construction/joinery/fabrication/building-materials trade; a NACE code
    from another sector (takeaway, gym) vetoes the name."""
    if not is_active_company(row):
        return None
    alone, with_name, name_pattern = TRADES[trade]
    code = nace_code(row)
    name = row.get("company_name") or ""
    named = bool(name_pattern.search(name))
    in_trade = not code or code.startswith(_TRADE_NACE_PREFIXES)
    if code in alone:
        return f"nace:{code}"
    if named and code in with_name:
        return f"name+nace:{code}"
    if named and in_trade:
        return "name+nace" if code else "name"
    if trade == "windows" and _DOOR.search(name) and code and code.startswith(_TRADE_NACE_PREFIXES):
        return "door+nace"
    return None


def parse_town_county(row: dict) -> tuple[str | None, str | None]:
    """address_4 is 'TOWN, COUNTY, IRELAND' / 'Town,COUNTY' / ',Dublin 22'."""
    for field in ("company_address_4", "company_address_3"):
        parts = [p.strip() for p in (row.get(field) or "").split(",")]
        parts = [p for p in parts if p and p.lower() not in ("ireland", "republic of ireland", "eire")]
        if parts:
            town = parts[0]
            county = parts[1] if len(parts) > 1 else None
            if county and county.lower().startswith("co. "):
                county = county[4:]
            return town.title(), (county.title() if county else None)
    return None, None


def _iso_to_uk(value: str) -> str | None:
    """CRO dates are YYYY-MM-DD; the store parses dd/mm/yyyy."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").strftime("%d/%m/%Y") if value else None
    except ValueError:
        return None


def row_to_lead(row: dict) -> dict:
    code = nace_code(row)
    sic = (NACE_TO_SIC.get(code) or f"{code}0") if code else ""
    town, county = parse_town_county(row)
    address = ", ".join(p for p in ((row.get(k) or "").strip() for k in ("company_address_1", "company_address_2")) if p)
    return {
        "company_name": (row.get("company_name") or "").strip(),
        "legal_name": (row.get("company_name") or "").strip(),
        "company_number": (row.get("company_num") or "").strip(),
        "postcode": (row.get("eircode") or "").strip() or None,
        "registered_postcode": (row.get("eircode") or "").strip() or None,
        "address": address or None,
        "city": town,
        "county": county,
        "sic_codes": sic,
        "nace_code": code or None,
        "industry": NACE_LABELS.get(code, f"NACE {code}" if code else ""),
        "incorporation_date": _iso_to_uk((row.get("company_reg_date") or "").strip()),
        "accounts_category": None,
        "company_category": (row.get("company_type") or "").strip(),
        "lead_source": "cro",
        "sources": ["cro"],
        "country": COUNTRY,
        "cro_raw": {k.strip(): v.strip() for k, v in row.items() if v and v.strip()},
    }


def iter_companies(zip_path: Path, trade: str):
    """Yields (lead, match_reason) for every live Irish company in `trade`."""
    with zipfile.ZipFile(zip_path) as archive:
        csv_name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        with archive.open(csv_name) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = [h.strip() for h in next(reader)]
            for values in reader:
                row = dict(zip(header, values))
                reason = match_reason(row, trade)
                if reason:
                    yield row_to_lead(row), reason


def download(dest: Path = DEFAULT_ZIP, url: str = DATASET_URL, session: requests.Session | None = None) -> Path:
    """Streams the daily zip to `dest` (gitignored under data/)."""
    session = session or requests.Session()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with session.get(url, headers={"User-Agent": USER_AGENT}, stream=True, timeout=120) as r:
        r.raise_for_status()
        tmp = dest.with_suffix(".part")
        with tmp.open("wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
        tmp.replace(dest)
    return dest


def load_trade_icp(trade: str) -> dict:
    """The UK ICP for the trade with the country swapped: scoring is
    name/website/activity-code based, nothing in it is UK-specific."""
    templates = Path(__file__).parents[2] / "config" / "templates"
    path = templates / ("icp-template.json" if trade == "windows" else f"icp-{trade}-uk.json")
    icp = json.loads(path.read_text(encoding="utf-8"))
    return {**icp, "country": COUNTRY, "name": icp.get("name", trade).replace("UK", "IE")}


@click.group()
def main() -> None:
    """CRO open data: Irish Ltd companies in our trades (nothing is sent)."""


@main.command("download")
@click.option("--dest", type=click.Path(path_type=Path), default=DEFAULT_ZIP, show_default=True)
def download_cmd(dest: Path) -> None:
    path = download(dest)
    click.echo(f"{path} ({path.stat().st_size / 1e6:.0f} MB). {ATTRIBUTION}.")


@main.command("extract")
@click.argument("zip_path", type=click.Path(exists=True, path_type=Path))
@click.option("--trade", type=click.Choice(sorted(TRADES)), default="windows", show_default=True)
@click.option("--output", "output_path", type=click.Path(path_type=Path), required=True)
def extract_cmd(zip_path: Path, trade: str, output_path: Path) -> None:
    counts: dict[str, int] = {}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*CSV_COLUMNS, "match_reason"], extrasaction="ignore")
        writer.writeheader()
        for lead, reason in iter_companies(zip_path, trade):
            writer.writerow({**lead, "cro_raw": json.dumps(lead["cro_raw"], ensure_ascii=False), "match_reason": reason})
            counts[reason] = counts.get(reason, 0) + 1
    click.echo(f"{sum(counts.values())} live Irish {trade} candidate companies -> {output_path}")
    for reason, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        click.echo(f"  {reason:16} {count:6}  {NACE_LABELS.get(reason.rpartition(':')[2], '')}")


@main.command("push")
@click.argument("csv_path", type=click.Path(exists=True, path_type=Path))
@click.option("--trade", type=click.Choice(sorted(TRADES)), required=True)
def push_cmd(csv_path: Path, trade: str) -> None:
    """Score with the trade's ICP and upsert as country='IE' rows."""
    from data.supabase_store import connect, push_universe
    from lib.normalization.normalize import normalize_lead
    from lib.scoring.icp_score import evaluate_lead
    from pipelines.uk_universe.build import load_csv

    icp = load_trade_icp(trade)
    leads = []
    for raw in load_csv(csv_path):
        raw["sources"] = ["cro"]
        raw["raw_sources"] = [{"source": "cro", "source_id": raw["company_number"], "payload": raw.pop("cro_raw", None) or {}}]
        lead = normalize_lead(raw)
        result = evaluate_lead(lead, icp)
        lead.update(icp_score=result["score"], tier=result["tier"], vertical_fit=result["vertical_fit"],
                    score_breakdown=result["breakdown"], score_reasons=result["reasons"])
        leads.append(lead)
    tiers = {}
    for lead in leads:
        tiers[lead["tier"]] = tiers.get(lead["tier"], 0) + 1
    with connect() as conn:
        stats = push_universe(conn, leads, trade, icp, country=COUNTRY)
    click.echo(f"{len(leads)} {trade} rows, tiers {tiers}, db {stats}")


@main.command("find-websites")
@click.option("--sample", default=200, show_default=True, help="Companies without a website to try, across trades")
@click.option("--seed", default=1, show_default=True)
@click.option("--workers", default=16, show_default=True)
@click.option("--cache", "cache_path", type=click.Path(path_type=Path), default=Path("data/domain_finder_cache_ie_v2.jsonl"), show_default=True)
@click.option("--csv", "csv_paths", type=click.Path(exists=True, path_type=Path), multiple=True,
              help="Sample from extracted CSVs instead of the database (results only cached, nothing written to the db)")
def find_websites_cmd(sample: int, seed: int, workers: int, cache_path: Path, csv_paths: tuple[Path, ...]) -> None:
    """Free website finder (name -> .ie/.com guess, verified) on a random
    sample of Irish rows; found sites, emails and re-scored tiers go back
    to the database. No Google Places: that quota stays for the UK."""
    from lib.normalization.normalize import normalize_lead
    from lib.scoring.icp_score import evaluate_lead
    from prospecting.enrichment.domain_finder import COUNTRY_MARKERS, COUNTRY_STRICT_TLDS, COUNTRY_TLDS, find_websites

    icps = {trade: load_trade_icp(trade) for trade in TRADES}
    if csv_paths:
        from pipelines.uk_universe.build import load_csv

        conn = None
        leads = []
        for path in csv_paths:
            trade = next(t for t in TRADES if t in path.stem)
            for raw in load_csv(path):
                lead = normalize_lead({**raw, "vertical": trade, "legal_name": raw["company_name"]})
                if evaluate_lead(lead, icps[trade])["tier"] != "reject":
                    leads.append(lead)
    else:
        from data.supabase_store import connect
        from psycopg.types.json import Jsonb

        conn = connect()
        conn.autocommit = True  # the write below is its own transaction; a read-opened one would never commit
        rows = conn.execute(
            """select id, vertical, legal_name, display_name, company_number, city, postcode, email, phone, sic_codes,
                      extra->>'industry', tier
               from companies where country = %s and website is null and tier <> 'reject'""", (COUNTRY,)).fetchall()
        leads = [{"company_id": r[0], "vertical": r[1], "legal_name": r[2], "company_name": r[2], "display_name": r[3],
                  "company_number": r[4], "city": r[5], "postcode": r[6], "email": r[7], "phone": r[8],
                  "sic_codes": " ".join(r[9] or []), "industry": r[10], "tier": r[11]} for r in rows]
    leads.sort(key=lambda l: l["company_number"])
    random.Random(seed).shuffle(leads)
    leads = leads[:sample]
    terms = sorted({t for icp in icps.values() for t in [*(icp.get("core_terms") or []), *(icp.get("adjacent_terms") or [])]})
    found = find_websites(leads, USER_AGENT, terms, workers=workers, cache_path=cache_path,
                          on_progress=lambda d, t: click.echo(f"  {d}/{t}", err=True), tlds=COUNTRY_TLDS[COUNTRY],
                          strict_tlds=COUNTRY_STRICT_TLDS[COUNTRY], local_markers=COUNTRY_MARKERS[COUNTRY])

    per_trade: dict[str, dict[str, int]] = {t: {"tried": 0, "website": 0, "email": 0} for t in TRADES}
    for lead in found:
        stats = per_trade[lead["vertical"]]
        stats["tried"] += 1
        if lead.get("website"):
            stats["website"] += 1
            stats["email"] += bool(lead.get("email"))
    if conn is not None:
        with conn.transaction():
            for lead in found:
                if not lead.get("website"):
                    continue
                result = evaluate_lead(lead, icps[lead["vertical"]])
                conn.execute(
                    """update companies set website = %s, website_status = %s, website_title = %s, emails_found = %s,
                         email = coalesce(email, %s), email_source = coalesce(email_source, %s), enriched_at = %s,
                         icp_score = %s, tier = %s, vertical_fit = %s, score_reasons = %s,
                         extra = extra || %s where id = %s""",
                    (lead["website"], lead.get("website_status"), lead.get("website_title"), lead.get("emails_found") or [],
                     lead.get("email"), "website" if lead.get("email") else None, lead.get("website_fetched_at"),
                     result["score"], result["tier"], result["vertical_fit"], result["reasons"],
                     Jsonb({"website_source": "domain_guess", "website_confidence": lead.get("website_confidence")}), lead["company_id"]))
                conn.execute(
                    """insert into website_snapshots (company_id, url, status, title, text, emails_found, fetched_at)
                       values (%s, %s, %s, %s, %s, %s, %s)""",
                    (lead["company_id"], lead["website"], lead.get("website_status") or "ok", lead.get("website_title"),
                     lead.get("website_text"), lead.get("emails_found") or [], lead.get("website_fetched_at") or datetime.now(timezone.utc)))
    for trade, stats in per_trade.items():
        click.echo(f"{trade:9} tried {stats['tried']:4}  website {stats['website']:4}  with email {stats['email']:4}")


if __name__ == "__main__":
    main()
