"""Daily website refresh: re-reads in-trade companies' own websites, oldest
first, with the improved email extraction (Cloudflare-protected and
"[at]/[dot]" emails, contact/about fallbacks).

    python -m prospecting.enrichment.website_refresh --limit 800

Order: companies with a website but no email first (where a new find turns
a tier C into a sendable lead), then sendable companies not yet checked for
ad tags, then everything else older than REFRESH_DAYS. Each fetch is stored in website_snapshots. A newly found
email is written to companies and, if the stored score already passes the
ICP threshold, the company moves from tier C to A/B (adding an email can
only raise the score, so this never promotes a weak lead).

Same politeness as the original enrichment: robots.txt respected, honest
User-Agent, rate-limited per process.
"""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from data.supabase_store import connect
from prospecting.enrichment.website import WebsiteEnrichmentProvider

REFRESH_DAYS = 30
# Snapshots before this date never looked for ad tags; re-read those once
# (a failed fetch after it is not retried daily).
AD_TAGS_SINCE = datetime(2026, 10, 5, tzinfo=timezone.utc)
USER_AGENT = "velarqo-enrichment/0.2 (+https://velarqo.com; hello@velarqo.com)"
ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


def _todo(conn, limit: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=REFRESH_DAYS)
    return conn.execute(
        """
        select c.id, c.website, c.email, c.tier, c.icp_score
        from companies c
        left join lateral (
          select max(fetched_at) as last, bool_or(ad_tags is not null) as ads_checked
          from website_snapshots s where s.company_id = c.id
        ) w on true
        where c.tier in ('A', 'B', 'C') and c.website is not null
          and (w.last is null or w.last < %s or (c.email is null and w.last < now() - interval '14 days')
               or (c.tier in ('A', 'B') and not coalesce(w.ads_checked, false) and w.last < %s))
        -- Sendable companies (A/B) first, so a parked or dead site is caught
        -- before we email it; then never-fetched; then oldest. No-email
        -- sites are retried every 14 days, not daily.
        order by (c.tier in ('A', 'B')) desc, (w.last is null) desc, w.last nulls first, c.icp_score desc nulls last
        limit %s
        """,
        (cutoff, AD_TAGS_SINCE, limit),
    ).fetchall()


def _new_tier(old_tier: str, score, icp: dict) -> str:
    if old_tier != "C" or score is None:
        return old_tier
    threshold = icp.get("qualification_score_threshold", 65)
    if score >= max(threshold, 80):
        return "A"
    return "B" if score >= threshold else "C"


@click.command()
@click.option("--limit", default=800, show_default=True, help="Websites per run")
@click.option("--workers", default=6, show_default=True)
def main(limit, workers):
    icp = json.loads(ICP_PATH.read_text())
    conn = connect()
    conn.autocommit = True
    todo = _todo(conn, limit)

    def fetch(row):
        provider = WebsiteEnrichmentProvider(user_agent=USER_AGENT)
        try:
            return row, provider.enrich({"website": row[1], "email": row[2]})
        except Exception as exc:  # noqa: BLE001 - one bad site must not stop the run
            return row, {"website_status": f"error: {type(exc).__name__}"}

    stats = {"fetched": 0, "ok": 0, "new_email": 0, "promoted": 0}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for (company_id, website, email, tier, score), result in pool.map(fetch, todo):
            stats["fetched"] += 1
            status = result.get("website_status") or "unknown"
            try:
                _save(conn, company_id, website, email, tier, score, status, result, icp, stats)
            except Exception as exc:  # noqa: BLE001 - one odd site must not stop (or block) every future run
                stats["errors"] = stats.get("errors", 0) + 1
                with conn.transaction():
                    conn.execute(
                        "insert into website_snapshots (company_id, url, status) values (%s, %s, %s)",
                        (company_id, website, f"error: {type(exc).__name__}"[:60]))
            if stats["fetched"] % 100 == 0:
                click.echo(f"{datetime.now():%H:%M} {stats}", err=True)
    click.echo(f"{datetime.now():%Y-%m-%d %H:%M} website refresh done: {stats}")


def _save(conn, company_id, website, email, tier, score, status, result, icp, stats) -> None:
    """One company's snapshot + updates, in its own transaction."""
    with conn.transaction():
        conn.execute(
            "insert into website_snapshots (company_id, url, status, title, text, emails_found, ad_tags) "
            "values (%s, %s, %s, %s, %s, %s, %s)",
            (company_id, website, status, result.get("website_title"), result.get("website_text"),
             result.get("emails_found") or [], result.get("ad_tags")),
        )
        conn.execute(
            "update companies set website_status = %s, enriched_at = now(), "
            "emails_found = coalesce(%s, emails_found) where id = %s",
            (status, result.get("emails_found"), company_id),
        )
        if status == "ok":
            stats["ok"] += 1
        if result.get("email") and not email:
            tier_after = _new_tier(tier, score, icp)
            conn.execute(
                "update companies set email = %s, email_source = 'website', tier = %s where id = %s",
                (result["email"], tier_after, company_id),
            )
            stats["new_email"] += 1
            stats["promoted"] += tier_after != tier


if __name__ == "__main__":
    main()
