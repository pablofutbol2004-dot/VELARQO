import csv
import json
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import click
import pandas as pd

from data.db import get_connection, init_db
from integrations.email.gmail import GmailProvider
from integrations.email.outlook import OutlookProvider
from integrations.email.sender import send_campaign
from integrations.ghl.client import GHLClient
from integrations.ghl.sync import sync_leads
from lib.ai.research import research_leads
from lib.normalization.normalize import normalize_lead
from lib.scoring.icp_score import evaluate_lead
from lib.tracking.experiments import record_send
from outreach.campaign_builder.queue import build_campaign_queue
from outreach.personalization.generator import generate_campaign_emails
from prospecting.deduplication.dedupe import deduplicate
from prospecting.enrichment.enrich import EnrichmentProvider, enrich_leads
from prospecting.enrichment.website import WebsiteEnrichmentProvider

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


TIER_ORDER = {"A": 0, "B": 1, "C": 2, "reject": 3, "duplicate": 4}

EXPORT_COLUMNS = [
    "tier", "icp_score", "vertical_fit", "display_name", "email", "website", "phone", "city",
    "postcode", "osm_category", "score_reasons", "research_summary", "email_subject", "email_body",
]


def run_pipeline_on_leads(
    leads: list[dict], icp: dict, enrichment_provider: EnrichmentProvider | None = None
) -> list[dict]:
    """Core processing, independent of where leads came from (a raw CSV,
    or already-mapped records from client_onboarding.intake.run_intake()).

    Enrichment runs before scoring so website content and discovered
    emails count toward the score, not just toward the copy.
    """
    for lead in leads:
        lead.setdefault("id", str(uuid.uuid4()))
        lead.setdefault("created_at", datetime.now(timezone.utc).isoformat())

    leads = [normalize_lead(lead) for lead in leads]
    leads = deduplicate(leads)
    leads = enrich_leads(leads, enrichment_provider)

    for lead in leads:
        if lead.get("duplicate_of"):
            lead.update(icp_score=None, qualified=False, tier="duplicate", score_reasons=["duplicate"])
            continue
        result = evaluate_lead(lead, icp)
        lead.update(
            icp_score=result["score"],
            qualified=result["qualified"],
            tier=result["tier"],
            vertical_fit=result["vertical_fit"],
            score_breakdown=result["breakdown"],
            score_reasons=result["reasons"],
        )

    return research_leads(leads, icp)


def run_pipeline(
    csv_path: Path, icp_path: Path = DEFAULT_ICP_PATH, enrichment_provider: EnrichmentProvider | None = None
) -> list[dict]:
    icp = load_icp(icp_path)
    leads = load_leads_from_csv(csv_path)
    return run_pipeline_on_leads(leads, icp, enrichment_provider)


def build_campaign(leads: list[dict], icp: dict, sender_name: str | None = None) -> dict:
    emails = generate_campaign_emails(leads, icp, sender_name)
    return build_campaign_queue(emails, icp)


