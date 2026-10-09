"""Find websites for registered window companies we can't reach yet, using
Google Places text search inside the free allowance (~30 lookups a day).

    python -m prospecting.enrichment.places_websites            # daily run
    python -m prospecting.enrichment.places_websites --check 13377953,04622044 --dry-run

Who: tier C limited companies with a good score but no website or email,
best first. For each one, Places is asked for "<name> <town>". A website it
returns only counts if the site itself proves it's the same company: the
company number on the page, or the name check used by the domain finder
(distinctive name words, or full name plus town/postcode). The email then
comes from the company's own site. Only the place ID is kept from Google.
"""

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

import click
import requests
from dotenv import load_dotenv

from data.supabase_store import connect
from integrations.places.client import FreeAllowanceUsed, PlacesClient, usage
from prospecting.enrichment.domain_finder import verify_site
from prospecting.enrichment.website import WebsiteEnrichmentProvider
from prospecting.enrichment.website_refresh import ICP_PATH, USER_AGENT, _new_tier

ROOT = Path(__file__).parents[2]
# Rows already handed to grokbot (Task 3): don't spend lookups twice.
GROKBOT_BATCHES = sorted((ROOT / "data" / "agent_tasks").rglob("find_websites_batch*.csv"))
CORPORATE = ("Private Limited Company", "Limited Liability Partnership", "Public Limited Company")


def search_name(legal_name: str) -> str:
    return re.sub(r"\b(limited|ltd\.?|llp|plc)\b", "", legal_name, flags=re.I).strip(" .,-")


def clean_url(uri: str) -> str:
    """Drops Google's ?utm_... tracking and keeps scheme + host + path."""
    parts = urlsplit(uri)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


def number_on_page(url: str, company_number: str) -> bool:
    """UK companies must show their registered number on their website."""
    digits = company_number.lstrip("0")
    try:
        html = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12).text
    except requests.RequestException:
        return False
    return bool(re.search(rf"(?<!\d)0*{re.escape(digits)}(?!\d)", re.sub(r"<[^>]+>", " ", html)))


def _grokbot_numbers() -> set[str]:
    numbers = set()
    for path in GROKBOT_BATCHES:
        with path.open(encoding="utf-8-sig") as f:
            numbers |= {row["company_number"] for row in csv.DictReader(f)}
    return numbers


def _todo(conn, limit: int, check: list[str] | None):
    if check:
        where, params = "c.company_number = any(%s)", [check]
    else:
        where = """c.tier = 'C' and c.email is null and c.website is null and c.icp_score >= 65
          and c.company_category = any(%s) and coalesce(c.accounts_category, '') not in ('DORMANT', 'NO ACCOUNTS FILED')
          and not (c.extra ? 'places_checked_at') and not (c.company_number = any(%s))"""
        params = [list(CORPORATE), list(_grokbot_numbers())]
    return conn.execute(
        f"""select c.id, c.company_number, c.legal_name, c.city, coalesce(c.postcode, c.registered_postcode),
                   c.tier, c.icp_score, c.website
            from companies c where c.vertical = 'windows' and {where}
            order by (c.legal_name ~* '(window|door|double glaz|upvc|conservator|sash|bifold|bi-fold)') desc,
                     (c.legal_name ~* '(glass merchant|marine|commercial|wholesale|trade frames)') asc,
                     c.icp_score desc, c.incorporation_date asc nulls last limit %s""",
        (*params, limit),
    ).fetchall()


def find_site(places: PlacesClient, provider, vertical_terms, company) -> tuple[dict | None, str | None, str | None]:
    """Returns (site, website, place_id) for the first Places result whose
    own website proves it is this company."""
    _, number, legal_name, city, postcode, *_ = company
    lead = {"company_name": legal_name, "city": city, "postcode": postcode}
    results = places.text_search(f"{search_name(legal_name)} {city or ''}".strip())
    for place in results:
        uri = clean_url(place["websiteUri"]) if place.get("websiteUri") else None
        if not uri or re.search(r"facebook\.com|instagram\.com|checkatrade\.com|yell\.com", uri):
            continue
        site = provider.enrich({"website": uri})
        if site.get("website_status") != "ok":
            continue
        if number_on_page(uri, number) or verify_site(lead, site, vertical_terms):
            return site, uri, place.get("id")
    return None, None, (results[0].get("id") if results else None)


@click.command()
@click.option("--limit", default=30, show_default=True, help="Lookups this run (the client also enforces the free allowance)")
@click.option("--check", default=None, help="Comma-separated company numbers to test (ignores the usual filters)")
@click.option("--dry-run", is_flag=True, help="Look up and print, don't write companies")
def main(limit, check, dry_run):
    load_dotenv(ROOT / ".env")
    icp = json.loads(ICP_PATH.read_text())
    vertical_terms = [*(icp.get("core_terms") or []), *(icp.get("adjacent_terms") or [])]
    conn = connect()
    conn.autocommit = True
    places = PlacesClient(os.environ["GOOGLE_PLACES_API_KEY"], conn)
    provider = WebsiteEnrichmentProvider(user_agent=USER_AGENT)
    stats = {"looked_up": 0, "website": 0, "email": 0, "sendable_tier": 0}

    for company in _todo(conn, limit, check.split(",") if check else None):
        company_id, number, legal_name, city, _, tier, score, known = company
        try:
            site, website, place_id = find_site(places, provider, vertical_terms, company)
        except FreeAllowanceUsed as exc:
            click.echo(f"stopping: free allowance reached ({exc})")
            break
        stats["looked_up"] += 1
        email = (site or {}).get("email")
        click.echo(f"{legal_name[:45]:45} {city or '':15} -> {website or '-'} {email or ''}"
                   + (f"   [known: {known}]" if check else ""))
        if dry_run:
            continue
        checked = {"places_checked_at": datetime.now(timezone.utc).isoformat(), "places_place_id": place_id}
        with conn.transaction():
            conn.execute("update companies set extra = extra || %s::jsonb where id = %s", (json.dumps(checked), company_id))
            if not website:
                continue
            new_tier = _new_tier(tier, score, icp) if email else tier
            conn.execute(
                "insert into website_snapshots (company_id, url, status, title, text, emails_found, ad_tags) "
                "values (%s, %s, 'ok', %s, %s, %s, %s)",
                (company_id, website, site.get("website_title"), site.get("website_text"),
                 site.get("emails_found") or [], site.get("ad_tags")),
            )
            conn.execute(
                "update companies set website = %s, website_status = 'ok', website_title = %s, enriched_at = now(), "
                "email = coalesce(email, %s), email_source = case when %s::text is null then email_source else 'website' end, "
                "tier = %s, updated_at = now() where id = %s",
                (website, site.get("website_title"), email, email, new_tier, company_id),
            )
        stats["website"] += 1
        stats["email"] += bool(email)
        stats["sendable_tier"] += new_tier in ("A", "B")

    day, month = usage(conn)
    click.echo(f"{datetime.now():%Y-%m-%d %H:%M} places lookup done: {stats}; free allowance used: {day} today, {month} this month")


if __name__ == "__main__":
    main()
