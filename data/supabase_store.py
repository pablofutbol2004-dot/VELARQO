"""Pushes the lead universe into Supabase Postgres (schema:
supabase/migrations/). Idempotent: re-running updates rows and appends
history instead of duplicating.

Connection: DATABASE_URL in the environment or D:/velarqo/.env (gitignored).
Use the "Session pooler" connection string from the Supabase dashboard
(Connect button). It carries the database password - never commit it.

A business keeps one row across runs even when its identity improves
(first seen on OSM, later matched to Companies House): existing rows are
found by any known identifier - company number, OSM id, or source_key.
"""

import hashlib
import json
import os
from datetime import date, datetime

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

from prospecting.deduplication.merge import match_name

COMPANY_COLUMNS = [
    "vertical", "source_key", "display_name", "legal_name", "match_name", "company_number",
    "osm_ids", "sources", "sic_codes", "accounts_category", "company_category", "incorporation_date",
    "brand", "website", "email", "email_source", "phone", "address", "city", "postcode",
    "registered_postcode", "lat", "lon", "website_status", "website_title", "emails_found",
    "enriched_at", "icp_score", "tier", "vertical_fit", "score_reasons", "score_breakdown",
    "icp_version", "merge_confidence", "extra",
]
_EXTRA_FIELDS = ("industry", "osm_category", "lead_source", "merged_count", "company_numbers", "match_reason", "website_signals", "accreditations")


def connect() -> psycopg.Connection:
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not set. Add the Supabase Session pooler connection string to D:/velarqo/.env"
        )
    return psycopg.connect(url)


def icp_version(icp: dict) -> str:
    return hashlib.sha1(json.dumps(icp, sort_keys=True).encode()).hexdigest()[:12]


def _district(postcode) -> str:
    postcode = str(postcode or "").strip().upper()
    return postcode.split()[0] if " " in postcode else postcode[:-3]


def source_key(lead: dict) -> str:
    if lead.get("company_number"):
        return f"ch:{lead['company_number']}"
    if lead.get("osm_ids"):
        return f"osm:{sorted(lead['osm_ids'])[0]}"
    return f"name:{match_name(lead.get('company_name') or lead.get('display_name'))}|{_district(lead.get('postcode'))}"


def _list(value) -> list:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(v) for v in value if v not in (None, "")]
    return str(value).split()


def _float(value):
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _date(value) -> date | None:
    try:
        return datetime.strptime(str(value), "%d/%m/%Y").date() if value else None
    except ValueError:
        return None


def company_row(lead: dict, vertical: str, version: str) -> dict:
    return {
        "vertical": vertical,
        "source_key": source_key(lead),
        "display_name": lead.get("display_name") or lead.get("company_name"),
        "legal_name": lead.get("legal_name"),
        "match_name": match_name(lead.get("company_name")),
        "company_number": lead.get("company_number"),
        "osm_ids": _list(lead.get("osm_ids") or lead.get("osm_id")),
        "sources": _list(lead.get("sources")),
        "sic_codes": _list(lead.get("sic_codes")),
        "accounts_category": lead.get("accounts_category"),
        "company_category": lead.get("company_category"),
        "incorporation_date": _date(lead.get("incorporation_date")),
        "brand": lead.get("brand"),
        "website": lead.get("website"),
        "email": lead.get("email"),
        "email_source": lead.get("email_source") or ("source" if lead.get("email") else None),
        "phone": lead.get("phone"),
        "address": lead.get("address"),
        "city": lead.get("city"),
        "postcode": lead.get("postcode"),
        "registered_postcode": lead.get("registered_postcode"),
        "lat": _float(lead.get("lat")),
        "lon": _float(lead.get("lon")),
        "website_status": lead.get("website_status"),
        "website_title": lead.get("website_title"),
        "emails_found": _list(lead.get("emails_found")),
        "enriched_at": lead.get("website_fetched_at"),
        "icp_score": lead.get("icp_score"),
        "tier": lead.get("tier") if lead.get("tier") in ("A", "B", "C", "reject") else None,
        "vertical_fit": lead.get("vertical_fit"),
        "score_reasons": lead.get("score_reasons") or [],
        "score_breakdown": Jsonb(lead.get("score_breakdown") or {}),
        "icp_version": version,
        "merge_confidence": lead.get("merge_confidence"),
        "extra": Jsonb({k: lead[k] for k in _EXTRA_FIELDS if lead.get(k) not in (None, "", [])}),
    }


# A rebuild must not undo work done since the last one: websites and emails
# verified by the daily refresh, Places lookup or grokbot imports, the tier
# they earned, and markers kept in extra (e.g. places_checked_at). Column
# names on the right of these expressions are the row's current values.
_STICKY = {
    "website": "coalesce(website, %(website)s)",
    "email": "coalesce(email, %(email)s)",
    "email_source": "case when email is not null then email_source else %(email_source)s end",
    "website_status": "coalesce(%(website_status)s, website_status)",
    "website_title": "coalesce(%(website_title)s, website_title)",
    "emails_found": "case when cardinality(%(emails_found)s::text[]) > 0 then %(emails_found)s::text[] else emails_found end",
    "enriched_at": "greatest(enriched_at, %(enriched_at)s::timestamptz)",
    "icp_score": "greatest(icp_score, %(icp_score)s::numeric)",
    "tier": "case when email is not null and tier in ('A', 'B') then tier else %(tier)s end",
    "extra": "extra || %(extra)s::jsonb",
}


def _update_expr(column: str) -> str:
    return _STICKY.get(column, f"%({column})s")