def export_leads(leads: list[dict], campaign: dict, output_path: Path) -> int:
    by_lead_id = {item["lead_id"]: item for item in campaign["queue"]}
    ordered = sorted(leads, key=lambda l: (TIER_ORDER.get(l.get("tier"), 9), -(l.get("icp_score") or 0)))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=EXPORT_COLUMNS)
        writer.writeheader()
        for lead in ordered:
            email = by_lead_id.get(lead["id"], {})
            row = {col: lead.get(col) for col in EXPORT_COLUMNS}
            row["score_reasons"] = " | ".join(lead.get("score_reasons") or [])
            row["email_subject"] = email.get("subject")
            row["email_body"] = email.get("body")
            writer.writerow(row)
    return len(ordered)


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
@click.option("--email-provider", type=click.Choice(["gmail", "outlook"]), default=None, help="Actually send the campaign via this provider (optional)")
@click.option("--email-token", envvar="EMAIL_ACCESS_TOKEN", default=None, help="OAuth2 access token for --email-provider")
@click.option("--sender-email", envvar="SENDER_EMAIL", default=None, help="Sending mailbox address (required for --email-provider gmail)")
@click.option("--enrich-websites", is_flag=True, help="Fetch each lead's website (robots.txt respected) for emails + content before scoring")
@click.option("--user-agent", default="velarqo-enrichment/0.1", help="Identify yourself when --enrich-websites fetches sites")
@click.option("--sender-name", default=None, help="Signature for generated emails (defaults to the ICP's sender_name)")
@click.option("--export", "export_path", type=click.Path(path_type=Path), default=None, help="Write every lead with tier, score reasons, research and email to CSV")
@click.option("--show-emails/--no-show-emails", default=False, help="Print generated emails")
def main(
    csv_path: Path,
    icp_path: Path,
    save: bool,
    ghl_token: str | None,
    ghl_location: str | None,
    email_provider: str | None,
    email_token: str | None,
    sender_email: str | None,
    enrich_websites: bool,
    user_agent: str,
    sender_name: str | None,
    export_path: Path | None,
    show_emails: bool,
) -> None:
    icp = load_icp(icp_path)
    enrichment_provider = WebsiteEnrichmentProvider(user_agent=user_agent) if enrich_websites else None
    leads = run_pipeline(csv_path, icp_path, enrichment_provider=enrichment_provider)

    if ghl_token:
        if not ghl_location:
            raise click.UsageError("--ghl-location is required when --ghl-token is set")
        client = GHLClient(api_token=ghl_token, location_id=ghl_location)
        leads = sync_leads(client, leads)
        click.echo(f"Synced {sum(1 for l in leads if l.get('ghl_contact_id'))} contacts to GHL\n")

    tiers = Counter(lead.get("tier") for lead in leads)
    click.echo(f"Processed {len(leads)} leads")
    click.echo("  A (send now): {A}   B (send): {B}   C (right fit, not sendable yet): {C}   "
               "reject: {reject}   duplicate: {duplicate}".format(**{t: tiers.get(t, 0) for t in TIER_ORDER}))
    if enrich_websites:
        found = sum(1 for lead in leads if lead.get("email_source") == "website")
        checked = sum(1 for lead in leads if lead.get("website_status") == "ok")
        click.echo(f"  Websites checked: {checked}, emails found on them: {found}")
    click.echo("")

    ordered = sorted(leads, key=lambda l: (TIER_ORDER.get(l.get("tier"), 9), -(l.get("icp_score") or 0)))
    for lead in ordered:
        if lead.get("tier") in ("reject", "duplicate"):
            continue
        reasons = "; ".join(lead.get("score_reasons") or [])
        click.echo(f"  [{lead['tier']}] {lead.get('icp_score'):5} {lead.get('display_name', '')[:34]:34} {reasons[:110]}")

    campaign = build_campaign(leads, icp, sender_name)
    click.echo(f"\nCampaign {campaign['campaign_id']} queued: {len(campaign['queue'])} emails")
    if show_emails:
        for item in campaign["queue"]:
            click.echo(f"\n--- {item['company_name']} (variant {item['variant_index']}, send {item['send_time']}) ---")
            click.echo(f"Subject: {item['subject']}")
            click.echo(item["body"])

    if export_path:
        count = export_leads(leads, campaign, export_path)
        click.echo(f"Exported {count} leads to {export_path}")

    if email_provider:
        if not email_token:
            raise click.UsageError("--email-token is required when --email-provider is set")
        if email_provider == "gmail":
            if not sender_email:
                raise click.UsageError("--sender-email is required when --email-provider gmail is set")
            provider = GmailProvider(access_token=email_token, sender_email=sender_email)
        else:
            provider = OutlookProvider(access_token=email_token)
        campaign = send_campaign(provider, campaign)
        sent_count = sum(1 for item in campaign["queue"] if item["status"] == "sent")
        click.echo(f"\nSent {sent_count}/{len(campaign['queue'])} emails via {email_provider}")
        blocked = Counter(r for item in campaign["queue"] for r in item.get("blocked_reasons", []))
        for reason, count in blocked.most_common():
            click.echo(f"  blocked {count}: {reason}")

    if save:
        save_leads(leads)
        for item in campaign["queue"]:
            record_send(item, vertical=icp.get("vertical"))
        click.echo("\nSaved to data/velarqo.db (leads + experiment_result rows)")


if __name__ == "__main__":
    main()
