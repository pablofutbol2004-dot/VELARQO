"""Re-enrich qualified leads in place, straight from Supabase: re-read each
company's own website and store the UK phone numbers (and any email) found.

Unlike build.py this doesn't rebuild the universe from source CSVs. It only
touches enrichment fields, never identity or score, and never overwrites an
existing email or phone. Every fetch is kept in website_snapshots.

  python -m pipelines.uk_universe.enrich_db --tiers A,B,C
"""

from pathlib import Path

import click
from psycopg.types.json import Jsonb

from data.supabase_store import connect
from prospecting.enrichment.batch import enrich_websites

SELECT_LEADS = """
    select id, website, email, phone from public.companies
    where vertical = %s and tier = any(%s) and website is not null
      and (%s or phone is null)
"""

UPDATE_COMPANY = """
    update public.companies set
      phone = coalesce(phone, %(phone)s),
      phone_source = case when phone is null and %(phone)s is not null then %(phone_source)s else phone_source end,
      phones_found = %(phones_found)s,
      email = coalesce(email, %(email)s),
      email_source = case when email is null and %(email)s is not null then %(email_source)s else email_source end,
      emails_found = %(emails_found)s,
      website_status = %(website_status)s,
      enriched_at = %(fetched_at)s,
      updated_at = now()
    where id = %(id)s
"""

INSERT_SNAPSHOT = """
    insert into public.website_snapshots (company_id, url, status, title, text, emails_found, phones_found, fetched_at)
    values (%(id)s, %(website)s, %(website_status)s, %(website_title)s, %(website_text)s,
            %(emails_found)s, %(phones_found)s, %(fetched_at)s)
    on conflict (company_id, url, fetched_at) do nothing
"""


def update_rows(leads: list[dict]) -> list[dict]:
    """Rows for leads whose site was actually fetched this run."""
    return [
        {
            "id": lead["id"],
            "website": lead["website"],
            "website_status": lead["website_status"],
            "website_title": lead.get("website_title"),
            "website_text": lead.get("website_text"),
            "fetched_at": lead["website_fetched_at"],
            "phone": lead.get("phone") if lead.get("phone_source") else None,
            "phone_source": lead.get("phone_source"),
            "phones_found": lead.get("phones_found") or [],
            "email": lead.get("email") if lead.get("email_source") == "website" else None,
            "email_source": lead.get("email_source"),
            "emails_found": lead.get("emails_found") or [],
        }
        for lead in leads
        if lead.get("enriched") and lead.get("website_status") and lead.get("website_fetched_at")
    ]


@click.command()
@click.option("--vertical", default="windows", show_default=True)
@click.option("--tiers", default="A,B,C", show_default=True)
@click.option("--all", "refetch_all", is_flag=True, help="Also re-fetch leads that already have a phone")
@click.option("--limit", type=int, default=None, help="Only the first N leads (for a trial run)")
@click.option("--user-agent", default="velarqo-enrichment/0.1", show_default=True)
@click.option("--workers", default=8, show_default=True)
@click.option("--cache", "cache_path", type=click.Path(path_type=Path),
              default=Path("data/phone_enrichment_cache.jsonl"), show_default=True)
@click.option("--dry-run", is_flag=True, help="Fetch and report, but write nothing to Supabase")
def main(vertical, tiers, refetch_all, limit, user_agent, workers, cache_path, dry_run) -> None:
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(SELECT_LEADS, (vertical, tiers.split(","), refetch_all))
            leads = [dict(zip(("id", "website", "email", "phone"), row)) for row in cur.fetchall()]
        leads = leads[:limit] if limit else leads
        click.echo(f"{len(leads)} leads to enrich", err=True)

        def progress(done, total):
            if done % 100 == 0 or done == total:
                click.echo(f"  fetched {done}/{total} websites", err=True)

        enriched = enrich_websites(leads, user_agent, workers=workers, cache_path=cache_path, on_progress=progress)
        rows = update_rows(enriched)
        new_phones = sum(1 for r in rows if r["phone"])
        new_emails = sum(1 for r in rows if r["email"])
        click.echo(f"{len(rows)} sites read: {new_phones} new phones, {new_emails} new emails", err=True)

        if dry_run:
            return
        with conn.transaction(), conn.cursor() as cur:
            cur.executemany(UPDATE_COMPANY, rows)
            cur.executemany(INSERT_SNAPSHOT, rows)
            cur.executemany(
                "insert into public.events (company_id, type, payload) values (%s, 'enriched', %s)",
                [(r["id"], Jsonb({"phone_found": bool(r["phone"]), "email_found": bool(r["email"])})) for r in rows],
            )
        click.echo("written to Supabase", err=True)


if __name__ == "__main__":
    main()
