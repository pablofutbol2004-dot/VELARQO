"""Sends a built campaign queue (outreach/campaign_builder/queue.py output)
through whichever EmailProvider the caller passes in. Nothing in the
pipeline knows or cares whether that's Gmail or Outlook.
"""

from integrations.email.base import EmailProvider


def send_campaign_email(provider: EmailProvider, campaign_item: dict) -> dict:
    if not campaign_item.get("email"):
        return {**campaign_item, "status": "skipped_no_email"}

    result = provider.send_email(
        to=campaign_item["email"],
        subject=campaign_item["subject"],
        body=campaign_item["body"],
    )
    return {
        **campaign_item,
        "status": "sent",
        "provider_message_id": result["message_id"],
        "provider_thread_id": result.get("thread_id"),
    }


def send_campaign(provider: EmailProvider, campaign: dict) -> dict:
    sent_queue = [send_campaign_email(provider, item) for item in campaign["queue"]]
    return {**campaign, "queue": sent_queue}
