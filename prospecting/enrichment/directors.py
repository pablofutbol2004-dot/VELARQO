"""Directors from the Companies House API -> public.contacts.

Gives the send list a real person to greet. Every active director is
stored (source 'companies_house'); is_primary is set only when a company
has exactly one active director, because guessing which of several is
"the owner" is how you end up writing to the wrong person.

    python -m prospecting.enrichment.directors            # every company in outreach_queue
    python -m prospecting.enrichment.directors --limit 20

Free API, 600 requests per 5 minutes: we pace at ~1.9/s. Re-runs skip
companies that already have Companies House contacts.
"""

import os
import time

import click
import requests
from dotenv import load_dotenv

from data.supabase_store import connect

API = "https://api.company-information.service.gov.uk"
PAUSE_SECONDS = 0.52


def parse_name(raw: str) -> tuple[str, str]:
    """'SMITH, Wayne John' -> ('Wayne John Smith', 'Wayne')."""
    if "," in raw:
        surname, forenames = (part.strip() for part in raw.split(",", 1))
    else:
        parts = raw.split()
        surname, forenames = (parts[-1], " ".join(parts[:-1])) if len(parts) > 1 else (raw, "")
    def tidy(s: str) -> str:
        words = []
        for w in s.split():
            w = w.title() if w.isupper() or w.islower() else w
            if w.startswith("Mc") and len(w) > 2:
                w = "Mc" + w[2].upper() + w[3:]
            words.append(w)
        return " ".join(words)
    forenames, surname = tidy(forenames), tidy(surname)
    full = f"{forenames} {surname}".strip()
    return full, (forenames.split()[0] if forenames else "")


def active_directors(items: list[dict]) -> list[dict]:
    return [o for o in items if o.get("officer_role") == "director" and not o.get("resigned_on")]


def fetch_officers(company_number: str, key: str, session: requests.Session) -> list[dict]:
    for attempt in range(4):
        r = session.get(f"{API}/company/{company_number}/officers", auth=(key, ""),
                        params={"items_per_page": 100}, timeout=30)
        if r.status_code == 429:
            time.sleep(60 * (attempt + 1))
            continue
        if r.status_code == 404:
            return []
        r.raise_for_status()
        return r.json().get("items", [])
    raise RuntimeError(f"rate limited on {company_number}")


@click.command()
@click.option("--limit", default=None, type=int)
def main(limit):
    load_dotenv(".env")
    key = os.environ["COMPANIES_HOUSE_API_KEY"]
    conn = connect()
    conn.autocommit = True
    todo = conn.execute(
        """
        select q.id, q.company_number from outreach_queue q
        where q.company_number is not null
          and not exists (select 1 from contacts c where c.company_id = q.id and c.source = 'companies_house')
        order by q.priority desc
        """ + (f" limit {int(limit)}" if limit else "")
    ).fetchall()
    session = requests.Session()
    stats = {"companies": 0, "single_director": 0, "multi": 0, "none": 0}
    for i, (company_id, number) in enumerate(todo, 1):
        directors = active_directors(fetch_officers(number, key, session))
        with conn.transaction():
            for officer in directors:
                full, _ = parse_name(officer.get("name", ""))
                conn.execute(
                    "insert into contacts (company_id, full_name, role, source, is_primary) values (%s, %s, 'director', 'companies_house', %s)",
                    (company_id, full, len(directors) == 1),
                )
            if not directors:
                # marker row so re-runs skip it
                conn.execute(
                    "insert into contacts (company_id, full_name, role, source, is_primary) values (%s, null, 'none_found', 'companies_house', false)",
                    (company_id,),
                )
        stats["companies"] += 1
        stats["single_director" if len(directors) == 1 else "multi" if directors else "none"] += 1
        if i % 100 == 0:
            click.echo(f"{i}/{len(todo)} {stats}", err=True)
        time.sleep(PAUSE_SECONDS)
    click.echo(f"done {stats}")


if __name__ == "__main__":
    main()
