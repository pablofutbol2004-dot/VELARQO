"""Build the UK-wide lead universe for a vertical: every candidate business
from every free source, merged into one record per business, scored,
optionally enriched, with a coverage report that says honestly how much of
it is actually reachable.

  python -m pipelines.uk_universe.build \\
      --osm data/osm_uk_doors_windows.csv --companies-house data/ch_uk_doors_windows.csv \\
      --enrich-websites --export data/uk_doors_windows_universe.csv
"""

import csv
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import click

from lib.normalization.normalize import normalize_lead
from lib.scoring.icp_score import evaluate_lead
from pipelines.cold_outreach.pipeline import DEFAULT_ICP_PATH, TIER_ORDER, build_campaign, export_leads, load_icp
from lib.ai.research import research_leads
from prospecting.deduplication.merge import merge_sources
from prospecting.enrichment.batch import enrich_websites as enrich_websites_batch


_JSON_COLUMNS = ("osm_tags", "ch_raw")


def load_csv(path: Path) -> list[dict]:
    csv.field_size_limit(10_000_000)
    rows = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row = {k: (v if v != "" else None) for k, v in row.items()}
            for column in _JSON_COLUMNS:
                if row.get(column):
                    row[column] = json.loads(row[column])
            rows.append(row)
    return rows


def build_universe(sources: list[list[dict]], icp: dict, enrich=None) -> list[dict]:
    leads = merge_sources([lead for source in sources for lead in source])
    now = datetime.now(timezone.utc).isoformat()
    leads = [normalize_lead({**lead, "id": str(uuid.uuid4()), "created_at": now}) for lead in leads]
    if enrich:
        leads = enrich(leads)
    for lead in leads:
        result = evaluate_lead(lead, icp)
        lead.update(
            icp_score=result["score"], qualified=result["qualified"], tier=result["tier"],
            vertical_fit=result["vertical_fit"], score_breakdown=result["breakdown"], score_reasons=result["reasons"],
        )
    return research_leads(leads, icp)


def coverage_report(raw_counts: dict[str, int], leads: list[dict]) -> list[str]:
    in_vertical = [l for l in leads if l.get("tier") in ("A", "B", "C")]
    sources = Counter(l.get("lead_source") for l in leads)
    tiers = Counter(l.get("tier") for l in leads)

    def share(n: int, of: int) -> str:
        return f"{n:>7,}  ({n / of:.0%})" if of else f"{n:>7,}"

    lines = ["RAW CANDIDATES"]
    lines += [f"  {name:28} {count:>7,}" for name, count in raw_counts.items()]
    lines += [
        "",
        f"AFTER MERGING DUPLICATES      {len(leads):>7,} unique businesses",
        f"  in both sources             {sources.get('companies_house+osm', 0):>7,}",
        f"  OpenStreetMap only          {sources.get('osm', 0):>7,}",
        f"  Companies House only        {sources.get('companies_house', 0):>7,}",
        "",
        "SCORED AGAINST THE ICP",
        f"  in the vertical (A/B/C)     {len(in_vertical):>7,}",
        f"  rejected (other trade etc.) {tiers.get('reject', 0):>7,}",
        "",
        f"CONTACT COVERAGE of the {len(in_vertical):,} in-vertical businesses",
        f"  email (sendable today)      {share(sum(1 for l in in_vertical if l.get('email')), len(in_vertical))}",
        f"    of which found on website {share(sum(1 for l in in_vertical if l.get('email_source') == 'website'), len(in_vertical))}",
        f"  website, no email found     {share(sum(1 for l in in_vertical if l.get('website') and not l.get('email')), len(in_vertical))}",
        f"  phone only                  {share(sum(1 for l in in_vertical if l.get('phone') and not l.get('email') and not l.get('website')), len(in_vertical))}",
        f"  name + address only         {share(sum(1 for l in in_vertical if not (l.get('phone') or l.get('email') or l.get('website'))), len(in_vertical))}",
        "",
        "TIERS",
        f"  A/B  sendable now           {tiers.get('A', 0) + tiers.get('B', 0):>7,}",
        f"  C    right trade, no email  {tiers.get('C', 0):>7,}",
    ]
    return lines


@click.command()
@click.option("--osm", "osm_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--companies-house", "ch_path", type=click.Path(exists=True, path_type=Path), default=None)
@click.option("--icp", "icp_path", type=click.Path(exists=True, path_type=Path), default=DEFAULT_ICP_PATH)
@click.option("--enrich-websites", is_flag=True, help="Fetch every lead's website (concurrent, cached)")
@click.option("--user-agent", default="velarqo-enrichment/0.1")
@click.option("--workers", default=8, show_default=True)
@click.option("--cache", "cache_path", type=click.Path(path_type=Path), default=Path("data/website_enrichment_cache.jsonl"), show_default=True)
@click.option("--export", "export_path", type=click.Path(path_type=Path), default=None)
@click.option("--report", "report_path", type=click.Path(path_type=Path), default=None)
@click.option("--push-to-supabase", is_flag=True, help="Upsert everything into Supabase (needs DATABASE_URL in .env)")
def main(osm_path, ch_path, icp_path, enrich_websites, user_agent, workers, cache_path, export_path, report_path, push_to_supabase) -> None:
    if not osm_path and not ch_path:
        raise click.UsageError("give --osm and/or --companies-house")
    icp = load_icp(icp_path)

    sources, raw_counts = [], {}
    if osm_path:
        sources.append(load_csv(osm_path))
        raw_counts["OpenStreetMap"] = len(sources[-1])
    if ch_path:
        sources.append(load_csv(ch_path))
        raw_counts["Companies House"] = len(sources[-1])

    enrich = None
    if enrich_websites:
        def progress(done, total):
            if done % 100 == 0 or done == total:
                click.echo(f"  enriched {done}/{total} websites", err=True)

        def enrich(leads):
            return enrich_websites_batch(leads, user_agent, workers=workers, cache_path=cache_path, on_progress=progress)

    leads = build_universe(sources, icp, enrich)
    report = coverage_report(raw_counts, leads)
    click.echo("\n".join(report))

    if report_path:
        report_path.write_text("\n".join(report) + "\n", encoding="utf-8")
    if export_path:
        in_vertical = [l for l in leads if l.get("tier") in TIER_ORDER and l.get("tier") != "duplicate"]
        campaign = build_campaign(in_vertical, icp)
        count = export_leads(in_vertical, campaign, export_path)
        click.echo(f"\nExported {count:,} leads to {export_path}")


if __name__ == "__main__":
    main()
