import click

from prospecting.sourcing.osm import find_businesses

DEFAULT_USER_AGENT = "velarqo-lead-sourcing/0.1 (contact: set SENDER_EMAIL env var or edit this string)"


@click.command()
@click.argument("place")
@click.option("--tag", "tags", multiple=True, required=True, help="OSM tag as key=value, repeatable (e.g. --tag shop=doors --tag craft=carpenter)")
@click.option("--user-agent", default=DEFAULT_USER_AGENT, help="Required by Nominatim's usage policy - identify yourself")
def main(place: str, tags: tuple[str, ...], user_agent: str) -> None:
    parsed_tags = [tuple(tag.split("=", 1)) for tag in tags]

    leads = find_businesses(place, parsed_tags, user_agent=user_agent)

    click.echo(f"Found {len(leads)} businesses in {place!r} matching {parsed_tags}\n")
    for lead in leads:
        click.echo(f"  {lead['company_name']:35} website={lead.get('website')!s:30} phone={lead.get('phone')}")


if __name__ == "__main__":
    main()
