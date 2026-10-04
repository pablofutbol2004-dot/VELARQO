"""Daily free-data collector: Companies House API facts for every in-trade
company, newest first for the send list.

    python -m prospecting.enrichment.free_facts                 # daily run
    python -m prospecting.enrichment.free_facts --max-requests 50

Per company: profile, officers, persons with significant control, filing
history, and charges / insolvency only when the profile says there are
any. Payloads are stored whole in company_facts (refreshed after
REFRESH_DAYS); company_signals derives usable columns. Officers also feed
public.contacts (see directors.py) the first time.

Free API limit is 600 requests / 5 min; we pace at ~1.9/s, and back off on
429. Safe to stop and re-run at any time.
"""

import os
import time
from datetime import datetime, timedelta, timezone

import click
import requests
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from data.supabase_store import connect
from prospecting.enrichment.directors import active_directors, parse_name

API = "https://api.company-information.service.gov.uk"
PAUSE_SECONDS = 0.52
REFRESH_DAYS = 30

ENDPOINTS = {
    "ch_profile": "/company/{n}",
    "ch_officers": "/company/{n}/officers?items_per_page=100",
    "ch_psc": "/company/{n}/persons-with-significant-control?items_per_page=100",
    "ch_filings": "/company/{n}/filing-history?items_per_page=50",
    "ch_charges": "/company/{n}/charges?items_per_page=100",
    "ch_insolvency": "/company/{n}/insolvency",
}


class Client:
    def __init__(self, key: str, max_requests: int):
        self.key, self.session = key, requests.Session()
        self.remaining = max_requests

    def get(self, path: str) -> dict | None:
        for attempt in range(5):
            if self.remaining <= 0:
                raise StopIteration
            self.remaining -= 1
            time.sleep(PAUSE_SECONDS)
            r = self.session.get(API + path, auth=(self.key, ""), timeout=30)
            if r.status_code == 429:
                time.sleep(60 * (attempt + 1))
                continue
            if r.status_code == 404:
                return {}
            if r.status_code >= 500:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        return None


def _store(conn, company_id, source: str, payload: dict) -> None:
    conn.execute(
        """
        insert into company_facts (company_id, source, payload, fetched_at) values (%s, %s, %s, now())
        on conflict (company_id, source) do update set payload = excluded.payload, fetched_at = now()
        """,
        (company_id, source, Jsonb(payload)),
    )


def _store_contacts(conn, company_id, officers: dict) -> None:
    if conn.execute("select 1 from contacts where company_id = %s and source = 'companies_house' limit 1",
                    (company_id,)).fetchone():
        return
    directors = active_directors(officers.get("items", []))
    for officer in directors:
        full, _ = parse_name(officer.get("name", ""))
        conn.execute(
            "insert into contacts (company_id, full_name, role, source, is_primary) values (%s, %s, 'director', 'companies_house', %s)",
            (company_id, full, len(directors) == 1),
        )
    if not directors:
        conn.execute(
            "insert into contacts (company_id, full_name, role, source, is_primary) values (%s, null, 'none_found', 'companies_house', false)",
            (company_id,),
        )


def companies_to_refresh(conn, limit: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=REFRESH_DAYS)
    return conn.execute(
        """
        select c.id, c.company_number, (q.id is not null) as in_queue
        from companies c
        left join outreach_queue q on q.id = c.id
        left join company_facts p on p.company_id = c.id and p.source = 'ch_profile'
        where c.company_number is not null and c.tier in ('A', 'B', 'C')
          and (p.fetched_at is null or p.fetched_at < %s)
        order by (q.id is not null) desc, q.priority desc nulls last, c.icp_score desc nulls last
        limit %s
        """,
        (cutoff, limit),
    ).fetchall()


@click.command()
@click.option("--max-requests", default=60000, show_default=True, help="Stop after this many API calls (one day ~ 160k max)")
def main(max_requests):
    load_dotenv(".env")
    client = Client(os.environ["COMPANIES_HOUSE_API_KEY"], max_requests)
    conn = connect()
    conn.autocommit = True
    todo = companies_to_refresh(conn, max_requests)
    done = 0
    try:
        for company_id, number, _ in todo:
            profile = client.get(ENDPOINTS["ch_profile"].format(n=number))
            if profile is None:
                continue
            facts = {"ch_profile": profile}
            for source in ("ch_officers", "ch_psc", "ch_filings"):
                facts[source] = client.get(ENDPOINTS[source].format(n=number))
            if profile.get("has_charges"):
                facts["ch_charges"] = client.get(ENDPOINTS["ch_charges"].format(n=number))
            if profile.get("has_insolvency_history"):
                facts["ch_insolvency"] = client.get(ENDPOINTS["ch_insolvency"].format(n=number))
            with conn.transaction():
                for source, payload in facts.items():
                    if payload is not None:
                        _store(conn, company_id, source, payload)
                if facts.get("ch_officers") is not None:
                    _store_contacts(conn, company_id, facts["ch_officers"])
            done += 1
            if done % 100 == 0:
                click.echo(f"{datetime.now():%H:%M} {done}/{len(todo)} companies, {client.remaining} calls left", err=True)
    except StopIteration:
        pass
    click.echo(f"{datetime.now():%Y-%m-%d %H:%M} done: {done} companies refreshed")


if __name__ == "__main__":
    main()
