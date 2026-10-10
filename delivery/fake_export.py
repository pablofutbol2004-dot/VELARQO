"""A made-up installer export for dry runs: ~300 old quotes as messy as a
real spreadsheet (mixed date formats, Excel-mangled phones, landlines,
"approx 5k" values, lead-site rows, opt-outs, the same person twice, a
TOTAL row at the bottom). Deterministic: the same seed gives the same file.

    python -m delivery.fake_export clients/dryrun-windows

Writes old_quotes.xlsx, old_quotes.csv and dnc.csv (the installer's
do-not-contact list) into that folder. Phones are Ofcom's drama range
(07700 900xxx), emails are @example.com, names are invented: nothing here
can reach a real person.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

import click
import pandas as pd

FIRST = ["Sarah", "James", "Emma", "David", "Claire", "Mark", "Lisa", "Paul", "Rachel", "Andrew", "Karen", "Steve",
         "Helen", "Gary", "Nicola", "Ian", "Julie", "Chris", "Amanda", "Rob", "Jo", "Mike", "Donna", "Lee", "Tracy"]
LAST = ["Smith", "Jones", "Taylor", "Brown", "Williams", "Wilson", "Johnson", "Davies", "Robinson", "Wright", "Thompson",
        "Evans", "Walker", "White", "Roberts", "Green", "Hall", "Wood", "Jackson", "Clarke", "Patel", "Khan", "Hughes"]
AREAS = ["LS", "LS", "LS", "LS", "BD", "BD", "HG", "WF", "WF", "YO"]        # mostly their area; YO is outside
FAR = ["SW1A 1AA", "M1 1AE", "B1 1AA"]
PRODUCTS = ["Windows", "windows x4", "UPVC windows", "Front door", "Composite door", "Windows & doors", "Bifold doors",
            "French doors", "Conservatory roof", "Patio door", "Back door", "Windows (whole house)", "Porch", ""]
STATUSES = ["Lost", "No reply", "Went elsewhere", "Quoted", "Follow up", "Not now", "DEAD", "Lost - price", "Sent",
            "", "Sold", "Won", "Installed", "Cancelled"]
SOURCES = ["Website", "Website", "Website", "Phone", "Phone", "Recommendation", "Showroom", "Facebook", "",
           "Checkatrade", "Checkatrade", "Bark", "MyBuilder", "Bought leads", "Rated People"]
OPT_OUT = ["", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "", "Y", "yes", "DO NOT CONTACT", "no"]


def _date_text(rng: random.Random, when: date):
    style = rng.randrange(10)
    if style < 5:
        return when.strftime("%d/%m/%Y")
    if style == 5:
        return when.isoformat()
    if style == 6:
        return when.strftime("%d %b %y")
    if style == 7:
        return when.strftime("%d.%m.%y")
    if style == 8:
        return when                                   # a real date cell
    return rng.choice(["", "TBC", "?", "last spring"])


def _phone_text(rng: random.Random, n: int):
    number = f"07700{n:06d}"
    style = rng.randrange(12)
    if style < 5:
        return f"{number[:5]} {number[5:]}"
    if style == 5:
        return number
    if style == 6:
        return f"+44 {number[1:5]} {number[5:]}"
    if style == 7:
        return int(number[1:])                        # Excel dropped the leading 0 and made it a number
    if style == 8:
        return f"{number} / 0113 496 0123"            # mobile and landline together
    if style == 9:
        return "0113 496 0123"                        # landline only: can't be texted
    return ""                                         # no phone (email only, or nothing)


def _value_text(rng: random.Random):
    value = rng.choice([1200, 1850, 2400, 3450, 4200, 5600, 7800, 9200, 12500, 18000])
    style = rng.randrange(8)
    if style < 3:
        return value
    if style == 3:
        return f"£{value:,}"
    if style == 4:
        return f"{value}.00"
    if style == 5:
        return f"approx {value // 1000}k"
    return ""


def rows(seed: int = 2026, n: int = 300, today: date | None = None) -> list[dict]:
    rng = random.Random(seed)
    today = today or date.today()
    out = []
    people = []
    for i in range(n):
        first, last = rng.choice(FIRST), rng.choice(LAST)
        months = rng.choice([1, 2, 2, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 16, 18, 20, 23, 25, 28, 36])
        quoted = today - timedelta(days=months * 30 + rng.randrange(28))
        postcode = rng.choice(FAR) if rng.randrange(25) == 0 else f"{rng.choice(AREAS)}{rng.randrange(1, 28)} {rng.randrange(1, 9)}{rng.choice('ABDEFGHJLNPQRSTUWXYZ')}{rng.choice('ABDEFGHJLNPQRSTUWXYZ')}"
        mail = f"{first}.{last}{i}@example.com".lower() if rng.randrange(3) else ""
        people.append((first, last, i, mail, postcode))
        out.append({
            "Quote No": f"Q-{2024 + (i % 3)}-{1000 + i}",
            "Date Quoted": _date_text(rng, quoted),
            "Customer": f"{first} {last}" if rng.randrange(20) else f"{last}, {first}",
            "Tel": _phone_text(rng, i),
            "Email": mail,
            "Post Code": postcode if rng.randrange(15) else "",
            "Job": rng.choice(PRODUCTS),
            "Quote £": _value_text(rng),
            "Status": rng.choice(STATUSES),
            "Source": rng.choice(SOURCES),
            "Opt out": rng.choice(OPT_OUT),
            "Notes": rng.choice(["", "", "", "", "said call back after Xmas", "wants finance", "partner to decide", "rang twice no answer"]),
        })
    # The same person again: a second quote with the same mobile, an
    # email-only row for someone who had a phone, and an exact duplicate.
    for j in range(12):
        src = out[rng.randrange(n)]
        twin = dict(src)
        twin["Quote No"] = f"Q-2025-{2000 + j}"
        twin["Date Quoted"] = (today - timedelta(days=rng.randrange(100, 600))).strftime("%d/%m/%Y")
        twin["Job"] = rng.choice(PRODUCTS[:6])
        twin["Status"] = rng.choice(["Lost", "No reply", "Quoted"])
        if j % 3 == 1 and twin["Email"]:
            twin["Tel"] = ""                              # same person, email only
        out.append(twin)
    out.append(dict(out[rng.randrange(n)]))             # exact duplicate row
    out.append({k: "" for k in out[0]})                 # blank row
    out.append({**{k: "" for k in out[0]}, "Customer": "TOTAL", "Quote £": sum(v for r in out if isinstance(v := r.get("Quote £"), int))})
    return out


def dnc_rows(records: list[dict], seed: int = 2026) -> list[dict]:
    """The installer's own do-not-contact list: a handful of phones/emails,
    some overlapping the export, some not."""
    rng = random.Random(seed + 1)
    picks = [r for r in rng.sample(records[:200], 6) if r.get("Tel") or r.get("Email")]
    out = [{"Phone": str(r["Tel"]).split("/")[0].strip() if r.get("Tel") else "", "Email": r.get("Email", "")} for r in picks]
    out.append({"Phone": "07700 900998", "Email": ""})
    out.append({"Phone": "", "Email": "nobody.here@example.com"})
    return out


def write(folder: Path, seed: int = 2026, n: int = 300, today: date | None = None) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    records = rows(seed, n, today)
    frame = pd.DataFrame(records)
    frame.to_excel(folder / "old_quotes.xlsx", index=False)
    frame.to_csv(folder / "old_quotes.csv", index=False)
    with (folder / "dnc.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["Phone", "Email"])
        writer.writeheader()
        writer.writerows(dnc_rows(records, seed))
    return {"rows": len(records), "xlsx": folder / "old_quotes.xlsx", "csv": folder / "old_quotes.csv", "dnc": folder / "dnc.csv"}


@click.command()
@click.argument("folder", type=click.Path(path_type=Path))
@click.option("--seed", default=2026, show_default=True)
@click.option("--rows", "n", default=300, show_default=True)
def main(folder: Path, seed: int, n: int):
    if "clients" not in folder.resolve().parts:
        raise click.UsageError("write it under clients/<slug>/ (git ignores that folder)")
    result = write(folder, seed, n)
    click.echo(f"{result['rows']} rows -> {result['xlsx']}, {result['csv']}, {result['dnc']}")


if __name__ == "__main__":
    main()
