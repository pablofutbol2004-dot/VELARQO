import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import click
import pandas as pd

from data.db import get_connection, init_db
from integrations.ghl.client import GHLClient
from integrations.ghl.sync import sync_leads
from lib.ai.research import research_leads
from lib.normalization.normalize import normalize_lead
from lib.scoring.icp_score import meets_threshold, score_icp
from lib.tracking.experiments import record_send
from outreach.campaign_builder.queue import build_campaign_queue
from outreach.personalization.generator import generate_campaign_emails
from prospecting.deduplication.dedupe import deduplicate
from prospecting.enrichment.enrich import enrich_leads

DEFAULT_ICP_PATH = Path(__file__).parents[2] / "config" / "templates" / "icp-template.json"


def load_icp(icp_path: Path) -> dict:
    return json.loads(icp_path.read_text())


def load_leads_from_csv(csv_path: Path) -> list[dict]:
    df = pd.read_csv(csv_path)
    df = df.astype(object).where(df.notna(), None)
    leads = df.to_dict(orient="records")
    for lead in leads:
        lead["id"] = str(uuid.uuid4())
        lead["created_at"] = datetime.now(timezone.utc).isoformat()
    return leads


def run_pipeline(csv_path: Path, icp_path: Path = DEFAULT_ICP_PATH) -> list[dict]:
    icp = load_icp(icp_path)
    leads = load_leads_from_csv(csv_path)

    leads = [normalize_lead(lead) for lead in leads]
    leads = deduplicate(leads)

    for lead in leads:
        if lead.get("duplicate_of"):
            lead["icp_score"] = None
            lead["qualified"] = False
            continue
        lead["icp_score"] = score_icp(lead, icp)
        lead["qualified"] = meets_threshold(lead["icp_score"], icp)

    leads = enrich_leads(leads)
    leads = research_leads(leads, icp)

    return leads


def build_campaign(leads: list[dict], icp: dict, sender_name: str = "The Team") -> dict:
    emails = generate_campaign_emails(leads, icp, sender_name)
    return build_campaign_queue(emails, icp)


def save_leads(leads: list[dict]) -> None:
    init_db()
    conn = get_connection()
    try:
        for lead in leads:
            conn.execute(
                """
                INSERT OR REPLACE INTO lead
                (id, company_name, website, email, phone, postcode, lead_source,
                 created_at, normalized, icp_score, duplicate_of, ghl_contact_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    lead["id"],
                    lead.get("company_name"),
                    lead.get("website"),
                    lead.get("email"),
                    lead.get("phone"),
                    lead.get("postcode"),
                    lead.get("lead_source"),
                    lead["created_at"],
                    1 if lead.get("normalized") else 0,
                    lead.get("icp_score"),
                    lead.get("duplicate_of"),
                    lead.get("ghl_contact_id"),
                ),
            )
        conn.commit()
    finally:
        conn.close()


@click.command()
@click.argument("csv_path", type=click.Path(exists=True, path_type=Path))
@click.option("--icp", "icp_path", type=click.Path(exists=True, path_type=Path), default=DEFAULT_ICP_PATH)
@click.option("--save/--no-save", default=True, help="Persist results to the SQLite database")
@click.option("--ghl-token", envvar="GHL_API_TOKEN", default=None, help="GHL Private Integration Token (optional)")
@click.option("--ghl-location", envvar="GHL_LOCATION_ID", default=None, help="GHL Location ID (required if --ghl-token is set)")
def main(csv_path: Path, icp_path: Path, save: bool, ghl_token: str | None, ghl_location: str | None) -> None:
    leads = run_pipeline(csv_path, icp_path)

    if ghl_token:
        if not ghl_location:
            raise click.UsageError("--ghl-location is required when --ghl-token is set")
        client = GHLClient(api_token=ghl_token, location_id=ghl_location)
        leads = sync_leads(client, leads)
        click.echo(f"Synced {sum(1 for l in leads if l.get('ghl_contact_id'))} contacts to GHL\n")

    total = len(leads)
    duplicates = sum(1 for lead in leads if lead.get("duplicate_of"))
    qualified = sum(1 for lead in leads if lead.get("qualified"))

    click.echo(f"Processed {total} leads")
    click.echo(f"  Duplicates removed: {duplicates}")
    click.echo(f"  Unique leads: {total - duplicates}")
    click.echo(f"  Qualified (ICP score met): {qualified}")
    click.echo("")

    for lead in leads:
        status = "DUPLICATE" if lead.get("duplicate_of") else ("QUALIFIED" if lead.get("qualified") else "unqualified")
        click.echo(f"  [{status:10}] {lead['company_name']:30} score={lead.get('icp_score')}")

    icp = load_icp(icp_path)
    campaign = build_campaign(leads, icp)
    click.echo(f"\nCampaign {campaign['campaign_id']} queued: {len(campaign['queue'])} emails")
    for item in campaign["queue"]:
        click.echo(f"\n--- {item['company_name']} (variant {item['variant_index']}, send {item['send_time']}) ---")
        click.echo(f"Subject: {item['subject']}")
        click.echo(item["body"])

    if save:
        save_leads(leads)
        for item in campaign["queue"]:
            record_send(item, vertical=icp.get("vertical"))
        click.echo("\nSaved to data/velarqo.db (leads + experiment_result rows)")


if __name__ == "__main__":
    main()
