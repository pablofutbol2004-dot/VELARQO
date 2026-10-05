"""Companies House free bulk register -> door/window/glazing companies.

Source: https://download.companieshouse.gov.uk/en_output.html
("BasicCompanyDataAsOneFile-YYYY-MM-01.zip", ~470 MB zip / 2.8 GB CSV,
every live UK company, refreshed monthly, free, no key). Streamed straight
out of the zip - never extracted to disk.

Coverage caveats, so the numbers aren't over-read:
- Registered companies only. Sole traders and most partnerships - a big
  share of UK window fitters - are not on Companies House at all.
- The address is the *registered office*, often an accountant's, not the
  trading premises. No website/phone/email.
- SIC codes are self-declared and coarse: 43320 "joinery installation"
  also covers kitchen fitters, so it's evidence, not proof - scoring
  decides.
"""

import csv
import io
import json
import re
import zipfile
from pathlib import Path

import click

# SIC 2007. Specific codes are strong evidence; broad ones only count with
# other evidence (name, website) - see sic_code_weights in the ICP.
DOOR_WINDOW_SIC_CODES = {
    "43342": "Glazing",
    "25120": "Manufacture of doors and windows of metal",
    "43320": "Joinery installation",
    "22230": "Manufacture of builders' ware of plastic",
    "16230": "Manufacture of other builders' carpentry and joinery",
    "47520": "Retail sale of hardware, paints and glass",
}

_CORE_NAME = re.compile(r"(^|[^a-z])(windows?|glazing|glaziers?|double glaz\w*)([^a-z]|$)", re.IGNORECASE)
_DOOR_NAME = re.compile(r"(^|[^a-z])doors?([^a-z]|$)", re.IGNORECASE)
# "door" alone is too ambiguous ("Next Door Lettings"), so it only counts
# for companies in construction, joinery, plastics/metal fabrication or
# building-materials trade/retail.
_TRADE_SIC_PREFIXES = ("41", "42", "43", "16", "22", "25", "46", "47")

_EXCLUDED_ACCOUNT_CATEGORIES = {"DORMANT"}

CSV_COLUMNS = [
    "company_name", "company_number", "postcode", "address", "city", "sic_codes", "industry",
    "incorporation_date", "accounts_category", "company_category", "lead_source", "ch_raw",
]


def _sic_codes(row: dict) -> list[str]:
    codes = []
    for i in range(1, 5):
        text = (row.get(f"SICCode.SicText_{i}") or "").strip()
        if text:
            codes.append(text.split(" - ", 1)[0].strip())
    return codes


# Other trades: (SIC codes that count on their own, name pattern that counts
# with a construction SIC). Counted on the 2026-09 register, active non-dormant
# Ltd/LLP/PLC: roofing ~13k, solar ~5k.
OTHER_TRADES = {
    "roofing": ({"43910": "Roofing activities"},
                re.compile(r"(^|[^a-z])(roof\w*|fascias?|soffits?|guttering)([^a-z]|$)", re.IGNORECASE)),
    "solar": ({"35110": "Production of electricity"},
              re.compile(r"(^|[^a-z])(solar|photovoltaics?|pv|renewables?|battery storage)([^a-z]|$)", re.IGNORECASE)),
}


def trade_match_reason(row: dict, trade: str) -> str | None:
    if row.get("CompanyStatus") != "Active":
        return None
    if (row.get("Accounts.AccountCategory") or "").upper() in _EXCLUDED_ACCOUNT_CATEGORIES:
        return None
    sic_codes, name_pattern = OTHER_TRADES[trade]
    codes = _sic_codes(row)
    name = row.get("CompanyName") or ""
    if name_pattern.search(name) and any(c.startswith(_TRADE_SIC_PREFIXES) for c in codes):
        return "name+trade_sic"
    # A specific SIC alone is enough for roofing; "electricity production"
    # (solar) also covers wind farms and SPVs, so it needs the name too.
    if trade == "roofing" and (matched := [c for c in codes if c in sic_codes]):
        return f"sic:{matched[0]}"
    if trade == "solar" and name_pattern.search(name) and any(c in sic_codes for c in codes):
        return "name+sic"
    return None


