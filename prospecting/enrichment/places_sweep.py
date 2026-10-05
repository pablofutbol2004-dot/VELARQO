"""Sweep the UK town by town with Google Places, inside the free allowance.

    python -m prospecting.enrichment.places_sweep --limit 30
    python -m prospecting.enrichment.places_sweep --limit 2 --dry-run

One free lookup ("double glazing Leeds") returns up to 20 businesses with
their websites, against 1 per lookup when searching company by company
(places_websites.py). For each business we don't already have a website for:
read its own site, find the company number on it (UK companies must show
it), and attach the website and email to that Companies House company. If
no number is shown, the business name must match one of our companies and
pass the domain finder's name/town check. Sole traders and firms outside our
Companies House list are skipped: we can't email them anyway.

Only the place ID would be storable under Google's terms; we store nothing
from Google, only what the company's own website says.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

import click
import requests
from dotenv import load_dotenv

from data.supabase_store import connect
from integrations.places.client import FreeAllowanceUsed, PlacesClient, usage
from prospecting.deduplication.merge import match_name
from prospecting.enrichment.domain_finder import verify_site
from prospecting.enrichment.places_websites import clean_url
from prospecting.enrichment.website import WebsiteEnrichmentProvider
from prospecting.enrichment.website_refresh import ICP_PATH, USER_AGENT, _new_tier

ROOT = Path(__file__).parents[2]
QUERIES = ("double glazing {town}", "windows and doors {town}")
SKIP_HOSTS = re.compile(r"facebook\.com|instagram\.com|checkatrade\.com|yell\.com|google\.|linktr\.ee|wix\.com$")
_NUMBER = re.compile(
    r"(?:company|registration|reg\.?|registered)\s*(?:no\.?|number|num\.?)?[\s:.#]*((?:SC|NI|OC)?\d{6,8})\b", re.I
)


def host(url: str) -> str:
    return (urlsplit(url if "://" in url else f"https://{url}").hostname or "").lower().removeprefix("www.")


def numbers_on_site(url: str) -> set[str]:
    """Company numbers shown on the homepage (usually in the footer)."""
    try:
        html = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12).text
    except requests.RequestException:
        return set()
    text = re.sub(r"<[^>]+>", " ", html)
    return {n.upper() if not n.isdigit() else n.zfill(8) for n in _NUMBER.findall(text)}


def towns_todo(conn, limit: int) -> list[tuple[str, str]]:
    """(query, town) pairs not yet run, towns with the most unreached
    window companies first."""
    towns = conn.execute(
        """select initcap(city) as town, count(*) from companies
           where vertical = 'windows' and tier = 'C' and email is null and city is not null
           group by 1 order by 2 desc"""
    ).fetchall()
    done = {q for (q,) in conn.execute("select query from places_sweep").fetchall()}
    todo = [(q.format(town=t), t) for t, _ in towns for q in QUERIES]
    return [(q, t) for q, t in todo if q not in done][:limit]


def find_company(conn, numbers: set[str], name: str, town: str):
    columns = "id, company_number, legal_name, city, coalesce(postcode, registered_postcode), tier, icp_score, email, website"
    if numbers:
        row = conn.execute(
            f"select {columns} from companies where vertical = 'windows' and company_number = any(%s) and tier <> 'reject' limit 1",
            (sorted(numbers),),
        ).fetchone()
        if row:
            return row, "number on site"
    key = match_name(name)
    if not key:
        return None, None
    row = conn.execute(
        f"select {columns} from companies where vertical = 'windows' and match_name = %s and tier <> 'reject' "
        "order by (initcap(city) = %s) desc limit 1",
        (key, town),
    ).fetchone()
    return (row, "name match") if row else (None, None)


@click.command()
@click.option("--limit", default=30, show_default=True, help="Searches this run (each is one free lookup)")
@click.option("--dry-run", is_flag=True)
def main(limit, dry_run):
    load_dotenv(ROOT / ".env")
    icp = json.loads(ICP_PATH.read_text())
    vertical_terms = [*(icp.get("core_terms") or []), *(icp.get("adjacent_terms") or [])]
    conn = connect()
    conn.autocommit = True
    places = PlacesClient(os.environ["GOOGLE_PLACES_API_KEY"], conn)
    provider = WebsiteEnrichmentProvider(user_agent=USER_AGENT)
    known_hosts = {host(w) for (w,) in conn.execute("select website from companies where website is not null").fetchall()}
    stats = {"searches": 0, "businesses": 0, "new_websites": 0, "matched": 0, "emails": 0, "sendable_tier": 0}

    for query, town in towns_todo(conn, limit):
        try:
            results = places.text_search(query, page_size=20)
        except FreeAllowanceUsed as exc:
            click.echo(f"stopping: free allowance reached ({exc})")
            break
        stats["searches"] += 1
        stats["businesses"] += len(results)
        matched_here = 0
        for place in results:
            uri = clean_url(place["websiteUri"]) if place.get("websiteUri") else None
            if not uri or SKIP_HOSTS.search(host(uri)) or host(uri) in known_hosts:
                continue
            known_hosts.add(host(uri))
            stats["new_websites"] += 1
            company, reason = find_company(conn, numbers_on_site(uri), (place.get("displayName") or {}).get("text", ""), town)
            if not company:
                continue
            company_id, number, legal_name, city, postcode, tier, score, email_before, website_before = company
            if website_before:
                continue
            site = provider.enrich({"website": uri})
            if site.get("website_status") != "ok":
                continue
            lead = {"company_name": legal_name, "city": city, "postcode": postcode}
            if reason == "name match" and not verify_site(lead, site, vertical_terms):
                continue
            email = site.get("email")
            matched_here += 1
            stats["matched"] += 1
            stats["emails"] += bool(email)
            new_tier = _new_tier(tier, score, icp) if email else tier
            stats["sendable_tier"] += new_tier in ("A", "B")
            click.echo(f"  {legal_name[:45]:45} {uri[:45]:45} {email or ''}  ({reason})")
            if dry_run:
                continue
            with conn.transaction():
                conn.execute(
                    "insert into website_snapshots (company_id, url, status, title, text, emails_found, ad_tags) "
                    "values (%s, %s, 'ok', %s, %s, %s, %s)",
                    (company_id, uri, site.get("website_title"), site.get("website_text"),
                     site.get("emails_found") or [], site.get("ad_tags")),
                )
                conn.execute(
                    "update companies set website = %s, website_status = 'ok', website_title = %s, enriched_at = now(), "
                    "email = coalesce(email, %s), email_source = case when email is null and %s::text is not null "
                    "then 'website' else email_source end, tier = %s, "
                    "extra = extra || %s::jsonb, updated_at = now() where id = %s",
                    (uri, site.get("website_title"), email, email, new_tier,
                     json.dumps({"website_found_via": "places_sweep", "website_check": reason}), company_id),
                )
        click.echo(f"{query}: {len(results)} businesses, {matched_here} matched")
        if not dry_run:
            conn.execute(
                "insert into places_sweep (query, town, results, matched) values (%s, %s, %s, %s) "
                "on conflict (query) do update set done_at = now(), results = excluded.results, matched = excluded.matched",
                (query, town, len(results), matched_here),
            )

    day, month = usage(conn)
    click.echo(f"{datetime.now():%Y-%m-%d %H:%M} places sweep done: {stats}; free allowance used: {day} today, {month} this month")


if __name__ == "__main__":
    main()