def _existing_index(cur, vertical: str) -> tuple[dict, dict, dict]:
    cur.execute("select id, source_key, company_number, osm_ids from public.companies where vertical = %s", (vertical,))
    by_key, by_number, by_osm = {}, {}, {}
    for company_id, key, number, osm_ids in cur.fetchall():
        by_key[key] = company_id
        if number:
            by_number[number] = company_id
        for osm_id in osm_ids or []:
            by_osm[osm_id] = company_id
    return by_key, by_number, by_osm


def _strip_nul(value):
    """Postgres text can't hold NUL (0x00); some scraped pages contain it."""
    if isinstance(value, str):
        return value.replace("\x00", "")
    if isinstance(value, dict):
        return {k: _strip_nul(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_strip_nul(v) for v in value]
    return value


def push_universe(conn: psycopg.Connection, leads: list[dict], vertical: str, icp: dict) -> dict:
    version = icp_version(icp)
    for lead in leads:
        lead.update(_strip_nul(dict(lead)))
    stats = {"inserted": 0, "updated": 0, "source_records": 0, "snapshots_new": 0, "scores_new": 0}

    with conn.transaction(), conn.cursor() as cur:
        by_key, by_number, by_osm = _existing_index(cur, vertical)
        rows = [company_row(lead, vertical, version) for lead in leads]

        updates, inserts = [], []
        for lead, row in zip(leads, rows):
            existing = (
                by_key.get(row["source_key"])
                or next((by_number[n] for n in lead.get("company_numbers") or [row["company_number"]] if n in by_number), None)
                or next((by_osm[o] for o in row["osm_ids"] if o in by_osm), None)
            )
            (updates if existing else inserts).append((lead, row, existing))

        set_clause = ", ".join(f"{c} = {_update_expr(c)}" for c in COMPANY_COLUMNS if c != "vertical")
        cur.executemany(
            f"update public.companies set {set_clause} where id = %(id)s",
            [{**row, "id": existing} for _, row, existing in updates],
        )
        for lead, _, existing in updates:
            lead["company_id"] = existing
        stats["updated"] = len(updates)

        columns = ", ".join(COMPANY_COLUMNS)
        placeholders = ", ".join(f"%({c})s" for c in COMPANY_COLUMNS)
        new_ids = _executemany_returning(
            cur,
            f"insert into public.companies ({columns}) values ({placeholders}) returning id",
            [row for _, row, _ in inserts],
        )
        for (lead, _, _), (company_id,) in zip(inserts, new_ids):
            lead["company_id"] = company_id
        stats["inserted"] = len(inserts)

        cur.executemany(
            "insert into public.events (company_id, type, payload) values (%s, 'sourced', %s)",
            [(lead["company_id"], Jsonb({"sources": lead.get("sources") or []})) for lead, _, _ in inserts],
        )

        source_rows = [
            (lead["company_id"], raw["source"], raw["source_id"], Jsonb(raw["payload"]))
            for lead in leads for raw in lead.get("raw_sources") or []
        ]
        cur.executemany(
            """insert into public.source_records (company_id, source, source_id, payload)
               values (%s, %s, %s, %s)
               on conflict (source, source_id) do update
               set company_id = excluded.company_id, payload = excluded.payload, last_seen_at = now()""",
            source_rows,
        )
        stats["source_records"] = len(source_rows)

        snapshot_rows = [
            (lead["company_id"], lead["website"], lead["website_status"], lead.get("website_title"),
             lead.get("website_text"), _list(lead.get("emails_found")), lead["website_fetched_at"])
            for lead in leads if lead.get("website_status") and lead.get("website_fetched_at") and lead.get("website")
        ]
        enriched_ids = [row[0] for row in _executemany_returning(
            cur,
            """insert into public.website_snapshots (company_id, url, status, title, text, emails_found, fetched_at)
               values (%s, %s, %s, %s, %s, %s, %s)
               on conflict (company_id, url, fetched_at) do nothing
               returning company_id""",
            snapshot_rows,
        )]
        stats["snapshots_new"] = len(enriched_ids)
        cur.executemany(
            "insert into public.events (company_id, type) values (%s, 'enriched')",
            [(company_id,) for company_id in enriched_ids],
        )

        scored = _executemany_returning(
            cur,
            """insert into public.score_history (company_id, icp_version, score, tier, vertical_fit, breakdown, reasons)
               values (%s, %s, %s, %s, %s, %s, %s)
               on conflict (company_id, icp_version) do update
               set score = excluded.score, tier = excluded.tier, vertical_fit = excluded.vertical_fit,
                   breakdown = excluded.breakdown, reasons = excluded.reasons, scored_at = now()
               returning company_id, (xmax = 0) as inserted""",
            [
                (lead["company_id"], version, lead.get("icp_score"), lead.get("tier"), lead.get("vertical_fit"),
                 Jsonb(lead.get("score_breakdown") or {}), lead.get("score_reasons") or [])
                for lead in leads
            ],
        )
        newly_scored = [company_id for company_id, inserted in scored if inserted]
        stats["scores_new"] = len(newly_scored)
        cur.executemany(
            "insert into public.events (company_id, type, payload) values (%s, 'scored', %s)",
            [(company_id, Jsonb({"icp_version": version})) for company_id in newly_scored],
        )
    return stats


def _executemany_returning(cur, sql: str, params: list) -> list[tuple]:
    """executemany + RETURNING, rows in input order. Statements that
    return nothing (ON CONFLICT DO NOTHING) contribute no row."""
    if not params:
        return []
    cur.executemany(sql, params, returning=True)
    rows = []
    while True:
        rows.extend(cur.fetchall())
        if not cur.nextset():
            break
    return rows

