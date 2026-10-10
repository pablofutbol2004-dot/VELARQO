"""Check an installer's sample of old quotes: how many are worth chasing.

    python -m client_onboarding.sample_audit clients/acme/sample.xlsx --company "Acme Windows"

Reads whatever their system exported (CSV or Excel), maps the columns, and
sorts every quote into "worth chasing" or a reason it isn't:
- already won / sold / booked: not ours to chase;
- opted out or marked do-not-contact;
- too recent (under 3 months): they may still be following it up, and
  chasing it is the "I'd have got it anyway" objection;
- too old (over 24 months): people have moved on or bought elsewhere;
- no usable date.

Writes `audit.md` next to the input file (inside clients/, which git
ignores) with counts by age, product and status. Prints only counts, never
homeowner details.
"""

import re
from collections import Counter
from datetime import date
from pathlib import Path

import click
import pandas as pd

from client_onboarding.field_mapping.mapper import apply_mapping, build_column_mapping

MIN_AGE_MONTHS, MAX_AGE_MONTHS = 3, 24
AGE_BUCKETS = [(3, "under 3 months"), (6, "3-6 months"), (12, "6-12 months"), (24, "12-24 months")]

# Extra header aliases for quote exports, on top of the generic mapper.
QUOTE_ALIASES = {
    "quote_date": ["date", "quote date", "quoted", "created", "created date", "enquiry date", "date quoted", "quote created"],
    "product": ["product", "products", "service", "job type", "job", "description", "type", "work type"],
    "quote_status": ["status", "stage", "quote status", "outcome", "result"],
    "record_id": ["id", "record id", "quote id", "quote ref", "quote reference", "reference", "ref", "quote number", "quote no", "job number", "job ref"],
    "quote_value": ["value", "price", "total", "amount", "quote total", "quote price"],
    "opt_out": ["opt out", "opted out", "do not contact", "dnc", "unsubscribed", "marketing opt out", "no marketing"],
}
WON = re.compile(r"\b(won|sold|accepted|ordered|booked|installed|complete|completed|deposit|signed|invoiced)\b", re.I)
YES = re.compile(r"^\s*(y|yes|true|1|x|opted out|unsubscribed)\s*$", re.I)


def load(path: Path) -> list[dict]:
    frame = pd.read_excel(path) if path.suffix.lower() in (".xlsx", ".xls") else pd.read_csv(path)
    frame = frame.astype(object).where(frame.notna(), None)
    return frame.to_dict(orient="records")


def map_columns(headers: list[str]) -> dict[str, str]:
    mapping = build_column_mapping(headers)
    for header in headers:
        normalized = header.strip().lower().replace("_", " ").replace("-", " ")
        for field, aliases in QUOTE_ALIASES.items():
            if normalized in aliases and field not in mapping.values():
                mapping[header] = field
    return mapping


def months_between(earlier: date, later: date) -> int:
    return (later.year - earlier.year) * 12 + later.month - earlier.month - (later.day < earlier.day)


def parse_date(value) -> date | None:
    if value in (None, ""):
        return None
    try:
        parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")  # UK exports are day-first
    except (ValueError, TypeError):
        return None
    return None if pd.isna(parsed) else parsed.date()


def classify(record: dict, today: date) -> tuple[str, int | None]:
    """('worth chasing' or a reason it isn't, age in months)."""
    status = str(record.get("quote_status") or "")
    if WON.search(status):
        return "already won/booked", None
    if YES.match(str(record.get("opt_out") or "")):
        return "opted out", None
    quoted = parse_date(record.get("quote_date"))
    if not quoted:
        return "no usable date", None
    age = months_between(quoted, today)
    if age < MIN_AGE_MONTHS:
        return "too recent (under 3 months)", age
    if age > MAX_AGE_MONTHS:
        return "too old (over 24 months)", age
    return "worth chasing", age


def age_bucket(age: int | None) -> str:
    if age is None:
        return "unknown"
    return next((label for limit, label in AGE_BUCKETS if age < limit), "over 24 months")


def audit(records: list[dict], today: date | None = None) -> dict:
    today = today or date.today()
    headers = list(dict.fromkeys(k for r in records for k in r))  # every column, even if only some rows have it
    mapping = map_columns(headers)
    mapped = apply_mapping(records, mapping)
    verdicts = [classify(r, today) for r in mapped]
    chase = [r for r, (v, _) in zip(mapped, verdicts) if v == "worth chasing"]
    return {
        "total": len(mapped),
        "mapping": mapping,
        "unmapped": [h for h in headers if h not in mapping],
        "verdicts": Counter(v for v, _ in verdicts),
        "ages": Counter(age_bucket(a) for _, a in verdicts),
        "chase_by_product": Counter(str(r.get("product") or "not given").strip().lower() for r in chase),
        "chase_by_status": Counter(str(r.get("quote_status") or "not given").strip().lower() for r in chase),
        "chase_values": [float(v) for r in chase if (v := _number(r.get("quote_value"))) is not None],
        "has_contact_details": any(r.get("phone") or r.get("email") for r in mapped),
    }


def _number(value) -> float | None:
    try:
        return float(str(value).replace("£", "").replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def report_markdown(result: dict, company: str) -> str:
    chase = result["verdicts"].get("worth chasing", 0)
    share = f"{chase / result['total']:.0%}" if result["total"] else "0%"
    lines = [f"# Old-quotes check: {company}", "",
             f"**{chase} of {result['total']} quotes ({share}) look worth chasing.**", "",
             "## Why the others aren't", ""]
    lines += [f"- {reason}: {n}" for reason, n in result["verdicts"].most_common() if reason != "worth chasing"] or ["- none"]
    lines += ["", "## Age of all quotes", ""]
    lines += [f"- {label}: {result['ages'].get(label, 0)}" for _, label in AGE_BUCKETS] + \
             [f"- over 24 months: {result['ages'].get('over 24 months', 0)}", f"- unknown date: {result['ages'].get('unknown', 0)}"]
    lines += ["", "## Worth chasing, by product", ""] + [f"- {k}: {n}" for k, n in result["chase_by_product"].most_common()]
    lines += ["", "## Worth chasing, by status", ""] + [f"- {k}: {n}" for k, n in result["chase_by_status"].most_common()]
    if result["chase_values"]:
        values = result["chase_values"]
        lines += ["", f"Quoted value of those worth chasing: £{sum(values):,.0f} in total, "
                      f"£{sum(values) / len(values):,.0f} on average ({len(values)} with a value)."]
    lines += ["", "## Columns", "", "Matched: " + ", ".join(f"{k} → {v}" for k, v in result["mapping"].items()),
              "Not used: " + (", ".join(result["unmapped"]) or "none"), "",
              "_Internal check by Velarqo. Counts only; no homeowner details in this file._"]
    return "\n".join(lines) + "\n"


@click.command()
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--company", required=True, help="Installer's name, for the report title")
def main(path: Path, company: str):
    if "clients" not in path.resolve().parts:
        raise click.UsageError("client files must live under clients/<company>/ (git ignores that folder)")
    result = audit(load(path))
    out = path.with_name("audit.md")
    out.write_text(report_markdown(result, company), encoding="utf-8")
    click.echo(f"{result['verdicts'].get('worth chasing', 0)} of {result['total']} worth chasing -> {out}")
    for reason, n in result["verdicts"].most_common():
        click.echo(f"  {reason}: {n}")


if __name__ == "__main__":
    main()