def match_reason(row: dict) -> str | None:
    """Why this company is a door/window candidate, or None if it isn't."""
    if row.get("CompanyStatus") != "Active":
        return None
    if (row.get("Accounts.AccountCategory") or "").upper() in _EXCLUDED_ACCOUNT_CATEGORIES:
        return None

    codes = _sic_codes(row)
    name = row.get("CompanyName") or ""
    if matched := [c for c in codes if c in DOOR_WINDOW_SIC_CODES]:
        return f"sic:{matched[0]}"
    if _CORE_NAME.search(name):
        return "name"
    if _DOOR_NAME.search(name) and any(c.startswith(_TRADE_SIC_PREFIXES) for c in codes):
        return "name+trade_sic"
    return None


def row_to_lead(row: dict) -> dict:
    codes = _sic_codes(row)
    address_parts = [row.get(k, "").strip() for k in ("RegAddress.AddressLine1", "RegAddress.AddressLine2")]
    town = (row.get("RegAddress.PostTown") or "").strip()
    return {
        "company_name": row.get("CompanyName", "").strip(),
        "company_number": row.get("CompanyNumber", "").strip(),
        "postcode": (row.get("RegAddress.PostCode") or "").strip() or None,
        "address": ", ".join(p for p in address_parts if p) or None,
        "city": town.title() or None,
        "sic_codes": " ".join(codes),
        "industry": "; ".join(DOOR_WINDOW_SIC_CODES.get(c, c) for c in codes),
        "incorporation_date": row.get("IncorporationDate") or None,
        "accounts_category": row.get("Accounts.AccountCategory") or None,
        "company_category": row.get("CompanyCategory") or None,
        "lead_source": "companies_house",
        # full original row (accounts dates, mortgages, previous names...) -
        # empty fields dropped, everything else kept
        "ch_raw": {k: v for k, v in row.items() if v},
    }


def iter_door_window_companies(zip_path: Path, trade: str = "windows"):
    """Yields (lead, match_reason). Header names in the real file have
    stray leading spaces (" CompanyNumber") - stripped here."""
    with zipfile.ZipFile(zip_path) as archive:
        csv_name = next(n for n in archive.namelist() if n.lower().endswith(".csv"))
        with archive.open(csv_name) as raw:
            reader = csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline=""))
            header = [h.strip() for h in next(reader)]
            for values in reader:
                row = dict(zip(header, values))
                reason = match_reason(row) if trade == "windows" else trade_match_reason(row, trade)
                if reason:
                    yield row_to_lead(row), reason


@click.command()
@click.argument("zip_path", type=click.Path(exists=True, path_type=Path))
@click.option("--output", "output_path", type=click.Path(path_type=Path), required=True)
@click.option("--trade", type=click.Choice(["windows", *OTHER_TRADES]), default="windows", show_default=True)
def main(zip_path: Path, output_path: Path, trade: str) -> None:
    counts: dict[str, int] = {}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[*CSV_COLUMNS, "match_reason"])
        writer.writeheader()
        for lead, reason in iter_door_window_companies(zip_path, trade):
            writer.writerow({**lead, "ch_raw": json.dumps(lead["ch_raw"], ensure_ascii=False), "match_reason": reason})
            counts[reason] = counts.get(reason, 0) + 1

    click.echo(f"{sum(counts.values())} active {trade} candidate companies -> {output_path}")
    for reason, count in sorted(counts.items(), key=lambda kv: -kv[1]):
        label = DOOR_WINDOW_SIC_CODES.get(reason.removeprefix("sic:"), "")
        click.echo(f"  {reason:16} {count:6}  {label}")


if __name__ == "__main__":
    main()
