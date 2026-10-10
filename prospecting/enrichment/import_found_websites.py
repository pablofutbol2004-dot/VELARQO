"""Load websites/emails that someone (grokbot, a VA) found for companies we
already hold, after checking them ourselves.

    python -m prospecting.enrichment.import_found_websites data/agent_tasks/find_websites_batch1_result.csv

Input columns: company_number, website, email, email_source_url,
number_on_site (as in docs/agent_briefs/grokbot_tasks.md, Task 3).

A website is accepted only if we can confirm it is that company: the company
number on its homepage or on the email's page, or the domain finder's
name/town check, or the finder saw the number and the email is on the same
domain. An email is accepted only if it is on the source page we fetch, or
on the website's own domain.
"""

import csv
import json
from pathlib import Path
from urllib.parse import urlsplit

import click
import requests

from data.supabase_store import connect
from prospecting.enrichment.domain_finder import verify_site
from prospecting.enrichment.places_websites import clean_url, number_on_page
from prospecting.enrichment.site_guard import website_taken
from prospecting.enrichment.website import WebsiteEnrichmentProvider
from prospecting.enrichment.website_refresh import ICP_PATH, USER_AGENT, _new_tier

ICP_PATHS = {"windows": ICP_PATH, "roofing": ICP_PATH.with_name("icp-roofing-uk.json")}


def _host(url: str) -> str:
    return (urlsplit(url if "://" in url else f"https://{url}").hostname or "").lower().removeprefix("www.")


def _email_on_page(url: str, email: str) -> bool:
    try:
        return email.lower() in requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=12).text.lower()
    except requests.RequestException:
        return False


def check_row(row: dict, company: dict, site: dict, vertical_terms) -> tuple[bool, str | None, str]:
    """(website ok, email to store, reason)."""
    website, email = row["website"], (row.get("email") or "").strip().lower()
    source = (row.get("email_source_url") or "").strip()
    number = company["company_number"]
    same_domain = bool(email) and (email.split("@")[-1] == _host(website) or email.split("@")[-1].endswith("." + _host(website)))
    if site.get("website_status") != "ok":
        return False, None, "site did not load"
    # The email's source page only counts if it's on the company's own site:
    # a directory or Companies House page always shows the number.
    source_on_site = bool(source) and _host(source) == _host(website)
    if number_on_page(website, number) or (source_on_site and number_on_page(source, number)):
        reason = "number on site"
    elif verify_site({"company_name": company["legal_name"], "city": company["city"], "postcode": company["postcode"]}, site, vertical_terms):
        reason = "name/town on site"
    elif (row.get("number_on_site") or "").lower() == "yes" and same_domain:
        reason = "finder saw number, email on same domain"
    else:
        return False, None, "could not confirm it's this company"
    if email and (email in (site.get("emails_found") or []) or same_domain or (source and _email_on_page(source, email))):
        return True, email, reason
    return True, None, reason + "; email not confirmed"


@click.command()
@click.argument("paths", nargs=-1, required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True)
def main(paths, dry_run):
    """One or more result files, e.g. data/agent_tasks/batch5/*_result.csv"""
    icps = {v: json.loads(path.read_text()) for v, path in ICP_PATHS.items()}
    terms = {v: [*(i.get("core_terms") or []), *(i.get("adjacent_terms") or [])] for v, i in icps.items()}
    conn = connect()
    conn.autocommit = True
    provider = WebsiteEnrichmentProvider(user_agent=USER_AGENT)
    rows = []
    for path in paths:
        with path.open(encoding="utf-8-sig") as f:
            rows += [(path, r) for r in csv.DictReader(f) if (r.get("website") or "").strip()]
    stats = {"rows_with_website": len(rows), "website_ok": 0, "email_ok": 0, "rejected": 0, "already_had_email": 0}
    for path, row in rows:
        found = conn.execute(
            "select id, company_number, legal_name, city, coalesce(postcode, registered_postcode), tier, icp_score, email, vertical "
            "from companies where company_number = %s and vertical = any(%s) and website is null "
            "order by (vertical = %s) desc limit 1",
            (row["company_number"], list(ICP_PATHS), row.get("trade") or "windows"),
        ).fetchone()
        if not found:
            continue  # unknown company, or already has a website (e.g. a re-run after an interruption)
        company = dict(zip(["id", "company_number", "legal_name", "city", "postcode", "tier", "icp_score", "email", "vertical"], found))
        icp, vertical_terms = icps[company["vertical"]], terms[company["vertical"]]
        website = clean_url(row["website"].strip() if "://" in row["website"] else f"https://{row['website'].strip()}")
        site = provider.enrich({"website": website})
        ok, email, reason = check_row({**row, "website": website}, company, site, vertical_terms)
        if ok and website_taken(conn, website, company["id"]):
            ok, email, reason = False, None, "website already belongs to another company"
        click.echo(f"{'OK ' if ok else '-- '}{company['legal_name'][:42]:42} {website[:40]:40} {email or '':35} {reason}")
        if not ok:
            stats["rejected"] += 1
            continue
        stats["website_ok"] += 1
        stats["email_ok"] += bool(email)
        stats["already_had_email"] += bool(company["email"])
        if dry_run:
            continue
        new_tier = _new_tier(company["tier"], company["icp_score"], icp) if (email or company["email"]) else company["tier"]
        with conn.transaction():
            conn.execute(
                "insert into website_snapshots (company_id, url, status, title, text, emails_found, ad_tags) "
                "values (%s, %s, 'ok', %s, %s, %s, %s)",
                (company["id"], website, site.get("website_title"), site.get("website_text"),
                 site.get("emails_found") or [], site.get("ad_tags")),
            )
            conn.execute(
                "update companies set website = %s, website_status = 'ok', website_title = %s, enriched_at = now(), "
                "email = coalesce(email, %s), email_source = case when email is null and %s::text is not null then 'website' else email_source end, "
                "tier = %s, extra = extra || %s::jsonb, updated_at = now() where id = %s",
                (website, site.get("website_title"), email, email, new_tier,
                 json.dumps({"website_found_via": path.stem, "website_check": reason, "email_source_url": row.get("email_source_url")}),
                 company["id"]),
            )
    click.echo(stats)


if __name__ == "__main__":
    main()
