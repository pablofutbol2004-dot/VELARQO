import csv
from pathlib import Path

import click

from prospecting.sourcing.osm import find_businesses

DEFAULT_USER_AGENT = "velarqo-lead-sourcing/0.1 (contact: set SENDER_EMAIL env var or edit this string)"

# Columns match pipelines/cold_outreach/pipeline.py's expected CSV shape,
# so output from this CLI can be fed straight into that pipeline.
CSV_COLUMNS = [
    "company_name", "website", "email", "phone", "postcode", "address", "city",
    "company_size", "revenue", "industry", "osm_category", "brand", "lead_source",
]


def _dedupe_raw(leads: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for lead in leads:
        key = (lead.get("company_name", "").lower(), lead.get("postcode") or "")
        if key in seen:
            continue
        seen.add(key)
        unique.append(lead)
    return unique


@click.command()
@click.option("--place", "places", multiple=True, required=True, help="Place name, repeatable (e.g. --place 'Manchester, UK' --place 'Leeds, UK')")
@click.option("--tag", "tags", multiple=True, required=True, help="OSM tag as key=value, repeatable (e.g. --tag shop=doors --tag craft=glaziery)")
@click.option("--user-agent", default=DEFAULT_USER_AGENT, help="Required by Nominatim's usage policy - identify yourself with a real contact")
@click.option("--output", "output_path", type=click.Path(path_type=Path), default=None, help="Write results as a CSV ready for pipelines.cold_outreach.pipeline")
def main(places: tuple[str, ...], tags: tuple[str, ...], user_agent: str, output_path: Path | None) -> None:
    parsed_tags = [tuple(tag.split("=", 1)) for tag in tags]

    all_leads: list[dict] = []
    for place in places:
        click.echo(f"Sourcing {place!r} for {parsed_tags}...")
        try:
            leads = find_businesses(place, parsed_tags, user_agent=user_agent)
        except Exception as exc:
            click.echo(f"  failed: {exc}")
            continue
        click.echo(f"  found {len(leads)}")
        all_leads.extend(leads)

    unique_leads = _dedupe_raw(all_leads)
    click.echo(f"\nTotal: {len(all_leads)} raw, {len(unique_leads)} after exact dedup across places")

    for lead in unique_leads:
        click.echo(f"  {lead['company_name']:35} {lead.get('postcode') or '':10} website={lead.get('website')}")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for lead in unique_leads:
                writer.writerow({col: lead.get(col, "") for col in CSV_COLUMNS})
        click.echo(f"\nWrote {len(unique_leads)} leads to {output_path}")


if __name__ == "__main__":
    main()
